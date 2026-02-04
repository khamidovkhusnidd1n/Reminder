from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    _ADMIN_IDS_RAW: str = os.getenv("ADMIN_IDS", "")
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/database.db"
    
    @property
    def ADMIN_IDS(self) -> list[int]:
        return [int(x.strip()) for x in self._ADMIN_IDS_RAW.split(",") if x.strip()]
    
    # Bot settings
    DAILY_WORDS_COUNT: int = 10
    
    class Config:
        case_sensitive = True

settings = Settings()
