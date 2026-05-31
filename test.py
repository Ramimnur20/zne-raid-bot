# this file isnt used by the codebase at all, you can safely delete this file, its just for testing purposes
import discord

class PresetList(discord.ui.LayoutView):    
    container1 = discord.ui.Container(
        discord.ui.TextDisplay(content="## your presets"),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
        discord.ui.Section(
            discord.ui.TextDisplay(content="{title} - 0 uses"),
            accessory=discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="view contents",
                custom_id="view_content",
            ),
        ),
    )