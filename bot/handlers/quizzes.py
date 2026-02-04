from aiogram import Router, types, F
from sqlalchemy import select, func
from core.database.session import AsyncSessionLocal
from core.database.models import User, Word, Quiz, Progress
import random

router = Router()

@router.callback_query(F.data == "start_test")
async def send_quiz(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        # Get user for stats
        res_user = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = res_user.scalar_one_or_none()
        
        current_streak = user.streak if user else 0
        current_xp = user.xp if user else 0

        # Get random quiz
        stmt = select(Quiz).order_by(select(func.random())).limit(1)
        res = await session.execute(stmt)
        quiz = res.scalar_one_or_none()
        
        if not quiz:
            await callback.message.edit_text("🚫 <b>O'yin uchun so'zlar yetarli emas!</b>\nAdmin panel orqali so'z va testlar qo'shing.")
            return

        text = (
            f"⚡️ <b>GAME MODE</b> ⚡️\n\n"
            f"🎯 <b>Translate:</b> <code>{quiz.word.word}</code>\n\n"
            f"🏆 <b>XP:</b> {current_xp} | 🔥 <b>Streak:</b> {current_streak}x\n\n"
            "👇 <i>To'g'ri javobni tanlang:</i>"
        )
        
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text=f"A) {quiz.option_a}", callback_data=f"quiz_{quiz.id}_a"),
                types.InlineKeyboardButton(text=f"B) {quiz.option_b}", callback_data=f"quiz_{quiz.id}_b")
            ],
            [
                types.InlineKeyboardButton(text=f"C) {quiz.option_c}", callback_data=f"quiz_{quiz.id}_c"),
                types.InlineKeyboardButton(text=f"D) {quiz.option_d}", callback_data=f"quiz_{quiz.id}_d")
            ],
            [types.InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="back_to_main")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("quiz_"))
async def handle_quiz_answer(callback: types.CallbackQuery):
    _, quiz_id, answer = callback.data.split("_")
    
    async with AsyncSessionLocal() as session:
        stmt = select(Quiz).where(Quiz.id == int(quiz_id))
        res = await session.execute(stmt)
        quiz = res.scalar_one_or_none()
        
        if not quiz:
            await callback.answer("⚠️ Xatolik: Test topilmadi!", show_alert=True)
            return
            
        # Get user to update stats
        res_user = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = res_user.scalar_one_or_none()
        
        if not user:
            # Should not happen usually
            await callback.answer("Foydalanuvchi topilmadi")
            return

        is_correct = quiz.correct_option.lower() == answer.lower()
        
        if is_correct:
            # Gamification logic: Correct
            xp_gain = 10 + (user.streak * 2) # Bonus XP for streak
            user.streak += 1
            user.xp += xp_gain
            user.words_learned += 1 # Creating a simple metric for now
            
            result_text = (
                f"🎉 <b>BOOM! TO'G'RI!</b>\n\n"
                f"✅ Javob: <b>{getattr(quiz, f'option_{answer.lower()}')}</b>\n"
                f"💎 <b>+{xp_gain} XP</b> qo'shildi!\n"
                f"🔥 Streak: <b>{user.streak}x</b>\n"
            )
            btn_text = "➡️ Keyingi Level"
            
            # Update Progress (optional, keeping it simple for now or mark word as REVIEWED)
            # ...
            
        else:
            # Gamification logic: Incorrect
            user.streak = 0
            correct_val = getattr(quiz, f"option_{quiz.correct_option.lower()}")
            result_text = (
                f"💀 <b>GAME OVER...</b>\n\n"
                f"❌ Sizning javobingiz noto'g'ri edi.\n"
                f"✅ To'g'ri javob: <b>{correct_val}</b>\n\n"
                f"💔 <b>Streak 0 ga tushdi!</b>"
            )
            btn_text = "🔄 Qayta urinish"
        
        await session.commit()
            
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=btn_text, callback_data="start_test")],
            [types.InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="back_to_main")]
        ])
        
        await callback.message.edit_text(result_text, reply_markup=keyboard)
