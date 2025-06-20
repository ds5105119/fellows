from dataclasses import dataclass
from typing import Any, Sequence, TypeVar, cast

from sqlalchemy import Result, SQLColumnExpression, delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute, Session
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import Select

T = TypeVar("T", bound=DeclarativeBase)
_P = Result[tuple[Any]]
_IP = Result[tuple[T]]


@dataclass
class PaginatedResult[T]:
    total: int
    items: T | None


class BaseRepository[T]:
    model: type[T]
    session: type[Session]

    def __init__(self, model: type[T]):
        self.model = model

    def _dict_to_model(self, kwargs: Any) -> Any:
        return {
            k: self.model.__mapper__.relationships[k].mapper.class_(**v) if isinstance(v, dict) else v
            for k, v in kwargs.items()
        }


class BaseCreateRepository[T](BaseRepository[T]):
    def create(self, session: Session, **kwargs: Any) -> T:
        kwargs = self._dict_to_model(kwargs)
        session.add(entity := self.model(**kwargs))
        session.commit()
        session.refresh(entity)

        return entity

    def bulk_create(self, session: Session, kwargs: Sequence[dict[str, Any]]) -> None:
        stmt = insert(self.model).values(kwargs)
        session.execute(stmt)
        session.commit()


class BaseReadRepository[T](BaseRepository[T]):
    def get(
        self,
        session: Session,
        filters: Sequence,
        columns: Sequence[SQLColumnExpression | DeclarativeBase] | None = None,
        orderby: Sequence[ColumnElement] | None = None,
        options: Sequence[ExecutableOption] = None,
        stmt: Select | None = None,
        join: Sequence[ColumnElement | InstrumentedAttribute] | None = None,
    ) -> _P:
        if stmt is None:
            stmt = select(self.model.__table__)
        if join:
            stmt = stmt.join(*join)
        if filters:
            stmt = stmt.where(*filters)
        if orderby:
            stmt = stmt.order_by(*orderby)
        if options:
            stmt = stmt.options(*options)
        if columns:
            stmt = stmt.with_only_columns(*columns)
        result = session.execute(stmt)

        return result

    def get_by_id(
        self,
        session: Session,
        id: int | str,
        columns: Sequence[SQLColumnExpression | DeclarativeBase] | None = None,
        orderby: Sequence[ColumnElement] | None = None,
        options: Sequence[ExecutableOption] = None,
        stmt: Select | None = None,
        join: Sequence[ColumnElement | InstrumentedAttribute] | None = None,
    ) -> _P:
        if not hasattr(self.model, "id"):
            raise AttributeError("Model does not have an 'id' attribute")

        return self.get(
            session=session,
            filters=[self.model.id == id],
            columns=columns,
            orderby=orderby,
            options=options,
            stmt=stmt,
            join=join,
        )

    def get_page(
        self,
        session: Session,
        page: int,
        size: int,
        filters: Sequence,
        columns: Sequence[SQLColumnExpression | DeclarativeBase] | None = None,
        orderby: Sequence[ColumnElement] | None = None,
        options: Sequence[ExecutableOption] = None,
        join: Sequence[ColumnElement | InstrumentedAttribute] | None = None,
    ) -> _P:
        return self.get(
            session=session,
            filters=filters,
            columns=columns,
            orderby=orderby,
            options=options,
            stmt=select(self.model.__table__).fetch(size).offset(page * size),
            join=join,
        )

    def get_instance(
        self,
        session: Session,
        filters: Sequence,
        orderby: Sequence[ColumnElement] | None = None,
        options: Sequence[ExecutableOption] = None,
        join: Sequence[ColumnElement | InstrumentedAttribute] | None = None,
    ) -> _IP:
        return self.get(
            session=session,
            filters=filters,
            orderby=orderby,
            options=options,
            stmt=select(self.model),
            join=join,
        )


class BaseUpdateRepository[T](BaseRepository[T]):
    def update(
        self,
        session: Session,
        filters: Sequence,
        columns: Sequence[SQLColumnExpression | DeclarativeBase] | None = None,
        options: Sequence[ExecutableOption] = None,
        stmt: Select | None = None,
        **kwargs,
    ) -> _P:
        if stmt is None:
            stmt = update(self.model)
        if filters:
            stmt = stmt.where(*filters)
        if options:
            stmt = stmt.options(*options)
        if columns:
            stmt = stmt.with_only_columns(*columns)
        stmt = stmt.values(**self._dict_to_model(kwargs))
        result = session.execute(stmt)
        session.commit()

        return result


class BaseDeleteRepository[T](BaseRepository[T]):
    def _delete(self, session: Session, id: int | str) -> None:
        stmt = delete(self.model).where(cast("ColumnElement[bool]", self.model.id == id))
        session.execute(stmt)
        session.commit()

    def _bulk_delete(self, session: Session, ids: list[int | str]) -> None:
        stmt = delete(self.model).where(cast("ColumnElement[bool]", self.model.id.in_(ids)))
        session.execute(stmt)
        session.commit()

    def delete(self, session: Session, id: int | str | tuple[int | str] | list[int | str]) -> None:
        if isinstance(id, (int, str)):
            self._delete(session, id)
        elif isinstance(id, (tuple, list)) and len(id):
            self._bulk_delete(session, list(id))
        else:
            raise ValueError("'id' must be an int, str, or Iterable of int or str")


class ABaseRepository[T](BaseRepository[T]):
    session: type[AsyncSession]


