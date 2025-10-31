from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
import json
import os
import uuid
import hashlib
from datetime import datetime, timedelta
import sqlite3

# -----------------------------
# Database setup
# -----------------------------
DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# -----------------------------
# Model
# -----------------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)
    full_name = Column(String, default="")
    email = Column(String, default="")
    security_question = Column(String, default="")
    security_answer_hash = Column(String, default="")
    age_group = Column(String, default="")
    language_preference = Column(String, default="")
    wellness_goals = Column(String, default="")


class PasswordReset(Base):
    __tablename__ = "password_resets"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)

Base.metadata.create_all(bind=engine)

def ensure_columns_sqlite():
    """Ensure new columns exist on the users table for legacy DBs.
    Uses a raw SQLite connection because PRAGMA/ALTER execution can be finicky via SQLAlchemy dialects.
    """
    try:
        raw = engine.raw_connection()
        try:
            cur = raw.cursor()
            cur.execute("PRAGMA table_info(users)")
            existing = {row[1] for row in cur.fetchall()}  # column name at index 1
            add_specs = [
                ("full_name", "TEXT"),
                ("email", "TEXT"),
                ("security_question", "TEXT"),
                ("security_answer_hash", "TEXT"),
                ("age_group", "TEXT"),
                ("language_preference", "TEXT"),
                ("wellness_goals", "TEXT"),
            ]
            for name, coltype in add_specs:
                if name not in existing:
                    cur.execute(f"ALTER TABLE users ADD COLUMN {name} {coltype}")
            raw.commit()
        finally:
            raw.close()
    except Exception:
        # Avoid crashing the app on startup; subsequent inserts may fail if schema is broken
        pass

ensure_columns_sqlite()

# -----------------------------
# API setup
# -----------------------------
app = FastAPI()

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str | None = None
    email: str | None = None
    security_question: str | None = None
    security_answer: str | None = None

class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = None
    email: str | None = None
    age_group: str | None = None
    language_preference: str | None = None
    wellness_goals: str | None = None


class ForgotPasswordStartRequest(BaseModel):
    username: str


class ForgotPasswordVerifyRequest(BaseModel):
    username: str
    security_answer: str


class ForgotPasswordResetRequest(BaseModel):
    token: str
    new_password: str


class ForgotPasswordEmailRequest(BaseModel):
    email: str


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

@app.post("/register")
def register_user(request: RegisterRequest):
    user_exists = db.query(User).filter(User.username == request.username).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Username already exists")

    security_answer_hash = hash_text(request.security_answer) if request.security_answer else ""
    new_user = User(
        username=request.username,
        password=request.password,
        full_name=request.full_name or "",
        email=request.email or "",
        security_question=request.security_question or "",
        security_answer_hash=security_answer_hash,
    )
    db.add(new_user)
    db.commit()
    return {"message": "Registration successful"}

@app.post("/login")
def login_user(request: LoginRequest):
    user = db.query(User).filter(User.username == request.username, User.password == request.password).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"message": f"Welcome {request.username}"}


@app.get("/profile/{username}")
def get_profile(username: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "username": user.username,
        "full_name": user.full_name or "",
        "email": user.email or "",
        "has_security_question": bool(user.security_question),
        "security_question": user.security_question or "",
        "age_group": user.age_group or "",
        "language_preference": user.language_preference or "",
        "wellness_goals": user.wellness_goals or "",
    }


@app.put("/profile/{username}")
def update_profile(username: str, request: ProfileUpdateRequest):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if request.full_name is not None:
        user.full_name = request.full_name
    if request.email is not None:
        user.email = request.email
    if request.age_group is not None:
        user.age_group = request.age_group
    if request.language_preference is not None:
        user.language_preference = request.language_preference
    if request.wellness_goals is not None:
        user.wellness_goals = request.wellness_goals
    db.commit()
    return {"message": "Profile updated"}


@app.post("/change_password")
def change_password(request: ChangePasswordRequest):
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.password != request.old_password:
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    user.password = request.new_password
    db.commit()
    return {"message": "Password changed successfully"}


@app.post("/forgot_password/start")
def forgot_password_start(request: ForgotPasswordStartRequest):
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.security_question:
        raise HTTPException(status_code=400, detail="No security question set for this user")
    return {"security_question": user.security_question}


@app.post("/forgot_password/verify")
def forgot_password_verify(request: ForgotPasswordVerifyRequest):
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.security_answer_hash:
        raise HTTPException(status_code=400, detail="Security answer not set")
    if user.security_answer_hash != hash_text(request.security_answer):
        raise HTTPException(status_code=400, detail="Security answer is incorrect")
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    reset = PasswordReset(username=request.username, token=token, expires_at=expires_at)
    db.add(reset)
    db.commit()
    return {"reset_token": token, "expires_at": expires_at.isoformat() + "Z"}


@app.post("/forgot_password/reset")
def forgot_password_reset(request: ForgotPasswordResetRequest):
    reset = db.query(PasswordReset).filter(PasswordReset.token == request.token).first()
    if not reset:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    if reset.expires_at < datetime.utcnow():
        db.delete(reset)
        db.commit()
        raise HTTPException(status_code=400, detail="Token expired")
    user = db.query(User).filter(User.username == reset.username).first()
    if not user:
        db.delete(reset)
        db.commit()
        raise HTTPException(status_code=404, detail="User not found")
    user.password = request.new_password
    db.delete(reset)
    db.commit()
    return {"message": "Password has been reset successfully"}


@app.post("/forgot_password/request_token")
def forgot_password_request_token(request: ForgotPasswordEmailRequest):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    reset = PasswordReset(username=user.username, token=token, expires_at=expires_at)
    db.add(reset)
    db.commit()
    # In real systems, email the token. Here we return it for demo.
    return {"reset_token": token, "expires_at": expires_at.isoformat() + "Z"}

# Database export endpoints
@app.get("/export/database")
def download_database():
    """Download the complete database file"""
    if not os.path.exists("./users.db"):
        raise HTTPException(status_code=404, detail="Database file not found")
    return FileResponse("./users.db", filename="users_database.db")

@app.get("/export/users/csv")
def export_users_csv():
    """Export users to CSV format"""
    try:
        df = pd.read_sql_query("SELECT * FROM users", db.bind.connect())
        csv_filename = "users_export.csv"
        df.to_csv(csv_filename, index=False)
        return FileResponse(csv_filename, filename="users_export.csv", media_type="text/csv")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/export/users/json")
def export_users_json():
    """Export users to JSON format"""
    try:
        users = db.query(User).all()
        user_data = [{"id": user.id, "username": user.username, "password": user.password} for user in users]
        return JSONResponse(content=user_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/export/users/sql")
def export_users_sql():
    """Export users to SQL format"""
    try:
        users = db.query(User).all()
        sql_content = "-- Users table export\n\n"
        
        for user in users:
            sql_content += f"INSERT INTO users (id, username, password) VALUES ({user.id}, '{user.username}', '{user.password}');\n"
        
        sql_filename = "users_export.sql"
        with open(sql_filename, 'w') as f:
            f.write(sql_content)
        
        return FileResponse(sql_filename, filename="users_export.sql", media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

