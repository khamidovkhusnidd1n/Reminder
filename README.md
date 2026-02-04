# Essential 4000 Words Bot & Admin Panel

Bu loyiha "4000 Essential English Words" kitobidan har kuni 10 tadan so'z yodlashni va ularni test orqali mustahkamlashni ta'minlaydi.

## Imkoniyatlar
- **Telegram Bot**: 
  - Har kuni 10 ta yangi so'z.
  - Multi-choice (A, B, C, D) testlar.
  - Motivatsion eslatmalar (soat 10:00 va 18:00 da).
  - Shaxsiy statistika (streak, o'rganilgan so'zlar).
- **Admin Panel (Web)**:
  - Premium dizayn (Glassmorphism).
  - So'zlarni qo'shish va boshqarish.
  - Testlarni (quizzes) yaratish.
  - Foydalanuvchilar statistikasi.

## O'rnatish

1. Kerakli kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```

2. `.env` faylini oching va bot tokeningizni kiriting:
   ```env
   BOT_TOKEN=Sizning_Bot_Tokeningiz
   ADMIN_IDS=Sizning_IDingiz
   ```

3. Loyihani ishga tushiring:
   ```bash
   python main.py
   ```

## Texnologiyalar
- **Bot**: Aiogram 3.x
- **Admin Panel**: FastAPI
- **Database**: SQLite (SQLAlchemy)
- **UI**: Vanilla HTML/CSS (Modern Glassmorphism)
