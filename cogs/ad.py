import discord
from discord.ext import commands
from discord import app_commands

class Components(discord.ui.LayoutView):    
    container1 = discord.ui.Container(
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
        discord.ui.Section(
            discord.ui.TextDisplay(content="## ☣ - 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙏𝙊 𝙕𝙉𝙀\n*Stop paying for garbage*\n*Join + main us!*"),
            accessory=discord.ui.Thumbnail(
                media="https://happydropbox.lovable.app/zne-logo.gif",
            ),
        ),
        discord.ui.TextDisplay(content="\n```\n▻ Nuke Bots, Wipe servers in seconds\n▻ FREE Raid Bots\n▻ NO Paywalls, all for FREE!\n▻ over 15+ commands in Raid Bot!\n▻ AMAZING Community, Non-toxic\n```\nSo? what are you waiting for? Join ZNE TODAY!"),
        discord.ui.ActionRow(
                discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="zne",
                    disabled=True,
                    custom_id="d0e839b6dd8b4645e95284551f9766e2",
                ),
                discord.ui.Button(
                    url="https://discord.com/invite/sillyz",
                    style=discord.ButtonStyle.link,
                    label="JOIN",
                ),
                discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="ontop",
                    disabled=True,
                    custom_id="56507a799c484884ec74e97ff3a2afde",
                ),
        ),
    )

class Panel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ad", description="send the zne advertisement")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ad(self, interaction: discord.Interaction):

        await interaction.response.send_message(
            "Loading Containr..",
            ephemeral=True
        )

        view = Components()

        await interaction.followup.send(
            view=view
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Panel(bot))