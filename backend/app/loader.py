import os
import asyncio
from uuid import uuid4
from tqdm import tqdm
from pdfminer.high_level import extract_text
from app.utils.splitter import TextSplitter
from app.openai import get_embeddings, token_size
from app.db import get_redis, setup_db, add_chunks_to_vector_db
from app.config import settings

# Split an iterable into chunks of size 'batch_size'
def batchify(iterable, batch_size):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i+batch_size]

# Load documents
# 1. Extract text from documents
# 2. Split documents into chunks
# 3. Embed chunks
# 4. Add chunks to Redis database  
async def process_docs(docs_dir=settings.DOCS_DIR):
    docs = []
    
    print('\nLoading documents')
    
    # If file ends with .pdf, add to list 'pdf_files'
    pdf_files = [file for file in os.listdir(docs_dir) if file.endswith('.pdf')]
    
    # Load PDF documents into memory
    for filename in tqdm(pdf_files):
        file_path = os.path.join(docs_dir, filename)
        text = extract_text(file_path)
        doc_name = os.path.splitext(filename)[0]
        docs.append((doc_name, text))
        
    print(f'Loaded {len(docs)} PDF documents')

    # Declare empty list 'chunks': Will store the chunks of text
    chunks = []
    
    # Initialize TextSplitter object: Will split text into chunks
    # chunk_size=512: Each chunk will contain 512 tokens
    # chunk_overlap=150: Each chunk will overlap with the previous chunk by 150 tokens 
    text_splitter = TextSplitter(chunk_size=512, chunk_overlap=150)
    
    print('\nSplitting documents into chunks')
    
    # Split documents into chunks
    for doc_name, doc_text in docs:
        doc_id = str(uuid4())[:8]
        doc_chunks = text_splitter.split(doc_text)
        for chunk_idx, chunk_text in enumerate(doc_chunks):
            chunk = {
                'chunk_id': f'{doc_id}:{chunk_idx+1:04}',
                'text': chunk_text,
                'doc_name': doc_name,
                'vector': None
            }
            chunks.append(chunk)
        print(f'{doc_name}: {len(doc_chunks)} chunks')
        
    chunk_sizes = [token_size(c['text']) for c in chunks]
    
    print(f'\nTotal chunks: {len(chunks)}')
    print(f'Min chunk size: {min(chunk_sizes)} tokens')
    print(f'Max chunk size: {max(chunk_sizes)} tokens')
    print(f'Average chunk size: {round(sum(chunk_sizes)/len(chunks))} tokens')

    vectors = []
    
    print('\nEmbedding chunks')
    
    # Used to show progress bar of embedding chunks
    with tqdm(total=len(chunks)) as pbar:
        for batch in batchify(chunks, batch_size=64):
            batch_vectors = await get_embeddings([chunk['text'] for chunk in batch])
            vectors.extend(batch_vectors)
            pbar.update(len(batch))

    for chunk, vector in zip(chunks, vectors):
        chunk['vector'] = vector
    return chunks

# Load knowledge base
async def load_knowledge_base():
    async with get_redis() as rdb:
        print('Setting up Redis database')
        await setup_db(rdb)
        chunks = await process_docs()
        print('\nAdding chunks to vector db')
        await add_chunks_to_vector_db(rdb, chunks)
        print('\nKnowledge base loaded')

def main():
    asyncio.run(load_knowledge_base())


if __name__ == '__main__':
    main()