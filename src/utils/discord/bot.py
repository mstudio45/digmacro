import logging
import io
import os
import json
import asyncio
import traceback
import platform
import datetime
import time
import threading

import nextcord
from nextcord.ext import commands
from nextcord import Embed, Interaction, Color

import numpy as np
import cv2
import mss

from PIL import Image
from utils.images.screen import logical_screen_region
from utils.images.screenshots import take_screenshot

import utils.general.filehandler as FileHandler
import interface.msgbox as msgbox

from config import Config
from variables import Variables, StaticVariables

__all__ = ["discord_bot"]
current_os = platform.system()

class DiscordBot:
    def __init__(self):
        self.running = False

        # config #
        self.config_failed = False
        self.discord_config = {}
        self.allowed_user_id = 0

        # modules #
        self.ocr_util = None
        self.stat_lib = None 
        self.bot = None

        # channels cache #
        self.channels = {}

        # rarity colors (https://digtionary.org/wiki/Items) #
        self.rarity_colors = {
            "junk": nextcord.Color.from_rgb(208, 207, 206),        # #d0cfce
            "common": nextcord.Color.from_rgb(172, 212, 243),      # #acd4f3
            "unusual": nextcord.Color.from_rgb(117, 199, 111),     # #75c76f
            "scarce": nextcord.Color.from_rgb(132, 106, 218),      # #846ada
            "legendary": nextcord.Color.from_rgb(255, 162, 56),    # #ffa238
            "mythical": nextcord.Color.from_rgb(255, 110, 185),    # #ff6eb9
            "divine": nextcord.Color.from_rgb(254, 43, 43),        # #fe2b2b
            "prismatic": nextcord.Color.from_rgb(237, 128, 219),   # #ed80db
        }
        self.mention_rarities = Config.DISCORD_ITEMS_TO_MENTION
        self.allowed_rarities = Config.DISCORD_ITEMS_TO_NOTIFY

    # styling funcs #
    def bool_to_emoji(self, val): return "✅" if val == True else "❌"

    # config #
    def _load_config(self):
        logging.info("[Discord] Loading configuration...")

        if os.path.exists(StaticVariables.discord_config_filepath):
            try:
                config_str = FileHandler.read(StaticVariables.discord_config_filepath)
                if config_str and isinstance(config_str, str):
                    return json.loads(config_str)
                else:
                    raise Exception("Empty or invalid config. Run /setup in Discord.")
            except Exception as e:
                msgbox.alert(f"[Discord] Failed to load configuration: {str(e)}")
                self.config_failed = True
                return {}
        else:
            msgbox.alert(f"[Discord] Please setup the bot. Use '/setup' command inside Discord.")
            self.config_failed = True
            return {}
        
    # channels #
    def _setup_channel(self, config_key, key):
        channel_id = self.discord_config.get(config_key, None)
        if channel_id is None:
            msgbox.alert(f"[Discord] Failed to find '{key}' channel inside configuration.", log_level=logging.CRITICAL)
            return

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            msgbox.alert(f"[Discord] Failed to find '{key}' channel.", log_level=logging.CRITICAL)
            return
        
        logging.info(f"[Discord] {key} channel loaded.")
        self.channels[key] = channel

    # events #
    def _register_events(self):
        @self.bot.event
        async def on_ready():
            if self.config_failed == False:
                # setup channels #
                logging.info("[Discord] Fetching channels...")
                self._setup_channel("LOG_CHANNEL", "logs")

                # startup log #
                try:
                    embed = Embed(
                        title="Information",
                        description="Started successfully.",
                        color=Color.green(),
                        timestamp=datetime.datetime.now()
                    )

                    embed.add_field(
                        name="Information",
                        value=f"""
`OCR Module`:   {self.bool_to_emoji(self.ocr_util is not None)}
`Stats Module`: {self.bool_to_emoji(Config.DISCORD_ENABLE_STATISTICS and self.stat_lib is not None)}
"""
                    )

                    await self.channels["logs"].send(embed=embed)
                except Exception as e: msgbox.alert(f"[Discord] Failed to send startup message: {str(e)}", log_level=logging.CRITICAL)

            # main loop #
            if Config.DISCORD_ENABLE_STATISTICS and self.stat_lib is not None:
                self.stat_lib.run_information_loop(Config.DISCORD_STATISTICS_INTERVAL)
            else:
                logging.info("[Discord] Statistics are disabled.")
            
            logging.info(f"[Discord] Logged in as '{self.bot.user.name}'.")
    
    # commands #
    def add_screenshot_to_embed(self, embed):
        file = None
        try:
            if Config.DISCORD_SHOW_SCREENSHOTS_IN_LOGS == True:
                sct = mss.mss()
                image_array = take_screenshot(logical_screen_region, sct)
                del sct

                image_array = cv2.cvtColor(image_array, cv2.COLOR_BGRA2RGB)

                # convert image #
                image = Image.fromarray(image_array)
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                buffer.seek(0)

                file = nextcord.File(fp=buffer, filename="screenshot.png")
                embed.set_image(url="attachment://screenshot.png")
        except Exception as e:
            logging.debug(f"Failed to take screenshot: {traceback.format_exc()}")
        
        return file

    async def send_message(self, channel_key, ping_user=False, **kwargs):
        channel = self.channels.get(channel_key, None)
        if not channel:
            logging.warning(f"Invalid channel key: {channel_key}")
            return
        
        try:
            format_content = str(kwargs.get("content", ""))
            if ping_user == True:
                format_content = f"<@{self.allowed_user_id}> {format_content}"
            
            await channel.send(content=format_content, **kwargs)
        except Exception as e:
            logging.warning(f"Failed to send message to '{channel_key}': {str(e)}")

    def _register_commands(self):
        logging.info("[Discord] Loading commands...")

        def slash_command(*args, **kwargs):
            def decorator(func):
                logging.info(f"    - /{kwargs.get('name')}")
                return self.bot.slash_command(*args, **kwargs)(func)
            return decorator

        @slash_command(name="help", description="List all avalaible commands.", force_global=True)
        async def help_command(interaction: Interaction):
            embed = Embed(
                title="Commands List",
                description="Here are all the available slash commands:",
                color=Color.blue(),
                timestamp=datetime.datetime.now()
            )

            for cmd in self.bot._connection.application_commands:
                embed.add_field(
                    name=f"/{cmd.name}",
                    value=cmd.description if cmd.description is not None else "No description",
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        @slash_command(name="setup", description="Configure the bot.", force_global=True)
        async def screenshot_command(
            interaction: Interaction,
            log_channel: nextcord.TextChannel = nextcord.SlashOption(name="log_channel", description="Select the log channel to use", required=True)
        ):
            if interaction.user.id != self.allowed_user_id:
                return await interaction.response.send_message("You are not allowed to run this command.")
        
            msg = await interaction.response.send_message(embed=Embed(
                title="Setup Started",
                description="Saving your changes, please wait...",
                color=Color.blue(),
                timestamp=datetime.datetime.now()
            ), ephemeral=True)

            # vars #
            if self.discord_config is None: self.discord_config = {}

            # set log_channel #
            if log_channel.guild.id != interaction.guild.id:
                return await msg.edit(embed=Embed(
                    title="Setup Failed",
                    description="The log channel is not part of this server.",
                    color=Color.red(),
                    timestamp=datetime.datetime.now()
                ))

            self.discord_config["LOG_CHANNEL"] = log_channel.id
            self.channels["logs"] = log_channel

            await interaction.followup.send(embed=Embed(
                title="Log Channel Set",
                description=f"Log channel set to {log_channel.mention}!",
                color=Color.green(),
                timestamp=datetime.datetime.now()
            ), ephemeral=True)

            # save changes
            success, err = FileHandler.write(StaticVariables.discord_config_filepath, json.dumps(self.discord_config, indent=4))
            if success:
                await msg.edit(embed=Embed(
                    title="Setup Finished",
                    description="Your changes have been saved successfully!",
                    color=Color.green(),
                    timestamp=datetime.datetime.now()
                ))
            else:
                await msg.edit(embed=Embed(
                    title="Setup Failed",
                    description=f"Failed to save your changes.\n```\n{str(err)}\n```",
                    color=Color.red(),
                    timestamp=datetime.datetime.now()
                ))

        @slash_command(name="current_setup", description="Get current configuration.", force_global=True)
        async def current_setup_command(interaction: Interaction):
            if interaction.user.id != self.allowed_user_id:
                return await interaction.response.send_message("You are not allowed to run this command.")

            embed = Embed(
                title="Configuration",
                description="Here is your current configuration:",
                color=Color.blue(),
                timestamp=datetime.datetime.now()
            )

            if hasattr(self.discord_config, "LOG_CHANNEL") and self.discord_config["LOG_CHANNEL"] is not None:
                embed.add_field(
                    name="Log Channel",
                    value=f"<#{self.discord_config["LOG_CHANNEL"]}>",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Log Channel",
                    value=f"None - Use `/setup` to configure this.",
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        @slash_command(name="screenshot", description="Take a screenshot of your screen.", force_global=True)
        async def screenshot_command(interaction: Interaction):
            if interaction.user.id != self.allowed_user_id:
                return await interaction.response.send_message("You are not allowed to run this command.")
            
            try:
                embed = Embed(
                    title="Screenshot",
                    color=nextcord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )

                file = self.add_screenshot_to_embed(embed)
                await interaction.response.send_message(embed=embed, file=file, ephemeral=True)
            except Exception as e:
                msg = f"Failed to take screenshot:\n```\n{traceback.format_exc()}\n```"
                logging.debug(msg)
                await interaction.response.send_message(msg, ephemeral=True)

        @slash_command(name="status", description="Get current status of the macro.", force_global=True)
        async def status_command(interaction: Interaction):
            region = Variables.minigame_region
            last_detection = Variables.last_minigame_detection or "None"
            is_idle = Variables.is_idle()

            content = f"""\
Flags:
  Is Running:           {self.bool_to_emoji(Variables.is_running)}
  Is Paused:            {self.bool_to_emoji(Variables.is_paused)}
  Is Roblox Focused:    {self.bool_to_emoji(Variables.is_roblox_focused)}

Macro Settings:
  Session ID:           {Variables.session_id}
  Version:              {Variables.current_version}
  Branch:               {Variables.current_branch}

Minigame Info:
  Dig Count:            {Variables.dig_count:,}
  Click Count:          {Variables.click_count:,}
  Failed Attempts:      {Variables.failed_minigame_attempts:,}
  Last Detection:       {last_detection}

Auto Rejoin Info:
  Rejoin Count:         {Variables.rejoin_count:,}
  Failed Rejoin:        {Variables.failed_rejoin_attempts:,}

Macro States:
  Is Minigame Active:   {self.bool_to_emoji(Variables.is_minigame_active)}
  Is Walking:           {self.bool_to_emoji(Variables.is_walking)}
  Is Selling:           {self.bool_to_emoji(Variables.is_selling)}
  Is Rejoining:         {self.bool_to_emoji(Variables.is_rejoining)}
  Is Idle:              {self.bool_to_emoji(is_idle)}
"""

            embed = Embed(
                title="Macro Status",
                description=f"```ansi\n{content}```",
                color=Color.blue(),
                timestamp=datetime.datetime.now()
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        @slash_command(name="current_money", description="Get current amount of money.", force_global=True)
        async def current_money_command(interaction: Interaction):
            if interaction.user.id != self.allowed_user_id:
                return await interaction.response.send_message("You are not allowed to run this command.")
            
            if self.ocr_util is None:
                await interaction.response.send_message("OCR Module is not initialized.", ephemeral=True)
                return

            try:
                with mss.mss() as sct:
                    await interaction.response.send_message(self.ocr_util.get_current_money(sct), ephemeral=True)
            except Exception as e:
                msg = f"Failed to get current money:\n```\n{traceback.format_exc()}\n```"
                logging.debug(msg)
                await interaction.response.send_message(msg, ephemeral=True)

        @slash_command(name="stats", description="Get current stats (image).", force_global=True)
        async def stats_command(interaction: Interaction):
            if interaction.user.id != self.allowed_user_id:
                return await interaction.response.send_message("You are not allowed to run this command.")
            
            if self.stat_lib is None:
                await interaction.response.send_message("Stats Module is not initialized.", ephemeral=True)
                return

            try:
                image_array = self.stat_lib.create_image()

                # convert image #
                image = Image.fromarray(image_array)
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                buffer.seek(0)

                file = nextcord.File(fp=buffer, filename="stats.png")

                await interaction.response.send_message(file=file, ephemeral=True)
            except Exception as e:
                msg = f"Failed to create stats image:\n```\n{traceback.format_exc()}\n```"
                logging.debug(msg)
                await interaction.response.send_message(msg, ephemeral=True)

    def run(self):
        if Config.ENABLE_DISCORD_BOT == False: return
        logging.info("[Discord] Starting bot...")

        # load config #
        self.discord_config = self._load_config()
        self.allowed_user_id = int(Config.DISCORD_USER_ID)

        if Config.DISCORD_ENABLE_STATISTICS:
            if self.ocr_util is None:
                msgbox.alert("[Discord] OCR Module is not initalized.", log_level=logging.CRITICAL)
            
            if self.stat_lib is None:
                msgbox.alert("[Discord] Stats Module is not initliazed.", log_level=logging.CRITICAL)

        # register bot #
        intents = nextcord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.messages = True
        intents.guild_messages = True
        intents.dm_messages = True
        intents.message_content = True

        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self._register_events()
        self._register_commands()

        # start bot #
        if self.bot.loop:
            self.loop = self.bot.loop
        else:
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)

        self.loop.run_in_executor(None, self._run_bot)
        logging.info("[Discord] Bot is running in a background thread.")

    def _run_bot(self):
        try:
            self.loop.run_until_complete(self.bot.start(Config.DISCORD_BOT_TOKEN, reconnect=True))
        except Exception as e:
            logging.error(f"[Discord] An error occurred in the bot thread: {e}")
        
        finally:
            if self.loop.is_running():
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
                self.loop.close()
            
            logging.info("[Discord] Bot has been shut down.")

    def stop(self):
        if self.bot and self.bot_thread and self.bot_thread.is_alive():
            logging.info("[Discord] Shutting down bot...")
            future = asyncio.run_coroutine_threadsafe(self.bot.close(), self.loop)
            
            try:
                future.result(timeout=5)
            except asyncio.TimeoutError:
                logging.error("[Discord] Timed out waiting for bot to close.")
            except Exception as e:
                logging.error(f"[Discord] Error closing the bot: {e}")

            self.bot_thread.join()
            logging.info("[Discord] Bot thread has been joined.")

    # global functions #
    def send_minigame_info(self):
        embed = Embed(
            title="Minigame Information",
            color=nextcord.Color.dark_green(),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(
            name=":tools: Total Dig Count",
            value=f"{Variables.dig_count:,}",
            inline=False
        )

        embed.add_field(
            name=":x: Total Failed Attempts",
            value=f"{Variables.failed_minigame_attempts:,}",
            inline=False
        )

        embed.add_field(
            name=":mouse_three_button: Total Click Count",
            value=f"{Variables.click_count:,}",
            inline=False
        )

        # send message #
        asyncio.run_coroutine_threadsafe(
            self.send_message("logs", embed=embed),
            self.bot.loop
        )
    
    def send_starting_reconnect(self, error_code):
        embed = Embed(
            title="Auto Rejoin",
            description="Attempting to rejoing DIG...\n\n" + str(error_code or "N/A"),
            color=nextcord.Color.orange(),
            timestamp=datetime.datetime.now()
        )

        file = self.add_screenshot_to_embed(embed)

        # send message #
        asyncio.run_coroutine_threadsafe(
            self.send_message("logs", embed=embed, file=file),
            self.bot.loop
        )

    def send_reconnect_success(self):
        embed = Embed(
            title="Auto Rejoin",
            description="Successfully rejoined!",
            color=nextcord.Color.green(),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(
            name=":repeat: Total Rejoins",
            value=f"{Variables.rejoin_count:,}",
            inline=True
        )

        file = self.add_screenshot_to_embed(embed)

        # send message #
        asyncio.run_coroutine_threadsafe(
            self.send_message("logs", embed=embed, file=file),
            self.bot.loop
        )

    def send_failed_to_reconnect(self, custom_msg="Failed to rejoing DIG, retrying.."):
        embed = Embed(
            title="Auto Rejoin",
            description=custom_msg,
            color=nextcord.Color.orange(),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(
            name=":repeat: Total Rejoins",
            value=f"{Variables.rejoin_count:,}",
            inline=True
        )
        
        embed.add_field(
            name=":x: Total Failed Rejoin Attempts",
            value=f"{Variables.failed_rejoin_attempts:,}",
            inline=True
        )

        # send message #
        asyncio.run_coroutine_threadsafe(
            self.send_message("logs", embed=embed),
            self.bot.loop
        )

    def send_auto_sell(self):
        embed = Embed(
            title="Auto Sell",
            description="Successfully sold the inventory.",
            color=nextcord.Color.green(),
            timestamp=datetime.datetime.now()
        )

        file = self.add_screenshot_to_embed(embed)

        # send message #
        asyncio.run_coroutine_threadsafe(
            self.send_message("logs", embed=embed, file=file),
            self.bot.loop
        )

    def send_statistic_embed(self):
        logging.info("[Discord] Sending statistic embed...")
        if self.stat_lib is None:
            logging.info("[Discord] Stats Module is not initialized.")
            return

        embed = Embed(
            title="Statistics",
            color=nextcord.Color.blurple(),
            timestamp=datetime.datetime.now()
        )

        image_array = self.stat_lib.create_image()

        # convert image #
        image = Image.fromarray(image_array)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        file = nextcord.File(fp=buffer, filename="stats.png")
        embed.set_image(url="attachment://stats.png")

        # send message #
        asyncio.run_coroutine_threadsafe(
            self.send_message("logs", embed=embed, file=file),
            self.bot.loop
        )

    def send_item_notification(self, item, rarity, is_new=False):
        embed = Embed(
            title="New Item!" if is_new == True else "Item Recieved",
            description="You have just recieved a new item!" if is_new == True else None,
            color=self.rarity_colors.get(rarity.lower(), nextcord.Color.blurple()),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(
            name=":grey_question: Item Name",
            value=str(item),
            inline=True
        )

        embed.add_field(
            name=":sparkles: Item Rarity",
            value=str(rarity),
            inline=True
        )

        # send message #
        asyncio.run_coroutine_threadsafe(
            self.send_message("logs", ping_user=is_new == True or rarity in self.mention_rarities, embed=embed),
            self.bot.loop
        )

    def check_new_item(self):
        with mss.mss() as sct:
            valid, cleaned_text, item, rarity, is_new = discord_bot.ocr_util.get_current_item(sct)
            logging.info(f"Item Detection:\n    valid={valid}\n    cleaned_text={cleaned_text}\n    item={item}\n    rarity={rarity}\n    is_new={is_new}")
            if valid == True and rarity in discord_bot.allowed_rarities:
                discord_bot.send_item_notification(item, rarity, is_new)

discord_bot = DiscordBot()