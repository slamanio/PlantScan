import customtkinter as ctk
from pathlib import Path
import requests
from PIL import Image

sessao = requests.Session()

icone_path = Path(__file__).parent.parent.parent / "static" / "assets" / "imgs" / "icon.ico"
default_image_path = Path(__file__).parent.parent.parent / "profpic" / "default.png"
images_path = Path(__file__).parent.parent.parent / "profpic"

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('dark-blue')

def validarlogin():
    email = inputuser.get()
    password = inputuserpass.get()
    url = "http://localhost:8000/login"

    data = {
        "email": email,
        "password": password
    }
    resposta_login = sessao.post(url, data=data, allow_redirects=False)
    if resposta_login.status_code in (301, 302):
        destino = resposta_login.headers.get("location")
        feedback.configure(text=f"Login OK, redirecionando para: {destino}", text_color='green')
        homepage()
    else:
        feedback.configure(text=f"Email ou senha incorretos!", text_color='red')

def homepage():
    url = "http://localhost:8000/api/homepage"
    for widget in app.winfo_children():
        widget.destroy()
    try:
        resposta_homepage = sessao.get(url)
        resposta_homepage.raise_for_status()
        data = resposta_homepage.json()
    except Exception as e:
        data = {"user_name": "Usuário", "profile_image": "default.png", "theme": "light"}
        print("Erro ao buscar dados:", e)

    # Container principal (ocupa tudo)
    if data.get('theme') == "light":
        ctk.set_appearance_mode(f'{data.get('theme')}')
        container = ctk.CTkFrame(app, corner_radius=15, fg_color="#757474")
        container.pack(padx=150, pady=100, fill="both", expand=True)
    else:
        container = ctk.CTkFrame(app, corner_radius=15, fg_color="#222222")
        container.pack(padx=150, pady=100, fill="both", expand=True)

    titulo = ctk.CTkLabel(container, text=f"Bem-vindo, {data.get('user_name', 'Usuário')}!", 
                          font=ctk.CTkFont(size=44, weight="bold"), text_color="#4CAF50")
    titulo.pack(pady=(20, 50))

    # Frame para o ícone no topo direito, colocado diretamente em app (não dentro do container)
    icon_frame = ctk.CTkFrame(app, width=80, height=80, fg_color="transparent")
    icon_frame.place(relx=1.0, y=20, anchor="ne")  # canto superior direito, 20px do topo

    img_path = default_image_path if data.get('profile_image') == "default.png" else images_path / data.get('profile_image')
    user_img = ctk.CTkImage(light_image=Image.open(img_path), dark_image=Image.open(img_path), size=(50, 50))
    icon_button = ctk.CTkButton(icon_frame, image=user_img, text="", width=50, height=50, fg_color="transparent",
                                hover_color="#4CAF50", corner_radius=25, command=logout)
    icon_button.pack()

    # Resto do conteúdo na container abaixo do título (ou seja, o container tem o conteúdo principal)
    info_frame = ctk.CTkFrame(container, corner_radius=10, fg_color="#4CAF50")
    info_frame.pack(padx=50, pady=40, fill="x")

    label_email = ctk.CTkLabel(info_frame, text=f"E-mail: {data.get('email', 'não disponível')}", 
                               font=ctk.CTkFont(size=22), anchor="w", padx=20)
    label_email.pack(fill="x", pady=15)

    label_theme = ctk.CTkLabel(info_frame, text=f"Tema atual: {data.get('theme', 'light')}", 
                               font=ctk.CTkFont(size=22), anchor="w", padx=20)
    label_theme.pack(fill="x", pady=15)

    btn_logout = ctk.CTkButton(container, text="Sair", fg_color="#4CAF50", hover_color="#ff4444", width=160, height=50, command=logout)
    btn_logout.pack(pady=60)
    

def logout():
    url = "http://localhost:8000/logout"
    sessao.cookies.clear()
    for widget in app.winfo_children():
        widget.destroy()
    construir_tela_login()

def construir_tela_login():
    container = ctk.CTkFrame(app, corner_radius=15, fg_color="#222222")
    container.pack(padx=200, pady=150, fill="both", expand=True)

    titulo_login = ctk.CTkLabel(container, text="Login PlantScan", font=ctk.CTkFont(size=40, weight="bold"), text_color="#4CAF50")
    titulo_login.pack(pady=(20, 50))

    global inputuser, inputuserpass, feedback

    label_email = ctk.CTkLabel(container, text="Email:", font=ctk.CTkFont(size=22), anchor="w")
    label_email.pack(fill="x", padx=20, pady=(0, 10))
    inputuser = ctk.CTkEntry(container, placeholder_text="Informe seu Email aqui!", font=ctk.CTkFont(size=20))
    inputuser.pack(fill="x", padx=20, pady=(0, 25))

    label_senha = ctk.CTkLabel(container, text="Senha:", font=ctk.CTkFont(size=22), anchor="w")
    label_senha.pack(fill="x", padx=20, pady=(0, 10))
    inputuserpass = ctk.CTkEntry(container, placeholder_text="Informe sua Senha!", show="*", font=ctk.CTkFont(size=20))
    inputuserpass.pack(fill="x", padx=20, pady=(0, 25))

    botao_submit = ctk.CTkButton(container, text="Entrar", command=validarlogin, font=ctk.CTkFont(size=22), height=50, fg_color="#4CAF50")
    botao_submit.pack(pady=40, padx=20, fill="x")

    feedback = ctk.CTkLabel(container, text="", font=ctk.CTkFont(size=18))
    feedback.pack(pady=20)

app = ctk.CTk()
app.title('PlantScan')
app.wm_iconbitmap(str(icone_path).replace("\\", "/"))
app.geometry('1600x900')
construir_tela_login()

app.mainloop()
