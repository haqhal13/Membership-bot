import os
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from waitress import serve

# ---- Configuration ----
BOT_TOKEN = "7559019704:AAEgnG14Nkm-x4_9K3m4HXSitCSrd2RdsaE"  # Replace with your bot token
ADMIN_ID = 7618426591  # Replace with your admin's Telegram user ID
GROUP_ID = -1002317604959  # Replace with your group ID
WEBHOOK_URL = f"https://webhook-ltcd.onrender.com/webhook/{BOT_TOKEN}"  # Replace with your webhook URL

# In-memory invite link storage
invite_links = {}

# Configure Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,  # Change to INFO in production
)
logger = logging.getLogger("bot")

# Flask app
app = Flask(__name__)

# ---- Flask Route: Health Check ----
@app.route("/", methods=["GET", "HEAD"])
def health_check():
    logger.info("[INFO] Health check received.")
    return "Bot webhook server is running!", 200

# ---- Flask Route: Webhook for Telegram ----
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    logger.info("[INFO] Webhook triggered.")
    if request.method == "POST":
        try:
            update_data = request.get_json()
            logger.debug(f"[DEBUG] Update received: {update_data}")
            update = Update.de_json(update_data, app_bot.bot)
            asyncio.run(app_bot.process_update(update))
            return "OK", 200
        except Exception as e:
            logger.error(f"[ERROR] Exception in webhook processing: {e}", exc_info=True)
            return jsonify({"error": "Webhook processing failed"}), 500
    return "Invalid request method", 405

# ---- Command: /start ----
async def start(update: Update, context):
    await update.message.reply_text("✅ Bot is running and connected!")

# ---- Command: /list_invites ----
async def list_invites(update: Update, context):
    if not invite_links:
        await update.message.reply_text("ℹ️ No invite links registered.")
    else:
        links_list = "\n".join(
            [f"{link} - {'Used' if used else 'Unused'}" for link, used in invite_links.items()]
        )
        await update.message.reply_text(f"📜 Registered Invite Links:\n{links_list}")

# ---- Command: /register_invite ----
async def register_invite_command(update: Update, context):
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

        if matched_invite:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"✅ New member joined:\nName: {full_name}\nUsername: {username}\nID: {user_id}\nInvite: {matched_invite}",
            )
        else:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ New member without invite:\nName: {full_name}\nUsername: {username}\nID: {user_id}",
            )

# ---- Setup Webhook ----
async def setup_webhook(bot):
    try:
        await bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"[INFO] Webhook set successfully: {WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to set webhook: {e}", exc_info=True)

# ---- Main Function ----
def main():
    global app_bot
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add command handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("list_invites", list_invites))
    app_bot.add_handler(CommandHandler("register_invite", register_invite_command))
    app_bot.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))

    # Set webhook asynchronously
    asyncio.run(setup_webhook(app_bot.bot))

    # Serve Flask app with Waitress
    port = int(os.environ.get("PORT", 5000))
    serve(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
