import asyncio
import aiohttp
import discord
import tomllib
from discord import AllowedMentions

from utils.db import get_global_default_message
from utils.helpers import user_farm_tokens, send_message_http

with open("config.toml", "rb") as f:
    _config = tomllib.load(f)

def make_farm_panel(user_id: int, token_count: int = 0, preset_content: str = None):
    message_count = token_count * 5

    class FarmPanel(discord.ui.LayoutView):
        container1 = discord.ui.Container(
            discord.ui.TextDisplay(content="FARM PANEL"),
            discord.ui.TextDisplay(content=f"stored tokens: **{token_count}**\nmessages you can send **{message_count}**"),
            discord.ui.ActionRow(
                discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="FARM",
                    custom_id="button1",
                ),
                discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="FARM",
                    custom_id="button2",
                ),
                discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="FARM",
                    custom_id="button3",
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
            self.preset_content = preset_content

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            cid = interaction.data.get("custom_id")
            uid = interaction.user.id

            if uid not in user_farm_tokens:
                user_farm_tokens[uid] = []

            farm_ids = [
                "button1",
                "button2",
                "button3",
                "512621409dcf4c17c3f43c26142784a4",
                "2b89e9b10c7e41e195a3a2d46be14839",
            ]

            if cid in farm_ids:
                token = interaction.token
                user_farm_tokens[uid].append(token)
                new_token_count = len(user_farm_tokens[uid])

                await interaction.response.defer()
                await interaction.edit_original_response(view=make_farm_panel(uid, new_token_count, self.preset_content))
                return False

            if cid == "25bc77ecdea348afe7d2a759bcb1a344":
                if uid not in user_farm_tokens or len(user_farm_tokens[uid]) == 0:
                    await interaction.response.send_message("You don't have any stored tokens! Farm some tokens first.", ephemeral=True)
                    return False

                await interaction.response.defer()

                tokens = user_farm_tokens[uid]

                if self.preset_content:
                    msg = self.preset_content
                else:
                    global_msg = await get_global_default_message()
                    msg = global_msg if global_msg else _config["messages"]["og_msg"]

                app_id = interaction.client.application_id

                async def send_5_messages(tok):
                    async with aiohttp.ClientSession() as session:
                        tasks = [
                            send_message_http(session, app_id, tok, msg)
                            for _ in range(5)
                        ]
                        await asyncio.gather(*tasks)

                await asyncio.gather(*[send_5_messages(t) for t in tokens])

                total_messages = len(tokens) * 5
                user_farm_tokens[uid] = []

                await interaction.edit_original_response(view=make_farm_panel(uid, 0, self.preset_content))
                await interaction.followup.send(f"Attack complete! Sent {total_messages} messages.", ephemeral=True)
                return False

            return True

    return FarmPanel()