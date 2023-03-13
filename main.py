from fastapi import Depends, FastAPI
from settings import get_settings, DevSettings, ProdSettings

app = FastAPI()


@app.get("/info")
async def info(settings: DevSettings | ProdSettings = Depends(get_settings)):
    return {"MAIL_SERVER": settings.MAIL_SERVER}


@app.get("/")
async def root():
    return {"message": "Hello World"}
