import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    _database_url = os.getenv("DATABASE_URL", "sqlite:///prode.db")
    if _database_url and _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)
    if _database_url and "postgresql" in _database_url:
        import re
        _database_url = re.sub(r'[\?&]sslmode=[^&]*', '', _database_url)
        if "?" in _database_url:
            _database_url += "&sslmode=disable"
        else:
            _database_url += "?sslmode=disable"
    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
    API_FOOTBALL_BASE_URL = "https://api.football-data.org/v4"
    WC_COMPETITION_ID = 2000
    WC_YEAR = 2026
