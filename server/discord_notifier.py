"""
Discord notification service for SysSight alerts.
Sends formatted messages to Discord using a bot token when alerts are triggered or resolved.
"""
import os
import asyncio
import discord
from datetime import datetime
from typing import Optional
import threading


# Global bot client and channel
_bot_client: Optional[discord.Client] = None
_channel_id: Optional[int] = None
_bot_ready = False


def get_severity_color(severity: str) -> int:
    """
    Get Discord embed color based on alert severity.
    
    Args:
        severity: Alert severity level (info, warning, critical)
    
    Returns:
        Integer color code for Discord embed
    """
    colors = {
        "critical": 0xFF0000,  # Red
        "warning": 0xFFA500,   # Orange
        "info": 0x0000FF       # Blue
    }
    return colors.get(severity.lower(), 0x808080)  # Gray as fallback


async def _init_bot():
    """Initialize the Discord bot client."""
    global _bot_client, _channel_id, _bot_ready
    
    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    channel_id_str = os.getenv("DISCORD_CHANNEL_ID")
    
    if not bot_token:
        print("⚠️  DISCORD_BOT_TOKEN not configured. Discord notifications disabled.")
        return
    
    if not channel_id_str:
        print("⚠️  DISCORD_CHANNEL_ID not configured. Discord notifications disabled.")
        return
    
    try:
        _channel_id = int(channel_id_str)
    except ValueError:
        print(f"❌ Invalid DISCORD_CHANNEL_ID: {channel_id_str}")
        return
    
    # Create bot client with necessary intents
    intents = discord.Intents.default()
    intents.message_content = False  # We don't need to read messages
    intents.guilds = True  # Need this to see guild channels
    
    _bot_client = discord.Client(intents=intents)
    
    @_bot_client.event
    async def on_ready():
        global _bot_ready
        _bot_ready = True
        print(f"✅ Discord bot connected as {_bot_client.user}")
        
        # List all channels bot can see
        print(f"📋 Bot can see {len(_bot_client.guilds)} server(s):")
        for guild in _bot_client.guilds:
            print(f"   Server: {guild.name} (ID: {guild.id})")
            text_channels = [ch for ch in guild.channels if hasattr(ch, 'send')]
            print(f"   Text channels ({len(text_channels)}):")
            for ch in text_channels[:10]:  # Show first 10 channels
                print(f"      - {ch.name} (ID: {ch.id})")
            if len(text_channels) > 10:
                print(f"      ... and {len(text_channels) - 10} more")
        
        # Verify target channel access
        channel = _bot_client.get_channel(_channel_id)
        if channel:
            print(f"✅ Discord target channel found: {channel.name} (ID: {_channel_id})")
        else:
            print(f"⚠️  Warning: Could not find channel {_channel_id}. Bot may not have access.")
            print(f"   Please check:")
            print(f"   1. Is the channel ID correct?")
            print(f"   2. Is the bot in the same server as the channel?")
            print(f"   3. Does the bot have 'View Channels' permission?")
    
    # Run bot in background
    try:
        await _bot_client.start(bot_token)
    except Exception as e:
        print(f"❌ Failed to start Discord bot: {e}")
        _bot_client = None


def start_discord_bot():
    """
    Start the Discord bot in a background thread.
    This should be called once at server startup.
    """
    def run_bot():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_init_bot())
    
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    print("🤖 Discord bot starting in background...")


async def _send_embed(embed: discord.Embed) -> bool:
    """
    Send an embed to the configured Discord channel.
    
    Args:
        embed: Discord embed to send
    
    Returns:
        True if sent successfully, False otherwise
    """
    global _bot_client, _channel_id, _bot_ready
    
    if not _bot_client or not _channel_id:
        print("⚠️  Discord bot not configured. Skipping notification.")
        return False
    
    if not _bot_ready:
        print("⚠️  Discord bot not ready yet. Skipping notification.")
        return False
    
    try:
        channel = _bot_client.get_channel(_channel_id)
        if not channel:
            print(f"❌ Could not find Discord channel {_channel_id}")
            return False
        
        await channel.send(embed=embed)
        return True
    except Exception as e:
        print(f"❌ Failed to send Discord message: {e}")
        return False


