import asyncio
from core.database.session import AsyncSessionLocal
from core.database.models import Word
from sqlalchemy import delete

async def clean_headers():
    async with AsyncSessionLocal() as session:
        # Delete words where word itself is 'word' or 'Word' or 'Inglizcha' etc
        bad_words = ["word", "inglizcha", "Inglizcha"]
        
        for w in bad_words:
            await session.execute(delete(Word).where(Word.word == w))
        
        await session.commit()
        print("Cleaned up bad data.")

if __name__ == "__main__":
    asyncio.run(clean_headers())
