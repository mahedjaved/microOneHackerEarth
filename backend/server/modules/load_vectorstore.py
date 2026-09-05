import time
from pathlib import Path
from tqdm.auto import tqdm
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from server.logger import logger
from server.config import settings


PINECONE_API_KEY = settings.pinecone_api_key
PINECONE_ENV = settings.pinecone_env
PINECONE_INDEX_NAME = settings.pinecone_index_name
RELAXATION_TIME = settings.relaxation_time

UPLOAD_DIR = settings.uploaded_docs_dir
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

pinecone = None
index = None
embedding_model = None

try:
    pinecone = Pinecone(api_key=PINECONE_API_KEY)
    serverless_spec = ServerlessSpec(
        cloud="aws",
        region=PINECONE_ENV,
    )

    existing_indexes = pinecone.list_indexes().names()
    if PINECONE_INDEX_NAME not in existing_indexes:
        print(f"Creating Pinecone index: {PINECONE_INDEX_NAME}")
        pinecone.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=768,
            metric="dotproduct",
            spec=serverless_spec,
        )

        while not pinecone.describe_index(PINECONE_INDEX_NAME).status["ready"]:
            print("Waiting for Pinecone index to be ready...")
            time.sleep(RELAXATION_TIME)

    index = pinecone.Index(name=PINECONE_INDEX_NAME)
    embedding_model = HuggingFaceEmbeddings(model_name="all-mpnet-base-v2")
except Exception as e:
    logger.warning(f"Pinecone not available: {e}. Vector store features disabled.")


# Load, split, embed and upsert pdf document content
def load_vectorstore(uploaded_files):
    file_paths = []

    # 1. Upload files and save to disk
    for uploaded_file in uploaded_files:
        # retrieve the filename
        save_path = Path(UPLOAD_DIR) / uploaded_file.filename
        with open(save_path, "wb") as f:
            f.write(uploaded_file.file.read())
        file_paths.append(str(save_path))

    # 2. Split the documents into chunks
    for file_path in file_paths:
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        # now the splitting part
        recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=100
        )
        chunks = recursive_splitter.split_documents(documents)

        # gather the text content of the chunks for embedding
        texts = [chunk.page_content for chunk in chunks]
        metadata = [{**chunk.metadata, "text": chunk.page_content} for chunk in chunks]

        # get the IDs for the chunks (we can use the filename and the chunk index to create unique IDs)
        ids = [f"{Path(file_path).stem}-{i}" for i in range(len(chunks))]

        # 3. Embedding the chunks
        logger.info(f"Now embedding chunks ...")
        embeddings = embedding_model.embed_documents(texts)

        # 4. Upsert to Pinecone
        logger.info(f"Now upserting {len(embeddings)} chunks ...")
        with tqdm(total=len(embeddings), desc="Upserting to Pinecone") as pbar:
            index.upsert(vectors=zip(ids, embeddings, metadata))
            pbar.update(len(ids))

        logger.info(
            f"Finished upserting {len(embeddings)} chunks for file: {file_path}"
        )

