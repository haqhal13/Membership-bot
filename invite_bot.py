import logging
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
import requests
import threading
import os

# ---- Configuration ----
BOT_TOKEN = os.getenv("BOT_TOKEN", "7559019704:AAEgnG14Nkm-x4_9K3m4HXSitCSrd2RdsaE")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-bot-render-url.onrender.com")  # Replace with your bot's Render URL
ADMIN_ID = int(os.getenv("ADMIN_ID", 7618426591))  # Admin's Telegram user ID
GROUP_ID = int(os.getenv("GROUP_ID", -1002317604959))  # Group ID to track new members

# In-memory invite link storage
invite_links = {}

# Configure Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,  # Set to DEBUG for detailed logging
)
logger = logging.getLogger("bot")

# Flask app for webhook listener
app = Flask(__name__)

# ---- Flask Route: Health Check ----
@app.route("/")
def health_check():
    """
    Health check endpoint to confirm the server is running.
    """
    logger.info("[INFO] Health check request received.")
    return "Bot and webhook are running!", 200


# ---- Flask Route: Webhook for Adding Invite Links ----
@app.route('/register_invite', methods=['POST'])
def register_invite_webhook():
    """
    Webhook endpoint for registering invite links.
    """
    logger.debug("[DEBUG] Received request on /register_invite endpoint.")
    try:
        data = request.get_json()
        logger.info(f"[INFO] Received data for invite registration: {data}")

        invite_link = data.get("invite_link")
        if not invite_link or not invite_link.startswith("https://t.me/"):
            logger.warning("[WARNING] Invalid invite link received.")
            return jsonify({"error": "Invalid invite link"}), 400

        if invite_link in invite_links:
            logger.info(f"[INFO] Invite link already exists: {invite_link}")
            return jsonify({"message": "Invite link already exists"}), 200

        invite_links[invite_link] = False  # Mark as unused
        logger.info(f"[INFO] Invite link registered: {invite_link}")
        logger.debug(f"[DEBUG] Updated invite_links state: {invite_links}")

        return jsonify({"status": "success", "message": "Invite link registered"}), 200

    except Exception as e:
        logger.error(f"[ERROR] Exception occurred in /register_invite: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ---- Command: /start ----
async def start(update: Update, context: CallbackContext):
    """
    Handle the /start command to confirm the bot is running.
    """
    logger.info("[INFO] /start command triggered.")
    await update.message.reply_text(
        "✅ Bot is running!\n"
        f"Registered Invite Links: {len(invite_links)}"
    )


# ---- Command: /list_invites ----
async def list_invites(update: Update, context: CallbackContext):
    """
    List all registered invite links.
    """
    logger.debug("[DEBUG] /list_invites command triggered.")
    if not invite_links:
        await update.message.reply_text("ℹ️ No invite links registered.")
    else:
        links_list = "\n".join(
            [f"{link} - {'Used' if used else 'Unused'}" for link, used in invite_links.items()]
        )
        await update.message.reply_text(f"📜 Registered Invite Links:\n{links_list}")


# ---- Handle New Members ----
async def new_member(update: Update, context: CallbackContext):
    """
    Handle new members joining the group.
    """
    logger.debug("[DEBUG] Received update for new member.")
    if update.effective_chat.id != GROUP_ID:
        logger.warning(f"[WARNING] Event from unauthorized group: {update.effective_chat.id}")
        return

    for member in update.message.new_chat_members:
        username = f"@{member.username}" if member.username else "No Username"
        full_name = f"{member.first_name} {member.last_name or ''}".strip()
        user_id = member.id

        logger.info(f"[INFO] New Member: Name: {full_name}, Username: {username}, ID: {user_id}")

        # Match Invite Link
        matched_invite = None
        for link, used in invite_links.items():
            if not used:  # Find the first unused invite link
                matched_invite = link
                invite_links[link] = True  # Mark as used
                logger.info(f"[INFO] Invite link matched and marked as used: {matched_invite}")
                break

        if not matched_invite:
            logger.warning(f"[WARNING] No matching invite link found for {full_name} ({username}).")
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ New member joined without using a tracked invite link:\n"
                     f"Name: {full_name}\nUsername: {username}\nUser ID: {user_id}"
            )
            return

        # Notify Admin
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"✅ New member joined:\n"
                 f"Name: {full_name}\n"
                 f"Username: {username}\n"
                 f"User ID: {user_id}\n"
                 f"Invite Link Used: {matched_invite}"
        )


# ---- Handle Unknown Commands ----
async def unknown(update: Update, context: CallbackContext):
    """
    Handle unknown commands.
    """
    logger.debug("[DEBUG] Unknown command received.")
    await update.message.reply_text("❌ Unknown command. Use /start or /list_invites.")


# ---- Main Function ----
def main():
    """
    Main function to start the bot and Flask webhook listener.
    """
    logger.info("[INFO] Starting the bot and webhook server...")

    # Start Flask app on a separate thread
    flask_thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000))
    flask_thread.start()

    # Start Telegram bot
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add command handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("list_invites", list_invites))
    app_bot.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
    app_bot.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Set webhook
    logger.info("[INFO] Setting webhook...")
    app_bot.bot.set_webhook(WEBHOOK_URL)

    # Run the bot
    app_bot.run_polling()


if __name__ == "__main__":
    main()
