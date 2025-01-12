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
    """Mark the current user's task as complete, reduce their debt, and assign the task to the next user only if an image is attached."""
    global pending_user, current_index

    # Check if there is an attachment in the message
    if not ctx.message.attachments:
        await ctx.send("You must attach a photo as proof of task completion. Please try again with a picture!")
        return

    # Validate that the attachment is an image (including compatibility with common formats)
    supported_image_types = {"image/png", "image/jpeg", "image/webp", "image/heic", "image/heif"}
    image_found = False

    for attachment in ctx.message.attachments:
        if attachment.content_type and attachment.content_type.lower() in supported_image_types:
            image_found = True
            break

    if not image_found:
        await ctx.send(
            "The attached file must be an image (PNG, JPEG, WebP, or iPhone-compatible formats like HEIC). "
            "Please try again with a valid photo!"
        )
        return

    if pending_user is None:
        await ctx.send("No task is currently assigned to a user.")
        return

    # Congratulate the current user
    user = await bot.fetch_user(pending_user)
    if user_debts[pending_user] > 0:
        user_debts[pending_user] -= 1
        await ctx.send(f"Thank you <@{user.id}>! Your debt has been reduced to {user_debts[pending_user]} week(s).")
    else:
        await ctx.send(f"Congratulations <@{user.id}> on completing your task! 🎉 You have no outstanding debt.")

    # Advance to the next person in the list
    current_index = (current_index + 1) % len(users_to_ping)
    pending_user = users_to_ping[current_index]
    next_user = await bot.fetch_user(pending_user)

    # Notify the next person
    await ctx.send(f"Hello <@{next_user.id}>, you're up next to take out the trash! You now have the remainder of this week until next Sunday at 8am.")

@bot.command()
async def who(ctx):
    """Displays who’s turn it is to take out the trash this week, considering the updated assignment after !complete."""
    global pending_user

    if pending_user is None:
        await ctx.send("No one is currently assigned to take out the trash this week.")
    else:
        # Fetch the user currently assigned
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
    """Lists all available commands with updated descriptions."""
    command_list = """
    **!start** - Start the weekly pinger. Users will be pinged every Sunday at 8am.
    **!stop** - Stop the weekly pinger.
    **!complete** - Mark your task as complete. You **must** attach a photo (PNG, JPEG, WebP, or HEIC) as proof of completion. Without a valid image, the task will not be marked complete.
    **!who** - See whose turn it is to take out the trash this week. If the current task is marked as complete, the next person will be shown.
    **!debt** - List all users' debt.
    **!next** - Manually advance to the next person in the list (admin-only).
    **!set username** - Manually set the timer to a specific username (admin-only).
    **!commands** - List all available commands. Congrats, you just used this!
    """
    await ctx.send(command_list)

@bot.command()
async def next(ctx):
    """Manually advance to the next person in the list."""
    global current_index, pending_user

    # Increment the current index to move to the next user
    current_index = (current_index + 1) % len(users_to_ping)
    pending_user = users_to_ping[current_index]

    # Fetch and notify the new user
    user = await bot.fetch_user(pending_user)
    await ctx.send(f"The weekly task has been passed to <@{user.id}>. It's now their turn to take out the trash!")

@bot.command()
async def set(ctx, username: str):
    """Set the weekly timer to a specific user by their username."""
    global current_index, pending_user

    # Find the user by their username
    for index, user_id in enumerate(users_to_ping):
        user = await bot.fetch_user(user_id)
        if user.name == username:
            current_index = index
            pending_user = user_id
            await ctx.send(f"The weekly task has been manually assigned to {user.name}. It's now their turn to take out the trash!")
            return

    # If no match is found
    await ctx.send(f"User {username} not found in the list.")

# Run the bot
bot.run(TOKEN)