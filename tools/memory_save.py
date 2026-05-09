from helpers.tool import Tool, Response
import httpx
import os

class MemorySave(Tool):
    async def execute(self, text="", area="", **kwargs):
        if not text:
            return Response(message="No text to save.", break_loop=False)
        if not area:
            area = "main"

        # Dynamically read environment variables to avoid update issues
        pi_server = os.environ.get("PI_SERVER", "http://host.docker.internal:7860")
        session_id = os.environ.get("PI_SESSION_ID", "agent_zero")

        importance_map = {"main": 0.7, "solutions": 0.9, "fragments": 0.5}
        importance = importance_map.get(area, 0.7)
        is_anchor = area == "solutions"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{pi_server}/api/v1/memory/fact",
                    json={
                        "text": text,
                        "importance": importance,
                        "is_anchor": is_anchor,
                        "session_id": session_id,
                        "metadata": {"area": area}
                    }
                )
                if resp.status_code == 200:
                    result = f"Memory saved to Pure Intellect (area={area}, session={session_id})"
                else:
                    result = f"PI server error: {resp.status_code}"
        except Exception as e:
            result = f"Pure Intellect unavailable: {e}"

        return Response(message=result, break_loop=False)
