import asyncio
import os
import httpx
from helpers.extension import Extension
from agent import LoopData
from helpers import log

RECALL_TIMEOUT = 15
DEFAULT_THRESHOLD = 0.4
DEFAULT_LIMIT = 5


async def search_pi(pi_server: str, session_id: str, query: str, limit: int = DEFAULT_LIMIT, threshold: float = DEFAULT_THRESHOLD) -> list:
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                f"{pi_server}/api/v1/memory/search",
                params={"query": query, "limit": limit, "session_id": session_id}
            )
            if r.status_code == 200:
                return [
                    item for item in r.json().get("results", [])
                    if item.get("score", 0) >= threshold
                ]
    except Exception:
        pass
    return []


class PIRecall(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent:
            return

        # Only recall on first iteration
        if loop_data.iteration != 0:
            return

        user_msg = loop_data.user_message.output_text() if loop_data.user_message else ""
        if not user_msg or len(user_msg) < 3:
            return

        # Read config from env (updated by _10_pi_sync on each monologue start)
        pi_server = os.environ.get("PI_SERVER", "http://host.docker.internal:7860")
        session_id = os.environ.get("PI_SESSION_ID", "agent_zero")
        threshold = float(os.environ.get("PI_RECALL_THRESHOLD", str(DEFAULT_THRESHOLD)))
        limit = int(os.environ.get("PI_RECALL_LIMIT", str(DEFAULT_LIMIT)))

        log_item = self.agent.context.log.log(
            type="util",
            heading="Searching Pure Intellect memory...",
        )

        try:
            results = await asyncio.wait_for(
                search_pi(pi_server, session_id, user_msg, limit=limit, threshold=threshold),
                timeout=RECALL_TIMEOUT
            )
        except asyncio.TimeoutError:
            log_item.update(heading="PI memory search timed out")
            return

        if not results:
            log_item.update(heading="No relevant memories found in PI")
            return

        memories_txt = "\n".join([f"- {r.get('text', '')}" for r in results])
        log_item.update(
            heading=f"{len(results)} memories found in Pure Intellect",
            memories=memories_txt
        )

        # Inject into extras so it appears in system prompt
        extras = loop_data.extras_persistent
        extras["memories"] = self.agent.parse_prompt(
            "agent.system.memories.md", memories=memories_txt
        ) if hasattr(self.agent, 'parse_prompt') else f"\n## Relevant memories:\n{memories_txt}\n"
