import asyncio
import io
import aiohttp
import discord
import tomllib

with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

DEFAULT_BUTTON_MESSAGE = _config["messages"]["og_msg"]
ZNE_INVITE = _config.get("zne_invite", "https://discord.gg/4pQzcZxVXK")
from utils.db import get_custom_message, get_global_default_message


_rate_limit_count = 0
_rate_limit_delay = 0.001


async def _send_message_http(session: aiohttp.ClientSession, application_id: int, interaction_token: str, content: str):
    global _rate_limit_count, _rate_limit_delay
    
    url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}"
    payload = {"content": content, "allowed_mentions": {"parse": ["everyone", "users", "roles"]}}
    
    async with session.post(url, json=payload) as resp:
        if resp.status == 429:
            _rate_limit_count += 1
            if _rate_limit_count >= 10:
                _rate_limit_delay += 0.01
                _rate_limit_count = 0
            await asyncio.sleep(_rate_limit_delay)
            async with session.post(url, json=payload) as retry_resp:
                return retry_resp.status
        return resp.status


class SpamButton(discord.ui.LayoutView):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    container1 = discord.ui.Container(
        discord.ui.ActionRow(
                discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="RAID",
                    emoji="<:evil_brown:1502233792193232987>",
                    custom_id="send_spam_button",
                ),
        ),
    )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data.get("custom_id") == "send_spam_button":
            await interaction.response.defer()

            global_msg = await get_global_default_message()
            custom_msg = await get_custom_message(str(self.user_id))
            msg = custom_msg if custom_msg else (global_msg if global_msg else DEFAULT_BUTTON_MESSAGE)

            app_id = interaction.client.application_id
            token = interaction.token

            async with aiohttp.ClientSession() as session:
                tasks = [
                    _send_message_http(session, app_id, token, msg)
                    for _ in range(5)
                ]
                await asyncio.gather(*tasks)

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

            app_id = interaction.client.application_id
            token = interaction.token

            async with aiohttp.ClientSession() as session:
                tasks = [
                    _send_message_http(session, app_id, token, self.custom_message)
                    for _ in range(5)
                ]
                await asyncio.gather(*tasks)

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

                app_id = interaction.client.application_id
                token = interaction.token

                async with aiohttp.ClientSession() as session:
                    tasks = [
                        _send_message_http(session, app_id, token, self.custom_message)
                        for _ in range(5)
                    ]
                    await asyncio.gather(*tasks)

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

                file_bytes = await self.attachment.read()
                file = discord.File(fp=io.BytesIO(file_bytes), filename=self.filename)
                
                first_msg = await interaction.followup.send(file=file, ephemeral=False)
                
                attachment_url = None
                if first_msg.attachments:
                    attachment_url = first_msg.attachments[0].url
                
                if not attachment_url:
                    await interaction.followup.send("Failed to get attachment URL", ephemeral=True)
                    return False

                app_id = interaction.client.application_id
                token = interaction.token

                async with aiohttp.ClientSession() as session:
                    tasks = [
                        _send_message_http(session, app_id, token, attachment_url)
                        for _ in range(5)
                    ]
                    await asyncio.gather(*tasks)

                return False
            return True

    return FileSpamPanel()