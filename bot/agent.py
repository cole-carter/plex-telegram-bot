"""Claude AI agent integration with tool support."""

import anthropic
import logging
from typing import List, Dict, Any, Callable
from bot.config import ANTHROPIC_API_KEY, DEFAULT_MODEL, CLAUDE_MD_PATH
from bot.tools.command_executor import execute_command
from bot.tools.docs_manager import read_docs, update_docs

logger = logging.getLogger(__name__)


# Tool definitions for Claude
TOOLS = [
    {
        "name": "execute_command",
        "description": (
            "Execute a shell command on the server. "
            "You have access to: api-call (for service APIs), recycle-bin (safe deletion), "
            "and standard Unix commands (ls, find, mv, cp, mkdir, cat, grep, head, tail, file, du, df, stat). "
            "NEVER use rm - use recycle-bin instead. "
            "NEVER access .env or secret files."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                }
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_docs",
        "description": (
            "Read your documentation files to recall learnings and patterns. "
            "Available files: MEMORY.md (system info), LEARNINGS.md (experience), "
            "API_REFERENCE.md (extended API docs)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file": {
                    "type": "string",
                    "enum": ["MEMORY.md", "LEARNINGS.md", "API_REFERENCE.md"],
                    "description": "Which documentation file to read",
                }
            },
            "required": ["file"],
        },
    },
    {
        "name": "update_docs",
        "description": (
            "Update your documentation files to remember things for future conversations. "
            "Use this to record learnings, API patterns, or system-specific information."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file": {
                    "type": "string",
                    "enum": ["MEMORY.md", "LEARNINGS.md", "API_REFERENCE.md"],
                    "description": "Which documentation file to update",
                },
                "content": {
                    "type": "string",
                    "description": "Content to add to the file",
                },
                "mode": {
                    "type": "string",
                    "enum": ["append", "replace"],
                    "description": "Whether to append to or replace the file content (default: append)",
                },
            },
            "required": ["file", "content"],
        },
    },
]


class PlexAgent:
    """AI agent for managing Plex media server through Telegram."""

    def __init__(self):
        """Initialize the agent with Claude API client."""
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = DEFAULT_MODEL

        # Load CLAUDE.md system instructions
        if CLAUDE_MD_PATH.exists():
            self.system_instructions = CLAUDE_MD_PATH.read_text()
        else:
            raise FileNotFoundError(f"CLAUDE.md not found at {CLAUDE_MD_PATH}")

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Tool input parameters

        Returns:
            Tool execution result
        """
        # Log tool execution
        if tool_name == "execute_command":
            logger.info(f"Tool: execute_command({tool_input['command']})")
            result = execute_command(tool_input["command"])
        elif tool_name == "read_docs":
            logger.info(f"Tool: read_docs({tool_input['file']})")
            result = read_docs(tool_input["file"])
        elif tool_name == "update_docs":
            mode = tool_input.get("mode", "append")
            logger.info(f"Tool: update_docs({tool_input['file']}, mode={mode})")
            result = update_docs(tool_input["file"], tool_input["content"], mode)
        else:
            logger.warning(f"Tool: Unknown tool '{tool_name}'")
            result = {"success": False, "error": f"Unknown tool: {tool_name}"}

        # Log result
        if result.get("success"):
            output = result.get("output") or result.get("content") or result.get("message", "")
            logger.info(f"Tool result: Success - {output[:100]}...")
        else:
            logger.error(f"Tool result: Error - {result.get('error', 'Unknown error')}")

        return result

    def process_message(self, user_message: str, conversation_history=None, max_turns: int = 5, interrupt_flag=None) -> str:
        """
        Process a user message and return the agent's response.

        Args:
            user_message: The message from the user
            conversation_history: List of previous messages in this conversation
            max_turns: Maximum number of agent turns (API calls) to prevent infinite loops
            interrupt_flag: Callable that returns True if processing should be interrupted

        Returns:
            The agent's final response
        """
        # Start with conversation history, then add current message
        messages = list(conversation_history) if conversation_history else []
        messages.append({"role": "user", "content": user_message})

        turn_count = 0

        while turn_count < max_turns:
            # Check for interrupt
            if interrupt_flag and interrupt_flag():
                logger.info("Agent interrupted by user")
                return "⏹️ Task interrupted by user."

            turn_count += 1
            logger.info(f"Agent turn {turn_count}/{max_turns}")

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_instructions,
                tools=TOOLS,
                messages=messages,
            )

            # Check for interrupt after API call
            if interrupt_flag and interrupt_flag():
                return "⏹️ Task interrupted by user."

            # Check stop reason
            if response.stop_reason == "end_turn":
                # Agent is done, extract final response
                final_text = ""
                for block in response.content:
                    if block.type == "text":
                        final_text += block.text
                logger.info(f"Agent finished: {final_text[:100]}...")
                return final_text or "Done."

            elif response.stop_reason == "tool_use":
                # Agent wants to use tools
                # Add assistant response to messages
                messages.append({"role": "assistant", "content": response.content})

                # Execute each tool call
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        # Check for interrupt before tool execution
                        if interrupt_flag and interrupt_flag():
                            return "⏹️ Task interrupted by user."

                        tool_name = block.name
                        tool_input = block.input

                        # Execute the tool
                        result = self._execute_tool(tool_name, tool_input)

                        # Format result for Claude
                        if result.get("success"):
                            content = result.get("output") or result.get("content") or result.get("message", "")
                        else:
                            content = f"Error: {result.get('error', 'Unknown error')}"

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": content,
                            }
                        )

                # Add tool results to messages
                messages.append({"role": "user", "content": tool_results})

            else:
                # Unexpected stop reason
                return f"Unexpected stop reason: {response.stop_reason}"

        logger.warning(f"Max turns ({max_turns}) reached without completion")
        return "Max turns reached. Task may be too complex."


def create_agent() -> PlexAgent:
    """Factory function to create a new agent instance."""
    return PlexAgent()
