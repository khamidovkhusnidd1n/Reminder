from aiogram import Router, types, F
from sqlalchemy import select, func
from core.database.session import AsyncSessionLocal
from core.database.models import User, Word, Progress
from datetime import datetime

router = Router()

async def get_daily_words(user_id: int):
    async with AsyncSessionLocal() as session:
        # Get user
        res = await session.execute(select(User).where(User.telegram_id == user_id))
        user = res.scalar_one_or_none()
        
        if not user:
            return []

        # Find words user hasn't mastered yet
        # For simplicity, we just pick 10 words from the current unit or next available
        stmt = select(Word).where(
            ~select(Progress).where(
                (Progress.user_id == user.id) & (Progress.word_id == Word.id) & (Progress.mastered == True)
            ).exists()
        ).limit(10)
        
        result = await session.execute(stmt)
        return result.scalars().all()

@router.callback_query(F.data == "start_learning")
async def start_learning(callback: types.CallbackQuery):
    words = await get_daily_words(callback.from_user.id)
    
    if not words:
        await callback.message.edit_text("Hozircha o'rganish uchun yangi so'zlar qolmagan! 🎉")
        return

    text = "📚 <b>Bugungi so'zlar:</b>\n\n"
    for i, w in enumerate(words, 1):
        text += f"{i}. <b>{w.word}</b> - {w.translation}\n"
        text += f"   <i>{w.definition}</i>\n\n"
    
    text += "Tayyor bo'lsangiz, testni boshlaymiz!"
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✍️ Testni boshlash", callback_data="start_test")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)


