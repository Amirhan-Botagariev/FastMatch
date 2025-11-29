from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.logging import app_logger
from app.core.debugger import DebugStop
from app.features.resumes.router import router as resumes_router

from app.core.debugger import debug

templates = Jinja2Templates(directory="templates")


def create_app() -> FastAPI:
    app_logger.info("Starting FastMatch API")

    app = FastAPI(
        title="FastMatch API",
        version="0.1.0",
        description="MVP backend for job hub / resume service",
    )

    origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["system"])
    async def root():
        return {"message": "JobHub API is running"}

    @app.get("/health", tags=["system"])
    async def health_check():
        return {"status": "ok"}

    # Подключаем модуль резюме
    app.include_router(resumes_router, prefix="/api/v1/resumes", tags=["resumes"])

    # ---------- DebugStop handler ----------

    @app.exception_handler(DebugStop)
    async def debug_stop_handler(request: Request, exc: DebugStop) -> HTMLResponse:
        """
        Обработчик специального debug-исключения.

        Важно:
          - НИЧЕГО не логируем (по твоему ТЗ)
          - Просто рендерим HTML-страницу с информацией из snapshot
          - Код ответа можно оставить 200, чтобы не пугать статусом 500
        """
        return templates.TemplateResponse(
            "debug.html",
            {
                "request": request,
                "snapshot": exc.snapshot,
            },
            status_code=200,
        )

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    app_logger.info("Running app via __main__")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)