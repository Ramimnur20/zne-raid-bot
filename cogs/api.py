import discord
from discord import app_commands
from discord.ext import commands
import requests
import re


class ApiCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    api_group = app_commands.Group(name="api", description="API related commands")

    @api_group.command(name="femboythighs", description="Get a femboythighs image")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def femboythighs(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            session = requests.Session()
            # Use the correct API endpoint
            response = session.get("https://fembthighs.rynzen.uk/thighs", timeout=10, allow_redirects=True)
            
            # Check if we got redirected to an image
            final_url = response.url
            content_type = response.headers.get("content-type", "").lower()
            
            # If the final URL is an image or the content-type is image, it's a direct image
            if content_type.startswith("image/"):
                embed = discord.Embed(
                    title="🍑 Femboy Thighs",
                    color=discord.Color.pink()
                )
                embed.set_image(url=final_url)
                await interaction.followup.send(embed=embed)
                return
            
            # Check if URL contains image extension
            if any(ext in final_url.lower() for ext in [".jpg", ".png", ".gif", ".webp", ".jpeg"]):
                embed = discord.Embed(
                    title="🍑 Femboy Thighs",
                    color=discord.Color.pink()
                )
                embed.set_image(url=final_url)
                await interaction.followup.send(embed=embed)
                return
            
            # Try to parse as JSON
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Check various possible JSON fields for image URL (recursive search)
                    def find_image_url(obj):
                        if isinstance(obj, str) and any(ext in obj.lower() for ext in ["jpg", "png", "gif", "webp", "jpeg"]):
                            return obj
                        if isinstance(obj, dict):
                            for key in ["url", "image", "link", "file", "src", "img", "path", "media"]:
                                if key in obj:
                                    result = find_image_url(obj[key])
                                    if result:
                                        return result
                        if isinstance(obj, list):
                            for item in obj:
                                result = find_image_url(item)
                                if result:
                                    return result
                        return None
                    
                    image_url = find_image_url(data)
                    if image_url:
                        embed = discord.Embed(
                            title="🍑 Femboy Thighs",
                            color=discord.Color.pink()
                        )
                        embed.set_image(url=image_url)
                        await interaction.followup.send(embed=embed)
                        return
                except:
                    pass
                
                # Try to find image in HTML img tags
                img_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', response.text, re.IGNORECASE)
                if img_matches:
                    embed = discord.Embed(
                        title="🍑 Femboy Thighs",
                        color=discord.Color.pink()
                    )
                    embed.set_image(url=img_matches[0])
                    await interaction.followup.send(embed=embed)
                    return
                
                # Try to find ANY URLs in the response text that look like images
                all_urls = re.findall(r'https://[^\s<>"]+', response.text)
                for url in all_urls:
                    if any(ext in url.lower() for ext in ["jpg", "png", "gif", "webp", "jpeg"]):
                        embed = discord.Embed(
                            title="🍑 Femboy Thighs",
                            color=discord.Color.pink()
                        )
                        embed.set_image(url=url)
                        await interaction.followup.send(embed=embed)
                        return
                
                # Debug: show what we got
                await interaction.followup.send(f"❌ Could not find image URL. Response: {response.text[:500]}")
            else:
                await interaction.followup.send(f"❌ Failed to fetch image. Status: {response.status_code}")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}")

    @api_group.command(name="ip-lookup", description="Look up IP address information")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ip_lookup(self, interaction: discord.Interaction, ip: str):
        await interaction.response.defer()

        try:
            # Use ip-api.com JSON API (free, no API key required for basic lookup)
            url = f"http://ip-api.com/json/{ip}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "fail":
                    await interaction.followup.send(f"❌ Invalid IP address or lookup failed: {data.get('message', 'Unknown error')}")
                    return
                
                # Build embed with IP info
                embed = discord.Embed(
                    title=f"🌐 IP Lookup: {ip}",
                    color=discord.Color.blue()
                )
                
                # Add fields with IP information
                if data.get("country"):
                    embed.add_field(name="Country", value=f"{data.get('country', 'N/A')} {data.get('countryCode', '')}", inline=True)
                if data.get("regionName"):
                    embed.add_field(name="Region", value=data.get("regionName", "N/A"), inline=True)
                if data.get("city"):
                    embed.add_field(name="City", value=data.get("city", "N/A"), inline=True)
                if data.get("zip"):
                    embed.add_field(name="ZIP", value=data.get("zip", "N/A"), inline=True)
                if data.get("isp"):
                    embed.add_field(name="ISP", value=data.get("isp", "N/A"), inline=False)
                if data.get("org"):
                    embed.add_field(name="Organization", value=data.get("org", "N/A"), inline=False)
                if data.get("as"):
                    embed.add_field(name="AS", value=data.get("as", "N/A"), inline=False)
                
                # Add lat/lon if available
                if data.get("lat") and data.get("lon"):
                    embed.add_field(name="Coordinates", value=f"{data.get('lat')}, {data.get('lon')}", inline=True)
                
                embed.set_footer(text="Powered by ip-api.com")
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"❌ Failed to lookup IP. Status: {response.status_code}")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ApiCog(bot))
