import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime
import random
from sqlalchemy import select
from core.config import settings
from core.database.session import init_db, AsyncSessionLocal
from core.database.models import User

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    # Initialize database
    await init_db()
    
    # Initialize bot and dispatcher
    from aiogram.client.default import DefaultBotProperties
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register routers
    from bot.handlers import common, words, quizzes, admin
    dp.include_router(common.router)
    dp.include_router(words.router)
    dp.include_router(quizzes.router)
    dp.include_router(admin.router)
    
    logging.info("Starting bot...")
    
    # Start reminder task
    asyncio.create_task(reminder_task(bot))
    
    await dp.start_polling(bot)

async def reminder_task(bot: Bot):
    motivational_messages = [
        "🚀 Bugun hali bitta ham so'z yodlamadingiz! Maqsadingiz sari bir qadam bo'lsa ham bosing.",
        "💡 Bilim - bu kuch. Kunlik 10 ta so'zni yodlashga atigi 5 daqiqa vaqt ketadi!",
        "🔥 Streakingizni yo'qotmang! Bugun ham faol bo'ling.",
        "🎯 Maqsadingiz sari, to'xtab qolmang!"
    ]
    
    while True:
        # Check every hour or at specific times
        now = datetime.now()
        if now.hour == 10 or now.hour == 18: # Remind at 10 AM and 6 PM
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(User))
                users = res.scalars().all()
                for user in users:
                    try:
                        await bot.send_message(
                            user.telegram_id, 
                            random.choice(motivational_messages)
                        )
                    except Exception as e:
                        logging.error(f"Could not send reminder to {user.telegram_id}: {e}")
        
        await asyncio.sleep(3600) # Sleep for 1 hour

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
