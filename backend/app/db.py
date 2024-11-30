import json
import numpy as np
from redis.asyncio import Redis
from redis.commands.search.field import TextField, VectorField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from redis.commands.json.path import Path
from app.config import settings

# Constants for index and prefix names
VECTOR_IDX_NAME = 'idx:vector'  # Index name for vector data
VECTOR_IDX_PREFIX = 'vector:'  # Prefix for keys stored in the vector index
CHAT_IDX_NAME = 'idx:chat'  # Index name for chat data
CHAT_IDX_PREFIX = 'chat:'  # Prefix for keys stored in the chat index

# Function to initialize a Redis connection
def get_redis():
    return Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

# VECTORS

# Create a Redis index for storing and searching vectors
async def create_vector_index(rdb):
    schema = (
        TextField('$.chunk_id', no_stem=True, as_name='chunk_id'),  # Chunk ID field for unique identifiers
        TextField('$.text', as_name='text'),  # Text field to store content
        TextField('$.doc_name', as_name='doc_name'),  # Document name field
        VectorField(  # Vector field for storing embeddings
            '$.vector',
            'FLAT',  # Flat indexing method for KNN search
            {
                'TYPE': 'FLOAT32',  # Data type of the vector
                'DIM': settings.EMBEDDING_DIMENSIONS,  # Dimensionality of embeddings
                'DISTANCE_METRIC': 'COSINE'  # Metric used for similarity search
            },
            as_name='vector'
        )
    )
    try:
        # Create the index with the specified schema
        await rdb.ft(VECTOR_IDX_NAME).create_index(
            fields=schema,
            definition=IndexDefinition(prefix=[VECTOR_IDX_PREFIX], index_type=IndexType.JSON)
        )
        print(f"Vector index '{VECTOR_IDX_NAME}' created successfully")
    except Exception as e:
        print(f"Error creating vector index '{VECTOR_IDX_NAME}': {e}")

# Add multiple vector chunks to the vector database
async def add_chunks_to_vector_db(rdb, chunks):
    async with rdb.pipeline(transaction=True) as pipe:
        # Use pipeline for batch processing of chunks
        for chunk in chunks:
            pipe.json().set(VECTOR_IDX_PREFIX + chunk['chunk_id'], Path.root_path(), chunk)
        await pipe.execute()

# Perform a KNN search on the vector database using a query vector
async def search_vector_db(rdb, query_vector, top_k=settings.VECTOR_SEARCH_TOP_K):
    query = (
        Query(f'(*)=>[KNN {top_k} @vector $query_vector AS score]')  # KNN query to find top_k matches
        .sort_by('score')  # Sort results by similarity score
        .return_fields('score', 'chunk_id', 'text', 'doc_name')  # Specify fields to return
        .dialect(2)  # Use JSONPath support
    )
    
    res = await rdb.ft(VECTOR_IDX_NAME).search(query, {
        'query_vector': np.array(query_vector, dtype=np.float32).tobytes()  # Convert vector to binary for Redis
    })
    
    # Transform results into a list of dictionaries
    return [{
        'score': 1 - float(d.score),  # Convert similarity score (1 - distance for cosine similarity)
        'chunk_id': d.chunk_id,
        'text': d.text,
        'doc_name': d.doc_name
    } for d in res.docs]

# Retrieve all vector entries from the database
async def get_all_vectors(rdb):
    count = await rdb.ft(VECTOR_IDX_NAME).search(Query('*').paging(0, 0))  # Count total documents
    res = await rdb.ft(VECTOR_IDX_NAME).search(Query('*').paging(0, count.total))  # Retrieve all documents
    
    return [json.loads(doc.json) for doc in res.docs]  # Convert JSON strings to Python dictionaries

# CHATS

# Create a Redis index for storing chat metadata
async def create_chat_index(rdb):
    try:
        schema = (
            NumericField('$.created', as_name='created', sortable=True),  # Timestamp field for sorting chats
        )
        await rdb.ft(CHAT_IDX_NAME).create_index(
            fields=schema,
            definition=IndexDefinition(prefix=[CHAT_IDX_PREFIX], index_type=IndexType.JSON)
        )
        print(f"Chat index '{CHAT_IDX_NAME}' created successfully")
    except Exception as e:
        print(f"Error creating chat index '{CHAT_IDX_NAME}': {e}")

# Create a new chat entry in the database
async def create_chat(rdb, chat_id, created):
    chat = {'id': chat_id, 'created': created, 'messages': []}  # Define chat structure
    await rdb.json().set(CHAT_IDX_PREFIX + chat_id, Path.root_path(), chat)  # Store chat in Redis
    
    return chat

# Add messages to an existing chat
async def add_chat_messages(rdb, chat_id, messages):
    await rdb.json().arrappend(CHAT_IDX_PREFIX + chat_id, '$.messages', *messages)  # Append messages to chat

# Check if a chat exists in the database
async def chat_exists(rdb, chat_id):
    return await rdb.exists(CHAT_IDX_PREFIX + chat_id)

# Retrieve messages from a chat (optionally limit to the last N messages)
async def get_chat_messages(rdb, chat_id, last_n=None):
    if last_n is None:
        messages = await rdb.json().get(CHAT_IDX_PREFIX + chat_id, '$.messages[*]')
    else:
        messages = await rdb.json().get(CHAT_IDX_PREFIX + chat_id, f'$.messages[-{last_n}:]')
        
    # Return formatted messages or an empty list if none exist
    return [{'role': m['role'], 'content': m['content']} for m in messages] if messages else []

# Retrieve a full chat entry by its ID
async def get_chat(rdb, chat_id):
    return await rdb.json().get(chat_id)

# Retrieve all chats sorted by creation time
async def get_all_chats(rdb):
    q = Query('*').sort_by('created', asc=False)  # Query to fetch chats sorted by timestamp
    count = await rdb.ft(CHAT_IDX_NAME).search(q.paging(0, 0))  # Count total chats
    res = await rdb.ft(CHAT_IDX_NAME).search(q.paging(0, count.total))  # Retrieve all chat entries
    
    return [json.loads(doc.json) for doc in res.docs]  # Convert JSON strings to Python dictionaries

# DB SETUP: VECTORS AND CHATS

# Setup both vector and chat indices in the database
async def setup_db(rdb):
    # Create the vector index (delete existing one if necessary)
    try:
        await rdb.ft(VECTOR_IDX_NAME).dropindex(delete_documents=True)
        print(f"Deleted vector index '{VECTOR_IDX_NAME}' and all associated documents")
    except Exception as e:
        pass
    finally:
        await create_vector_index(rdb)

    # Ensure the chat index exists, create if not present
    try:
        await rdb.ft(CHAT_IDX_NAME).info()
    except Exception:
        await create_chat_index(rdb)

# Clear all data by dropping both vector and chat indices
async def clear_db(rdb):
    for index_name in [VECTOR_IDX_NAME, CHAT_IDX_NAME]:
        try:
            await rdb.ft(index_name).dropindex(delete_documents=True)
            print(f"Deleted index '{index_name}' and all associated documents")
        except Exception as e:
            print(f"Index '{index_name}': {e}")
