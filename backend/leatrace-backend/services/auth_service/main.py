from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from database.connection import get_db, Base, engine
from database import models
from shared import schemas, utils
from config.settings import settings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service", version="1.0.0")

@app.post("/auth/register", response_model=schemas.TokenResponse)
def register(request: schemas.UserRegisterRequest, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == request.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        user_id=str(uuid.uuid4()),
        email=request.email,
        name=request.name,
        password_hash=utils.get_password_hash(request.password),
        role="user",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = utils.create_access_token({"sub": new_user.email, "role": new_user.role})
    return schemas.TokenResponse(
        access_token=token,
        user_id=new_user.user_id,
        username=new_user.name,
        role=new_user.role
    )

@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(request: schemas.UserLoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == request.email).first()
    if not db_user or not utils.verify_password(request.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    token = utils.create_access_token({"sub": db_user.email, "role": db_user.role})
    return schemas.TokenResponse(
        access_token=token,
        user_id=db_user.user_id,
        username=db_user.name,
        role=db_user.role
    )
