import asyncio
from core.database.session import AsyncSessionLocal
from core.database.models import Word, Quiz, Progress
from sqlalchemy import delete

async def clear_data():
    async with AsyncSessionLocal() as session:
        print("Deleting Progress...")
        await session.execute(delete(Progress))
        
        print("Deleting Quizzes...")
        await session.execute(delete(Quiz))
        
        print("Deleting Words...")
        await session.execute(delete(Word))
        
        await session.commit()
        print("All words and related data cleared successfully!")

if __name__ == "__main__":
    asyncio.run(clear_data())
