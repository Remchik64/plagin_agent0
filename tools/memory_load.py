from helpers.tool import Tool, Response
import httpx
import os

PI_SERVER = os.environ.get("PI_SERVER", "http://host.docker.internal:7860")
DEFAULT_THRESHOLD = 0.4


class MemoryLoad(Tool):
    async def execute(self, query="", threshold=DEFAULT_THRESHOLD, limit=10, filter="", **kwargs):
        if not query:
            return Response(message="No query provided.", break_loop=False)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{PI_SERVER}/api/v1/memory/search",
                    params={"query": query, "limit": limit, "session_id": "agent_zero"}
                )
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if not results:
                        result = f"No memories found for: {query}"
                    else:
                        lines = [
                            f"[{i+1}] (score={r.get('score', 0):.2f}) {r.get('text', '')}"
                            for i, r in enumerate(results)
                            if r.get('score', 0) >= float(threshold)
                        ]
                        result = "\n\n".join(lines) if lines else f"No memories above threshold {threshold}"
                else:
                    result = f"PI server error: {resp.status_code}"
        except Exception as e:
            result = f"Pure Intellect unavailable: {e}"
        return Response(message=result, break_loop=False)
