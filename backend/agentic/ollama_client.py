"""
Async Ollama HTTP Client — Handles all communication with the local Ollama instance.

Features:
- Async HTTP via httpx (already available via FastAPI dependency)
- Connection pooling with persistent client
- Health check endpoint
- Graceful timeout handling
- Structured error responses (never raises to caller)
- Support for generate, chat, and embed endpoints

100% local. No cloud APIs.
"""

import json
import time
import asyncio
from typing import Any, Dict, List, Optional, Union

import httpx

from .agent_config import get_agentic_config, AgenticConfig

# ── Logger Setup ─────────────────────────────────────────────────────────────
try:
    from backend.core.logging import get_logger
    logger = get_logger("backend.agentic.ollama_client")
except ImportError:
    import logging
    logger = logging.getLogger("agentic.ollama_client")


# ══════════════════════════════════════════════════════════════════════════════
# OLLAMA CLIENT
# ══════════════════════════════════════════════════════════════════════════════

class OllamaClient:
    """
    Async HTTP client for the local Ollama API.

    Usage:
        client = OllamaClient()
        text = await client.generate("deepseek-r1", "Explain async/await")
        embedding = await client.embed("nomic-embed-text", "Hello world")
        available = await client.is_available()
    """

    def __init__(self, config: Optional[AgenticConfig] = None):
        self._config = config or get_agentic_config()
        self._client: Optional[httpx.AsyncClient] = None
        self._available: Optional[bool] = None
        self._last_health_check: float = 0.0
        self._health_check_ttl: float = 30.0  # Cache health status for 30s

    @property
    def base_url(self) -> str:
        return self._config.ollama_base_url.rstrip("/")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the persistent async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(
                    connect=5.0,
                    read=self._config.timeout_seconds,
                    write=10.0,
                    pool=5.0,
                ),
                limits=httpx.Limits(
                    max_connections=10,
                    max_keepalive_connections=5,
                ),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client and release connections."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ── Health Check ─────────────────────────────────────────────────────────

    async def is_available(self) -> bool:
        """
        Check if Ollama is reachable and responding.

        Caches the result for 30 seconds to avoid hammering the health endpoint.
        """
        now = time.time()
        if (now - self._last_health_check) < self._health_check_ttl and self._available is not None:
            return self._available

        try:
            client = await self._get_client()
            response = await client.get(
                "/api/tags",
                timeout=self._config.health_check_timeout,
            )
            self._available = response.status_code == 200
            self._last_health_check = now
            if self._available:
                logger.debug("ollama_health_check", status="available")
            else:
                logger.warning("ollama_health_check", status="unhealthy", code=response.status_code)
        except (httpx.ConnectError, httpx.TimeoutException, OSError) as e:
            self._available = False
            self._last_health_check = now
            logger.warning("ollama_health_check", status="unavailable", error=str(e))
        except Exception as e:
            self._available = False
            self._last_health_check = now
            logger.error("ollama_health_check", status="error", error=str(e))

        return self._available

    async def list_models(self) -> List[str]:
        """List available models on the Ollama instance."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error("ollama_list_models_failed", error=str(e))
        return []

    # ── Generate (Completion) ────────────────────────────────────────────────

    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 1024,
        timeout: Optional[float] = None,
    ) -> Optional[str]:
        """
        Generate a completion using Ollama's /api/generate endpoint.

        Args:
            model: Model name (e.g., "deepseek-r1", "llama3")
            prompt: The user prompt
            system: Optional system message
            temperature: Generation temperature (default from config)
            max_tokens: Maximum tokens to generate
            timeout: Custom timeout (default from config)

        Returns:
            Generated text string, or None if the request failed.
        """
        if temperature is None:
            temperature = self._config.temperature

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        effective_timeout = timeout or self._config.timeout_seconds

        try:
            client = await self._get_client()
            start = time.time()

            response = await client.post(
                "/api/generate",
                json=payload,
                timeout=effective_timeout,
            )

            elapsed = time.time() - start

            if response.status_code == 200:
                data = response.json()
                text = data.get("response", "").strip()
                logger.info(
                    "ollama_generate_success",
                    model=model,
                    elapsed_s=round(elapsed, 2),
                    prompt_len=len(prompt),
                    response_len=len(text),
                )
                return text
            else:
                logger.error(
                    "ollama_generate_failed",
                    model=model,
                    status=response.status_code,
                    body=response.text[:200],
                )
                return None

        except httpx.TimeoutException:
            logger.warning(
                "ollama_generate_timeout",
                model=model,
                timeout_s=effective_timeout,
            )
            return None
        except (httpx.ConnectError, OSError) as e:
            logger.warning("ollama_generate_connection_error", model=model, error=str(e))
            self._available = False
            return None
        except Exception as e:
            logger.error("ollama_generate_unexpected_error", model=model, error=str(e))
            return None

    # ── Chat (Multi-turn) ────────────────────────────────────────────────────

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 512,
        timeout: Optional[float] = None,
    ) -> Optional[str]:
        """
        Multi-turn chat using Ollama's /api/chat endpoint.

        Args:
            model: Model name (e.g., "llama3")
            messages: List of {"role": "user"|"assistant", "content": "..."}
            system: Optional system message (prepended as system role)
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            timeout: Custom timeout

        Returns:
            Assistant's response text, or None if failed.
        """
        if temperature is None:
            temperature = self._config.chat_temperature

        # Build message list with optional system
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        payload: Dict[str, Any] = {
            "model": model,
            "messages": full_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        effective_timeout = timeout or self._config.timeout_seconds

        try:
            client = await self._get_client()
            start = time.time()

            response = await client.post(
                "/api/chat",
                json=payload,
                timeout=effective_timeout,
            )

            elapsed = time.time() - start

            if response.status_code == 200:
                data = response.json()
                text = data.get("message", {}).get("content", "").strip()
                logger.info(
                    "ollama_chat_success",
                    model=model,
                    elapsed_s=round(elapsed, 2),
                    messages_count=len(full_messages),
                    response_len=len(text),
                )
                return text
            else:
                logger.error(
                    "ollama_chat_failed",
                    model=model,
                    status=response.status_code,
                    body=response.text[:200],
                )
                return None

        except httpx.TimeoutException:
            logger.warning("ollama_chat_timeout", model=model, timeout_s=effective_timeout)
            return None
        except (httpx.ConnectError, OSError) as e:
            logger.warning("ollama_chat_connection_error", model=model, error=str(e))
            self._available = False
            return None
        except Exception as e:
            logger.error("ollama_chat_unexpected_error", model=model, error=str(e))
            return None

    # ── Embed ────────────────────────────────────────────────────────────────

    async def embed(
        self,
        model: str,
        text: Union[str, List[str]],
        timeout: Optional[float] = None,
    ) -> Optional[List[float]]:
        """
        Generate embeddings using Ollama's /api/embed endpoint.

        Args:
            model: Embedding model name (e.g., "nomic-embed-text")
            text: Text string or list of strings to embed
            timeout: Custom timeout

        Returns:
            Embedding vector as list of floats, or None if failed.
            For batch input, returns the first embedding.
        """
        # Normalize input
        if isinstance(text, str):
            input_text = text
        else:
            input_text = text[0] if text else ""

        if not input_text.strip():
            return None

        payload: Dict[str, Any] = {
            "model": model,
            "input": input_text,
        }

        effective_timeout = timeout or self._config.embed_timeout_seconds

        try:
            client = await self._get_client()
            start = time.time()

            response = await client.post(
                "/api/embed",
                json=payload,
                timeout=effective_timeout,
            )

            elapsed = time.time() - start

            if response.status_code == 200:
                data = response.json()
                # Ollama returns {"embeddings": [[...], ...]} for /api/embed
                embeddings = data.get("embeddings", [])
                if embeddings and len(embeddings) > 0:
                    logger.debug(
                        "ollama_embed_success",
                        model=model,
                        elapsed_s=round(elapsed, 2),
                        dim=len(embeddings[0]),
                    )
                    return embeddings[0]
                # Fallback: some older Ollama versions use "embedding" key
                embedding = data.get("embedding", [])
                if embedding:
                    return embedding
                logger.warning("ollama_embed_empty", model=model, data_keys=list(data.keys()))
                return None
            else:
                logger.error(
                    "ollama_embed_failed",
                    model=model,
                    status=response.status_code,
                    body=response.text[:200],
                )
                return None

        except httpx.TimeoutException:
            logger.warning("ollama_embed_timeout", model=model, timeout_s=effective_timeout)
            return None
        except (httpx.ConnectError, OSError) as e:
            logger.warning("ollama_embed_connection_error", model=model, error=str(e))
            self._available = False
            return None
        except Exception as e:
            logger.error("ollama_embed_unexpected_error", model=model, error=str(e))
            return None

    # ── Batch Embed ──────────────────────────────────────────────────────────

    async def embed_batch(
        self,
        model: str,
        texts: List[str],
        timeout: Optional[float] = None,
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts concurrently.

        Args:
            model: Embedding model name
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (None for failed items)
        """
        tasks = [self.embed(model, text, timeout=timeout) for text in texts]
        return await asyncio.gather(*tasks)


# ══════════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL SINGLETON
# ══════════════════════════════════════════════════════════════════════════════

_client_instance: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get or create the global OllamaClient singleton."""
    global _client_instance
    if _client_instance is None:
        _client_instance = OllamaClient()
    return _client_instance


async def shutdown_ollama_client() -> None:
    """Shutdown the global client — call on app shutdown."""
    global _client_instance
    if _client_instance:
        await _client_instance.close()
        _client_instance = None
