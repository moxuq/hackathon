from app.api.v1.auth import auth_router
from fastapi import FastAPI

app = FastAPI(
    title='Геймифицированный тренажёр для проводников ВСМ',
    description='API обучающего тренажёра сценариев для проводников ВСМ',
    version='0.1.0',
)

app.include_router(auth_router)


@app.get('/health', tags=['Summary'])
async def health():
    return {'status': 'ok'}
