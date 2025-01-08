import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# ---- Configuration ----
BOT_TOKEN = os.getenv("BOT_TOKEN", "your-bot-token")  # Replace with your bot token
ADMIN_ID = int(os.getenv("ADMIN_ID", 123456789))  # Replace with your Telegram admin ID
GROUP_ID = int(os.getenv("GROUP_ID", -1001234567890))  # Replace with your group ID
WEBHOOK_URL = f"https://webhook-ltcd.onrender.com/{BOT_TOKEN}"  # Replace with your Render app URL

# ---- Flask App ----
app = Flask(__name__)

# ---- Logging Configuration ----
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MembershipBot")

# ---- Telegram Bot Application ----
application = ApplicationBuilder().token(BOT_TOKEN).build()

# ---- Bot Command Handlers ----
async def start(update: Update, context):
    """Handle the /start command."""
    await update.message.reply_text("Hello! Your bot is running with webhooks!")

async def ping(update: Update, context):
    """Handle the /ping command."""
    await update.message.reply_text("Pong!")

async def notify_admin(update: Update, context):
    """Notify the admin with a custom message."""
    message = f"New message from @{update.effective_user.username}: {update.message.text}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=message)

# ---- Custom Message Handler ----
async def handle_message(update: Update, context):
    """Handle all other text messages."""
    await update.message.reply_text(f"Hi {update.effective_user.first_name}, I received your message!")

# ---- Add Handlers to the Bot ----
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ping", ping))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ---- Flask Webhook Endpoints ----
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    """Handle incoming Telegram webhook updates."""
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return "OK", 200

@app.route("/register_invite", methods=["POST"])
def register_invite():
    """Handle invite registration."""
    data = request.get_json()
    invite_link = data.get("invite_link")
    if not invite_link:
        return {"error": "Invalid invite link"}, 400
    logger.info(f"Invite link registered: {invite_link}")
    return {"status": "success", "invite_link": invite_link}, 200

# ---- Webhook Setup ----
if __name__ == "__main__":
    # Set Webhook on Startup
    import requests
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        json={"url": WEBHOOK_URL},
    )
    if response.status_code == 200:
        logger.info(f"Webhook successfully set to {WEBHOOK_URL}")
    else:
        logger.error(f"Failed to set webhook: {response.text}")

    # Run the Flask App
    app.run(host="0.0.0.0", port=5000)
