import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# ---- Configuration ----
BOT_TOKEN = "7559019704:AAEgnG14Nkm-x4_9K3m4HXSitCSrd2RdsaE"  # Replace with your bot token
ADMIN_ID = 7618426591  # Replace with your admin's Telegram user ID
WEBHOOK_URL = f"https://webhook-ltcd.onrender.com/webhook/{BOT_TOKEN}"  # Replace with your Render webhook URL

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,  # Set to DEBUG for more details
)
logger = logging.getLogger("bot")

# Flask app
app = Flask(__name__)

# ---- Flask Route: Health Check ----
@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint."""
    logger.info("[INFO] Health check received.")
    return "Webhook is running!", 200

# ---- Flask Route: Webhook ----
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """Telegram Webhook handler."""
    try:
        update_data = request.get_json()
        update = Update.de_json(update_data, bot)
        app_bot.update_queue.put(update)
        logger.info(f"[INFO] Received update: {update_data}")
        return "OK", 200
    except Exception as e:
        logger.error(f"[ERROR] Exception in webhook handler: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

# ---- Telegram Command Handlers ----
async def start(update: Update, context):
    """Handle the /start command."""
    await update.message.reply_text("✅ Bot is running!")

async def help_command(update: Update, context):
    """Handle the /help command."""
    await update.message.reply_text("ℹ️ Available commands:\n/start - Check if the bot is running\n/help - List available commands")

async def echo(update: Update, context):
    """Echo any text message."""
    await update.message.reply_text(f"You said: {update.message.text}")

# ---- Main Function ----
def main():
    global bot, app_bot
    bot = Bot(token=BOT_TOKEN)
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add command handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_command))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Set the webhook
    bot.set_webhook(url=WEBHOOK_URL)
    logger.info(f"[INFO] Webhook set to {WEBHOOK_URL}")

    # Run Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
