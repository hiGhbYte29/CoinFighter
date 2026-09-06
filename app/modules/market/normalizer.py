import re

from app.core.exceptions import AppError


def normalize_symbol(symbol: str) -> str:
    value = symbol.strip().upper().replace("-", "/").replace("_", "/")
    if "/" not in value:
        for quote in ("USDT", "USDC", "USD", "BTC", "ETH"):
            if value.endswith(quote) and len(value) > len(quote):
                value = f"{value[: -len(quote)]}/{quote}"
                break
    if not re.fullmatch(r"[A-Z0-9.]+/[A-Z0-9.]+(?::[A-Z0-9.]+)?", value):
        raise AppError("MARKET_SYMBOL_INVALID", "交易对格式无效")
    return value
