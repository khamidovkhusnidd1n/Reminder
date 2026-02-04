from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)
    
    # Progress tracking
    current_unit = Column(Integer, default=1)
    words_learned = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    xp = Column(Integer, default=0)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    progress = relationship("Progress", back_populates="user")

class Word(Base):
    __tablename__ = 'words'
    
    id = Column(Integer, primary_key=True)
    word = Column(String(100), nullable=False)
    definition = Column(Text, nullable=False)
    translation = Column(String(255), nullable=True)
    example = Column(Text, nullable=True)
    audio_path = Column(String(255), nullable=True)
    unit = Column(Integer, nullable=False) # Unit in the book (1-30 typically)
    book_volume = Column(Integer, nullable=False) # 1 to 6

class Quiz(Base):
    __tablename__ = 'quizzes'
    
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey('words.id'))
    question = Column(Text, nullable=False)
    option_a = Column(String(255), nullable=False)
    option_b = Column(String(255), nullable=False)
    option_c = Column(String(255), nullable=False)
    option_d = Column(String(255), nullable=False)
    correct_option = Column(String(1), nullable=False) # 'a', 'b', 'c', or 'd'
    
    word = relationship("Word")

class Progress(Base):
    __tablename__ = 'progress'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    word_id = Column(Integer, ForeignKey('words.id'))
    mastered = Column(Boolean, default=False)
    last_reviewed = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="progress")
    word = relationship("Word")
