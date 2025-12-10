import ccxt.async_support as ccxt
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/")
async def get_exchanges():
    """
    Returns a list of available exchanges from the ccxt library.
    """
    return ccxt.exchanges

@router.get("/{exchange_id}/pairs")
async def get_exchange_pairs(exchange_id: str):
    """
    Returns a list of available trading pairs for a given exchange.
    """
    try:
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class()
        await exchange.load_markets()
        # Filter for USDT pairs for simplicity, supporting both formats
        pairs = [symbol for symbol in exchange.symbols if symbol.endswith(('/USDT', ':USDT'))]
        await exchange.close()
        return sorted(pairs)
    except AttributeError:
        raise HTTPException(status_code=404, detail=f"Exchange '{exchange_id}' not found.")
    except Exception as e:
        # It's good practice to close the exchange connection in case of any error
        if 'exchange' in locals() and hasattr(exchange, 'close'):
            await exchange.close()
        raise HTTPException(status_code=500, detail=str(e))
