from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.portfolio import Portfolio
from app.models.user import User

class PortfolioService:
    """사용자 자산 상태 계산 및 조회 엔진"""

    @staticmethod
    async def get_user_status(db: AsyncSession, user: User, current_price: float):
        """실시간 시세를 반영한 총 자산 및 수익률 계산 (정수 처리)"""
        
        # 1. DB에서 해당 유저의 포트폴리오(보유 주식) 조회
        result = await db.execute(select(Portfolio).where(Portfolio.user_id == user.id))
        p = result.scalars().first()

        # 2. 보유 정보 추출 (없으면 0)
        amount = p.amount if p else 0
        avg_price = p.avg_price if p else 0

        # 3. 자산 계산 (원화 기준이므로 모든 금액은 정수화/반올림)
        # 투자 원금 (보유수량 * 평단가)
        investment = int(amount * avg_price)
        
        # 평가 금액 (보유수량 * 현재 실시간 시세)
        evaluation = int(amount * current_price)
        
        # 평가 손익 (평가 금액 - 투자 원금)
        profit = evaluation - investment
        
        # 총 자산 (보유 현금 + 현재 주식 가치)
        total_asset = int(user.balance + evaluation)

        # 4. 결과 반환
        return {
            "cash": int(user.balance),
            "holdings": amount,
            "evaluation": evaluation,
            "profit": profit,
            "total_asset": total_asset
        }
