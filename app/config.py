import os
from pathlib import Path
from dotenv import load_dotenv

# === Load .env file ===
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Configuration class for the Document QA System"""

    #LLM Configuration 
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_API_BASE = os.getenv("GROQ_API_BASE", "https://api.groq.com/openai/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3-70b-8192")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    #vector store
    FAISS_INDEX_PATH = "data/vector_store"
    EMBEDDING_DIMENSION = 384
    CHUNK_SIZE = 300
    CHUNK_OVERLAP = 50
    MAX_CHUNKS_PER_QUERY = 10

    #upload
    UPLOAD_FOLDER = "uploads"
    MAX_FILE_SIZE = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.jpg', '.jpeg', '.png', '.md', '.csv', '.docx'}

    # query
    MAX_QUERY_LENGTH = 1000
    MIN_SIMILARITY_SCORE = 0.3

    # theme
    MAX_THEMES = 5
    MIN_THEME_DOCUMENTS = 2

    #PAths
    DATA_DIR = BASE_DIR / "data"
    UPLOADS_DIR = BASE_DIR / UPLOAD_FOLDER
    LOGS_DIR = BASE_DIR / "logs"

    #OCR
    TESSERACT_CONFIG = '--oem 3 --psm 6'

    #logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def create_directories(cls):
        for dir_path in [cls.DATA_DIR, cls.UPLOADS_DIR, cls.LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate_config(cls):
        errors = []

        if cls.LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is not set")
        elif cls.LLM_PROVIDER == "groq" and not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is not set")

        if cls.CHUNK_OVERLAP >= cls.CHUNK_SIZE:
            errors.append("CHUNK_OVERLAP must be less than CHUNK_SIZE")

        if cls.MAX_CHUNKS_PER_QUERY <= 0:
            errors.append("MAX_CHUNKS_PER_QUERY must be positive")

        if errors:
            raise ValueError("Configuration errors: " + "; ".join(errors))

        return True

def get_config():
    env = os.getenv('FASTAPI_ENV','development').lower()
    return Config()

config = get_config()
config.create_directories()
