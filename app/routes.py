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
import hashlib
from .models import User, Plant, PlantImage
from sqlalchemy.orm import joinedload
from . import models, database
from passlib.hash import bcrypt
from passlib.context import CryptContext
import re
import json, re
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


router = APIRouter()
genai.configure(api_key="")
templates = Jinja2Templates(directory="app/templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")




#Validação da senha, 8 caractéres e pelo menos uma letra.

def validar_senha(senha):
    padrao = r'^(?=.*[A-Za-z]).{8,}$'
    return bool(re.match(padrao, senha))

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
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
    profile_image: UploadFile = File(None),
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
    
    user = models.User(full_name=full_name, email=email, password=hashed_password, theme="light")

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
    
    if profile_image:
        if profile_image.filename and profile_image.filename.lower() != "default.png":
            file_bytes = await profile_image.read()
            if file_bytes:
                file_hash = hashlib.sha256(file_bytes).hexdigest()
                filename = f"imagem_{user.id}_{file_hash[:8]}.png"
                filepath = os.path.join("app", "profpic", filename)

                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(file_bytes)

                user.profile_image = filename
        else:   
            user.profile_image = "default.png"

        db.commit()
    

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
def homepage(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user_name = request.session.get("user_name")
    user_email = request.session.get("user_email")
    user_profile_image = db.query(User.profile_image).filter(User.email == user_email).first()


    image_urls = f"/profpic/{user_profile_image[0]}"

    theme = user.theme if user and user.theme else "light"
    if image_urls is None:
        image_urls = f"/profpic/default.png"

    top_plants = db.query(models.Plant)\
    .order_by(models.Plant.count.desc())\
    .limit(3)\
    .all()
    if user_name:
        return templates.TemplateResponse("homepage.html", {
            "request": request,
            "user_name": user_name,
            "profile_image": image_urls,
            "theme": theme,
            "top_plants": top_plants,

        })
    
    return RedirectResponse(url="/login", status_code=302)

@router.get("/api/homepage", response_class=JSONResponse)
def homepage_api(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"error": "Não autenticado"})

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return JSONResponse(status_code=404, content={"error": "Usuário não encontrado"})

    top_plants = db.query(models.Plant)\
    .order_by(models.Plant.count.desc())\
    .limit(3)\
    .all()

    return {
        "user_name": user.full_name,
        "profile_image": user.profile_image or "default.png",
        "theme": user.theme or "light",
        "top_plants": top_plants,

    }

