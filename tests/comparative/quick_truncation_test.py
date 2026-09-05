"""Quick truncation test - query Pinecone directly to check passage lengths."""
import os
import sys
from pathlib import Path

# Change to backend directory and add it to path
script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
backend_dir = project_dir / "backend"
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from server.modules.load_vectorstore import embedding_model, PINECONE_INDEX_NAME
from server.config import settings
from pinecone import Pinecone

pc = Pinecone(api_key=settings.pinecone_api_key)
index = pc.Index(PINECONE_INDEX_NAME)

questions = [
    ('D1', 'According to the aspirin document, what is the maximum single adult dose?'),
    ('D2', 'What does the aspirin document say about administration with food?'),
    ('D5', 'According to the document, should aspirin be taken with food or on an empty stomach?'),
]

for qid, q in questions:
    print(f'\n[{qid}] {q[:60]}...')
    emb = embedding_model.embed_query(q)
    resp = index.query(vector=emb, top_k=2, include_metadata=True)
    for i, match in enumerate(resp['matches']):
        text = match['metadata'].get('text', '')
        print(f'  Passage {i+1}: {len(text)} chars, score={match["score"]:.3f}')
        print(f'    Full text: "{text}"')
        # Check keywords
        keywords = ['500', 'mg', 'dose', 'food', 'stomach', 'irritation', 'empty', 'maximum', 'single', 'adult']
        for kw in keywords:
            if kw in text.lower():
                print(f'    Keyword "{kw}" FOUND')
