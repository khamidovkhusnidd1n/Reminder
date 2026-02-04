from aiogram import Router, types, F
from aiogram.filters import Command
import re
from aiogram.fsm.context import FSMContext
from core.config import settings
from bot.states import AddWordState, BulkImportState
from core.database.session import AsyncSessionLocal
from core.database.models import Word, User
from sqlalchemy import select

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS

@router.message(Command("addword"))
async def cmd_addword(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Bu buyruq faqat adminlar uchun.")
        return
        
    await message.answer("📝 Yangi so'zni kiriting (inglizcha):")
    await state.set_state(AddWordState.waiting_for_word)

@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Faqat adminlar uchun!", show_alert=True)
        return

    builder = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ So'z qo'shish", callback_data="admin_add_word")],
        [types.InlineKeyboardButton(text="📥 Text Import", callback_data="admin_text_import")],
        [types.InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text("👨‍💻 <b>Admin Panel</b>\n\nKerakli bo'limni tanlang:", reply_markup=builder)

@router.callback_query(F.data == "admin_add_word")
async def cb_add_word(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📝 Yangi so'zni kiriting (inglizcha):")
    await state.set_state(AddWordState.waiting_for_word)
    await callback.answer()

@router.callback_query(F.data == "admin_text_import")
async def cb_text_import(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("🔢 Qaysi <b>Unit</b> uchun so'zlar qo'shmoqchisiz? (raqam kiriting):")
    await state.set_state(BulkImportState.waiting_for_unit)
    await callback.answer()

@router.message(BulkImportState.waiting_for_unit)
async def bulk_process_unit(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Iltimos, raqam kiriting.")
        return
    await state.update_data(unit=int(message.text))
    await message.answer("📚 Qaysi <b>Kitob</b> (Volume) uchun? (raqam kiriting):")
    await state.set_state(BulkImportState.waiting_for_book)

@router.message(BulkImportState.waiting_for_book)
async def bulk_process_book(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Iltimos, raqam kiriting.")
        return
    await state.update_data(book=int(message.text))
    
    msg = (
        "📝 Endi so'zlar ro'yxatini quyidagi formatda yuboring:\n\n"
        "<code>word,translation</code>\n"
        "<code>apple,olma</code>\n"
        "<code>book-kitob</code>\n\n"
        "⚠️ Siz vergul (,) yoki chiziqcha (-) ishlatishingiz mumkin.\n"
        "⚠️ Har bir so'z yangi qatorda bo'lishi shart!\n"
        "⚠️ Definition (tavsif) avtomatik ravishda '...' deb belgilanadi."
    )
    await message.answer(msg)
    await state.set_state(BulkImportState.waiting_for_data)

@router.message(BulkImportState.waiting_for_data)
async def bulk_process_data(message: types.Message, state: FSMContext):
    data = await state.get_data()
    unit = data['unit']
    book = data['book']
    
    lines = message.text.strip().split('\n')
    added_count = 0
    errors = []
    
    async with AsyncSessionLocal() as session:
        for line in lines:
            # Split by comma OR hyphen
            parts = re.split(r'[,-]', line, maxsplit=1)
            
            # Skip potential header rows or empty/short lines
            if len(parts) >= 2:
                w_check = parts[0].strip().lower()
                t_check = parts[1].strip().lower()
                if w_check in ["word", "inglizcha", "so'z"] or t_check in ["translation", "tarjima"]:
                    continue
                word_text = parts[0].strip()
                translation = parts[1].strip()
                # Optional: extra parts logic if needed
                
                new_word = Word(
                    word=word_text,
                    translation=translation,
                    definition="...", # Default definition
                    unit=unit,
                    book_volume=book
                )
                session.add(new_word)
                added_count += 1
            else:
                if line.strip():
                    errors.append(line)
        
        if added_count > 0:
            await session.commit()
            
    res_msg = f"✅ <b>{added_count} ta so'z muvaffaqiyatli qo'shildi!</b>"
    if errors:
        res_msg += f"\n\n⚠️ Quyidagi qatorlar tushunarsiz formatda:\n" + "\n".join(errors[:10])
    
    await message.answer(res_msg)
    await state.clear()

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: types.CallbackQuery):
    # This should act like /start but editing the message
    await callback.message.delete()
    # We can't easily trigger the exact logic of cmd_start without the builder code duplication or a shared function.
    # For now, just send a new message is easier or copy the builder.
    # Let's just ask user to press /start or mock it.
    await callback.message.answer("Asosiy menyuga qaytish uchun /start ni bosing.") 
    # Or proper way: import cmd_start logic. But keeping it simple.


@router.message(AddWordState.waiting_for_word)
async def process_word(message: types.Message, state: FSMContext):
    await state.update_data(word=message.text)
    await message.answer("🇺🇿 Tarjimasini kiriting:")
    await state.set_state(AddWordState.waiting_for_translation)

@router.message(AddWordState.waiting_for_translation)
async def process_translation(message: types.Message, state: FSMContext):
    await state.update_data(translation=message.text)
    await message.answer("📖 Tavsifini (definition) kiriting:")
    await state.set_state(AddWordState.waiting_for_definition)

@router.message(AddWordState.waiting_for_definition)
async def process_definition(message: types.Message, state: FSMContext):
    await state.update_data(definition=message.text)
    await message.answer("🔢 Unit raqamini kiriting (masalan: 1):")
    await state.set_state(AddWordState.waiting_for_unit)

@router.message(AddWordState.waiting_for_unit)
async def process_unit(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Iltimos, raqam kiriting.")
        return
    await state.update_data(unit=int(message.text))
    await message.answer("📚 Kitob raqamini kiriting (masalan: 1):")
    await state.set_state(AddWordState.waiting_for_book)

@router.message(AddWordState.waiting_for_book)
async def process_book(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Iltimos, raqam kiriting.")
        return
        
    data = await state.get_data()
    book_volume = int(message.text)
    
    # Save to DB
    async with AsyncSessionLocal() as session:
        new_word = Word(
            word=data['word'],
            translation=data['translation'],
            definition=data['definition'],
            unit=data['unit'],
            book_volume=book_volume
        )
        session.add(new_word)
        await session.commit()
    
    await message.answer(
        f"✅ <b>Yangi so'z qo'shildi!</b>\n\n"
        f"🇺🇸 Word: {data['word']}\n"
        f"🇺🇿 Tarjima: {data['translation']}\n"
        f"📖 Definition: {data['definition']}\n"
        f"🔢 Unit: {data['unit']}, Book: {book_volume}"
    )
    await state.clear()
