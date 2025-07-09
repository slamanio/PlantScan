from fastapi import FastAPI
from .database import Base, engine
from .routes import router
from starlette.middleware.sessions import SessionMiddleware
import secrets

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(router)

app.add_middleware(SessionMiddleware, secret_key=print(secrets.token_hex(32)), max_age=60 * 60 * 24 * 7)
