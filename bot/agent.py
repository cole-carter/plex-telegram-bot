"""Claude AI agent integration with tool support."""

import anthropic
import logging
from typing import List, Dict, Any, Callable
from bot.config import ANTHROPIC_API_KEY, ORCHESTRATOR_MODEL, AGENT_MD_PATH, SOUL_MD_PATH, MEMORY_MD_PATH
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
            "sonarr-find, radarr-find, sonarr-missing, qbt-status (helper scripts), "
            "and standard Unix commands (ls, find, mv, cp, mkdir, cat, grep, head, tail, file, du, df, stat). "
            "NEVER use rm - use recycle-bin instead. "
            "NEVER access .env or secret files. "
            "IMPORTANT: After any POST/PUT/DELETE, make a follow-up GET to verify the change took effect."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                },
                "raw": {
                    "type": "boolean",
                    "description": (
                        "If true, return command output directly without executor processing. "
                        "Use when you've already filtered output (jq, grep, head) and expect a small result."
                    ),
                },
                "context": {
                    "type": "string",
                    "description": (
                        "Tell the executor what you need from this output. "
                        "E.g. 'I need the series ID and title for Fresh Off the Boat' or "
                        "'Return just the episode IDs for missing episodes'. "
                        "Only used when raw is false (default)."
                    ),
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_docs",
        "description": (
            "Read your documentation files. "
            "Available: REFERENCE.md (API docs), MEMORY.md (your knowledge), "
            "TASKS.md (active task state), SOUL.md (your personality). "
            "Also: skills/<name>.md — your skill docs with tested patterns and workflows. "
            "See the 'Your Skills' section in your prompt for available skills."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file": {
                    "type": "string",
                    "description": "Which file to read (e.g. 'REFERENCE.md', 'skills/sonarr.md')",
                }
            },
            "required": ["file"],
        },
    },
    {
        "name": "update_docs",
        "description": (
            "Write to your documentation files. "
            "MEMORY.md: permanent facts and user preferences. "
            "TASKS.md: active task progress. "
            "SOUL.md: your personality and tone. "
            "skills/<name>.md: update or create skill docs with tested patterns."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file": {
                    "type": "string",
                    "description": "Which file to update (e.g. 'MEMORY.md', 'skills/sonarr.md')",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write",
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


class BlackbeardAgent:
    """Blackbeard - AI agent for managing a media server through Telegram."""

    def __init__(self):
        """Initialize the agent with Claude API client."""
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = ORCHESTRATOR_MODEL

        # Load AGENT.md system instructions
        if AGENT_MD_PATH.exists():
            system_instructions = AGENT_MD_PATH.read_text()
        else:
            raise FileNotFoundError(f"AGENT.md not found at {AGENT_MD_PATH}")

        # Append SOUL.md for personality
        if SOUL_MD_PATH.exists():
            soul_content = SOUL_MD_PATH.read_text().strip()
            if soul_content and len(soul_content) > 50:
                system_instructions += "\n\n" + soul_content

        # Inject available skills (progressive disclosure — names and descriptions only)
        from bot.tools.docs_manager import list_skills
        skills = list_skills()
        if skills:
            skills_list = "\n".join(
                f"- `{s['filename']}`: {s['description']}"
                for s in skills
            )
            system_instructions += (
                "\n\n## Your Skills\n\n"
                "You have skill docs with tested patterns and workflows. "
                "Load one with `read_docs` when starting a relevant task:\n"
                f"{skills_list}\n\n"
                "You can also update skills or create new ones with `update_docs` "
                "when you discover useful patterns."
            )

        # Append MEMORY.md (lean — should contain only short facts and preferences)
        if MEMORY_MD_PATH.exists():
            memory_content = MEMORY_MD_PATH.read_text().strip()
            # Only inject if there's real content beyond the header
            header_only = memory_content.strip().startswith("# ") and memory_content.count("\n") < 5
            if memory_content and not header_only:
                system_instructions += "\n\n## Your Memory\n\n" + memory_content

        self.system_instructions = system_instructions

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
            raw = tool_input.get("raw", False)
            context = tool_input.get("context", "")
            logger.info(f"Tool: execute_command({tool_input['command']}, raw={raw})")
            result = execute_command(tool_input["command"], raw=raw, context=context)
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

    def _format_tool_description(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Generate a user-friendly description of a tool call."""
        if tool_name == "execute_command":
            cmd = tool_input.get("command", "")
            # Parse common command patterns for better descriptions
            if cmd.startswith("api-call"):
                parts = cmd.split()
                if len(parts) >= 3:
                    service = parts[1]
                    endpoint = parts[3] if len(parts) > 3 else ""
                    return f"Calling {service.upper()} API{f': {endpoint}' if endpoint else ''}"
            return f"Running: {cmd[:50]}"
        elif tool_name == "read_docs":
            return f"Reading {tool_input.get('file', 'documentation')}"
        elif tool_name == "update_docs":
            return f"Updating {tool_input.get('file', 'documentation')}"
        return f"Using {tool_name}"

    def process_message(self, user_message: str, conversation_history=None, max_turns: int = 20, interrupt_flag=None, progress_callback=None) -> Dict[str, Any]:
        """
        Process a user message and return the agent's response with tool log.

        Args:
            user_message: The message from the user
            conversation_history: List of previous messages in this conversation
            max_turns: Maximum number of agent turns (API calls) to prevent infinite loops
            interrupt_flag: Callable that returns True if processing should be interrupted
            progress_callback: Optional callback(description, summary, completed) for progress updates

        Returns:
            Dict with "response" (str) and "tool_log" (list of tool interactions)
        """
        # Start with conversation history, then add current message
        messages = list(conversation_history) if conversation_history else []
        messages.append({"role": "user", "content": user_message})

        turn_count = 0
        tool_log = []  # Track tool interactions for conversation history

        def _make_result(text: str) -> Dict[str, Any]:
            return {"response": text, "tool_log": tool_log}

        while turn_count < max_turns:
            # Check for interrupt
            if interrupt_flag and interrupt_flag():
                logger.info("Agent interrupted by user")
                return _make_result("⏹️ Task interrupted by user.")

            turn_count += 1
            logger.info(f"Agent turn {turn_count}/{max_turns}")

            # Inject turn counter into system prompt
            system_with_turn = f"[Turn {turn_count}/{max_turns}]\n\n{self.system_instructions}"

            # Save-state checkpoints every 10 turns
            if turn_count % 10 == 0 and turn_count < max_turns:
                messages.append({
                    "role": "user",
                    "content": (
                        f"[SYSTEM: Checkpoint — turn {turn_count}/{max_turns}. "
                        "Update TASKS.md with current progress, then continue working.]"
                    ),
                })

            # Wind-down warning 2 turns before limit
            if turn_count == max_turns - 2:
                messages.append({
                    "role": "user",
                    "content": (
                        f"[SYSTEM: 2 turns remaining. Wrap up now — update TASKS.md with progress "
                        "and give the user a final summary of what you completed and what remains.]"
                    ),
                })

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=system_with_turn,
                tools=TOOLS,
                messages=messages,
            )

            # Check for interrupt after API call
            if interrupt_flag and interrupt_flag():
                return _make_result("⏹️ Task interrupted by user.")

            # Check stop reason
            if response.stop_reason in ("end_turn", "max_tokens"):
                # Agent is done (or hit output limit — return what we have)
                final_text = ""
                for block in response.content:
                    if block.type == "text":
                        final_text += block.text
                if response.stop_reason == "max_tokens":
                    logger.warning("Response truncated by max_tokens limit")
                logger.info(f"Agent finished: {final_text[:100]}...")
                return _make_result(final_text or "Done.")

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
                            return _make_result("⏹️ Task interrupted by user.")

                        tool_name = block.name
                        tool_input = block.input

                        # Notify progress callback that tool is starting
                        if progress_callback:
                            description = self._format_tool_description(tool_name, tool_input)
                            progress_callback(description, summary=None, completed=False)

                        # Execute the tool
                        result = self._execute_tool(tool_name, tool_input)

                        # Format result for Claude
                        if result.get("success"):
                            content = result.get("output") or result.get("content") or result.get("message", "")
                        else:
                            content = f"Error: {result.get('error', 'Unknown error')}"

                        # Build compact summary for tool log and progress message
                        summary = content[:200] if len(content) > 200 else content

                        # Record in tool log for conversation history
                        tool_log.append({
                            "tool": tool_name,
                            "input": tool_input.get("command", "") if tool_name == "execute_command" else tool_input.get("file", ""),
                            "summary": summary,
                        })

                        # Notify progress callback with summary
                        if progress_callback:
                            description = self._format_tool_description(tool_name, tool_input)
                            progress_callback(description, summary=summary, completed=True)

                        # Executor already processed output, no truncation needed
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
                return _make_result(f"Unexpected stop reason: {response.stop_reason}")

        logger.warning(f"Max turns ({max_turns}) reached without completion")
        return _make_result(f"Reached maximum of {max_turns} steps. Task incomplete - consider breaking into smaller subtasks.")


def create_agent() -> BlackbeardAgent:
    """Factory function to create a new agent instance."""
    return BlackbeardAgent()
