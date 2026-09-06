"""Short import path for the CoinFighter technical-indicator API.

Strategy scripts can use ``import indicators`` while the implementation remains
in :mod:`coinfighter.indicators`.
"""

from coinfighter import indicators as _implementation

__all__ = _implementation.__all__

globals().update({name: getattr(_implementation, name) for name in __all__})
