"""Pure Intellect — синхронизация конфига при старте монолога.

При каждом новом сообщении читает актуальный конфиг с PI сервера
и обновляет переменные окружения для плагина.
"""
import os
import httpx
from python.helpers.extension import Extension
from agent import LoopData


class PIConfigSync(Extension):
    """Синхронизирует конфиг плагина с PI сервером при старте монолога."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        """Читает конфиг с PI сервера и сохраняет в env."""
        pi_server = os.environ.get("PI_SERVER", "http://host.docker.internal:7860")

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{pi_server}/api/v1/az-plugin/config")
                if resp.status_code == 200:
                    config = resp.json()
                    # Сохраняем utility_model в env для использования другими частями плагина
                    utility_model = config.get("utility_model", "qwen3.5:9b")
                    os.environ["PI_UTILITY_MODEL"] = utility_model
                    os.environ["PI_SERVER"] = config.get("pi_server", pi_server)
                    os.environ["PI_SESSION_ID"] = config.get("session_id", "agent_zero")
                    self.agent.context.log.log(
                        type="info",
                        content=f"[PI Sync] Config loaded: utility_model={utility_model}",
                    )
        except Exception as e:
            # Не прерываем работу AZ если PI недоступен
            self.agent.context.log.log(
                type="warning",
                content=f"[PI Sync] Could not sync config from {pi_server}: {e}",
            )
