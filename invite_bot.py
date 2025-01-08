from telegram import Update, Bot, ChatInviteLink
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
from datetime import datetime, timedelta
import threading

# ---- Configuration ----
BOT_TOKEN = "7559019704:AAEgnG14Nkm-x4_9K3m4HXSitCSrd2RdsaE"
ADMIN_ID = 7618426591
GROUP_ID = -1002317604959
WEBHOOK_URL_INFO = "https://hook.eu2.make.com/jj5f9zweffha9j8q2cfar2ri1s85bdar"

# Local storage for invite link tracking (in-memory)
invite_links = {}
membership_expiry = {}

# ---- Helper Functions ----
def notify_admin(bot: Bot, user_data: dict):
    """Send member details to admin."""
    message = (
        f"New Member Joined:\n"
        f"Name: {user_data.get('name', 'N/A')}\n"
        f"Username: @{user_data.get('username', 'N/A')}\n"
        f"User ID: {user_data['id']}\n"
        f"Invite Link: {user_data.get('invite_link', 'N/A')}"
    )
    bot.send_message(chat_id=ADMIN_ID, text=message)

def generate_invite_link(bot: Bot) -> ChatInviteLink:
    """Generate and register a one-time invite link."""
    link = bot.create_chat_invite_link(chat_id=GROUP_ID, expire_date=int((datetime.now() + timedelta(days=1)).timestamp()))
    invite_links[link.invite_link] = None
    return link

def check_membership():
    """Periodic check for membership expiry."""
    while True:
        now = datetime.now()
        for user_id, expiry_date in list(membership_expiry.items()):
            if now > expiry_date:
                bot.kick_chat_member(chat_id=GROUP_ID, user_id=user_id)
                del membership_expiry[user_id]
            elif now + timedelta(days=1) > expiry_date:
                bot.send_message(chat_id=user_id, text="Your membership is about to expire. Please renew!")
        time.sleep(3600)

# ---- Command Handlers ----
def start(update: Update, context: CallbackContext):
    """Start command handler."""
    update.message.reply_text("Welcome! Use /generate_invite to get a one-time invite link.")

def generate_invite(update: Update, context: CallbackContext):
    """Generate a one-time invite link."""
    bot = context.bot
    link = generate_invite_link(bot)
    update.message.reply_text(f"Here is your one-time invite link: {link.invite_link}")

def member_join(update: Update, context: CallbackContext):
    """Handle new member join events."""
    bot = context.bot
    new_members = update.message.new_chat_members
    for member in new_members:
        user_data = {
            "name": member.full_name,
            "username": member.username,
            "id": member.id,
            "invite_link": "Tracked from webhook"  # Fill this via webhook in Flow 2
        }
        notify_admin(bot, user_data)
        membership_expiry[member.id] = datetime.now() + timedelta(days=28)

# ---- Main Program ----
def main():
    """Start the bot."""
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("generate_invite", generate_invite))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, member_join))

    # Start membership expiry thread
    threading.Thread(target=check_membership, daemon=True).start()

    # Start polling
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
