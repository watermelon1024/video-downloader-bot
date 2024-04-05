"""
Cog module for the error commands.
"""

import uuid

import discord

from src.client.i18n import I18n, option, slash_command
from src.main import BaseCog, Bot


class ErrorCog(BaseCog):
    """
    The cog class for the error commands.
    """

    @slash_command("error_log")
    @option("error_log", "err_id")
    async def error_log(self, ctx: discord.ApplicationContext, err_id: str):
        await ctx.defer(ephemeral=True)

        if not await self.bot.is_owner(ctx.author):
            await ctx.respond(I18n.get("slash.error_log.response.no_permission", ctx))
            return

        try:
            err_uuid = uuid.UUID(err_id)
        except ValueError:
            await ctx.respond(I18n.get("slash.error_log.response.invalid_id", ctx))
            return

        err_log = await self.db.get_error_log(str(err_uuid))
        if err_log is None:
            await ctx.respond(I18n.get("slash.error_log.response.not_found", ctx))
            return

        traceback: str = err_log["traceback"]
        msg = (
            I18n.get("slash.error_log.response.success", ctx)
            + f"<t:{err_log['timestamp']}:F> (<t:{err_log['timestamp']}:R>)"
        )
        if len(msg) + len(traceback) <= 1994:  # 2000 - 6(len of "`"*6)
            await ctx.respond(f"{msg}```{traceback}```")
        else:
            await ctx.respond(file=discord.File(traceback, f"{err_uuid}.txt"))


def setup(bot: Bot) -> None:
    """
    The setup function of the cog.
    """
    bot.add_cog(ErrorCog(bot))
