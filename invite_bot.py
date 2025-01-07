import logging
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import threading

# ---- Configuration ----
BOT_TOKEN = "7559019704:AAEgnG14Nkm-x4_9K3m4HXSitCSrd2RdsaE"
WEBHOOK_URL = "https://your-render-url.onrender.com"  # Replace with your Render URL
ADMIN_ID = 7618426591  # Admin's Telegram user ID
GROUP_ID = -1002317604959  # Group ID to track new members

# In-memory invite link storage
invite_links = {}

# Configure Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,  # Use INFO for production, DEBUG for troubleshooting
)
logger = logging.getLogger("bot")

# Flask app for webhook listener
app = Flask(__name__)

# ---- Flask Route: Health Check ----
@app.route("/")
def health_check():
    """
    Health check endpoint to confirm the webhook server is running.
    """
    logger.info("[INFO] Health check received.")
    return "Webhook is running!", 200


# ---- Flask Route: Register Invite Link ----
@app.route("/register_invite", methods=["POST"])
def register_invite():
    """
    Webhook endpoint to register invite links.
    """
    logger.info("[INFO] Received request on /register_invite endpoint.")
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
        return jsonify({"status": "success", "message": "Invite link registered"}), 200

    except Exception as e:
        logger.error(f"[ERROR] Exception occurred in /register_invite: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ---- Telegram Webhook Route ----
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    """
    Endpoint for Telegram to send webhook updates.
    """
    try:
        update = Update.de_json(request.get_json(force=True), app_bot.bot)
        app_bot.process_update(update)
        return "OK", 200
    except Exception as e:
        logger.error(f"[ERROR] Failed to process update: {e}", exc_info=True)
        return "Internal Server Error", 500


# ---- Command: /start ----
async def start(update: Update, context):
    """
    Handle the /start command.
    """
    await update.message.reply_text(
        f"✅ Bot is running!\n"
        f"Registered Invite Links: {len(invite_links)}"
    )


# ---- Command: /list_invites ----
async def list_invites(update: Update, context):
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


# ---- Command: /register_invite ----
async def register_invite_command(update: Update, context):
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

    if invite_link in invite_links:
        await update.message.reply_text(f"❌ This invite link is already registered: {invite_link}")
    else:
        invite_links[invite_link] = False  # Mark as unused
        await update.message.reply_text(f"✅ Invite link registered: {invite_link}")


# ---- Handle New Members ----
async def new_member(update: Update, context):
    """
    Handle new members joining the group.
    """
    if update.effective_chat.id != GROUP_ID:
        return

    for member in update.message.new_chat_members:
        username = f"@{member.username}" if member.username else "No Username"
        full_name = f"{member.first_name} {member.last_name or ''}".strip()
        user_id = member.id

        # Find unused invite link
        matched_invite = None
        for link, used in invite_links.items():
            if not used:
                matched_invite = link
                invite_links[link] = True  # Mark as used
                break

        if not matched_invite:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ New member joined without using a tracked invite link:\n"
                     f"Name: {full_name}\nUsername: {username}\nUser ID: {user_id}"
            )
        else:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"✅ New member joined:\n"
                     f"Name: {full_name}\nUsername: {username}\nUser ID: {user_id}\n"
                     f"Invite Link Used: {matched_invite}"
            )


# ---- Main Function ----
def main():
    """
    Main function to start the bot and Flask webhook listener.
    """
    global app_bot
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("list_invites", list_invites))
    app_bot.add_handler(CommandHandler("register_invite", register_invite_command))
    app_bot.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))

    # Set webhook
    webhook_url = f"{WEBHOOK_URL}/webhook/{BOT_TOKEN}"
    app_bot.bot.set_webhook(webhook_url)
    logger.info(f"[INFO] Webhook set: {webhook_url}")

    # Start Flask app
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
