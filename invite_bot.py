import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests

# ---- Configuration ----
BOT_TOKEN = os.getenv("BOT_TOKEN", "your-bot-token")  # Replace with your bot token
ADMIN_ID = int(os.getenv("ADMIN_ID", 123456789))  # Replace with your Telegram admin ID
GROUP_ID = int(os.getenv("GROUP_ID", -1001234567890))  # Replace with your group ID
WEBHOOK_URL = f"https://webhook-ltcd.onrender.com/webhook/{BOT_TOKEN}"  # Replace with your Render app URL

# ---- Flask App ----
app = Flask(__name__)

# ---- Logging Configuration ----
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AdvancedMembershipBot")

# ---- Telegram Bot Application ----
application = Application.builder().token(BOT_TOKEN).build()

# ---- Telegram Bot Instance ----
bot = Bot(token=BOT_TOKEN)

# ---- Command Handlers ----
async def start(update: Update, context):
    """Handle the /start command."""
    logger.info(f"Received /start command from {update.effective_user.username}")
    await update.message.reply_text("Welcome! The bot is running successfully!")

async def ping(update: Update, context):
    """Handle the /ping command."""
    logger.info(f"Received /ping command from {update.effective_user.username}")
    await update.message.reply_text("Pong! The bot is alive.")

async def notify_admin(update: Update, context):
    """Send a notification to the admin."""
    message = (
        f"New message from @{update.effective_user.username}:\n"
        f"Message: {update.message.text}"
    )
    logger.info(f"Notifying admin about a message from {update.effective_user.username}")
    await context.bot.send_message(chat_id=ADMIN_ID, text=message)

# ---- Custom Message Handler ----
async def handle_message(update: Update, context):
    """Handle all text messages."""
    logger.info(f"Handling message from {update.effective_user.username}")
    await update.message.reply_text(
        f"Hi {update.effective_user.first_name}, your message has been received!"
    )

# ---- Add Handlers ----
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ping", ping))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ---- Flask Webhook Endpoint ----
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    """Receive webhook updates from Telegram."""
    update = Update.de_json(request.get_json(force=True), bot)
    logger.info(f"Received update: {update}")
    application.process_update(update)
    return "OK", 200

@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Bot is running"}), 200

@app.route("/register_invite", methods=["POST"])
def register_invite():
    """Handle invite registration."""
    data = request.get_json()
    invite_link = data.get("invite_link")
    if not invite_link:
        logger.warning("Invalid invite link received")
        return {"error": "Invalid invite link"}, 400
    logger.info(f"Invite link registered: {invite_link}")
    return {"status": "success", "invite_link": invite_link}, 200

# ---- Webhook Setup ----
def set_webhook():
    """Set the Telegram bot webhook."""
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        json={"url": WEBHOOK_URL},
    )
    if response.status_code == 200:
        logger.info(f"Webhook successfully set to {WEBHOOK_URL}")
    else:
        logger.error(f"Failed to set webhook: {response.json()}")

# ---- Run the Application ----
if __name__ == "__main__":
    # Set the webhook on startup
    set_webhook()

    # Start the Flask app
    logger.info("Starting Flask server...")
    app.run(host="0.0.0.0", port=5000)
