"""
Cog module for the command logger.
"""


import aiohttp
import discord
from discord.ext import commands, tasks

from src.client.i18n import I18n
from src.main import BaseCog, Bot
from src.utils.discord import get_user_name


class CmdLogger(BaseCog):
    """
    The cog class for the command logger.
    """

    log_content: str = ""
    log_buffer: list[str] = []
    message_id: int = None

    async def _log_command(
        self,
        ctx: commands.Context | discord.ApplicationContext,
        command_type: str,
        command_args: str,
    ) -> None:
        """
        Log a command usage.
        This is an internal function and should not be called directly.

        :param ctx: The context of the command.
        :type ctx: commands.Context | discord.ApplicationContext
        :param command_type: The type of the command.
        :type command_type: str
        :param command_args: The arguments of the command.
        :type command_args: str
        """
        command_name = (
            f"{ctx.command.full_parent_name} {ctx.command.name}"
            if ctx.command.full_parent_name
            else ctx.command.name
        )
        command_args = f" - {command_args}" if command_args else ""
        msg = (
            f"[{ctx.guild.name} #{ctx.channel.name}] {get_user_name(ctx.author)}: "
            f"({command_type}-command) {command_name}{command_args}"
        )
        # terminal log
        self.bot.logger.info(msg)
        # webhook log
        if self.bot.log_webhook:
            self.log_buffer.append(msg)

    @discord.Cog.listener()
    async def on_command(self, ctx: commands.Context) -> None:
        """
        The event that is triggered when a message command is used.
        """
        await self._log_command(ctx, "text", ", ".join(f"{k}: {v}" for k, v in ctx.kwargs))

    @discord.Cog.listener()
    async def on_application_command(self, ctx: discord.ApplicationContext) -> None:
        """
        The event that is triggered when an application command is used.
        """
        command_type = "application"
        args = ""
        match ctx.command.type:
            case 1:
                command_type = "slash"
                if (options := ctx.interaction.data.get("options")) is not None:
                    args = ", ".join(f"{option['name']}: {option['value']}" for option in options)
            case 2:
                command_type = "user"
                args = f"user: {ctx.interaction.data['target_id']}"
            case 3:
                command_type = "message"
                args = f"message: {ctx.interaction.data['target_id']}"
        await self._log_command(ctx, command_type, args)

    @discord.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """
        The event that is triggered when a message command error occurs.
        """
        if isinstance(error, (commands.CommandNotFound, commands.NotOwner)):
            return
        self.logger.exception(type(error).__name__)

    @discord.Cog.listener()
    async def on_application_command_error(
        self,
        ctx: discord.ApplicationContext,
        error: discord.DiscordException,
    ) -> None:
        """
        The event that is triggered when an application command error occurs.
        """
        error_id = await self.db.new_error_log(error)
        await ctx.respond(
            I18n.get("slash.error_log.hint_message", ctx, err_id=str(error_id)),
            ephemeral=True,
        )
        self.logger.exception(type(error).__name__, exc_info=error)

    @tasks.loop(seconds=10)
    async def _edit_message(self) -> None:
        if not self.log_buffer:
            return

        buffer = "\n".join(self.log_buffer)
        self.log_buffer.clear()
        if len(self.log_content) + len(buffer) >= 1994:  # 2000 (max len) - 6 (code block markdown)
            self.log_content = buffer
            self.message_id = None
        else:
            self.log_content += buffer + "\n"
        # send webhook message
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(self.bot.log_webhook, session=session)
            if self.message_id is None:
                message = await webhook.send(f"```{self.log_content}```", wait=True)
                self.message_id = message.id
            else:
                await webhook.edit_message(self.message_id, content=f"```{self.log_content}```")

    @discord.Cog.listener()
    async def on_ready(self) -> None:
        if self.bot.log_webhook and not self._edit_message.is_running():
            self._edit_message.start()


def setup(bot: Bot) -> None:
    """
    The setup function of the cog.
    """
    bot.add_cog(CmdLogger(bot))
