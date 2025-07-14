from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .database import SessionLocal
from .models import User
from . import models, database
from passlib.hash import bcrypt
import re

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

#Validação da senha, 8 caractéres e pelo menos uma letra.
def validar_senha(senha):
    padrao = r'^(?=.*[A-Za-z]).{8,}$'
    return bool(re.match(padrao, senha))

#Conexão com o banco.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
#Homepage deslogada
@router.get("/", response_class=HTMLResponse, name="index")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


#Registro abaixo.

@router.get("/register", response_class=HTMLResponse, name="register_form")
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse, name="register_form")
async def register_user(request: Request, 
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if not validar_senha(password):
        return templates.TemplateResponse("register.html", {
            "request": request,
            "mensagem": "Senha deve conter no mínimo 8 caracteres e pelo menos uma letra."
        })
    if password != confirm_password:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "mensagem": "As senhas não coincidem."
        })

    usuario_existente = db.query(User).filter_by(email=email).first()
    if usuario_existente:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "mensagem": "Este email já está cadastrado no sistema."
        })
    
    hashed_password = bcrypt.hash(password)
    user = models.User(full_name=full_name, email=email, password=hashed_password)

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse("register.html", {
            "request": request,
            "mensagem": "Erro inesperado ao registrar. Tente novamente."
        })
    
    return RedirectResponse(url="/", status_code=302)


#Login

@router.get("/login", response_class=HTMLResponse, name="login_form")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse, name="login_form")
def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()

    if user and bcrypt.verify(password, user.password):
        request.session["user_id"] = user.id
        request.session["user_name"] = user.full_name
        request.session["user_email"] = user.email
        return RedirectResponse(url="/homepage", status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "mensagem": "Email ou senha Incorretos!"
    }) 
   
    
#Área do cliente


@router.get("/homepage", response_class=HTMLResponse, name="home")
def homepage(request: Request):
    user_name = request.session.get("user_name")
    if user_name:
        return templates.TemplateResponse("homepage.html", {
            "request": request,
            "user_name": user_name

        })
    return RedirectResponse(url="/login", status_code=302)

@router.get("/logout", name="logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

@router.get("/update", name="update")
def update(request: Request):
    user_name = request.session.get("user_name")
    user_email = request.session.get("user_email")

    return templates.TemplateResponse("update.html", {
        "request": request,
        "user_name": user_name,
        "user_email": user_email
    })
@router.post("/update", name="update_user")
def update_user(
    request: Request,
    full_name: str = Form(""),
    email: str = Form(""),
    db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")
    
    if not user_id:
        return RedirectResponse("/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    usuario_existente = db.query(User).filter_by(email=email).first()
    
    if user:
        # Apenas atualiza se o valor foi preenchido no formulário
        if full_name.strip():
            user.full_name = full_name
            request.session["user_name"] = full_name  # atualiza a sessão
        if usuario_existente:
            return templates.TemplateResponse("update.html", {
            "request": request,
            "mensagem": "Este email já está cadastrado no sistema."
        })
        if email.strip():
            user.email = email
            request.session["user_email"] = email  # atualiza a sessão

        db.commit()

    return RedirectResponse("/homepage", status_code=302)

@router.post("/delete-account", name="delete_account")
def delete_account(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()

    if user:
        db.delete(user)
        db.commit()
        request.session.clear()  # encerra a sessão

    return RedirectResponse(url="/login", status_code=302)