from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters
from flask import Flask, request
import os
from datetime import datetime

# Replace this with your bot token
BOT_TOKEN = os.getenv("BOT_TOKEN", "7559019704:AAHLrqyyJvQS47_sxWSNyDRxAPCMBgjd_74")

# Replace this with your admin's Telegram chat ID
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "7618426591")

# Flask app for webhook and uptime monitoring
app = Flask(__name__)

def new_member(update: Update, context):
    """Handles new chat members and notifies the admin."""
    group_name = update.message.chat.title  # Group name
    group_id = update.message.chat.id       # Group ID
    
    for member in update.message.new_chat_members:
        name = member.full_name
        username = member.username or "No username"
        telegram_id = member.id
        join_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Notification message for the admin
        notification_message = (
            f"🎉 A new member has joined the group!\n\n"
            f"Group Name: {group_name}\n"
            f"Group ID: {group_id}\n\n"
            f"Name: {name}\n"
            f"Username: @{username}\n"
            f"Telegram ID: {telegram_id}\n"
            f"Joined at: {join_time}\n"
        )
        
        # Send a direct message (DM) to the admin
        context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=notification_message)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """Handle incoming updates from Telegram."""
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

@app.route("/uptime", methods=["GET"])
def uptime():
    """Endpoint for uptime monitoring."""
    return "Bot is running!", 200

@app.route("/", methods=["GET"])
def root():
    """Root endpoint for service health check."""
    return "Service is live!", 200

if __name__ == "__main__":
    # Telegram bot setup
    from telegram import Bot
    from telegram.ext import Dispatcher

    bot = Bot(token=BOT_TOKEN)
    dispatcher = Dispatcher(bot, None, workers=0)
    
    # Add handler for new members
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_member))
    
    # Set webhook
    webhook_url = f"https://membership-bot-grng.onrender.com/{BOT_TOKEN}"
    bot.set_webhook(url=webhook_url)
    
    # Run Flask app
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8443)))
