from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from core.database.session import AsyncSessionLocal
from core.database.models import User
from core.config import settings

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    async with AsyncSessionLocal() as session:
        # Check if user exists
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name
            )
            session.add(user)
            await session.commit()
            
    welcome_text = (
        f"👋 Salom, {message.from_user.full_name}!\n\n"
        "Men sizga har kuni <b>yangi so'zlar</b> o'rganishga yordam beraman.\n\n"
        "💡 Har kuni yangi so'zlar va testlar orqali bilimingizni oshirib boramiz.\n\n"
        "Qani, boshladikmi? Quyidagi tugmalardan birini tanlang:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🚀 Boshlash", callback_data="start_learning"))
    builder.row(types.InlineKeyboardButton(text="📊 Mening natijalarim", callback_data="my_stats"))
    
    if message.from_user.id in settings.ADMIN_IDS:
        builder.row(types.InlineKeyboardButton(text="👨‍💻 Admin Panel", callback_data="admin_panel"))
    
    await message.answer(welcome_text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "my_stats")
async def show_stats(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = res.scalar_one_or_none()
        
    if not user:
        await callback.answer("Ma'lumot topilmadi", show_alert=True)
        return
        
    # Simple Level calculation
    level = int(user.xp / 100) + 1
    
    text = (
        f"📊 <b>SIZNING NATIJALARINGIZ</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {user.full_name}\n"
        f"⭐️ <b>Level:</b> {level}\n"
        f"💎 <b>XP:</b> {user.xp}\n"
        f"🔥 <b>Streak:</b> {user.streak}\n"
        f"📚 <b>O'rganilgan so'zlar:</b> {user.words_learned}\n\n"
        f"<i>Davom eting, hali hammasi oldinda!</i> 🚀"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_main"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.delete()
    # Mocking start message again
    # In a real app we might refactor to reuse the welcome message logic
    welcome_text = (
        f"👋 Salom, {callback.from_user.full_name}!\n\n"
        "Men sizga har kuni <b>yangi so'zlar</b> o'rganishga yordam beraman.\n\n"
        "💡 Har kuni yangi so'zlar va testlar orqali bilimingizni oshirib boramiz.\n\n"
        "Qani, boshladikmi? Quyidagi tugmalardan birini tanlang:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🚀 Boshlash", callback_data="start_learning"))
    builder.row(types.InlineKeyboardButton(text="📊 Mening natijalarim", callback_data="my_stats"))
    
    if callback.from_user.id in settings.ADMIN_IDS:
        builder.row(types.InlineKeyboardButton(text="👨‍💻 Admin Panel", callback_data="admin_panel"))
        
    await callback.message.answer(welcome_text, reply_markup=builder.as_markup())
