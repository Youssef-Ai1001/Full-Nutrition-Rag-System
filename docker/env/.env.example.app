APP_NAME="Nutrition-Rag-App"
APP_VERSION="0.1"
OPENAI_API_KEY="your_openai_api_key_here"

FILE_ALLOWED_TYPES= # ["text/plain","application/pdf"]
FILE_MAX_SIZE=10
FILE_DEFAULT_CHUNK_SIZE=512000  # 512KB   

# ========================= PostgresDB Config =========================
POSTGRES_USERNAME=""
POSTGRES_PASSWORD=""
POSTGRES_HOST="pgvector"
POSTGRES_PORT=5432
POSTGRES_MAIN_DATABASE=""

# ========================= LLM Config =========================
GENERATION_BACKEND="COHERE"
EMBEDDING_BACKEND="COHERE"

OPENAI_API_KEY=""
OPENAI_API_URL=
COHERE_API_KEY=""

GENERATION_MODEL_ID_LITERAL = ["llama3:latest", "qwen3:latest"]
GENERATION_MODEL_ID="command-a-03-2025"
EMBEDDING_MODEL_ID= "embed-multilingual-v3.0"     # "embed-multilingual-light-v3.0"
EMBEDDING_MODEL_SIZE= 1024  # 384

INPUT_DAFAULT_MAX_CHARACTERS=1024
GENERATION_DAFAULT_MAX_TOKENS=200
GENERATION_DAFAULT_TEMPERATURE=0.1

# ========================= Vector DB Config =========================
VECTOR_DB_BACKEND_LITERAL = ["QDRANT", "PGVECTOR"]
VECTOR_DB_BACKEND="PGVECTOR"
VECTOR_DB_PATH="qdrant_db"
VECTOR_DB_DISTANCE_METHOD="cosine"
VECTOR_DB_PGVEC_INDEX_THRESHOLD = 

# ========================= Template Configs =========================
PRIMARY_LANG = "en"
DEFAULT_LANG = "en"