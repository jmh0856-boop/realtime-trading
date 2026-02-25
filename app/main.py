import asyncio
from fastapi import FastAPI
from app.routers import trade, auth  # 거래 및 인증 라우터
from app.websocket import market    # 시세 웹소켓 라우터
from app.websocket.market import price_generator # 시세 생성 함수

app = FastAPI(title="Realtime Trading System")

# 1. 앱 시작 시 실시간 시세 생성기 백그라운드 실행
@app.on_event("startup")
async def startup_event():
    # market.py에서 만든 가격 생성 루프를 백그라운드 태스크로 실행
    asyncio.create_task(price_generator())

# 2. 작성한 라우터들 등록
app.include_router(trade.router, prefix="/api", tags=["Trade"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(market.router, tags=["Market"])

@app.get("/")
async def root():
    return {"status": "Asset Engine is running"}
