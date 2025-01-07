import requests
import logging
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
import asyncio

# ---- Configuration ----
BOT_TOKEN = "7559019704:AAEgnG14Nkm-x4_9K3m4HXSitCSrd2RdsaE"
WEBHOOK_URL = "https://your-render-url.onrender.com"  # Replace with your Render app URL
ADMIN_ID = 7618426591  # Admin's Telegram user ID
GROUP_ID = -1002317604959  # Group ID to track new members

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

# ---- Flask Route: Webhook Endpoint ----
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """
    Telegram webhook endpoint to receive updates.
    """
    logger.debug("[DEBUG] Webhook endpoint triggered.")
    data = request.get_json(force=True)
    logger.debug(f"[DEBUG] Received webhook data: {data}")
    app_bot.update_queue.put_nowait(Update.de_json(data, app_bot.bot))
    return jsonify({"status": "success"}), 200


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


# ---- Command: /register_invite ----
async def register_invite_command(update: Update, context: CallbackContext):
    """
    Command to register a new invite link manually.
    """
    logger.debug("[DEBUG] /register_invite command triggered.")
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
        logger.info(f"[INFO] Invite link registered via /register_invite: {invite_link}")


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


# ---- Set Up Webhook ----
async def setup_webhook(bot):
    """
    Asynchronous function to set the webhook for the bot.
    """
    webhook_url = f"{WEBHOOK_URL}/webhook/{BOT_TOKEN}"
    await bot.set_webhook(webhook_url)
    logger.info(f"[INFO] Webhook set: {webhook_url}")


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

    # Set webhook asynchronously
    asyncio.run(setup_webhook(app_bot.bot))

    # Start Flask app with production-ready WSGI server
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
