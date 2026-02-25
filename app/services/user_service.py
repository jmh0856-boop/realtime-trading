from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.portfolio import Portfolio
from app.models.user import User
import app.schemas.trade as schemas
from fastapi import HTTPException

class TradeService:
    """자산 계산 및 거래 로직 엔진"""

    @staticmethod
    async def get_user_portfolio(db: AsyncSession, user_id: int):
        """유저의 포트폴리오 정보 조회"""
        result = await db.execute(select(Portfolio).where(Portfolio.user_id == user_id))
        return result.scalars().first()

    @staticmethod
    async def process_trade(db: AsyncSession, user: User, action: str, payload: schemas.TradeRequest):
        """매수/매도 로직 처리 및 자산 계산 (정수 처리 포함)"""
        
        # 1. 포트폴리오 조회
        p = await TradeService.get_user_portfolio(db, user.id)
        cost = payload.amount * payload.price

        if action == "buy":
            # 잔액 체크
            if user.balance < cost:
                raise HTTPException(status_code=400, detail="잔액이 부족합니다.")
            
            user.balance -= int(cost) # 원화 기준 정수 처리

            if p:
                # 가중 평균 평단가 계산 (정수 처리)
                total_cost = (p.amount * p.avg_price) + cost
                p.amount += payload.amount
                p.avg_price = round(total_cost / p.amount) # 2번 요청하신 정수 반올림
            else:
                new_p = Portfolio(
                    user_id=user.id,
                    amount=payload.amount,
                    avg_price=round(payload.price)
                )
                db.add(new_p)

        elif action == "sell":
            if not p or p.amount < payload.amount:
                raise HTTPException(status_code=400, detail="보유 수량이 부족합니다.")
            
            user.balance += int(payload.amount * payload.price)
            p.amount -= payload.amount

            if p.amount == 0:
                await db.delete(p)

        await db.commit()
        return {"msg": "success"}
