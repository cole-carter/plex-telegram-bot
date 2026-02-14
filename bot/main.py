"""Plex Telegram Bot - Main entry point."""

import logging
from pathlib import Path
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from bot.config import TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS, validate_config, PROJECT_ROOT
from bot.agent import create_agent

# Configure logging to both file and console
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / f"bot_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Separate conversation logger
conversation_logger = logging.getLogger("conversation")
conversation_handler = logging.FileHandler(LOG_DIR / f"conversations_{datetime.now().strftime('%Y%m%d')}.log")
conversation_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
conversation_logger.addHandler(conversation_handler)
conversation_logger.setLevel(logging.INFO)

# Global agent instance and processing state
agent = None
processing_interrupted = False

# Conversation history per user (limited to last N messages)
conversation_history = {}
MAX_HISTORY_MESSAGES = 4  # Keep last 4 exchanges (8 messages total)
MAX_MESSAGE_LENGTH = 4000  # Truncate messages longer than this


def truncate_message(content: str, max_length: int = MAX_MESSAGE_LENGTH) -> str:
    """Truncate long messages to prevent context overflow."""
    if len(content) <= max_length:
        return content
    return content[:max_length] + f"\n\n[... truncated {len(content) - max_length} characters]"


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
/stop - Interrupt current task

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


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command - interrupt current processing."""
    global processing_interrupted

    if not is_authorized(update):
        await update.message.reply_text("Unauthorized user.")
        return

    processing_interrupted = True
    logger.info("Stop command received - interrupting agent processing")
    await update.message.reply_text("⏹️ Stopping current task...")


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command - clear conversation history."""
    if not is_authorized(update):
        await update.message.reply_text("Unauthorized user.")
        return

    user_id = update.effective_user.id
    if user_id in conversation_history:
        conversation_history[user_id] = []
        logger.info(f"Cleared conversation history for user {user_id}")
        await update.message.reply_text("🗑️ Conversation history cleared.")
    else:
        await update.message.reply_text("No conversation history to clear.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    global processing_interrupted, conversation_history

    # Check authorization
    if not is_authorized(update):
        logger.warning(
            f"Unauthorized access attempt from user {update.effective_user.id} "
            f"({update.effective_user.username})"
        )
        await update.message.reply_text("Unauthorized user.")
        return

    user_id = update.effective_user.id
    user_message = update.message.text
    username = update.effective_user.username or update.effective_user.first_name

    logger.info(f"User {username}: {user_message}")
    conversation_logger.info(f"USER [{username}]: {user_message}")

    # Initialize conversation history for this user if needed
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # Reset interrupt flag
    processing_interrupted = False

    # Send "typing" indicator
    await update.message.chat.send_action(action="typing")

    try:
        # Get recent conversation history
        history = conversation_history[user_id]

        # Process message with agent (with history)
        response = agent.process_message(
            user_message,
            conversation_history=history,
            interrupt_flag=lambda: processing_interrupted
        )

        # Check if interrupted
        if processing_interrupted:
            response = "⏹️ Task interrupted."
            processing_interrupted = False

        # Send response
        await update.message.reply_text(response)

        # Update conversation history (truncate long messages to prevent context overflow)
        history.append({"role": "user", "content": truncate_message(user_message)})
        history.append({"role": "assistant", "content": truncate_message(response)})

        # Trim history if too long (keep last N exchanges = 2N messages)
        if len(history) > MAX_HISTORY_MESSAGES * 2:
            history = history[-(MAX_HISTORY_MESSAGES * 2):]
            conversation_history[user_id] = history

        logger.info(f"Bot response: {response[:100]}...")
        conversation_logger.info(f"BOT: {response}")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        conversation_logger.error(f"ERROR: {str(e)}")
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
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.add_error_handler(error_handler)

    # Start polling
    logger.info("Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
