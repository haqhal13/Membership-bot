from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler
import asyncio
import logging

# ---- Configuration ----
BOT_TOKEN = "7559019704:AAEgnG14Nkm-x4_9K3m4HXSitCSrd2RdsaE"  # Replace with your bot token

# Configure Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,  # Set to DEBUG for detailed logging
)
logger = logging.getLogger("bot")

# Flask app
app = Flask(__name__)

# Telegram Bot Application
app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

# ---- Command Handlers ----
async def start_command(update: Update, context):
    """
    Responds to the /start command.
    """
    await update.message.reply_text("✅ Bot is running! Send /help for more information.")

# Add the command handler to the bot
app_bot.add_handler(CommandHandler("start", start_command))

# ---- Webhook Endpoint ----
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """
    Handles incoming webhook updates from Telegram.
    """
    try:
        data = request.get_json()
        update = Update.de_json(data, app_bot.bot)
        asyncio.run(app_bot.process_update(update))
        return "OK", 200
    except Exception as e:
        logger.error(f"Error processing update: {e}", exc_info=True)
        return "Internal Server Error", 500

# ---- Health Check Endpoint ----
@app.route("/")
def health_check():
    """
    Simple health check endpoint.
    """
    return "Webhook is running!", 200

# ---- Run the Flask App ----
if __name__ == "__main__":
    logger.info("Starting webhook server...")
    app.run(host="0.0.0.0", port=5000, debug=True)
