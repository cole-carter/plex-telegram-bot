"""Plex Telegram Bot - Main entry point."""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from bot.config import TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS, validate_config
from bot.agent import create_agent

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# Global agent instance
agent = None


def is_authorized(update: Update) -> bool:
    """Check if the user is authorized to use the bot."""
    user_id = update.effective_user.id
    return user_id in ALLOWED_USER_IDS


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    if not is_authorized(update):
        await update.message.reply_text("Unauthorized user.")
        return

    welcome_message = """
🤖 **Plex Bot** - AI-powered media server manager

I can help you:
• Request TV shows and movies
• Manage downloads
• Organize media files
• Check library status
• And much more!

Just chat with me naturally. Examples:
• "Get me Breaking Bad season 5"
• "What's downloading right now?"
• "Do I have The Office?"
• "Check disk space"

I'm powered by Claude AI and have access to your Sonarr, Radarr, qBittorrent, and Plex.
"""
    await update.message.reply_text(welcome_message, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    if not is_authorized(update):
        await update.message.reply_text("Unauthorized user.")
        return

    help_message = """
**Available Commands:**
/start - Welcome message
/help - This help message
/status - Check bot status

**How to use:**
Just send me messages naturally! I understand requests like:

**TV Shows:**
• "Get me Naruto episodes 471-479"
• "Download the new season of The Office"
• "Am I missing any Breaking Bad episodes?"

**Movies:**
• "Add Inception to my library"
• "Find The Matrix"

**Downloads:**
• (Send a magnet link and tell me what it is)
• "What's downloading?"
• "Is that download done yet?"

**Library:**
• "What shows do I have?"
• "List all movies"
• "Scan my library"

**System:**
• "Check disk space"
• "How much storage is left?"

I'm intelligent and conversational - just tell me what you want!
"""
    await update.message.reply_text(help_message, parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    if not is_authorized(update):
        await update.message.reply_text("Unauthorized user.")
        return

    await update.message.reply_text("🟢 Bot is online and ready!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    # Check authorization
    if not is_authorized(update):
        logger.warning(
            f"Unauthorized access attempt from user {update.effective_user.id} "
            f"({update.effective_user.username})"
        )
        await update.message.reply_text("Unauthorized user.")
        return

    user_message = update.message.text
    logger.info(f"User {update.effective_user.username}: {user_message}")

    # Send "typing" indicator
    await update.message.chat.send_action(action="typing")

    try:
        # Process message with agent
        response = agent.process_message(user_message)

        # Send response
        await update.message.reply_text(response)

        logger.info(f"Bot response: {response[:100]}...")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await update.message.reply_text(
            f"Sorry, I encountered an error: {str(e)}\n\n"
            "Please try again or contact the administrator."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)


def main():
    """Start the bot."""
    global agent

    # Validate configuration
    if not validate_config():
        return

    # Initialize agent
    logger.info("Initializing Claude agent...")
    agent = create_agent()
    logger.info(f"Agent initialized with model: {agent.model}")

    # Create Telegram application
    logger.info("Starting Telegram bot...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.add_error_handler(error_handler)

    # Start polling
    logger.info("Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
