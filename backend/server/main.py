from fastapi import FastAPI

from .routes.upload_pdfs import router as upload_router
from .routes.ask_question import router as ask_router
from .routes.simple_ask import router as simple_ask_router
from .routes.sota_ask import router as sota_ask_router
from .routes.medrag_baseline import router as medrag_baseline_router
from .routes.no_rag import router as no_rag_router
from .routes.health import router as health_router
from .routes.langsmith_health import router as langsmith_router
from .routes.metrics import router as metrics_router

from .modules.rate_limiter import limiter

from fastapi.middleware.cors import CORSMiddleware
from .middlewares.exceptionHandlers import catch_exception_from_middleware
from .modules.db_logger import init_db

app = FastAPI(
    title="Medical Assistant API",
    version="1.0",
    description="API for Medical Assistant ChatBot Application",
)

app.state.limiter = limiter


@app.on_event("startup")
async def startup_event():
    await init_db()
    _init_uq_pipeline()


def _init_uq_pipeline():
    """Initialize UQ pipeline with trained models."""
    from pathlib import Path
    from server.modules.verifier.classifier import ThreeWayVerifier
    from server.modules.verifier.conformal import ConformalPredictor
    from server.modules.verifier.calibration import ProbabilityCalibrator
    from server.modules.claims.composer import ClaimComposer
    from server.modules.eav.controller import EAVController
    from server.modules.output.answer import AnswerComposer
    from server.modules.query_handlers import init_uq_pipeline
    from server.schemas import CalibrationArtifact
    from sentence_transformers import SentenceTransformer
    import json

    repo_root = Path(__file__).parent.parent.parent
    models_dir = repo_root / "data" / "models"

    # Load embedding model
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    # Load verifier
    verifier_path = str(models_dir / "verifier_gp.joblib")
    verifier = ThreeWayVerifier(model_path=verifier_path, embedding_model=embedding_model)

    # Load conformal quantile and create predictor
    conformal_path = models_dir / "conformal_quantile.json"
    with open(conformal_path, 'r') as f:
        conformal_data = json.load(f)
    alpha = conformal_data.get("alpha", 0.10)
    quantile = conformal_data.get("quantile", 0.5)

    # Create conformal predictor from saved quantile (no calibration data needed at inference)
    conformal = ConformalPredictor.from_quantile(quantile=quantile, alpha=alpha, method="LAC")

    # Create calibrator (loaded from training)
    calibrator_path = str(models_dir / "calibrator.joblib")
    calibrator = ProbabilityCalibrator(method="isotonic")
    calibrator.load(calibrator_path)

    # Create other components
    claim_composer = ClaimComposer()
    eav_controller = EAVController(action_budget=1)
    answer_composer = AnswerComposer()

    # Create calibration artifact
    calibration_artifact = CalibrationArtifact(
        calibration_id="calibration-v1",
        verifier_model="random-forest-v1",
        calibrator_type="isotonic",
        conformal_method="LAC",
        alpha=alpha,
        feature_schema_version="v1",
        corpus_family="mirage-pubmed",
        quantile=quantile,
    )

    init_uq_pipeline(
        claim_composer=claim_composer,
        verifier=verifier,
        conformal_predictor=conformal,
        eav_controller=eav_controller,
        answer_composer=answer_composer,
        calibration_artifact=calibration_artifact,
        embedding_model=embedding_model,
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=["*"],
    allow_headers=["*"],
)

# add middleware exception handlers
app.middleware("http")(catch_exception_from_middleware)

# add routers - 1) upload PDF documents 2) asking query 3) simple RAG baseline 4) SOTA baseline 5) MedRAG baseline 6) No-RAG baseline
app.include_router(upload_router)
app.include_router(ask_router)
app.include_router(simple_ask_router)
app.include_router(sota_ask_router)
app.include_router(medrag_baseline_router)
app.include_router(no_rag_router)
app.include_router(health_router)
app.include_router(langsmith_router)
app.include_router(metrics_router)
