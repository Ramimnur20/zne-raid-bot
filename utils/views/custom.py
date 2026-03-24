import discord
from discord import AllowedMentions

from utils.db import get_custom_message, delete_custom_message, set_custom_message


class CustomButtonPanel(discord.ui.LayoutView):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    container1 = discord.ui.Container(
        discord.ui.Section(
            discord.ui.TextDisplay(content="# custom message panel"),
            accessory=discord.ui.Button(style=discord.ButtonStyle.danger, label="remove message", custom_id="remove_custom_message")
        ),
        discord.ui.Section(
            discord.ui.TextDisplay(content="set your message"),
            accessory=discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="set",
                custom_id="set_custom_message",
            ),
        ),
        discord.ui.Section(
            discord.ui.TextDisplay(content="view your message"),
            accessory=discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="view",
                custom_id="view_custom_message",
            ),
        ),
    )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        cid = interaction.data.get("custom_id")
        uid = str(interaction.user.id)

        if cid == "remove_custom_message":
            await delete_custom_message(uid)
            await interaction.response.send_message("Your custom message has been removed!", ephemeral=True)
            return False

        if cid == "set_custom_message":
            class SetMessageModal(discord.ui.Modal, title="Set your custom ra1d message"):
                custom_msg = discord.ui.TextInput(label="Your message", style=discord.TextStyle.paragraph)

                async def on_submit(self2, modal_interaction: discord.Interaction):
                    await set_custom_message(uid, self2.custom_msg.value)
                    await modal_interaction.response.send_message("Custom ra1d message saved!", ephemeral=True)

            await interaction.response.send_modal(SetMessageModal())
            return False

        if cid == "view_custom_message":
            custom = await get_custom_message(uid)
            if custom:
                await interaction.response.send_message(f"Your current message:\n```\n{custom}\n```", ephemeral=True)
            else:
                await interaction.response.send_message("You do not have a custom message set.", ephemeral=True)
            return False

        return True
