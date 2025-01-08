import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests

# ---- Configuration ----
BOT_TOKEN = os.getenv("BOT_TOKEN", "7559019704:AAEgnG14Nkm-x4_9K3m4HXSitCSrd2RdsaE")  # Replace with your bot token
ADMIN_ID = int(os.getenv("ADMIN_ID", 123456789))  # Replace with your Telegram admin ID
WEBHOOK_URL = f"https://webhook-ltcd.onrender.com/webhook/{BOT_TOKEN}"  # Replace with your Render app URL

# ---- Flask App ----
app = Flask(__name__)

# ---- Logging Configuration ----
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TelegramBotWebhook")

# ---- Telegram Bot Application ----
application = Application.builder().token(BOT_TOKEN).build()
bot = Bot(token=BOT_TOKEN)

# ---- Command Handlers ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force reply to /start command."""
    logger.info(f"Triggered /start by {update.effective_user.username}")
    try:
        await update.message.reply_text("Welcome! The bot is running successfully!")
    except Exception as e:
        logger.error(f"Failed to reply to /start: {e}")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force reply to /ping command."""
    logger.info(f"Triggered /ping by {update.effective_user.username}")
    try:
        await update.message.reply_text("Pong! The bot is alive.")
    except Exception as e:
        logger.error(f"Failed to reply to /ping: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages."""
    logger.info(f"Handling message from {update.effective_user.username}: {update.message.text}")
    try:
        await update.message.reply_text(f"Hi {update.effective_user.first_name}, I received your message!")
    except Exception as e:
        logger.error(f"Failed to reply to message: {e}")

# ---- Add Handlers ----
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ping", ping))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ---- Flask Webhook Endpoint ----
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    """Receive updates from Telegram."""
    try:
        data = request.get_json()
        logger.info(f"Webhook received data: {data}")
        update = Update.de_json(data, bot)

        # Force process update even if something fails
        application.process_update(update)
    except Exception as e:
        logger.error(f"Error processing update: {e}")
    return "OK", 200

@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Bot is running"}), 200

# ---- Webhook Setup ----
def set_webhook():
    """Set the Telegram bot webhook."""
    logger.info(f"Setting webhook to {WEBHOOK_URL}")
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        json={"url": WEBHOOK_URL},
    )
    if response.status_code == 200:
        logger.info(f"Webhook successfully set to {WEBHOOK_URL}")
    else:
        logger.error(f"Failed to set webhook: {response.json()}")

# ---- Run Application ----
if __name__ == "__main__":
    # Set the webhook on startup
    set_webhook()

    # Start the Flask app
    logger.info("Starting Flask server...")
    app.run(host="0.0.0.0", port=5000)
