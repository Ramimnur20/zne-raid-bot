import discord
from utils.config import OWNER_IDS, LOG_CHANNEL_ID

# Shared state for farm tokens: {user_id: [token, ...]}
user_farm_tokens: dict[int, list[str]] = {}


def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id in OWNER_IDS


async def log_command(interaction: discord.Interaction, name: str, details: str):
    username = interaction.user.name
    user_mention = interaction.user.mention
    avatar_url = interaction.user.display_avatar.url
    channel = interaction.client.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    class Components(discord.ui.LayoutView):
        container1 = discord.ui.Container(
            discord.ui.Section(
                discord.ui.TextDisplay(
                    content=f"# COMMAND USED\n\nuser: `{username}` ({user_mention})\ncommand `{name}`"
                ),
                accessory=discord.ui.Thumbnail(
                    media=avatar_url
                ),
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(content=f"details:\n```{details}```"),
        )

    view = Components()
    await channel.send(view=view)
