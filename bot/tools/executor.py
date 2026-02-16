"""Executor agent for processing command outputs with AI."""

import anthropic
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """Rough estimate: 1 token ≈ 4 characters."""
    return len(text) // 4


def should_use_pagination(command: str) -> bool:
    """Check if command could benefit from pagination."""
    command_lower = command.lower()
    return any([
        "plex" in command_lower and "all" in command_lower,
        "radarr" in command_lower and "/movie" in command_lower,
        "sonarr" in command_lower and "/series" in command_lower,
    ])


def generate_pagination_suggestion(command: str, output_size: int) -> str:
    """Generate specific pagination advice for the command."""
    estimated_tokens = estimate_tokens(str(output_size))

    if "plex" in command.lower():
        return (
            f"⚠️ Response too large ({estimated_tokens:,} tokens, {output_size:,} chars).\n\n"
            f"Use pagination or filters:\n"
            f"• Pagination: api-call plex GET '/library/sections/1/all' "
            f"-q 'X-Plex-Container-Start=0&X-Plex-Container-Size=50'\n"
            f"• Filter by genre: api-call plex GET '/library/sections/1/all?genre=Comedy'\n"
            f"• Filter by year: api-call plex GET '/library/sections/1/all?year=2020'\n\n"
            f"First 2000 characters:\n{str(output_size)[:2000]}"
        )
    elif "radarr" in command.lower():
        return (
            f"⚠️ Response too large ({estimated_tokens:,} tokens, {output_size:,} chars).\n\n"
            f"Use pagination:\n"
            f"• api-call radarr GET /movie -q 'page=1&pageSize=50'\n\n"
            f"First 2000 characters:\n{str(output_size)[:2000]}"
        )
    elif "sonarr" in command.lower():
        return (
            f"⚠️ Response too large ({estimated_tokens:,} tokens, {output_size:,} chars).\n\n"
            f"Use pagination:\n"
            f"• api-call sonarr GET /series -q 'page=1&pageSize=50'\n\n"
            f"First 2000 characters:\n{str(output_size)[:2000]}"
        )
    else:
        return (
            f"⚠️ Response too large ({estimated_tokens:,} tokens, {output_size:,} chars).\n\n"
            f"Try limiting the output or using more specific queries.\n\n"
            f"First 2000 characters:\n{str(output_size)[:2000]}"
        )


def execute_with_executor(command: str, raw_output: str, context: str = "") -> Dict[str, Any]:
    """
    Process command output using executor AI agent.

    The executor agent intelligently processes command outputs:
    - Returns short outputs as-is
    - Summarizes long outputs
    - Extracts structured data from API responses

    Args:
        command: The command that was executed
        raw_output: The raw output from the command
        context: Optional intent from the orchestrator describing what data is needed

    Returns:
        Dict with success, output, and error keys
    """
    from bot.config import (
        ANTHROPIC_API_KEY,
        EXECUTOR_MODEL,
        MAX_EXECUTOR_INPUT_TOKENS,
        MAX_EXECUTOR_OUTPUT_TOKENS,
    )

    # Pre-flight check: is output too large for executor?
    estimated_tokens = estimate_tokens(raw_output)

    if estimated_tokens > MAX_EXECUTOR_INPUT_TOKENS:
        logger.warning(
            f"Output too large for executor: {estimated_tokens:,} tokens "
            f"({len(raw_output):,} chars) > {MAX_EXECUTOR_INPUT_TOKENS:,} limit"
        )

        # Return helpful pagination suggestion
        if should_use_pagination(command):
            return {
                "success": False,
                "output": "",
                "error": generate_pagination_suggestion(command, len(raw_output)),
            }
        else:
            # For non-API commands, truncate with warning
            return {
                "success": True,
                "output": (
                    f"⚠️ Output too large to process ({estimated_tokens:,} tokens). "
                    f"Showing first 4000 characters:\n\n"
                    f"{raw_output[:4000]}\n\n"
                    f"[... truncated {len(raw_output) - 4000:,} characters]"
                ),
                "error": "",
            }

    # Output is reasonable size, send to executor AI
    context_block = ""
    if context:
        context_block = f"\nThe agent specifically needs: {context}\nPrioritize returning exactly what was requested.\n"

    executor_prompt = f"""You are a command execution assistant. You ran this command:
{command}
{context_block}
The full output is below. Your job:

1. If output is short (<100 lines) or simple: return it EXACTLY as-is
2. If output is long or complex (like API responses with many items):
   • Extract key structured data (e.g., list of titles with years)
   • Summarize: "Found X items: [list first 20]"
   • Note if there are more items not shown
   • Note any errors or warnings
   • Be concise but complete
3. When returning structured data, prefer JSON snippets over prose descriptions

The main agent needs accurate information to respond to the user.

Output:
{raw_output}"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        logger.info(
            f"Calling executor ({EXECUTOR_MODEL}) with {estimated_tokens:,} token input"
        )

        response = client.messages.create(
            model=EXECUTOR_MODEL,
            max_tokens=MAX_EXECUTOR_OUTPUT_TOKENS,
            messages=[{"role": "user", "content": executor_prompt}],
        )

        processed_output = response.content[0].text

        logger.info(
            f"Executor processed {len(raw_output):,} chars → {len(processed_output):,} chars"
        )

        return {
            "success": True,
            "output": processed_output,
            "error": "",
        }

    except anthropic.APIError as e:
        error_str = str(e).lower()
        logger.error(f"Executor API error: {e}")

        # Handle specific API errors
        if "context_length_exceeded" in error_str or "prompt is too long" in error_str:
            return {
                "success": False,
                "output": "",
                "error": (
                    "Response too large for processing. "
                    "Try using pagination or more specific queries."
                ),
            }
        elif "rate_limit" in error_str or "overloaded" in error_str:
            return {
                "success": False,
                "output": "",
                "error": "API rate limit exceeded. Please wait a moment and try again.",
            }
        else:
            return {
                "success": False,
                "output": "",
                "error": f"Processing error: {str(e)}",
            }

    except Exception as e:
        logger.error(f"Unexpected error in executor: {e}", exc_info=True)
        return {
            "success": False,
            "output": "",
            "error": f"Unexpected error: {str(e)}",
        }
