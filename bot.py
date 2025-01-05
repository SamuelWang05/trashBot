import discord
from discord.ext import commands
import json
import asyncio
from datetime import datetime, timedelta

# Load token from config.json
with open("config.json") as f:
    config = json.load(f)
    TOKEN = config["bot_token"]

# Intents for bot
intents = discord.Intents.default()
intents.message_content = True

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

# List of users to ping (with provided user IDs)
users_to_ping = [
    1104425492704149526,  # @edabas's user ID
    722150075912159252,   # @ant101gm's user ID
    879940180100919367,   # @samuelwang's user ID
    619299228669313035,   # @shadowbirdcat's user ID
    606628393361866773,   # @neptune8906's user ID
    409502956317048842,   # @kavan7751's user ID
    960714374874562630,   # @secretnephilim's user ID
    743617557797273745,   # @aw0000001's user ID
    1198321572113567936   # @vardo.0's user ID
]

# Global variables
running = False  # Whether the weekly cycle is active
current_index = 0  # Index of the current user being pinged
task = None  # Background task reference
user_debts = {user: 0 for user in users_to_ping}  # Tracks how many times each user has missed completion
pending_user = None  # Tracks the current user who needs to complete the task

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

async def weekly_pinger(ctx):
    """Background task to ping users weekly and manage debt."""
    global current_index, running, pending_user

    # Ping the first person immediately when the bot starts
    pending_user = users_to_ping[current_index]
    user = await bot.fetch_user(pending_user)  # Fetch the user by their ID
    await ctx.send(f"Hello <@{user.id}>, it's your turn to take out the trash this week!")

    while running:
        # Calculate the next Sunday at 8am
        now = datetime.now()
        next_sunday = now + timedelta(days=(6 - now.weekday()))  # Sunday is 6
        next_sunday = next_sunday.replace(hour=8, minute=0, second=0, microsecond=0)

        # If it's already past 8am on Sunday, set the next ping for the following Sunday
        if now >= next_sunday:
            next_sunday += timedelta(weeks=1)

        # Calculate how long until the next Sunday at 8am
        wait_time = (next_sunday - now).total_seconds()

        # Wait until the next Sunday at 8am
        await asyncio.sleep(wait_time)

        # Handle incomplete task for the previous user
        if pending_user is not None:
            user_debts[pending_user] += 1
            user = await bot.fetch_user(pending_user)  # Fetch the user by their ID
            await ctx.send(f"User <@{user.id}> did not take out their trash! Shame on them! Their debt is now {user_debts[pending_user]} week(s).")

        # Ping the current user for this week
        pending_user = users_to_ping[current_index]
        user = await bot.fetch_user(pending_user)  # Fetch the user by their ID
        await ctx.send(f"Hello <@{user.id}>, it's your turn to take out the trash this week!")

        # Ping for outstanding debt if applicable
        debt_weeks = user_debts[pending_user]
        if debt_weeks > 0:
            await ctx.send(f"Reminder: <@{user.id}>, you still owe {debt_weeks} week(s) of tasks. Please complete them!")

        # Cycle to the next user
        current_index = (current_index + 1) % len(users_to_ping)

@bot.command()
async def start(ctx):
    """Start the weekly pinger."""
    global running, task

    if running:
        await ctx.send("The weekly pinger is already running!")
        return

    running = True
    task = bot.loop.create_task(weekly_pinger(ctx))
    await ctx.send("The weekly trash bot has started! Users will be pinged every Sunday at 8am. Make sure to take out your trash, or else you will accumulate debt! Once you take out the trash, respond with \"!complete\"")

@bot.command()
async def stop(ctx):
    """Stop the weekly pinger."""
    global running, task

    if not running:
        await ctx.send("The weekly pinger is not running.")
        return

    running = False
    if task:
        task.cancel()
        task = None
    await ctx.send("The weekly pinger has been stopped.")

@bot.command()
async def complete(ctx):
    """Mark the current user's task as complete and reduce their debt."""
    global pending_user

    if pending_user is None:
        await ctx.send("No task is currently assigned to a user.")
        return

    if user_debts[pending_user] > 0:
        user_debts[pending_user] -= 1
        user = await bot.fetch_user(pending_user)  # Fetch the user by their ID
        await ctx.send(f"Thank you <@{user.id}>! Your debt has been reduced to {user_debts[pending_user]} week(s).")
    else:
        user = await bot.fetch_user(pending_user)  # Fetch the user by their ID
        await ctx.send(f"Congratulations <@{user.id}> on completing your task! 🎉 You have no outstanding debt.")

    pending_user = None

@bot.command()
async def who(ctx):
    """Displays who’s turn it is to take out the trash this week without pinging or using @."""
    global pending_user
    if pending_user is None:
        await ctx.send("No one is currently assigned to take out the trash this week.")
    else:
        # Find the username from the user ID
        user = await bot.fetch_user(pending_user)
        await ctx.send(f"It's {user.name}'s turn to take out the trash this week.")

@bot.command()
async def debt(ctx):
    """Displays the debt status of all users without pinging or using @."""
    debt_message = "Debt Status:\n"
    for user_id, debt in user_debts.items():
        user = await bot.fetch_user(user_id)
        debt_message += f"{user.name}: {debt} week(s)\n"
    await ctx.send(debt_message)

@bot.command()
async def commands(ctx):
    """Lists all available commands."""
    command_list = """
    **!start** - Start the weekly pinger.
    **!stop** - Stop the weekly pinger.
    **!complete** - Mark your task as complete.
    **!who** - See who's turn it is to take out the trash.
    **!debt** - List all users' debt.
    **!commands** - List all available commands. Congrats, you just used this!
    """
    await ctx.send(command_list)

# Run the bot
bot.run(TOKEN)
