import asyncio
from collections import defaultdict
from pathlib import Path


class FileLockRegistry:
    def __init__(self) -> None:
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    def for_path(self, path: Path) -> asyncio.Lock:
        return self._locks[str(path.resolve())]
