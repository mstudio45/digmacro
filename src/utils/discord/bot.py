import logging
import threading
import io
import os
import json
import asyncio
import traceback
import platform
import datetime

import nextcord
from nextcord.ext import commands
from nextcord import Embed, Interaction, Color

import numpy as np
import cv2

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
        self.discord_config = self._load_config()
        self.allowed_user_id = int(Config.DISCORD_USER_ID)

        # load ocr #
        self.ocr_util = None 
        if Config.DISCORD_ENABLE_STATISTICS:
            logging.info("[Discord] Loading OCR...")
            from utils.OCR.ocr import GameOCR
            from utils.OCR.stats import GameStatLib

            self.ocr_util = GameOCR()
            self.stat_lib = GameStatLib(self)

        # load bot #
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

        # channels cache #
        self.channels = {}

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
                return {}
        else:
            msgbox.alert(f"[Discord] Please setup the bot. Use '/setup' command inside Discord.")
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

                if current_os == "Windows":
                    embed.add_field(
                        name="Statistics",
                        value=f"`Enabled: {self.bool_to_emoji(self.ocr_util is not None)}`"
                    )

                await self.channels["logs"].send(embed=embed)
            except Exception as e: msgbox.alert(f"[Discord] Failed to send startup message: {str(e)}", log_level=logging.CRITICAL)

            # main loop #
            self.stat_lib.run_information_loop(Config.DISCORD_STATISTICS_INTERVAL)

            logging.info(f"[Discord] Logged in as '{self.bot.user.name}'.")
    
    # commands #
    def add_screenshot_to_embed(self, embed):
        file = None
        try:
            if Config.DISCORD_SHOW_SCREENSHOTS_IN_LOGS == True:
                image_array = take_screenshot(region=logical_screen_region)
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

    async def send_message(self, channel_key, **kwargs):
        channel = self.channels.get(channel_key, None)
        if not channel:
            logging.warning(f"Invalid channel key: {channel_key}")
            return
        
        try:
            await channel.send(**kwargs)
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

        async def ask_user(interaction: Interaction, question: str, timeout=60):
            await interaction.followup.send(question, ephemeral=True)

            def check(m): 
                return m.author == interaction.user and m.channel == interaction.channel

            try:
                msg = await self.bot.wait_for("message", timeout=timeout, check=check)
                return msg.content
            except TimeoutError:
                await interaction.followup.send("You took too long to reply. Please run the setup again.", ephemeral=True)
                return None

        @slash_command(name="setup", description="Show the current configuration or configure the bot.", force_global=True)
        async def screenshot_command(interaction: Interaction):
            if interaction.user.id != self.allowed_user_id:
                return await interaction.response.send_message("You are not allowed to run this command.")
        
            msg = await interaction.response.send_message(embed=Embed(
                title="Setup Started",
                description="Please follow the instructions.",
                color=Color.blue(),
                timestamp=datetime.datetime.now()
            ), ephemeral=True)

            # vars #
            if self.discord_config is None: self.discord_config = {}
            changes_made = False

            # create log channel #
            if self.discord_config.get("LOG_CHANNEL", None) is None:
                answer = await ask_user(interaction, "Please create a log channel in this server, then send the **channel ID** of the log channel.")
                if answer is None: return

                try:
                    channel_id = int(answer)
                except ValueError:
                    await interaction.followup.send(embed=Embed(
                        description="Invalid Channel ID provided.",
                        color=Color.red(),
                        timestamp=datetime.datetime.now()
                    ), ephemeral=True)
                    return
                
                log_channel = self.bot.get_channel(channel_id)
                if log_channel is None or log_channel.guild.id != interaction.guild.id:
                    await interaction.followup.send(embed=Embed(
                        description="Invalid channel or channel does not belong to this server.",
                        color=Color.red(),
                        timestamp=datetime.datetime.now()
                    ), ephemeral=True)
                    return
                
                changes_made = True
                self.discord_config["LOG_CHANNEL"] = channel_id
                self.channels["logs"] = log_channel

                await interaction.followup.send(embed=Embed(
                    title="Log Channel Set",
                    description=f"Log channel set to {log_channel.mention}!",
                    color=Color.green(),
                    timestamp=datetime.datetime.now()
                ), ephemeral=True)

            if changes_made == True:
                FileHandler.write(StaticVariables.discord_config_filepath, json.dumps(self.discord_config, indent=4))

            embed = Embed(
                title="Configuration Summary",
                description="Here is your current setup:",
                color=Color.blue(),
                timestamp=datetime.datetime.now()
            )

            embed.add_field(
                name="Log Channel",
                value=f"<#{self.discord_config["LOG_CHANNEL"]}>",
                inline=False
            )

            if changes_made == True:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await msg.edit(embed=embed, ephemeral=True)

        @slash_command(name="screenshot", description="Take a screenshot of your screen.", force_global=True)
        async def screenshot_command(interaction: Interaction):
            if interaction.user.id != self.allowed_user_id:
                return await interaction.response.send_message("You are not allowed to run this command.")
            
            try:
                image_array = take_screenshot(region=logical_screen_region)
                image_array = cv2.cvtColor(image_array, cv2.COLOR_BGRA2RGB)

                # convert image #
                image = Image.fromarray(image_array)
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                buffer.seek(0)

                file = nextcord.File(fp=buffer, filename="screenshot.png")
                await interaction.response.send_message(file=file, ephemeral=True)
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
            
            try:
                await interaction.response.send_message(self.ocr_util.get_current_money(), ephemeral=True)
            except Exception as e:
                msg = f"Failed to get current money:\n```\n{traceback.format_exc()}\n```"
                logging.debug(msg)
                await interaction.response.send_message(msg, ephemeral=True)

        @slash_command(name="stats", description="Get current stats (image).", force_global=True)
        async def stats_command(interaction: Interaction):
            if interaction.user.id != self.allowed_user_id:
                return await interaction.response.send_message("You are not allowed to run this command.")
            
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
        if Config.DISCORD_BOT_ENABLED == False:
            logging.info("[Discord] Bot is disabled.")
            return None
        
        logging.info("[Discord] Starting bot...")

        def _run_bot(): 
            self.running = True
            self.bot.run(Config.DISCORD_BOT_TOKEN)
        thread = threading.Thread(target=_run_bot, name="discord_bot", daemon=True)
        thread.start()

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

discord_bot = DiscordBot()