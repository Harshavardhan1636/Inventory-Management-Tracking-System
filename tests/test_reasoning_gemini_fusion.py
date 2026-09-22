"""
Reasoning fusion regression tests for YOLO + Gemini hybrid logic.
"""

from reasoning.reasoning_engine import ReasoningEngine


def _engine_with_gemini_fusion():
    return ReasoningEngine(
        slot_ids=["SLOT_0_0"],
        expected_items={"SLOT_0_0": "bottle"},
        config={
            "temporal_window": 10,
            "short_absence_threshold": 2,
            "removal_threshold": 5,
            "confidence_threshold": 0.65,
            "gemini_fusion": {
                "enabled": True,
                "agreement_weight": 0.3,
                "conflict_confidence_threshold": 0.75,
                "conflict_penalty": 0.5,
                "inject_min_confidence": 0.7,
                "inject_confidence_scale": 0.9,
            },
        },
    )


def test_gemini_hint_can_inject_presence_when_yolo_misses_slot():
    """High-confidence Gemini item hints should still drive temporal reasoning."""
    engine = _engine_with_gemini_fusion()

    all_events = []
    for _ in range(4):
        events = engine.process_detections(
            [],
            gemini_slot_hints={
                "SLOT_0_0": {
                    "status": "item",
                    "item_class": "bottle",
                    "confidence": 0.95,
                }
            },
        )
        all_events.extend(events)

    assert any(event.event_type.value == "item_added" for event in all_events)


def test_gemini_conflict_penalizes_yolo_confidence_before_buffering():
    """Conflicting high-confidence Gemini hints should reduce fused confidence."""
    engine = _engine_with_gemini_fusion()

    engine.process_detections(
        [
            {
                "slot_id": "SLOT_0_0",
                "class_name": "bottle",
                "confidence": 0.92,
                "fused_confidence": 0.92,
            }
        ],
        gemini_slot_hints={
            "SLOT_0_0": {
                "status": "empty",
                "item_class": None,
                "confidence": 0.95,
            }
        },
    )

    recent = engine.buffer.get_most_recent("SLOT_0_0")
    assert recent is not None
    assert recent.item_class == "bottle"
    assert recent.confidence < 0.92


def test_gemini_unknown_hint_does_not_override_default_empty_fallback():
    """Unknown Gemini hints should not inject unreliable slot states."""
    engine = _engine_with_gemini_fusion()

    engine.process_detections(
        [],
        gemini_slot_hints={
            "SLOT_0_0": {
                "status": "unknown",
                "item_class": None,
                "confidence": 0.95,
            }
        },
    )

    recent = engine.buffer.get_most_recent("SLOT_0_0")
    assert recent is not None
    assert recent.item_class is None
    assert recent.confidence == 0.9


def test_expected_item_alignment_allows_hybrid_override():
    """When Gemini strongly matches expected item, it can correct conflicting YOLO class."""
    engine = _engine_with_gemini_fusion()

    engine.set_expected_item("SLOT_0_0", "bottle")
    engine.process_detections(
        [
            {
                "slot_id": "SLOT_0_0",
                "class_name": "cup",
                "confidence": 0.86,
                "fused_confidence": 0.86,
            }
        ],
        gemini_slot_hints={
            "SLOT_0_0": {
                "status": "item",
                "item_class": "bottle",
                "confidence": 0.95,
            }
        },
    )

    recent = engine.buffer.get_most_recent("SLOT_0_0")
    assert recent is not None
    assert recent.item_class == "bottle"
    assert recent.confidence > 0.8
