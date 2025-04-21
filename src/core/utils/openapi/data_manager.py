import inspect
import json
from abc import ABC, abstractmethod
from typing import Any, Callable

import polars as pl

from .data_cache import BaseDataCache
from .data_loader import BaseOpenDataLoader


async def execute(func, *args, **kwargs):
    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        return func(*args, **kwargs)


class BaseDataManager(ABC):
    """
    REST API 의 데이터를 캐시하는 클래스

    Attributes:
        data (Any): 데이터
    """

    data: Any
    is_initialized: bool
    path: str
    params: dict
    id: int

    @abstractmethod
    async def init(self):
        """
        BaseDataManager 의 데이터를 초기화하는 클래스
        """
        pass

    @abstractmethod
    def register_callback(self, callback: Callable):
        """
        BaseDataManager 의 데이터의 변경을 감지해야 하는 경우 콜백 함수를 등록하여 사용할 수 있습니다.

        Args:
            callback: 콜백
        """
        pass


class PolarsDataManager(BaseDataManager):
    def __init__(
        self,
        data_loader: BaseOpenDataLoader,
        data_cache: BaseDataCache,
        path: str,
        params: dict | None = None,
        infer_scheme_length: int = 100000,
    ):
        self.data: pl.DataFrame = pl.DataFrame()
        self.path: str = path
        self.params: dict = params or {}
        self.is_initialized: bool = False
        self._data_loader = data_loader
        self._data_cache = data_cache
        self._infer_scheme_length = infer_scheme_length
        self._callbacks: list[Callable] = []
        self.id = hash(json.dumps(self.params).encode() + self.path.encode())

    async def init(self, always_reload: bool = False):
        if not always_reload:
            data = await self._data_cache.get_cache(self.path)
        else:
            data = None

        if data is None:
            data = await self._data_loader.get_data(self.path, self.params)
            await self._data_cache.set_cache(self.path, data)

        self.data = pl.DataFrame(data, infer_schema_length=self._infer_scheme_length)
        self.is_initialized = True
        await self._notify_callbacks()

    async def _notify_callbacks(self):
        [await execute(callback) for callback in self._callbacks]

    def register_callback(self, callback: Callable):
        self._callbacks.append(callback)