@router.get("/logout", name="logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

@router.get("/update", name="update")
def update(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    user_name = request.session.get("user_name")
    user_email = request.session.get("user_email")
    theme = user.theme if user and user.theme else "light"
    user_profile_image = db.query(User.profile_image).filter(User.full_name == user_name).first()
    image_urls = f"/profpic/{user_profile_image[0]}"
    if image_urls is None:
        image_urls = f"/profpic/default.png"
    return templates.TemplateResponse("update.html", {
        "request": request,
        "user_name": user_name,
        "user_email": user_email,
        "user_profile_image": image_urls,
        "theme": theme
    })

@router.post("/update_theme")
async def update_theme(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    theme = data.get("theme", "light")
    user_id = request.session.get("user_id")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.theme = theme
        db.commit()
        return {"status": "success", "theme": theme}
    return {"status": "error", "message": "user not found"}

# área de atualização de cadastro
@router.post("/planta-info")
async def planta_info(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    nome = form.get("nome")
    planta = db.query(Plant).filter(Plant.name == nome).first()
    if planta:
        # 🔹 Consulta imagens da planta
        imagens = db.query(models.PlantImage).filter(models.PlantImage.plant_id == planta.id).all()
    # 🔹 Consulta imagens da planta separadas por cor
        cores = ["Green", "Yellow", "Red"]
        imagens_por_cor = {cor.lower(): [] for cor in cores}

        for cor in cores:
            imgs = db.query(models.PlantImage).filter(
                models.PlantImage.plant_id == planta.id,
                models.PlantImage.color == cor
                
            ).all()
            imagens_por_cor[cor.lower()] = [f"/uploads/{img.image_path}" for img in imgs]
        return JSONResponse(content={
            "especie": planta.name,
            "familia": planta.species,
            "image": [f"/uploads/{img.image_path}" for img in imagens],
            "imagegreen": imagens_por_cor["green"],
            "imageyellow": imagens_por_cor["yellow"],
            "imagered": imagens_por_cor["red"]
        })
      
    return JSONResponse(content={
            "especie": "Desconhecida",
            "familia": "Desconhecida",
            "image": None
        })

@router.post("/userplant-info")
async def userplant_info(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    plant_id = form.get("plant_id")
    user_id = request.session.get("user_id")

    if not plant_id:
        return JSONResponse(status_code=400, content={"error": "plant_id não fornecido"})

    imagens = (
        db.query(models.PlantImage)
        .filter(models.PlantImage.id == plant_id, models.PlantImage.user_id == user_id)
        .all()
    )

    if not imagens:
        return JSONResponse(content={
            "especie": "Desconhecida",
            "familia": "Desconhecida",
            "descricao": "Não encontramos dados para essa planta.",
            "imagens": []
        })

    return JSONResponse(content={
        "especie": imagens[0].plant.name,
        "imagens": [
            {
                "descricao": img.description,
                "cor": img.color,
                "path": f"/uploads/{img.image_path}"
            }
            for img in imagens
        ]
    })




@router.post("/update", name="update_user")
async def update_user(
    request: Request,
    full_name: str = Form(""),
    email: str = Form(""),
    profile_image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")
    

    if not user_id:
        return RedirectResponse("/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    usuario_existente = db.query(User).filter_by(email=email).first()
    
    if user:
        if usuario_existente and usuario_existente.id != user.id:
            return templates.TemplateResponse("update.html", {
                "request": request,
                "mensagem": "Este email já está cadastrado no sistema.",
                "user_name": user.full_name,
                "user_email": user.email,
                "user_profile_image": user.profile_image,
            })

        if full_name.strip():
            user.full_name = full_name
            request.session["user_name"] = full_name

        if email.strip():
            user.email = email
            request.session["user_email"] = email


        if profile_image:
            file_bytes = await profile_image.read()
            if file_bytes:  
                file_hash = hashlib.sha256(file_bytes).hexdigest()
                filename = f"imagem_{user.id}_{file_hash[:8]}.png"
                filepath = os.path.join("app", "profpic", filename)
                if user.profile_image and user.profile_image != "default.png":
                    old_path = os.path.join("app", "profpic", user.profile_image)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                with open(filepath, "wb") as f:
                    f.write(file_bytes)

                user.profile_image = filename
                request.session["user_profile_image"] = filename
                db.commit()
        
            if not file_bytes:
                user.profile_image = "default.png"
                request.session["user_profile_image"] = "default.png"
                db.commit()
    return RedirectResponse("/homepage", status_code=302)

# Exclusão de conta

@router.post("/delete", name="delete")
def delete_account(request: Request,
    senha: str = Form(""), 
    db: Session = Depends(get_db)):

    user_id = request.session.get("user_id")
    
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    
    if user and bcrypt.verify(senha, user.password):
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
          "especie": "<Aqui irá a o nome da planta, TENTE COLOCAR O NOME MAIS SIMPLES POSSÍVEL, SEMPRE NO SINGULAR E CONTENDO APENAS 1 PALAVRA SE POSSÍVEL.>",
          "familia": "<Aqui irá a família que a planta pertence, pode dar detalhes sobre e até mesmo dar alguns exemplos breves de outras plantas ou arvores da familia, como dito antes, essa deve ser a parte mais completa junto com a condição da planta, pois preciso de uma descrição geral da família e espécie, então pode caprichar!>",
          "condicao_saude": <aqui irá a saúde da planta>,
          "colorAlert": <aqui você dará uma cor baseada na condição da planta, que vai de "Green", "Yellow" ou "Red", sendo vermelho a pior das situações, e verde a melhor delas. (APENAS RETORNE UMA DAS 3 CORES, NADA MAIS QUE ISSO)>
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
async def register_plant(
    request: Request, 
    nome: str = Form(...),
    especie: str = Form(...),
    descricao: str = Form(...),
    image: UploadFile = File(None),
    cor: str = Form(...),
    db: Session = Depends(get_db)
):
    file_hash = None
    filename = None
    user_id = request.session.get("user_id")

    if image:
        file_bytes = await image.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        await image.seek(0)  # reseta o ponteiro para leitura futura

    # 🔹 Verifica se a planta já existe no banco global
    existing_plant = db.query(models.Plant).filter(models.Plant.name == nome).first()

    # 🔹 Se a planta já existe (registro global)
    if existing_plant:
        existing_plant.count += 1
        db.commit()
        db.refresh(existing_plant)


        if file_hash:
            filename = f"user_{user_id}_plant_{existing_plant.id}_{file_hash[:8]}.png"
            file_path = os.path.join("app/uploads", filename)
            with open(file_path, "wb") as buffer:
                buffer.write(file_bytes)

            plant_image = models.PlantImage(
                    user_id=user_id,
                    name=nome,
                    image_path=filename,
                    image_hash=file_hash,
                    description=descricao,
                    color = cor,
                    plant_id=existing_plant.id
            )
            db.add(plant_image)
            db.commit()

        return {"message": f"Planta '{nome}' já existe, contador atualizado e imagem salva!"}

    # 🔹 Se a planta NÃO existe, cria o registro global
    new_plant = models.Plant(
        name=nome,
        species=especie,
        count=1
    )
    db.add(new_plant)
    db.commit()
    db.refresh(new_plant)


    # ✅ Salva imagem enviada pelo usuário (histórico individual)
    if file_hash:
        filename = f"user_{user_id}_plant_{new_plant.id}_{file_hash[:8]}.png"
        file_path = os.path.join("app/uploads", filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)

        plant_image = models.PlantImage(
                    user_id=user_id,
                    name=new_plant.name,
                    image_path=filename,
                    image_hash=file_hash,
                    description=descricao,
                    color = cor,
                    plant_id=new_plant.id
            )
        db.add(plant_image)
        db.commit()

    return {"message": "Planta registrada com sucesso e imagem salva no histórico!", "plant_id": new_plant.id}

#Jardim

@router.get("/plants", response_class=HTMLResponse, name="plants")
def homepage(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    user_name = request.session.get("user_name")
    user_email = request.session.get("user_email")

    user_profile_image = db.query(models.User.profile_image).filter(models.User.email == user_email).first()

    if user_profile_image is None:
        image_urls = "/profpic/default.png"
    else:
        image_urls = f"/profpic/{user_profile_image}"

    # Buscar plantas do usuário com dados da planta via joinedload para facilitar template
    user_plants = (
        db.query(models.PlantImage)
        .filter(models.PlantImage.user_id == user_id)
        .options(joinedload(models.PlantImage.plant))  # Assuming PlantImage has 'plant' relationship
        .all()
    )

    theme = user.theme if user and user.theme else "light"

    return templates.TemplateResponse("plant.html", {
        "request": request,
        "user_name": user_name,
        "profile_image": image_urls,
        "theme": theme,
        "plants": user_plants
    })


@router.post("/update_plant_image")
async def update_plant_image(
    request: Request, 
    db: Session = Depends(get_db),
    nova_imagem: UploadFile = File(...),
):
    form = await request.form()
    plant_id = form.get("plant_id")
    user_id = request.session.get("user_id")

    imagem_db = (
        db.query(models.PlantImage)
        .filter(models.PlantImage.id == plant_id, models.PlantImage.user_id == user_id)
        .first()
    )
    if not imagem_db:
        return JSONResponse(status_code=404, content={"error": "Imagem anterior não encontrada"})

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    caminho_imagem_anterior = os.path.join(BASE_DIR, "uploads", imagem_db.image_path.lstrip("/"))

    image_bytes = await nova_imagem.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    with open(caminho_imagem_anterior, "rb") as f:
        img = Image.open(f).convert("RGB")

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(
        [
            image, img,
            """
            Aqui estão duas imagens, quero que me diga se conseguiu ler ambas, apenas retorne um json:

            {
              "icanread": <true ou false>
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
            data_json = {"icanread": False}
    else:
        data_json = {"icanread": False}

    # Retorna sempre o JSON com os dados
    return JSONResponse(content={"dados": data_json})



