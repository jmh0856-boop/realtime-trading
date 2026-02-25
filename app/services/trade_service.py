from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.portfolio import Portfolio
from app.models.user import User
import app.schemas.trade as schemas
from fastapi import HTTPException

class TradeService:
    """매수/매도 자산 계산 엔진 (Asset Engine)"""

    @staticmethod
    async def process_trade(db: AsyncSession, user: User, action: str, payload: schemas.TradeRequest):
        """매수 및 매도 시 잔액과 수량을 계산하여 DB에 반영"""
        
        # 1. 현재 사용자의 해당 종목 포트폴리오 조회
        result = await db.execute(select(Portfolio).where(Portfolio.user_id == user.id))
        p = result.scalars().first()

        # 거래 총액 계산 (수량 * 가격)
        total_trade_amount = payload.amount * payload.price

        if action == "buy":
            # [체크] 잔액이 부족한 경우 에러 발생
            if user.balance < total_trade_amount:
                raise HTTPException(status_code=400, detail="잔액이 부족합니다.")
            
            # [계산] 현금 차감 (정수 처리)
            user.balance -= int(total_trade_amount)

            if p:
                # [계산] 기존 보유 시: 가중 평균 평단가 계산 (반올림하여 정수화)
                current_total_cost = p.amount * p.avg_price
                new_total_cost = current_total_cost + total_trade_amount
                p.amount += payload.amount
                p.avg_price = round(new_total_cost / p.amount) 
            else:
                # [생성] 신규 매수 시: 새로운 포트폴리오 객체 생성
                new_p = Portfolio(
                    user_id=user.id,
                    amount=payload.amount,
                    avg_price=round(payload.price)
                )
                db.add(new_p)

        elif action == "sell":
            # [체크] 보유 수량이 부족하거나 포트폴리오가 없는 경우
            if not p or p.amount < payload.amount:
                raise HTTPException(status_code=400, detail="매도 가능한 수량이 부족합니다.")
            
            # [계산] 현금 증가 및 주식 수량 차감
            user.balance += int(total_trade_amount)
            p.amount -= payload.amount

            # [삭제] 수량이 0이 되면 포트폴리오 내역 삭제
            if p.amount == 0:
                await db.delete(p)

        # 2. DB 변경 사항 저장 (트랜잭션 커밋)
        await db.commit()
        
        return {"msg": "success", "action": action}
