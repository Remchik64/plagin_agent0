import os
import asyncio
import httpx
from helpers.extension import Extension
from agent import LoopData

MIN_LENGTH = 20  # Don't save very short responses


class PIMemorize(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent:
            return

        # Read config from env (updated by _10_pi_sync on each monologue start)
        pi_server = os.environ.get("PI_SERVER", "http://host.docker.internal:7860")
        session_id = os.environ.get("PI_SESSION_ID", "agent_zero")
        memorize_enabled = os.environ.get("PI_MEMORIZE_ENABLED", "true").lower() == "true"

        if not memorize_enabled:
            return

        # Get the agent's last response
        response = ""
        if loop_data.last_response:
            response = str(loop_data.last_response)[:500]
        elif hasattr(loop_data, 'assistant_response'):
            response = str(loop_data.assistant_response)[:500]

        user_msg = loop_data.user_message.output_text() if loop_data.user_message else ""

        if not response or len(response) < MIN_LENGTH:
            return

        # Save conversation fragment to PI in background (fire and forget)
        asyncio.ensure_future(self._save_to_pi(pi_server, session_id, user_msg, response))

    async def _save_to_pi(self, pi_server: str, session_id: str, user_msg: str, response: str):
        try:
            fragment = f"Q: {user_msg[:200]}\nA: {response[:300]}" if user_msg else response[:400]
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{pi_server}/api/v1/memory/fact",
                    json={
                        "text": fragment,
                        "importance": 0.5,
                        "is_anchor": False,
                        "session_id": session_id,
                        "metadata": {"area": "fragments", "source": "auto"}
                    }
                )
        except Exception:
            pass  # Silent fail - memorization is best-effort
