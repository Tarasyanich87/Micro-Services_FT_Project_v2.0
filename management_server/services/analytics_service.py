"""
Service for handling analytics queries.
"""

from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.models import Bot
from ..tools.redis_streams_event_bus import core_streams_event_bus


class AnalyticsService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.event_bus = core_streams_event_bus

    async def get_performance_analytics(
        self, bot_id: Optional[int], timeframe: str, user_id: Any
    ) -> Dict[str, Any]:
        """Calculate and return performance analytics for bots."""
        # For now, return mock data to test API
        result = {
            "total_trades": 150,
            "profitable_trades": 90,
            "avg_profit": 2.5,
            "win_rate": 60.0,
        }

        return result

    async def get_profit_analytics(
        self, bot_id: Optional[int], period: str, user_id: int
    ) -> Dict[str, Any]:
        """Calculate and return profit analytics."""
        query = select(func.sum(Bot.total_profit)).where(Bot.created_by == user_id)

        if bot_id:
            query = query.where(Bot.id == bot_id)

        # Period-based filtering would require a more complex query on a trades table.
        # This is a simplified version based on the bot's lifetime profit.

        total_profit = await self.db.scalar(query)
        return {"total_profit": total_profit or 0.0}

    async def get_risk_analytics(
        self, bot_id: Optional[int], user_id: int
    ) -> Dict[str, Any]:
        """Calculate and return risk analytics (e.g., max drawdown)."""
        query = select(func.max(Bot.max_drawdown)).where(Bot.created_by == user_id)
        if bot_id:
            query = query.where(Bot.id == bot_id)

        max_drawdown = await self.db.scalar(query)
        return {"max_drawdown": max_drawdown or 0.0}

    async def get_portfolio_analytics(self, user_id: int) -> Dict[str, Any]:
        """Get overall portfolio analytics."""
        query = select(
            func.sum(Bot.stake_amount).label("total_stake"),
            func.sum(Bot.total_profit).label("total_profit_sum"),
        ).where(Bot.created_by == user_id)

        result = await self.db.execute(query)
        stats = result.first()

        total_stake = stats.total_stake or 0.0
        total_profit_sum = stats.total_profit_sum or 0.0
        portfolio_value = total_stake + total_profit_sum

        return {"portfolio_value": portfolio_value}

    async def get_market_analytics(self, symbol: str = "bitcoin") -> Dict[str, Any]:
        """Get general market analytics from CoinGecko."""
        try:
            from pycoingecko import CoinGeckoAPI

            cg = CoinGeckoAPI()
            price_data = cg.get_price(
                ids=symbol,
                vs_currencies="usd",
                include_24hr_change="true",
            )

            if not price_data or symbol not in price_data:
                return {"error": f"Could not fetch data for symbol: {symbol}"}

            market_data = price_data[symbol]
            current_price = market_data.get("usd")
            price_change_24h = market_data.get("usd_24h_change")

            sentiment = "neutral"
            if price_change_24h is not None:
                if price_change_24h > 2:
                    sentiment = "positive"
                elif price_change_24h < -2:
                    sentiment = "negative"

            return {
                "symbol": symbol,
                "current_price_usd": current_price,
                "price_change_percentage_24h": price_change_24h,
                "market_sentiment": sentiment,
            }
        except Exception as e:
            return {"error": str(e)}
