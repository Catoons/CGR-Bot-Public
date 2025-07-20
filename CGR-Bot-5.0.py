# Written by Catoons with assistance from ChatGPT

import discord
from discord.ext import commands, tasks
import json
from datetime import datetime, timedelta
import asyncio

# Intents and bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# File to store reminders
REMINDER_FILE = "reminders.json"

# Load reminders from file
def load_reminders():
    try:
        with open(REMINDER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save reminders to file
def save_reminders(reminders):
    with open(REMINDER_FILE, "w") as file:
        json.dump(reminders, file, indent=4)

# Check if a reminder is due
def is_reminder_due(reminder):
    due_date = datetime.fromisoformat(reminder["next_reminder"])
    return datetime.now() >= due_date

# Update the next reminder date
def update_next_reminder(reminder):
    reminder["next_reminder"] = (datetime.now() + timedelta(days=180)).isoformat()

# Task to check and send reminders
@tasks.loop(minutes=1)
async def reminder_task():
    reminders = load_reminders()
    for user_id, reminder in reminders.items():
        if is_reminder_due(reminder):
            channel_id = reminder["channel_id"]
            channel = bot.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(f"Reminder for <@{user_id}>: You're eligible to submit a game for us to review! Within 30 days, respond to this message with the title of the game and the platform(s) on which it is available. A member of our team will get to it shortly!")
                except discord.Forbidden:
                    print(f"Could not send reminder to channel {channel_id}.")
            update_next_reminder(reminder)
    save_reminders(reminders)

@bot.event
async def on_ready():
    print(f"Bot is ready as {bot.user}")
    reminder_task.start()

# Command to set a reminder
@bot.command()
async def set_reminder(ctx, user: discord.User):
    """Set a reminder for a mentioned user in the current channel."""
    user_id = str(user.id)  # The mentioned user's ID
    channel_id = ctx.channel.id
    reminders = load_reminders()

    reminders[user_id] = {
        "next_reminder": (datetime.now() + timedelta(days=180)).isoformat(),
        "channel_id": channel_id,
    }
    save_reminders(reminders)

    await ctx.send(f"Reminder set for {user.mention}! I'll remind them in 6 months in this channel.")


# Command to view your reminder
@bot.command()
async def view_reminders(ctx):
    """View all reminders set for everyone."""
    reminders = load_reminders()

    if reminders:
        response = "Here are all the reminders:\n"
        for user_id, reminder in reminders.items():
            channel_id = reminder.get("channel_id", "Unknown Channel")
            next_reminder = datetime.fromisoformat(reminder["next_reminder"]).strftime('%Y-%m-%d %H:%M:%S')
            response += (
                f"- <{user_id}>:"
                f"(Next Reminder: {next_reminder}, Channel: <#{channel_id}>)\n"
            )
        await ctx.send(response)
    else:
        await ctx.send("There are no reminders set.")
        
# Command to delete your reminder
@bot.command()
async def delete_reminder(ctx, user: discord.User):
    """Delete a reminder for a specific user."""
    user_id = str(user.id)
    reminders = load_reminders()
    if user_id in reminders:
        del reminders[user_id]
        save_reminders(reminders)
        await ctx.send(f"Reminder for {user.mention} has been deleted.")
    else:
        await ctx.send(f"There are no reminders set for {user.mention}.")
        
# Event triggered when a message is sent in a channel
@bot.event
async def on_message(message):
    # Define the specific channel where the bot will pin Google Docs links
    specific_channel_id = '[A specific integer that you dont need to see]'
    
    # Check if the message is in the specific channel and contains a Google Docs link
    if message.channel.id == specific_channel_id and 'docs.google.com' in message.content:
        try:
            await message.pin()
        except discord.errors.Forbidden:
            await message.channel.send("I don't have permission to pin messages in this channel.")
        except discord.errors.HTTPException:
            await message.channel.send("Failed to pin the message due to an API error.")
    
    # Don't forget to process other commands
    await bot.process_commands(message)
        
# Pings the bot to see if it's still breathing
@bot.command()
async def ping_cgr_bot(ctx):
    await ctx.send("I'm alive :)")
        
# Run the bot
TOKEN = "[A specific token that you definitley don't need to see]"
bot.run(TOKEN)