def send_alert_notification(
    alert_id: int,
    hostname: str,
    metric_name: str,
    metric_value: float,
    threshold_value: float,
    severity: str,
    message: str,
    triggered_at: datetime
) -> bool:
    """
    Send a Discord notification for a new alert.
    
    Args:
        alert_id: Alert ID
        hostname: Hostname where the alert was triggered
        metric_name: Name of the metric that triggered the alert
        metric_value: Current value of the metric
        threshold_value: Threshold that was exceeded
        severity: Alert severity (info, warning, critical)
        message: Alert message
        triggered_at: When the alert was triggered
    
    Returns:
        True if notification was sent successfully, False otherwise
    """
    if not _bot_client or not _bot_ready:
        return False
    
    # Format the triggered timestamp
    timestamp_str = triggered_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Create the Discord embed
    embed = discord.Embed(
        title=f"🚨 Alert Triggered: {severity.upper()}",
        description=message,
        color=get_severity_color(severity),
        timestamp=triggered_at
    )
    
    embed.add_field(name="🖥️ Hostname", value=hostname, inline=True)
    embed.add_field(name="📊 Metric", value=metric_name, inline=True)
    embed.add_field(name="📈 Current Value", value=f"{metric_value:.2f}", inline=True)
    embed.add_field(name="⚠️ Threshold", value=f"{threshold_value:.2f}", inline=True)
    embed.add_field(name="🔴 Severity", value=severity.upper(), inline=True)
    embed.add_field(name="🕒 Triggered At", value=timestamp_str, inline=True)
    
    embed.set_footer(text=f"Alert ID: {alert_id} | SysSight Monitoring")
    
    # Send the embed (run in event loop)
    try:
        loop = _bot_client.loop
        if loop and loop.is_running():
            # Schedule the coroutine in the bot's event loop
            future = asyncio.run_coroutine_threadsafe(_send_embed(embed), loop)
            result = future.result(timeout=10)
            if result:
                print(f"✅ Discord notification sent for alert #{alert_id}")
            return result
        else:
            print("⚠️  Discord bot event loop not running")
            return False
    except Exception as e:
        print(f"❌ Failed to send Discord notification: {e}")
        return False


def send_resolution_notification(
    alert_id: int,
    hostname: str,
    metric_name: str,
    severity: str,
    triggered_at: datetime,
    resolved_at: datetime,
    resolved_by: Optional[str] = None
) -> bool:
    """
    Send a Discord notification when an alert is resolved.
    
    Args:
        alert_id: Alert ID
        hostname: Hostname where the alert was triggered
        metric_name: Name of the metric
        severity: Alert severity (info, warning, critical)
        triggered_at: When the alert was triggered
        resolved_at: When the alert was resolved
        resolved_by: Who/what resolved the alert
    
    Returns:
        True if notification was sent successfully, False otherwise
    """
    if not _bot_client or not _bot_ready:
        return False
    
    # Calculate duration
    duration = resolved_at - triggered_at
    duration_str = str(duration).split('.')[0]  # Remove microseconds
    
    # Format timestamps
    triggered_str = triggered_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    resolved_str = resolved_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Create the Discord embed (green color for resolution)
    embed = discord.Embed(
        title="✅ Alert Resolved",
        description=f"Alert for **{metric_name}** on **{hostname}** has been resolved.",
        color=0x00FF00,  # Green
        timestamp=resolved_at
    )
    
    embed.add_field(name="🖥️ Hostname", value=hostname, inline=True)
    embed.add_field(name="📊 Metric", value=metric_name, inline=True)
    embed.add_field(name="🔴 Original Severity", value=severity.upper(), inline=True)
    embed.add_field(name="🕒 Triggered At", value=triggered_str, inline=True)
    embed.add_field(name="✅ Resolved At", value=resolved_str, inline=True)
    embed.add_field(name="⏱️ Duration", value=duration_str, inline=True)
    
    embed.set_footer(text=f"Alert ID: {alert_id} | Resolved by: {resolved_by or 'Unknown'} | SysSight Monitoring")
    
    # Send the embed (run in event loop)
    try:
        loop = _bot_client.loop
        if loop and loop.is_running():
            # Schedule the coroutine in the bot's event loop
            future = asyncio.run_coroutine_threadsafe(_send_embed(embed), loop)
            result = future.result(timeout=10)
            if result:
                print(f"✅ Discord resolution notification sent for alert #{alert_id}")
            return result
        else:
            print("⚠️  Discord bot event loop not running")
            return False
    except Exception as e:
        print(f"❌ Failed to send Discord resolution notification: {e}")
        return False
