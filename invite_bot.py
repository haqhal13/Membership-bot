from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters
from datetime import datetime

# Replace this with your bot token
BOT_TOKEN = '7559019704:AAHLrqyyJvQS47_sxWSNyDRxAPCMBgjd_74'

# Replace this with your admin's Telegram chat ID
ADMIN_CHAT_ID = 7618426591

def new_member(update: Update, context):
    """Handles new chat members and notifies the admin."""
    for member in update.message.new_chat_members:
        name = member.full_name
        username = member.username or "No username"
        telegram_id = member.id
        join_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Notification message for the admin
        notification_message = (
            f"🎉 A new member has joined the group!\n\n"
            f"Name: {name}\n"
            f"Username: @{username}\n"
            f"Telegram ID: {telegram_id}\n"
            f"Joined at: {join_time}\n"
        )
        
        # Send a direct message (DM) to the admin
        context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=notification_message)

def main():
    # Initialize the updater and dispatcher
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Add a handler for new members
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_member))
    
    # Start polling
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
