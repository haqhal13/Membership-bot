import os
import sys
from telegram import Update, ChatInviteLink
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from datetime import datetime, timedelta
import threading
import time

# ---- Environment Variables ----
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
GROUP_ID = os.getenv("GROUP_ID")

# Validate environment variables
if not BOT_TOKEN:
    sys.exit("Error: BOT_TOKEN is not set in environment variables.")
if not ADMIN_ID:
    sys.exit("Error: ADMIN_ID is not set in environment variables.")
if not GROUP_ID:
    sys.exit("Error: GROUP_ID is not set in environment variables.")

# Convert environment variables to appropriate types
ADMIN_ID = int(ADMIN_ID)
GROUP_ID = int(GROUP_ID)

# ---- Data Storage ----
invite_links = {}  # To track invite links
membership_expiry = {}  # To track membership expiry dates

# ---- Helper Functions ----
async def notify_admin(context: ContextTypes.DEFAULT_TYPE, user_data: dict):
    """Send member details to the admin."""
    message = (
        f"New Member Joined:\n"
        f"Name: {user_data.get('name', 'N/A')}\n"
        f"Username: @{user_data.get('username', 'N/A')}\n"
        f"User ID: {user_data['id']}\n"
        f"Invite Link: {user_data.get('invite_link', 'N/A')}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=message)


async def generate_invite_link(context: ContextTypes.DEFAULT_TYPE) -> ChatInviteLink:
    """Generate and register a one-time invite link."""
    bot = context.bot
    link = await bot.create_chat_invite_link(
        chat_id=GROUP_ID, expire_date=int((datetime.now() + timedelta(days=1)).timestamp())
    )
    invite_links[link.invite_link] = None
    return link


def check_membership():
    """Periodic check for membership expiry."""
    while True:
        now = datetime.now()
        for user_id, expiry_date in list(membership_expiry.items()):
            if now > expiry_date:
                # Kick the user
                try:
                    application.bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                except Exception as e:
                    print(f"Error kicking user {user_id}: {e}")
                del membership_expiry[user_id]
            elif now + timedelta(days=1) > expiry_date:
                try:
                    application.bot.send_message(
                        chat_id=user_id,
                        text="Your membership is about to expire. Please renew!",
                    )
                except Exception as e:
                    print(f"Error notifying user {user_id}: {e}")
        time.sleep(3600)  # Check every hour

# ---- Command Handlers ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler."""
    await update.message.reply_text("Welcome! Use /generate_invite to get a one-time invite link.")


async def generate_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a one-time invite link."""
    link = await generate_invite_link(context)
    await update.message.reply_text(f"Here is your one-time invite link: {link.invite_link}")


async def member_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new member join events."""
    new_members = update.message.new_chat_members
    for member in new_members:
        user_data = {
            "name": member.full_name,
            "username": member.username,
            "id": member.id,
            "invite_link": "Tracked from webhook",  # Fill this via webhook integration
        }
        await notify_admin(context, user_data)
        membership_expiry[member.id] = datetime.now() + timedelta(days=28)

# ---- Main Program ----
if __name__ == "__main__":
    # Initialize the bot application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("generate_invite", generate_invite))

    # Add event handler for new chat members
    application.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, member_join)
    )

    # Start a background thread to check membership expiry
    threading.Thread(target=check_membership, daemon=True).start()

    # Start the bot
    application.run_polling()
