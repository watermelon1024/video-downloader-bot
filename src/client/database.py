"""
The database module of the bot.
"""

import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite


class Database:
    """
    The database class of the bot.
    """

    def __init__(self, path: str) -> None:
        self.path = path

    async def initialize(self) -> None:
        """
        Initializes the database.
        """
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            # create error log
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS error_log (
                    id TEXT PRIMARY KEY,
                    traceback TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    async def _get(self, table: str, where: dict[str, Any], fetch_size: int = 1) -> aiosqlite.Row:
        """
        Gets the data from database.

        :param table: The table to get the configuration from.
        :type table: str
        :param where: The where clause of the query.
        :type where: dict[str, Any]
        :param fetch_size: The number of rows to fetch. 0 equal to fetchall(), 1 equal to fetchone().
        :type fetch_size: int
        :return: The configuration of the guild.
        :rtype: aiosqlite.Row
        """
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                f"SELECT * FROM {table} WHERE {' AND '.join(f'{k} = ?' for k in where.keys())}",
                (*where.values(),),
            ) as cursor:
                if fetch_size == 0:
                    return await cursor.fetchall()
                if fetch_size == 1:
                    return await cursor.fetchone()
                return await cursor.fetchmany(fetch_size)

    async def _insert(self, table: str, data: dict[str, Any]) -> None:
        """
        Inserts the data into the specified table.

        :param table: The table to insert the data into.
        :type table: str
        :param data: The data to insert.
        :type data: dict[str, Any]
        :return: None
        :rtype: None
        """
        column = (*data.keys(),)
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                f"""
                INSERT INTO {table}
                    ({', '.join(column)})
                VALUES
                    (?{', ?' * (len(column) - 1)})
                """,
                (*data.values(),),
            )
            await db.commit()
            return

    async def _edit(
        self, table: str, where: dict[str, Any], on_conflict: str, data: dict[str, Any]
    ) -> None:
        """
        Edits the data of the specified table. (INSERT OR UPDATE)

        :param table: The table to edit the data in.
        :type table: str
        :param where: The where clause of the query.
        :type where: dict[str, Any]
        :param on_conflict: The on conflict clause of the query.
        :type on_conflict: str
        :param data: The data to edit.
        :type data: dict[str, Any]
        :return: None
        :rtype: None
        """
        column = (*where.keys(), *data.keys())
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                f"""
                INSERT INTO {table}
                    ({', '.join(column)})
                VALUES
                    (?{', ?' * (len(column) - 1)})
                ON CONFLICT ({on_conflict}) DO UPDATE SET
                    {', '.join(f"{k} = ?" for k in column)}
                """,
                (*where.values(), *data.values()) * 2,
            )
            await db.commit()
            return

    async def _update(self, table: str, where: dict[str, Any], data: dict[str, Any]) -> None:
        """
        Updates the data of the specified table. (UPDATE)

        :param table: The table to update the data in.
        :type table: str
        :param where: The where clause of the query.
        :type where: dict[str, Any]
        :param data: The data to update.
        :type data: dict[str, Any]
        :return: None
        :rtype: None
        """
        column = (*data.keys(),)
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                f"""
                UPDATE {table}
                SET {', '.join(f"{k} = ?" for k in column)}
                WHERE {' AND '.join(f"{k} = ?" for k in where.keys())}
                """,
                (*data.values(), *where.keys()),
            )
            await db.commit()
            return

    async def new_error_log(self, exception: str | Exception) -> uuid.UUID:
        """
        Creates a new error log.
        """
        await self._insert(
            "error_log",
            {
                "id": str(err_id := uuid.uuid4()),
                "traceback": (
                    "".join(traceback.format_exception(exception))
                    if issubclass(type(exception), Exception)
                    else exception
                ),
                "timestamp": int(datetime.now().timestamp()),
            },
        )
        return err_id

    async def get_error_log(self, err_id: str) -> aiosqlite.Row:
        """
        Gets the error log.
        """
        return await self._get("error_log", {"id": err_id})
