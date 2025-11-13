import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

class Config:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET")
    ALGORITHM: str = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    #SECRET_KEY = os.getenv("SECRET")
    REFRESH_SECRET_KEY: str = os.getenv("REFRESH_SECRET")
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
