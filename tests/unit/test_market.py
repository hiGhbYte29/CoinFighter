import pytest

from app.modules.market.normalizer import normalize_symbol


@pytest.mark.parametrize(
    ("source", "expected"),
    [("btc-usdt", "BTC/USDT"), ("ETH_USDT", "ETH/USDT"), ("solusdt", "SOL/USDT")],
)
def test_normalize_symbol(source: str, expected: str) -> None:
    assert normalize_symbol(source) == expected
