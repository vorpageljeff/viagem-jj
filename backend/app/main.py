from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.routes.api import router

app = FastAPI(title="Trip Manager API", version="1.0.0", description="API de gestão colaborativa de viagens")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

@app.get("/health")
def health(): return {"status":"ok"}

@app.exception_handler(Exception)
async def unhandled_error(_:Request,exc:Exception):
    return JSONResponse(status_code=500,content={"detail":"Erro interno inesperado"})
