from fastapi import FastAPI, Request, Form, Depends, HTTPException, UploadFile, File
import json
import re
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.sql.expression import func
import random
from core.database.session import get_db, AsyncSessionLocal
from core.database.models import Word, Quiz, User
from sqlalchemy.orm import joinedload
import uvicorn
import os

app = FastAPI()

# Mount static files
os.makedirs("admin/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="admin/static"), name="static")

# Templates
os.makedirs("admin/templates", exist_ok=True)
templates = Jinja2Templates(directory="admin/templates")

@app.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    # Count stats
    res_words = await db.execute(select(Word))
    words_count = len(res_words.scalars().all())
    
    res_users = await db.execute(select(User))
    users = res_users.scalars().all()
    users_count = len(users)
    
    res_quizzes = await db.execute(select(Quiz))
    quizzes_count = len(res_quizzes.scalars().all())
    
    # Get first user as 'demo' user for local experience
    user = users[0] if users else None
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "words_count": words_count,
        "users_count": users_count,
        "quizzes_count": quizzes_count,
        "user": user
    })

@app.get("/learn", response_class=HTMLResponse)
async def learn_page(request: Request, db: AsyncSession = Depends(get_db)):
    # Get 10 words for today
    res = await db.execute(select(Word).limit(10))
    words = res.scalars().all()
    return templates.TemplateResponse("learn.html", {"request": request, "words": words})

@app.get("/game", response_class=HTMLResponse)
async def game_page(request: Request, db: AsyncSession = Depends(get_db)):
    # Get random quiz with Word relation loaded
    res = await db.execute(
        select(Quiz)
        .options(joinedload(Quiz.word))
        .order_by(func.random())
        .limit(1)
    )
    quiz = res.unique().scalar_one_or_none()
    
    # Get user for stats display
    res_user = await db.execute(select(User))
    user = res_user.scalars().first()
    
    return templates.TemplateResponse("game.html", {"request": request, "quiz": quiz, "user": user})

@app.post("/api/game/answer")
async def game_answer(
    request: Request,
    quiz_id: int = Form(...),
    answer: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Quiz)
        .options(joinedload(Quiz.word))
        .where(Quiz.id == quiz_id)
    )
    quiz = res.unique().scalar_one_or_none()
    
    if not quiz:
        return {"error": "Quiz not found"}
        
    is_correct = quiz.correct_option.lower() == answer.lower()
    
    # Update first user progress
    res_user = await db.execute(select(User))
    user = res_user.scalars().first()
    
    xp_gain = 0
    if user:
        if is_correct:
            xp_gain = 10 + (user.streak * 2)
            user.streak += 1
            user.xp += xp_gain
        else:
            user.streak = 0
        await db.commit()
    
    return {
        "correct": is_correct,
        "correct_option": quiz.correct_option.upper(),
        "correct_text": getattr(quiz, f"option_{quiz.correct_option.lower()}"),
        "xp_gain": xp_gain,
        "new_streak": user.streak if user else 0,
        "new_xp": user.xp if user else 0
    }

@app.get("/words", response_class=HTMLResponse)
async def list_words(request: Request, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Word).order_by(Word.id.desc()))
    words = res.scalars().all()
    return templates.TemplateResponse("words.html", {"request": request, "words": words})

@app.post("/words/delete/{word_id}")
async def delete_word(word_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Word).where(Word.id == word_id))
    await db.commit()
    return RedirectResponse(url="/words", status_code=303)

