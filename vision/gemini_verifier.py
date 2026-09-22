"""
Gemini hybrid verifier for Inventory-Management-Tracking-System.

Uses Gemini as a secondary validator to refine decision confidence while
keeping YOLO as the primary real-time detector used for frontend overlays.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class GeminiHybridVerifier:
    """Asynchronous Gemini-backed validation for slot-level hints."""

    def __init__(
        self,
        config: Dict[str, Any],
        slot_ids: List[str],
        expected_items: Dict[str, str],
    ):
        self.enabled = bool(config.get("enabled", False))
        self.mode = str(config.get("mode", "live")).strip().lower()
        self.model = self._normalize_model_name(
            str(config.get("model", "models/gemini-3.1-flash-live-preview")).strip()
        )
        self.fallback_model = str(config.get("fallback_model", "")).strip()
        self.fallback_models = self._resolve_fallback_models(
            config.get("fallback_models"),
            self.fallback_model,
        )
        self.allow_generate_content_fallback = bool(
            config.get("allow_generate_content_fallback", False)
        )
        self.generate_retry_attempts = max(1, int(config.get("generate_retry_attempts", 3)))
        self.generate_retry_backoff_seconds = max(
            0.25,
            float(config.get("generate_retry_backoff_seconds", 1.0)),
        )
        self.error_cooldown_seconds = max(0.0, float(config.get("error_cooldown_seconds", 8.0)))
        self.min_interval_seconds = max(0.25, float(config.get("min_interval_seconds", 1.0)))
        self.request_timeout_seconds = max(
            1.0, float(config.get("request_timeout_seconds", 3.5))
        )
        self.max_hint_age_seconds = max(0.5, float(config.get("max_hint_age_seconds", 5.0)))
        self.trigger_confidence_threshold = float(config.get("trigger_confidence_threshold", 0.6))
        self.verify_all_frames = bool(config.get("verify_all_frames", True))
        self.verify_when_no_detections = bool(config.get("verify_when_no_detections", True))
        self.max_image_side = max(320, int(config.get("max_image_side", 960)))
        self.jpeg_quality = max(50, min(95, int(config.get("jpeg_quality", 75))))
        self.log_verbose = bool(config.get("log_verbose", False))
        self.api_key_env = str(config.get("api_key_env", "GEMINI_API_KEY")).strip()

        api_key_from_config = config.get("api_key")
        self.api_key = str(api_key_from_config).strip() if api_key_from_config else ""
        if not self.api_key:
            self.api_key = os.getenv(self.api_key_env, "").strip()

        self.slot_ids = set(slot_ids)
        self.expected_items = expected_items.copy()

        self._active = False
        self._executor: Optional[ThreadPoolExecutor] = None
        self._pending_future: Optional[Future] = None
        self._last_request_ts = 0.0
        self._last_update_ts = 0.0
        self._next_request_allowed_ts = 0.0
        self._last_latency_ms: Optional[float] = None
        self._last_backend = "none"
        self._last_error: Optional[str] = None
        self._slot_hints: Dict[str, Dict[str, Any]] = {}

        if not self.enabled:
            logger.info("Gemini hybrid verifier disabled by configuration")
            return

        if not self.api_key:
            logger.warning(
                "Gemini verifier enabled but no API key found. "
                f"Set {self.api_key_env} or provide gemini.api_key in config."
            )
            return

        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="gemini-hybrid")
        self._active = True
        logger.info("Gemini hybrid verifier initialized")

    def _normalize_model_name(self, model_name: str) -> str:
        """Normalize model names to the canonical models/... format."""
        text = str(model_name or "").strip()
        if not text:
            return "models/gemini-3.1-flash-live-preview"
        if text.startswith("models/"):
            return text
        return f"models/{text}"

    def close(self) -> None:
        """Shutdown verifier background resources."""
        self._active = False
        self._pending_future = None
        if self._executor:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None

    def _ensure_executor(self) -> bool:
        """Ensure async executor exists when verifier is active."""
        if not self._active:
            return False

        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="gemini-hybrid")
            logger.warning("Gemini verifier executor was unavailable and has been recreated")

        return True

    def get_status(self) -> Dict[str, Any]:
        """Expose runtime status for health and diagnostics."""
        age_seconds = 0.0
        if self._last_update_ts > 0:
            age_seconds = max(0.0, time.monotonic() - self._last_update_ts)

        return {
            "enabled": self.enabled,
            "active": self._active,
            "mode": self.mode,
            "model": self.model,
            "backend": self._last_backend,
            "pending_request": bool(self._pending_future and not self._pending_future.done()),
            "last_latency_ms": self._last_latency_ms,
            "last_error": self._last_error,
            "last_update_age_seconds": round(age_seconds, 3),
            "slot_hints": len(self._slot_hints),
        }

    def update(
        self,
        frame: Optional[np.ndarray],
        detections: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Refresh completed requests and schedule new verification if eligible.

        Returns the latest non-stale slot hints.
        """
        self._collect_completed_result()

        if not self._active or frame is None:
            return self._get_fresh_slot_hints()

        if not self._should_submit(detections):
            return self._get_fresh_slot_hints()

        if self._pending_future and not self._pending_future.done():
            return self._get_fresh_slot_hints()

        now = time.monotonic()
        if now < self._next_request_allowed_ts:
            return self._get_fresh_slot_hints()

        if now - self._last_request_ts < self.min_interval_seconds:
            return self._get_fresh_slot_hints()

        encoded = self._encode_frame(frame)
        if encoded is None:
            return self._get_fresh_slot_hints()

        prompt = self._build_prompt(detections)
        if not self._ensure_executor():
            return self._get_fresh_slot_hints()

        executor = self._executor
        if executor is None:
            return self._get_fresh_slot_hints()

        self._last_request_ts = now
        self._pending_future = executor.submit(self._verify_once, encoded, prompt)

        return self._get_fresh_slot_hints()

    def _collect_completed_result(self) -> None:
        future = self._pending_future
        if not future or not future.done():
            return

        self._pending_future = None

        try:
            slot_hints, backend, latency_ms = future.result()
            self._slot_hints = slot_hints
            self._last_backend = backend
            self._last_latency_ms = latency_ms
            self._last_error = None
            self._last_update_ts = time.monotonic()
        except Exception as exc:  # pragma: no cover - defensive runtime fallback
            self._last_backend = "error"
            self._last_error = str(exc)
            if self.error_cooldown_seconds > 0:
                self._next_request_allowed_ts = time.monotonic() + self.error_cooldown_seconds
            logger.warning(f"Gemini verification failed: {exc}")

    def _get_fresh_slot_hints(self) -> Dict[str, Dict[str, Any]]:
        if not self._slot_hints:
            return {}

        age = time.monotonic() - self._last_update_ts
        if age > self.max_hint_age_seconds:
            return {}

        return self._slot_hints

    def _should_submit(self, detections: List[Dict[str, Any]]) -> bool:
        if self.verify_all_frames:
            return True

        if not detections:
            return self.verify_when_no_detections

        return any(
            float(d.get("confidence", 0.0)) <= self.trigger_confidence_threshold
            for d in detections
            if d.get("slot_id")
        )

    def _encode_frame(self, frame: np.ndarray) -> Optional[bytes]:
        try:
            height, width = frame.shape[:2]
            max_dim = max(height, width)
            if max_dim > self.max_image_side:
                scale = self.max_image_side / float(max_dim)
                frame = cv2.resize(
                    frame,
                    (max(1, int(width * scale)), max(1, int(height * scale))),
                    interpolation=cv2.INTER_AREA,
                )

            ok, encoded = cv2.imencode(
                ".jpg",
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality],
            )
            if not ok:
                return None

            return encoded.tobytes()
        except Exception as exc:  # pragma: no cover - defensive runtime fallback
            logger.warning(f"Failed to encode frame for Gemini verification: {exc}")
            return None

    def _build_prompt(self, detections: List[Dict[str, Any]]) -> str:
        yolo_entries = []
        for detection in detections:
            slot_id = detection.get("slot_id")
            if not slot_id:
                continue

            yolo_entries.append(
                {
                    "slot_id": str(slot_id),
                    "item_class": str(detection.get("class_name", "unknown")).lower(),
                    "confidence": round(float(detection.get("confidence", 0.0)), 4),
                }
            )

        payload = {
            "slots": sorted(self.slot_ids),
            "expected_items": self.expected_items,
            "yolo": yolo_entries,
        }

        return (
            "You are verifying shelf-slot detections for an inventory system. "
            "Respond with strict JSON only, without markdown fences. "
            "Schema: {\"slot_hints\":[{\"slot_id\":str,\"item_class\":str,"
            "\"confidence\":float,\"agreement\":\"agree|disagree|unknown\"}]}. "
            "Use item_class=\"empty\" if the slot appears empty. "
            "Use item_class=\"unknown\" if uncertain. "
            "Confidence must be between 0 and 1. "
            f"Input={json.dumps(payload, separators=(',', ':'))}"
        )

    def _verify_once(self, frame_bytes: bytes, prompt: str) -> Tuple[Dict[str, Dict[str, Any]], str, float]:
        start = time.monotonic()

        if self.mode in {"live", "auto"}:
            try:
                slot_hints = asyncio.run(self._verify_with_live_sdk(frame_bytes, prompt))
                latency_ms = (time.monotonic() - start) * 1000.0
                return slot_hints, "live", latency_ms
            except Exception as exc_live:
                if not self.allow_generate_content_fallback:
                    raise

                logger.warning(f"Live verification failed, trying generate_content fallback: {exc_live}")

        if self.mode in {"generate", "generate_content", "auto", "live"}:
            if not self.fallback_models:
                raise RuntimeError("No generate_content fallback model configured")

            fallback_errors: List[str] = []
            for model_name in self.fallback_models:
                try:
                    slot_hints = self._verify_with_generate_content_with_retries(
                        frame_bytes,
                        prompt,
                        model_name,
                    )
                    latency_ms = (time.monotonic() - start) * 1000.0
                    return slot_hints, f"generate_content:{model_name}", latency_ms
                except Exception as exc_generate:
                    fallback_errors.append(f"{model_name}: {exc_generate}")

            raise RuntimeError("All generate_content fallbacks failed: " + " | ".join(fallback_errors))

        raise RuntimeError(f"Unsupported Gemini verifier mode: {self.mode}")

    def _verify_with_generate_content_with_retries(
        self,
        frame_bytes: bytes,
        prompt: str,
        model_name: str,
    ) -> Dict[str, Dict[str, Any]]:
        """Retry generate_content calls for retryable load/rate-limit failures."""
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.generate_retry_attempts + 1):
            try:
                return self._verify_with_generate_content(frame_bytes, prompt, model_name)
            except Exception as exc:
                last_exc = exc

                is_last_attempt = attempt >= self.generate_retry_attempts
                if is_last_attempt or not self._is_retryable_generate_error(exc):
                    raise

                backoff = self.generate_retry_backoff_seconds * attempt
                logger.warning(
                    f"Gemini generate_content retry {attempt}/{self.generate_retry_attempts} "
                    f"for model={model_name} in {backoff:.2f}s due to: {exc}"
                )
                time.sleep(backoff)

        if last_exc is None:
            raise RuntimeError("Gemini generate_content retries exhausted without error details")
        raise last_exc

    async def _verify_with_live_sdk(self, frame_bytes: bytes, prompt: str) -> Dict[str, Dict[str, Any]]:
        try:
            from google import genai
            from google.genai import types
        except Exception as exc:
            raise RuntimeError(
                "google-genai package is required for Gemini Live verification"
            ) from exc

        client = genai.Client(api_key=self.api_key)
        config = {
            "response_modalities": ["TEXT"],
            "system_instruction": {
                "parts": [
                    {
                        "text": "You validate object detections for shelf inventory tracking. "
                        "Return only strict JSON."
                    }
                ]
            },
        }

        async with client.aio.live.connect(model=self.model, config=config) as session:
            await session.send_realtime_input(
                video=types.Blob(data=frame_bytes, mime_type="image/jpeg")
            )
            await session.send_realtime_input(text=prompt)

            response_text = await asyncio.wait_for(
                self._collect_live_text_response(session),
                timeout=self.request_timeout_seconds,
            )

        return self._parse_slot_hints(response_text)

    async def _collect_live_text_response(self, session: Any) -> str:
        chunks: List[str] = []

        async for response in session.receive():
            chunks.extend(self._extract_live_text_chunks(response))

            if chunks and self._is_live_turn_complete(response):
                break

            # Stop early once a substantial text payload is present.
            if chunks and sum(len(c) for c in chunks) >= 20:
                break

        if not chunks:
            raise RuntimeError("No text returned by Gemini Live verifier")

        return "\n".join(chunks)

    def _extract_live_text_chunks(self, response: Any) -> List[str]:
        chunks: List[str] = []

        server_content = getattr(response, "server_content", None)
        if server_content is not None:
            model_turn = getattr(server_content, "model_turn", None)
            if model_turn is not None:
                for part in getattr(model_turn, "parts", []) or []:
                    text = getattr(part, "text", None)
                    if text:
                        chunks.append(str(text))

            output_transcription = getattr(server_content, "output_transcription", None)
            if output_transcription is not None:
                transcribed = getattr(output_transcription, "text", None)
                if transcribed:
                    chunks.append(str(transcribed))

        direct_text = getattr(response, "text", None)
        if direct_text:
            chunks.append(str(direct_text))

        # Deduplicate while preserving order.
        deduped: List[str] = []
        seen = set()
        for value in chunks:
            normalized = value.strip()
            if not normalized or normalized in seen:
                continue
            deduped.append(normalized)
            seen.add(normalized)

        return deduped

    def _is_live_turn_complete(self, response: Any) -> bool:
        server_content = getattr(response, "server_content", None)
        if server_content is None:
            return False

        candidates = [
            getattr(server_content, "turn_complete", None),
            getattr(server_content, "turnComplete", None),
            getattr(server_content, "generation_complete", None),
            getattr(server_content, "generationComplete", None),
        ]
        return any(value is True for value in candidates)

    def _verify_with_generate_content(
        self,
        frame_bytes: bytes,
        prompt: str,
        model_name: str,
    ) -> Dict[str, Dict[str, Any]]:
        try:
            from google import genai
            from google.genai import types
        except Exception as exc:
            raise RuntimeError(
                "google-genai package is required for Gemini verification fallback"
            ) from exc

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=[
                types.Part.from_bytes(data=frame_bytes, mime_type="image/jpeg"),
                prompt,
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )

        response_text = getattr(response, "text", None)
        if not response_text:
            raise RuntimeError("No text returned by Gemini generate_content fallback")

        return self._parse_slot_hints(str(response_text))

    def _is_retryable_generate_error(self, exc: Exception) -> bool:
        """Return True when generate_content errors are transient and worth retrying."""
        message = str(exc).lower()
        retryable_tokens = [
            "503",
            "unavailable",
            "429",
            "resource_exhausted",
            "rate limit",
            "temporarily",
            "deadline_exceeded",
            "timeout",
        ]
        return any(token in message for token in retryable_tokens)

    def _resolve_fallback_models(
        self,
        configured: Any,
        primary_fallback: str,
    ) -> List[str]:
        """Normalize fallback model configuration into a de-duplicated ordered list."""
        candidates: List[str] = []

        if isinstance(configured, list):
            for model_name in configured:
                if model_name is None:
                    continue
                text = str(model_name).strip()
                if text:
                    candidates.append(text)
        elif configured is not None:
            text = str(configured).strip()
            if text:
                candidates.extend(
                    [entry.strip() for entry in text.split(',') if entry.strip()]
                )

        if primary_fallback:
            candidates.insert(0, primary_fallback)

        ordered: List[str] = []
        for model_name in candidates:
            if model_name not in ordered:
                ordered.append(model_name)

        return ordered

    def _parse_slot_hints(self, response_text: str) -> Dict[str, Dict[str, Any]]:
        cleaned = self._extract_json_payload(response_text)
        parsed = json.loads(cleaned)

        raw_hints = parsed.get("slot_hints", parsed)
        if not isinstance(raw_hints, list):
            raise ValueError("Gemini slot_hints payload must be a list")

        slot_hints: Dict[str, Dict[str, Any]] = {}
        for row in raw_hints:
            if not isinstance(row, dict):
                continue

            slot_id = str(row.get("slot_id", "")).strip()
            if slot_id not in self.slot_ids:
                continue

            confidence = self._safe_confidence(row.get("confidence", 0.0))
            status, item_class = self._normalize_item_class(row.get("item_class"))

            agreement = str(row.get("agreement", "unknown")).strip().lower()
            if agreement not in {"agree", "disagree", "unknown"}:
                agreement = "unknown"

            hint = {
                "status": status,
                "item_class": item_class,
                "confidence": confidence,
                "agreement": agreement,
            }

            previous = slot_hints.get(slot_id)
            if previous is None or hint["confidence"] >= previous["confidence"]:
                slot_hints[slot_id] = hint

        if self.log_verbose:
            logger.debug(f"Gemini slot hints: {slot_hints}")

        return slot_hints

    def _extract_json_payload(self, raw_text: str) -> str:
        text = (raw_text or "").strip()
        if not text:
            raise ValueError("Empty Gemini response")

        if "```" in text:
            pieces = text.split("```")
            for piece in pieces:
                candidate = piece.strip()
                if not candidate:
                    continue
                if candidate.lower().startswith("json"):
                    candidate = candidate[4:].strip()
                if candidate.startswith("{") or candidate.startswith("["):
                    text = candidate
                    break

        first_obj = text.find("{")
        last_obj = text.rfind("}")
        if first_obj != -1 and last_obj != -1 and last_obj > first_obj:
            return text[first_obj:last_obj + 1]

        first_arr = text.find("[")
        last_arr = text.rfind("]")
        if first_arr != -1 and last_arr != -1 and last_arr > first_arr:
            return "{\"slot_hints\":" + text[first_arr:last_arr + 1] + "}"

        raise ValueError("Unable to locate JSON payload in Gemini response")

    def _safe_confidence(self, value: Any) -> float:
        try:
            conf = float(value)
        except (TypeError, ValueError):
            return 0.0

        if conf < 0.0:
            return 0.0
        if conf > 1.0:
            return 1.0
        return conf

    def _normalize_item_class(self, value: Any) -> Tuple[str, Optional[str]]:
        text = str(value or "").strip().lower()

        if text in {"", "none", "null", "empty", "vacant"}:
            return "empty", None

        if text in {"unknown", "uncertain", "n/a", "na"}:
            return "unknown", None

        return "item", text
