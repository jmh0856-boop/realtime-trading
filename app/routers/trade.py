from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import get_current_user
import app.models as models
import app.schemas.trade as schemas
from app.services.trade_service import TradeService
from app.services.portfolio_service import PortfolioService
from app.routers.market import manager

router = APIRouter()

@router.get("/user/status")
async def get_status(
    current_price: float,
    user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[Asset Engine] 실시간 시세 반영 자산 상태 조회"""
    # PortfolioService를 호출하여 계산된 자산 정보 반환
    status = await PortfolioService.get_user_status(db, user, current_price)
    return status


@router.post("/trade/{action}")
async def trade(
    action: str,
    payload: schemas.TradeRequest,
    user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[Asset Engine] 매수 및 매도 처리 로직 실행"""
    
    # 1. TradeService를 호출하여 비즈니스 로직(계산/저장) 처리
    result = await TradeService.process_trade(db, user, action, payload)
    
    # 2. 거래 성공 시 전체 사용자에게 실시간 알림 브로드캐스트
    await manager.broadcast({
        "type": "trade_news", 
        "msg": f"🔔 {user.username}님 {action} 완료"
    })

    return result