@app.post("/words/add")
async def add_word(
    word: str = Form(...),
    translation: str = Form(...),
    definition: str = Form(...),
    unit: int = Form(...),
    book_volume: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    new_word = Word(
        word=word,
        translation=translation,
        definition=definition,
        unit=unit,
        book_volume=book_volume
    )
    db.add(new_word)
    await db.commit()
    return RedirectResponse(url="/words", status_code=303)

@app.post("/words/bulk_add")
async def bulk_add_words(
    file: UploadFile = File(None),
    content: str = Form(None),
    default_unit: int = Form(1),
    default_book_volume: int = Form(1),
    db: AsyncSession = Depends(get_db)
):
    data = []
    
    # helper to process raw text lines
    def parse_text_lines(text):
        lines = text.strip().split('\n')
        parsed_data = []
        for line in lines:
            line = line.strip()
            if not line: continue
            # Split by comma OR hyphen
            parts = re.split(r'[,-]', line, maxsplit=1)
            if len(parts) >= 2:
                word_text = parts[0].strip()
                translation = parts[1].strip()
                parsed_data.append({
                    "word": word_text,
                    "translation": translation,
                    "definition": "...", # default
                    "unit": default_unit,
                    "book_volume": default_book_volume
                })
        return parsed_data

    if file and file.filename:
        content_bytes = await file.read()
        try:
            # Try JSON first
            data = json.loads(content_bytes)
        except json.JSONDecodeError:
            # Try text parsing
            try:
                text_content = content_bytes.decode('utf-8')
                data = parse_text_lines(text_content)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid file format")
                
    elif content:
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
             # Fallback to text parsing
             data = parse_text_lines(content)
    
    if not isinstance(data, list):
         raise HTTPException(status_code=400, detail="Data must be a list")

    for item in data:
        # Basic validation
        # If parsing text, we ensured structure. If JSON, we might need validation.
        # But let's be flexible.
        
        word_text = item.get("word")
        if not word_text: continue
        
        unit_val = int(item.get("unit", default_unit))
        book_volume_val = int(item.get("book_volume", default_book_volume))

        new_word = Word(
            word=word_text,
            translation=item.get("translation", ""),
            definition=item.get("definition", "..."),
            unit=unit_val,
            book_volume=book_volume_val,
            example=item.get("example"),
            audio_path=item.get("audio_path")
        )
        db.add(new_word)
    
    await db.commit()
    return RedirectResponse(url="/words", status_code=303)


@app.get("/quizzes", response_class=HTMLResponse)
async def list_quizzes(request: Request, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Quiz).order_by(Quiz.id.desc()))
    quizzes = res.scalars().all()
    
    res_words = await db.execute(select(Word))
    words = res_words.scalars().all()
    
    return templates.TemplateResponse("quizzes.html", {"request": request, "quizzes": quizzes, "words": words})

@app.post("/quizzes/add")
async def add_quiz(
    word_id: int = Form(...),
    question: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct_option: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    new_quiz = Quiz(
        word_id=word_id,
        question=question,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_option=correct_option
    )
    db.add(new_quiz)
    await db.commit()
    await db.commit()
    return RedirectResponse(url="/quizzes", status_code=303)

@app.post("/quizzes/auto_generate")
async def auto_generate_quizzes(db: AsyncSession = Depends(get_db)):
    # Get all words
    res_words = await db.execute(select(Word))
    words = res_words.scalars().all()
    
    if len(words) < 4:
        # Not enough words to generate distractors
        return RedirectResponse(url="/quizzes", status_code=303)

    generated_count = 0
    
    for word in words:
        # Check if quiz exists
        res_quiz = await db.execute(select(Quiz).where(Quiz.word_id == word.id))
        if res_quiz.scalar_one_or_none():
            continue
            
        # Generate distractors
        distractors = random.sample([w for w in words if w.id != word.id], 3)
        options = [word.translation] + [d.translation for d in distractors]
        random.shuffle(options)
        
        correct_index = options.index(word.translation)
        correct_char = ['a', 'b', 'c', 'd'][correct_index]
        
        new_quiz = Quiz(
            word_id=word.id,
            question=f"Translate: {word.word}",
            option_a=options[0],
            option_b=options[1],
            option_c=options[2],
            option_d=options[3],
            correct_option=correct_char
        )
        db.add(new_quiz)
        generated_count += 1
        
    if generated_count > 0:
        await db.commit()
        
    return RedirectResponse(url="/quizzes", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
