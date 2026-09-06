import importlib.util
import inspect
import re
from pathlib import Path
from types import ModuleType
from uuid import uuid4

from app.core.exceptions import AppError
from app.modules.strategies.base import Strategy
from app.modules.strategies.schemas import StrategyInfo, StrategySource
from app.modules.strategies.validator import validate_python_source

DEFAULT_STRATEGY_SOURCE = """import indicators
from app.modules.strategies.base import Bar, Strategy, StrategyContext


class MyStrategy(Strategy):
    name = "{name}"
    description = "用户策略"
    default_parameters = {{}}

    def on_bar(self, context: StrategyContext, bar: Bar) -> None:
        # 示例：通过 indicators.rsi(context.closes(), 14) 计算指标并产生模拟交易信号
        pass
"""


class StrategyLoader:
    def __init__(self, user_directory: Path, example_directory: Path) -> None:
        self.user_directory = user_directory.resolve()
        self.example_directory = example_directory.resolve()
        self.user_directory.mkdir(parents=True, exist_ok=True)
        self.example_directory.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str, *, examples: bool = False) -> Path:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,63}", name):
            raise AppError("STRATEGY_NAME_INVALID", "策略名称只能包含字母、数字和下划线")
        directory = self.example_directory if examples else self.user_directory
        path = (directory / f"{name}.py").resolve()
        if path.parent != directory:
            raise AppError("STRATEGY_PATH_INVALID", "策略路径越界")
        return path

    def _all_paths(self) -> list[tuple[Path, bool]]:
        paths = [(path, False) for path in sorted(self.user_directory.glob("*.py"))]
        user_names = {path.stem for path, _ in paths}
        paths.extend(
            (path, True)
            for path in sorted(self.example_directory.glob("*.py"))
            if path.stem not in user_names
        )
        return paths

    @staticmethod
    def _load_module(path: Path) -> ModuleType:
        module_name = f"coinfighter_strategy_{path.stem}_{uuid4().hex}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"无法读取策略 {path.name}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def load_class(self, name: str) -> type[Strategy]:
        user_path = self._path(name)
        example_path = self._path(name, examples=True)
        path = user_path if user_path.exists() else example_path
        if not path.exists():
            raise AppError("STRATEGY_NOT_FOUND", "没有找到指定策略", status_code=404)
        source = path.read_text(encoding="utf-8")
        errors = validate_python_source(source, str(path))
        if errors:
            raise AppError("STRATEGY_VALIDATION_FAILED", "策略校验失败", details={"errors": errors})
        try:
            module = self._load_module(path)
        except Exception as error:
            raise AppError(
                "STRATEGY_IMPORT_FAILED",
                "策略导入失败",
                details={"errors": [str(error)]},
            ) from error
        candidates = [
            value
            for _, value in inspect.getmembers(module, inspect.isclass)
            if issubclass(value, Strategy)
            and value is not Strategy
            and value.__module__ == module.__name__
        ]
        if len(candidates) != 1:
            raise AppError(
                "STRATEGY_CLASS_INVALID",
                "每个策略文件必须定义且只能定义一个 Strategy 子类",
            )
        return candidates[0]

    def inspect(self, path: Path, example: bool) -> StrategyInfo:
        source = path.read_text(encoding="utf-8")
        errors = validate_python_source(source, str(path))
        strategy_class: type[Strategy] | None = None
        if not errors:
            try:
                strategy_class = self.load_class(path.stem)
            except AppError as error:
                errors.append(error.message)
                errors.extend(error.details.get("errors", []))
        return StrategyInfo(
            name=path.stem,
            class_name=strategy_class.__name__ if strategy_class else None,
            description=getattr(strategy_class, "description", "") if strategy_class else "",
            default_parameters=getattr(strategy_class, "default_parameters", {})
            if strategy_class
            else {},
            source_path=str(path),
            editable=not example,
            valid=not errors,
            errors=errors,
        )

    def list(self) -> list[StrategyInfo]:
        return [self.inspect(path, example) for path, example in self._all_paths()]

    def get_info(self, name: str) -> StrategyInfo:
        for info in self.list():
            if info.name == name:
                return info
        raise AppError("STRATEGY_NOT_FOUND", "没有找到指定策略", status_code=404)

    def source(self, name: str) -> StrategySource:
        user_path = self._path(name)
        example_path = self._path(name, examples=True)
        path = user_path if user_path.exists() else example_path
        if not path.exists():
            raise AppError("STRATEGY_NOT_FOUND", "没有找到指定策略", status_code=404)
        source = path.read_text(encoding="utf-8")
        errors = validate_python_source(source, str(path))
        return StrategySource(name=name, source=source, valid=not errors, errors=errors)

    def create(self, name: str, source: str | None = None) -> StrategySource:
        path = self._path(name)
        if path.exists():
            raise AppError("STRATEGY_EXISTS", "同名策略已经存在", status_code=409)
        return self.save(name, source or DEFAULT_STRATEGY_SOURCE.format(name=name))

    def save(self, name: str, source: str) -> StrategySource:
        path = self._path(name)
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        temporary.write_text(source, encoding="utf-8")
        temporary.replace(path)
        errors = validate_python_source(source, str(path))
        return StrategySource(name=name, source=source, valid=not errors, errors=errors)
