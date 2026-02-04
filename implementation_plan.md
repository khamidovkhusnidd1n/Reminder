# Implementation Plan - Essential 4000 Words Bot

This project aims to create a Telegram bot that helps users learn 10 words daily from "4000 Essential English Words" and includes an admin dashboard for test management.

## Tech Stack
- **Language**: Python 3.10+
- **Bot Framework**: `aiogram` (v3)
- **Web Framework**: `FastAPI` (for Admin Panel)
- **Database**: `SQLite` with `SQLAlchemy`
- **Frontend**: Vanilla HTML/JS with modern CSS (Admin Panel)

## Project Structure
```
/
├── bot/
│   ├── handlers/
│   ├── keyboards/
│   ├── middlewares/
│   └── bot.py
├── admin/
│   ├── static/
│   ├── templates/
│   └── main.py
├── core/
│   ├── database/
│   │   ├── models.py
│   │   └── session.py
│   └── config.py
├── data/
│   └── database.db
├── main.py
└── requirements.txt
```

## Phases
1. **Phase 1: Foundation**
   - [ ] Setup database models (User, Word, Quiz, Progress).
   - [ ] Configure environment variables (Bot Token, DB Path).
2. **Phase 2: Telegram Bot**
   - [ ] Implement /start and registration.
   - [ ] Daily schedule for word delivery (10 words).
   - [ ] Quiz system (Multiple choice).
   - [ ] Motivation/Reminder logic.
3. **Phase 3: Admin Panel**
   - [ ] Develop FastAPI backend for word/quiz management.
   - [ ] Build premium-looking UI for admin.
   - [ ] Import functionality for word lists.
4. **Phase 4: Integration & Deployment**
   - [ ] Connect bot and admin panel via shared database.
   - [ ] Testing and polish.
