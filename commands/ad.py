import discord
from discord.ext import commands
from discord import app_commands


class Components(discord.ui.LayoutView):    
    container1 = discord.ui.Container(
        discord.ui.TextDisplay(content="# __WELCOME TO ZNE__\n**STOP PAYING FOR GARBAGE BOTS THAT BARELY HAVE ANY FEATURES**\nZNE is a 100% free discord raid bot, no premium shenanigans, no hidden paywalls\nZNE has been free for a *YEAR* now (made in april 2025)"),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
        discord.ui.TextDisplay(content="## `❓` What does ZNE offer?\n> Blazing fast discord raider bots\n> Nuke bots that will **100%** crash your phone\n> Easy-to use Webhook spammers\n> Weekly Giveaways!"),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
        discord.ui.MediaGallery(
            discord.MediaGalleryItem(
                media="https://camo.githubusercontent.com/20e833e1611a6b1abb35bb2f6c10411e381b9f145c604a9b7a173a35d10b3ca8/68747470733a2f2f646e7673727a65696a686475697173726c6b6d632e73757061626173652e636f2f73746f726167652f76312f6f626a6563742f7075626c69632f686f737465642d66696c65732f35346130383462322d613765362d343431352d383165392d6364343035326439316335382f56644c785a4d444e5f7374616e646172642e676966",
            ),
        ),
    )


class Panel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ad", description="send the zne advertisement")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ad(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        view = Components()

        await interaction.followup.send(
            "ok loading it nooow!!",
            ephemeral=True
        )
        await interaction.followup.send(
            content="@everyone https://discord.gg/4pQzcZxVXK",
            view=view
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Panel(bot))
