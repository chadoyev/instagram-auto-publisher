from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Content, SourcePlatform, User


class UserRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def upsert(
        self,
        user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        is_admin: bool = False,
        language: str = "ru",
    ) -> User:
        stmt = (
            pg_insert(User)
            .values(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_admin=is_admin,
                language=language,
            )
            .on_conflict_do_update(
                index_elements=[User.id],
                set_=dict(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    # language is intentionally NOT updated here —
                    # manual admin override must persist across logins
                ),
            )
            .returning(User)
        )
        result = await self.s.execute(stmt)
        await self.s.commit()
        return result.scalar_one()

    async def set_language(self, user_id: int, language: str) -> None:
        await self.s.execute(
            update(User).where(User.id == user_id).values(language=language)
        )
        await self.s.commit()

    async def get(self, user_id: int) -> User | None:
        return await self.s.get(User, user_id)

    async def increment_downloads(self, user_id: int) -> None:
        await self.s.execute(
            update(User)
            .where(User.id == user_id)
            .values(downloads_count=User.downloads_count + 1)
        )
        await self.s.commit()

    async def increment_approved(self, user_id: int) -> None:
        await self.s.execute(
            update(User)
            .where(User.id == user_id)
            .values(approved_count=User.approved_count + 1)
        )
        await self.s.commit()

    async def total_users(self) -> int:
        result = await self.s.execute(select(func.count()).select_from(User))
        return result.scalar_one()

    async def total_downloads(self) -> int:
        result = await self.s.execute(
            select(func.coalesce(func.sum(User.downloads_count), 0))
        )
        return result.scalar_one()

    async def downloads_by_platform(self) -> dict[str, int]:
        q = (
            select(Content.source_platform, func.count())
            .group_by(Content.source_platform)
        )
        result = await self.s.execute(q)
        return {row[0].value: row[1] for row in result.all()}

    async def get_all_ids(self) -> list[int]:
        result = await self.s.execute(select(User.id))
        return list(result.scalars().all())