class ABaseCreateRepository[T](ABaseRepository[T]):
    async def create(self, session: AsyncSession, **kwargs: Any) -> T:
        kwargs = self._dict_to_model(kwargs)
        session.add(entity := self.model(**kwargs))
        await session.commit()
        await session.refresh(entity)

        return entity

    async def bulk_create(self, session: AsyncSession, kwargs: Sequence[dict[str, Any]]) -> None:
        stmt = insert(self.model).values(kwargs)
        await session.execute(stmt)
        await session.commit()


class ABaseReadRepository[T](ABaseRepository[T]):
    async def get(
        self,
        session: AsyncSession,
        filters: Sequence,
        columns: Sequence[SQLColumnExpression | DeclarativeBase] | None = None,
        orderby: Sequence[ColumnElement] | None = None,
        options: Sequence[ExecutableOption] = None,
        stmt: Select | None = None,
        join: Sequence[ColumnElement | InstrumentedAttribute] | None = None,
    ) -> _P:
        if stmt is None:
            stmt = select(self.model.__table__)
        if join:
            for t in join:
                stmt = stmt.join(t)
        if filters:
            stmt = stmt.where(*filters)
        if orderby:
            stmt = stmt.order_by(*orderby)
        if options:
            stmt = stmt.options(*options)
        if columns:
            stmt = stmt.with_only_columns(*columns)
        result = await session.execute(stmt)

        return result

    async def get_by_id(
        self,
        session: AsyncSession,
        id: int | str,
        columns: Sequence[SQLColumnExpression | DeclarativeBase] | None = None,
        orderby: Sequence[ColumnElement] | None = None,
        options: Sequence[ExecutableOption] = None,
        stmt: Select | None = None,
        join: Sequence[ColumnElement | InstrumentedAttribute] | None = None,
    ) -> _P:
        if not hasattr(self.model, "id"):
            raise AttributeError("Model does not have an 'id' attribute")

        return await self.get(
            session=session,
            filters=[self.model.id == id],
            columns=columns,
            orderby=orderby,
            options=options,
            stmt=stmt,
            join=join,
        )

    async def get_page(
        self,
        session: AsyncSession,
        page: int,
        size: int,
        filters: Sequence,
        columns: Sequence[SQLColumnExpression | DeclarativeBase] | None = None,
        orderby: Sequence[ColumnElement] | None = None,
        options: Sequence[ExecutableOption] = None,
        join: Sequence[ColumnElement | InstrumentedAttribute] | None = None,
    ) -> _P:
        return await self.get(
            session=session,
            filters=filters,
            columns=columns,
            orderby=orderby,
            options=options,
            stmt=select(self.model).fetch(size).offset(page * size),
            join=join,
        )

    async def get_page_with_total(
        self,
        session: AsyncSession,
        page: int,
        size: int,
        filters: Sequence,
        columns: Sequence[SQLColumnExpression | DeclarativeBase] | None = None,
        orderby: Sequence[ColumnElement] | None = None,
        options: Sequence[ExecutableOption] = None,
        join: Sequence[ColumnElement | InstrumentedAttribute] | None = None,
    ) -> PaginatedResult[_P]:
        total_result = await self.get(
            session,
            filters,
            join=join,
            stmt=select(func.count(self.model.id)),
        )
        total = int(total_result.scalar_one_or_none()) or 0

        if total == 0:
            return PaginatedResult(total, [])

        items = await self.get_page(session, page, size, filters, columns, orderby, options, join)
        items = items.scalars().all()

        return PaginatedResult(total, items)

    async def get_instance(
        self,
        session: AsyncSession,
        filters: Sequence,
        orderby: Sequence[ColumnElement] | None = None,
        options: Sequence[ExecutableOption] = None,
        join: Sequence[ColumnElement | InstrumentedAttribute] | None = None,
    ) -> _IP:
        return await self.get(
            session=session,
            filters=filters,
            orderby=orderby,
            options=options,
            stmt=select(self.model),
            join=join,
        )


class ABaseUpdateRepository[T](ABaseRepository[T]):
    async def update(
        self,
        session: AsyncSession,
        filters: Sequence,
        columns: Sequence[SQLColumnExpression | DeclarativeBase] | None = None,
        options: Sequence[ExecutableOption] = None,
        stmt: Select | None = None,
        **kwargs,
    ) -> _P:
        if stmt is None:
            stmt = update(self.model)
        if filters:
            stmt = stmt.where(*filters)
        if options:
            stmt = stmt.options(*options)
        if columns:
            stmt = stmt.with_only_columns(*columns)
        stmt = stmt.values(**self._dict_to_model(kwargs))
        result = await session.execute(stmt)
        await session.commit()

        return result


class ABaseDeleteRepository[T](ABaseRepository[T]):
    async def _delete(self, session: AsyncSession, id: int | str) -> None:
        stmt = delete(self.model).where(cast("ColumnElement[bool]", self.model.id == id))
        await session.execute(stmt)
        await session.commit()

    async def _bulk_delete(self, session: AsyncSession, ids: list[int | str]) -> None:
        stmt = delete(self.model).where(cast("ColumnElement[bool]", self.model.id.in_(ids)))
        await session.execute(stmt)
        await session.commit()

    async def delete(self, session: AsyncSession, id: int | str | tuple[int | str] | list[int | str]) -> None:
        if isinstance(id, (int, str)):
            await self._delete(session, id)
        elif isinstance(id, (tuple, list)) and len(id):
            await self._bulk_delete(session, list(id))
        else:
            raise ValueError("'id' must be an int, str, or Iterable of int or str")
