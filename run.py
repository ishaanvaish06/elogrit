import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    print(f"Starting server on http://{settings.HOST}:{settings.PORT}")
    print(f"Swagger API Docs: http://127.0.0.1:{settings.PORT}/docs")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
