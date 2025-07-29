from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .database import SessionLocal
from PIL import Image
import google.generativeai as genai
import io
import shutil, os
from .models import User, Plant, PlantImage
from . import models, database
from passlib.hash import bcrypt
import re
import json, re
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


router = APIRouter()
genai.configure(api_key="")
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
    plants = db.query(Plant).filter(Plant.user_id == user.id).all() if user else []
    if user and bcrypt.verify(password, user.password):
        request.session["user_id"] = user.id
        request.session["user_name"] = user.full_name
        request.session["user_email"] = user.email
        request.session["plants"] = [plant.name for plant in plants]
        return RedirectResponse(url="/homepage", status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "mensagem": "Email ou senha Incorretos!"
    }) 
   
    
#Área do cliente


@router.get("/homepage", response_class=HTMLResponse, name="home")
def homepage(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    user_name = request.session.get("user_name")

    top_plants = db.query(models.Plant)\
    .order_by(models.Plant.count.desc())\
    .limit(3)\
    .all()

    plants = db.query(models.Plant).filter(models.Plant.user_id == user_id).all() if user_id else []
    plantsall = db.query(models.Plant).all()
    if user_name:
        return templates.TemplateResponse("homepage.html", {
            "request": request,
            "user_name": user_name,
            "plants": plants,
            "plantsall": plantsall,
            "top_plants": top_plants
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

# área de atualização de cadastro
@router.post("/planta-info")
async def planta_info(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    nome = form.get("nome")

    planta = db.query(Plant).filter(Plant.name == nome).first()
    
    if planta:
        image_url = f"/uploads/{planta.image_path}"
        return JSONResponse(content={
            "especie": planta.name,
            "familia": planta.species,
            "descricao": planta.description,
            "image": image_url
        })
    else:
        return JSONResponse(content={
            "especie": "Desconhecida",
            "familia": "Desconhecida",
            "descricao": "Não encontramos dados para essa planta.",
            "image": None
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
        
        if full_name.strip():
            user.full_name = full_name
            request.session["user_name"] = full_name  
        if usuario_existente:
            return templates.TemplateResponse("update.html", {
            "request": request,
            "mensagem": "Este email já está cadastrado no sistema."
        })
        if email.strip():
            user.email = email
            request.session["user_email"] = email  

        db.commit()

    return RedirectResponse("/homepage", status_code=302)

# Exclusão de conta

@router.post("/delete-account", name="delete_account")
def delete_account(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()

    if user:
        db.delete(user)
        db.commit()
        request.session.clear()  

    return RedirectResponse(url="/login", status_code=302)

#Scan das imagens

@router.post("/analyze")
async def analyze_with_gemini(file: UploadFile = File(...)):
    
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(
    [
        image,
        """Analise a espécie e família da planta ou árvore presente na imagem.
        Em seguida, forneça um parecer detalhado sobre a condição de saúde da planta, espécie e família.
        Retorne tudo em português no seguinte formato JSON:
        Se a imagem fornecida não for uma planta ou árvore, retorne isplant = false
        {
          "especie": "<Aqui irá a o nome da planta, TENTE COLOCAR O NOME MAIS SIMPLES POSSÍVEL, CONTENDO APENAS 1 PALAVRA SE POSSÍVEL.>",
          "familia": "<Aqui irá a família que a planta pertence, pode dar detalhes sobre e até mesmo dar alguns exemplos breves de outras plantas ou arvores da familia>",
          "condicao_saude": <aqui irá a saúde da planta>,
          "isplant": <true ou false>
        }
        
        """
    ],
    stream=False
)
    text_response = response.text
    match = re.search(r"\{[\s\S]*\}", text_response)
    if match:
        try:
            data_json = json.loads(match.group())
        except json.JSONDecodeError:
            data_json = {
            "especie": None,
            "familia": None,
            "condicao_saude": None,
            "isplant": False
        }
    else:
        data_json = {
        "especie": None,
        "familia": None,
        "condicao_saude": None,
        "isplant": False
    }
    return JSONResponse(content={"dados": data_json})


@router.post("/rplant", name="rplant")
async def register_plant(request: Request, 
    nome: str = Form(...),
    especie: str = Form(...),
    descricao: str = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    filename = f"imagem_{timestamp}.png"
    file_path = os.path.join("app/uploads", filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    user_id = request.session.get("user_id")
    if not user_id:
     return RedirectResponse(url="/login", status_code=302)

    existing_plant = db.query(models.Plant).filter(
        models.Plant.name == nome,
        models.Plant.user_id == user_id
    ).first()

    if existing_plant:
        existing_plant.count += 1
        db.commit()
        db.refresh(existing_plant)
        return {"message": f"Planta '{nome}' já existe, contador atualizado para {existing_plant.count}"}

    
    new_plant = models.Plant(
        name=nome,
        species=especie,
        description=descricao,
        user_id=user_id,
        count=1
    )
    new_image = models.PlantImage(
        image_path=filename,
        plant_id=new_plant.id
    )

    db.add(new_plant)
    db.commit()
    db.refresh(new_plant)
    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    return {"message": "Planta registrada com sucesso!", "plant_id": new_plant.id}
