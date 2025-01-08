import requests
import logging
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

# ---- Configuration ----
BOT_TOKEN = "7559019704:AAEgnG14Nkm-x4_9K3m4HXSitCSrd2RdsaE"
ADMIN_ID = 7618426591  # Admin's Telegram user ID
GROUP_ID = -1002317604959  # Group ID to track new members
WEBHOOK_URL_INFO = "https://hook.eu2.make.com/jj5f9zweffha9j8q2cfar2ri1s85bdar"  # Webhook for sending data to Make
WEBHOOK_URL = f"https://webhook-ltcd.onrender.com/webhook/{BOT_TOKEN}"  # Webhook for Telegram updates

# In-memory invite link storage
invite_links = {}

# Configure Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger("bot")

# Flask app for handling webhooks
app = Flask(__name__)

# ---- Flask Route: Webhook for Registering Invite Links ----
@app.route("/register_invite", methods=["POST"])
def register_invite_webhook():
    """
    Webhook endpoint for registering invite links via an external service.
    """
    try:
        data = request.get_json()
        invite_link = data.get("invite_link")
        if not invite_link or not invite_link.startswith("https://t.me/"):
            return jsonify({"error": "Invalid invite link"}), 400

        invite_links[invite_link] = False  # Mark as unused
        return jsonify({"status": "success", "message": "Invite link registered"}), 200
    except Exception as e:
        logger.error(f"[ERROR] Exception in /register_invite: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# ---- Flask Route: Webhook for Telegram Updates ----
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    """
    Webhook to handle incoming Telegram updates.
    """
    try:
        data = request.get_json()
        update = Update.de_json(data, bot_instance.bot)
        bot_instance.process_update(update)
        return "OK", 200
    except Exception as e:
        logger.error(f"[ERROR] Exception in telegram_webhook: {str(e)}", exc_info=True)
        return "Internal Server Error", 500

# ---- Command Handlers ----
async def start(update: Update, context: CallbackContext):
    """
    Handle the /start command.
    """
    await update.message.reply_text(f"✅ Bot is running!\nRegistered Invite Links: {len(invite_links)}")

async def list_invites(update: Update, context: CallbackContext):
    """
    List all registered invite links.
    """
    if not invite_links:
        await update.message.reply_text("ℹ️ No invite links registered.")
    else:
        links_list = "\n".join(
            [f"{link} - {'Used' if used else 'Unused'}" for link, used in invite_links.items()]
        )
        await update.message.reply_text(f"📜 Registered Invite Links:\n{links_list}")

async def register_invite(update: Update, context: CallbackContext):
    """
    Command to register a new invite link manually.
    """
    if len(context.args) < 1:
        await update.message.reply_text("❌ Usage: /register_invite <invite_link>")
        return

    invite_link = context.args[0]
    if not invite_link.startswith("https://t.me/"):
        await update.message.reply_text("❌ Invalid invite link. Must start with 'https://t.me/'.")
        return

    invite_links[invite_link] = False  # Mark as unused
    await update.message.reply_text(f"✅ Invite link registered: {invite_link}")

async def new_member(update: Update, context: CallbackContext):
    """
    Handle new members joining the group.
    """
    if update.effective_chat.id != GROUP_ID:
        return

    for member in update.message.new_chat_members:
        username = f"@{member.username}" if member.username else "No Username"
        full_name = f"{member.first_name} {member.last_name or ''}".strip()
        user_id = member.id

        matched_invite = None
        for link, used in invite_links.items():
            if not used:
                matched_invite = link
                invite_links[link] = True
                break

        # Send data to Make webhook
        make_payload = {
            "name": full_name,
            "username": username,
            "user_id": user_id,
            "invite_link": matched_invite or "Unknown",
        }
        try:
            requests.post(WEBHOOK_URL_INFO, json=make_payload, timeout=10)
        except Exception as e:
            logger.error(f"[ERROR] Failed to send data to Make webhook: {e}")

        # Notify Admin
        message = (
            f"✅ New member joined:\n"
            f"Name: {full_name}\n"
            f"Username: {username}\n"
            f"User ID: {user_id}\n"
            f"Invite Link Used: {matched_invite}" if matched_invite else
            f"⚠️ New member joined without a tracked invite link:\nName: {full_name}\nUsername: {username}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=message)

# ---- Main Function ----
def main():
    """
    Main function to start the bot and Flask server.
    """
    global bot_instance

    # Initialize Telegram bot
    bot_instance = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add command handlers
    bot_instance.add_handler(CommandHandler("start", start))
    bot_instance.add_handler(CommandHandler("list_invites", list_invites))
    bot_instance.add_handler(CommandHandler("register_invite", register_invite))
    bot_instance.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))

    # Start the Flask app and bot webhook
    bot_instance.run_webhook(
        listen="0.0.0.0",
        port=5001,
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()
