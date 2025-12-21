from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routes import CardRouter, CardTypeRouter
from app.settings import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Список строк или паттернов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все HTTP методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешаем все заголовки
)

app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")


app.include_router(CardRouter)
app.include_router(CardTypeRouter)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"message": "Welcome to the API!", "docs": "api/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
