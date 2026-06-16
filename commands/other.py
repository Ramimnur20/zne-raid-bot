import discord
import base64
from discord import app_commands
from discord.ext import commands
from utils.helpers import log_command
from utils.constants import CHECKMARK, CROSS

class OtherCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="userinfo", description="general info about a user")
    @app_commands.describe(user="The user to get info about")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def userinfo(self, interaction: discord.Interaction, user: discord.User = None):
        await interaction.response.defer(ephemeral=True)
        target = user or interaction.user
        
        # Fetch full user to ensure banner access
        try:
            full_user = await self.bot.fetch_user(target.id)
        except:
            full_user = target

        display_name = full_user.display_name
        join_ts = f"<t:{int(full_user.created_at.timestamp())}:R>"
        
        serv_ts = "not in server"
        if interaction.guild:
            member = interaction.guild.get_member(full_user.id)
            if member and member.joined_at:
                serv_ts = f"<t:{int(member.joined_at.timestamp())}:R>"

        userid_into_base64 = base64.b64encode(str(full_user.id).encode()).decode().rstrip("=")
        bot_status = CHECKMARK if full_user.bot else CROSS
        usericon = full_user.display_avatar.url
        banner = full_user.banner.url if hasattr(full_user, 'banner') and full_user.banner else "https://placehold.co/680x240?text=nobanner"

        class UserInfo(discord.ui.LayoutView):    
            container1 = discord.ui.Container(
                discord.ui.Section(
                    discord.ui.TextDisplay(content=f"# {display_name}\ndiscord join: {join_ts}\nserver join: {serv_ts}\nusername: `{full_user.name}`\nid: `{full_user.id}`\nfirst token segment: `{userid_into_base64}`\nbot?: {bot_status}"),
                    accessory=discord.ui.Thumbnail(
                        media=usericon,
                    ),
                ),
                discord.ui.MediaGallery(
                    discord.MediaGalleryItem(
                        media=banner,
                    ),
                ),
                accent_colour=discord.Colour(16777215),
            )

        await interaction.followup.send(view=UserInfo())
        await log_command(interaction, "userinfo", f"viewed info for {full_user.id}")

    @app_commands.command(name="permcheck", description="check if the server is raidable or not")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def permcheck(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        class Components(discord.ui.LayoutView):    
            container1 = discord.ui.Container(
                discord.ui.TextDisplay(content="**check if server is raidable or not**\nthis checks if the bot can send public messages which shows if a server is raidable"),
                discord.ui.ActionRow(
                        discord.ui.Button(
                            style=discord.ButtonStyle.secondary,
                            label="say",
                            custom_id="5b1ec20e48b54f008bd08c2644ba1d66",
                        ),
                ),
            )

            async def interaction_check(self, it: discord.Interaction) -> bool:
                cid = it.data.get("custom_id")
                if cid == "5b1ec20e48b54f008bd08c2644ba1d66":
                    await it.response.defer(ephemeral=True)
                    status_text = "not raidable"

                    # Attempt a standard message send first. 
                    # This is the most reliable way to check for read-only or locked channels.
                    try:
                        msg = await it.channel.send("\u200c")
                        status_text = "yes its raidable"
                        try: await msg.delete()
                        except: pass
                    except discord.Forbidden:
                        # If standard fails, try the bot's interaction raid method (webhook followup)
                        try:
                            msg = await it.followup.send("\u200c", ephemeral=False)
                            # Detect if Discord forced the message to be ephemeral (common if External Apps are restricted)
                            if msg.flags.ephemeral:
                                status_text = "not raidable"
                            else:
                                status_text = "yes its raidable"
                            
                            try: await msg.delete()
                            except: pass
                        except:
                            pass
                    except Exception:
                        pass
                    
                    class ResultView(discord.ui.LayoutView):
                        container1 = discord.ui.Container(
                            discord.ui.TextDisplay(content=f"**check if server is raidable or not**\n\nresult: **{status_text}**"),
                            accent_colour=discord.Colour(16777215)
                        )
                    await interaction.edit_original_response(view=ResultView())

                    raid_status = "is raidable" if status_text == "yes its raidable" else "isnt raidable"
                    await log_command(it, "permcheck", f"checked server raidability, the server {raid_status}")
                    return False


        await interaction.followup.send(view=Components(), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(OtherCog(bot))