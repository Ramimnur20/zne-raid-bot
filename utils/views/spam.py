import asyncio
import io
import discord
from discord import AllowedMentions

from utils.config import DEFAULT_BUTTON_MESSAGE
from utils.db import get_custom_message, get_global_default_message


class SpamButton(discord.ui.LayoutView):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    container1 = discord.ui.Container(
        discord.ui.Section(
            discord.ui.TextDisplay(content="# press button below to ra1d\njoin [our server](https://discord.gg/sillyz) for more swag bots!!"),
            accessory=discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label="Send",
                custom_id="spam_send_button"
            )
        )
    )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data.get("custom_id") == "spam_send_button":
            await interaction.response.defer()

            global_msg = await get_global_default_message()
            custom_msg = await get_custom_message(str(self.user_id))
            msg = global_msg if global_msg else (custom_msg if custom_msg else DEFAULT_BUTTON_MESSAGE)

            allowed = AllowedMentions(everyone=True, users=True, roles=True)

            await asyncio.sleep(0.5)
            await asyncio.gather(*[
                interaction.followup.send(msg, ephemeral=False, allowed_mentions=allowed)
                for _ in range(5)
            ])

            return False
        return True


class CustomSpamButton(discord.ui.LayoutView):
    def __init__(self, user_id: int, message: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.custom_message = message

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data.get("custom_id") == "custom_spam_send_button":
            await interaction.response.defer()

            allowed = AllowedMentions(everyone=True, users=True, roles=True)

            for _ in range(5):
                await interaction.followup.send(self.custom_message, ephemeral=False, allowed_mentions=allowed)
                await asyncio.sleep(0.5)

            return False
        return True


# Dynamic factory for custom spam button
def make_custom_spam_panel(user_id: int, message: str):
    class CustomSpamPanel(discord.ui.LayoutView):
        def __init__(self):
            super().__init__(timeout=None)
            self.custom_message = message

        container1 = discord.ui.Container(
            discord.ui.Section(
                discord.ui.TextDisplay(content=f"# spam message: {message}\npress button to start spam"),
                accessory=discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label="Send",
                    custom_id="custom_spam_send_button"
                )
            )
        )

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.data.get("custom_id") == "custom_spam_send_button":
                await interaction.response.defer()

                allowed = AllowedMentions(everyone=True, users=True, roles=True)

                async def send_with_delay(index: int):
                    await asyncio.sleep(index * 0.5)
                    await interaction.followup.send(self.custom_message, ephemeral=False, allowed_mentions=allowed)

                await asyncio.gather(*[send_with_delay(i) for i in range(5)])

                return False
            return True

    return CustomSpamPanel()


# Dynamic factory for file spam panel
def make_filespam_panel(user_id: int, attachment: discord.Attachment):
    class FileSpamPanel(discord.ui.LayoutView):
        def __init__(self):
            super().__init__(timeout=None)
            self.attachment = attachment
            self.filename = attachment.filename
            self.url = attachment.url

        container1 = discord.ui.Container(
            discord.ui.Section(
                discord.ui.TextDisplay(content=f"# file spam: {attachment.filename}\npress button to start file spam"),
                accessory=discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label="Send",
                    custom_id="file_spam_send_button"
                )
            )
        )

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.data.get("custom_id") == "file_spam_send_button":
                await interaction.response.defer()

                # Upload file once and get the Discord attachment URL
                file_bytes = await self.attachment.read()
                file = discord.File(fp=io.BytesIO(file_bytes), filename=self.filename)
                
                # Send first message to get the Discord attachment URL
                first_msg = await interaction.followup.send(file=file, ephemeral=False)
                
                # Extract the attachment URL from the sent message
                attachment_url = None
                if first_msg.attachments:
                    attachment_url = first_msg.attachments[0].url
                
                if not attachment_url:
                    await interaction.followup.send("Failed to get attachment URL", ephemeral=True)
                    return False

                async def send_with_delay(index: int):
                    await asyncio.sleep(index * 0.5)
                    await interaction.followup.send(attachment_url, ephemeral=False)

                await asyncio.gather(*[send_with_delay(i) for i in range(5)])

                return False
            return True

    return FileSpamPanel()
