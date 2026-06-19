#!/usr/bin/env python3
"""Artic risk/readiness contract helpers.

The functions in this module are intentionally pure and deterministic: no IO, no
network access, and no clock reads. They turn early Artic answers/intent into a
machine-readable readiness contract that distinguishes strategy/preview from
final implementation readiness.
"""
from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "artic-risk-readiness-v1"

CORE_FIELDS = ("project", "audience", "goal", "vibe")

_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "core_visual_asset_dependency": (
        "image", "photo", "product photo", "3d model", "video", "illustration", "person", "place",
        "제품 사진", "이미지", "3d", "석고상", "영상", "일러스트", "사진",
    ),
    "interaction_dependency": (
        "drag", "edit", "game", "map", "realtime preview", "real-time preview", "canvas", "webgl",
        "마우스로", "드래그", "편집", "지도", "실시간", "캔버스",
    ),
    "brand_dependency": (
        "logo", "colors", "fonts", "brand system", "reference brands",
        "로고", "색상", "폰트", "브랜드",
    ),
    "technical_runtime_dependency": (
        "next.js", "nextjs", "react", "shopify", "webgl", "cms", "animation runtime",
    ),
    "legal_license_dependency": (
        "external assets", "external asset", "fonts", "data", "music", "video", "model", "trademark", "license",
        "라이선스", "외부 에셋", "상표",
    ),
    "accessibility_performance": (
        "motion-heavy", "media-heavy", "mobile-first", "data-heavy", "fast mobile", "reduced motion",
        "모바일에서 빠르게", "접근성", "성능", "애니메이션",
    ),
    "conversion_business": (
        "payment", "booking", "lead", "contact", "download", "demo",
        "결제", "예약", "문의", "리드", "다운로드", "데모",
    ),
}

_FIELD_BY_CATEGORY: dict[str, tuple[str, ...]] = {
    "core_visual_asset_dependency": ("asset_source",),
    "interaction_dependency": ("interaction_model",),
    "brand_dependency": ("brand_assets",),
    "technical_runtime_dependency": ("technical_runtime",),
    "legal_license_dependency": ("license_clearance",),
    "accessibility_performance": ("performance_accessibility_plan",),
}

_CONVERSION_HARD_KEYWORDS = ("payment", "booking", "lead", "contact", "download", "결제", "예약", "문의", "리드", "다운로드")

_QUALITY_CRITICAL_PATTERNS = (
    ("product photo", "Real product photography is a quality-critical visual requirement."),
    ("제품 사진", "실제 제품 사진은 품질 핵심 시각 요구사항입니다."),
    ("actual product", "Actual product imagery is a quality-critical visual requirement."),
    ("실제 제품", "실제 제품 이미지는 품질 핵심 시각 요구사항입니다."),
    ("real gallery", "A real gallery-like visual asset is quality-critical."),
    ("실제 갤러리", "실제 갤러리 같은 시각 자산은 품질 핵심 요구사항입니다."),
    ("석고상", "The 3D plaster-cast subject is a quality-critical core asset."),
)

_PLACEHOLDER_BOUNDARY = (
    "Placeholders may be used to communicate layout or interaction intent in strategy and preview, "
    "but implementation cannot use a placeholder as the final substitute for core requirements."
)

_SUBSTITUTE_STOP = (
    "Substitute stop rule: stop before implementation if a missing core asset, interaction model, "
    "license clearance, brand asset, runtime decision, or performance/accessibility plan would be replaced by a generic substitute."
)


def _flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        parts: list[str] = []
        for key in sorted(value):
            parts.append(str(key))
            parts.append(_flatten_text(value[key]))
        return " ".join(parts)
    if isinstance(value, (list, tuple, set)):
        return " ".join(_flatten_text(item) for item in value)
    return str(value)


def _has_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _detect_categories(answers: dict[str, Any], intent: dict[str, Any] | None = None) -> list[str]:
    text = _flatten_text({"answers": answers or {}, "intent": intent or {}})
    categories = [category for category, words in _CATEGORY_KEYWORDS.items() if _has_any(text, words)]

    # Avoid making a simple low-risk SaaS demo CTA implementation-blocking while
    # still detecting explicitly requested business mechanics.
    if "conversion_business" in categories and not _has_any(text, _CONVERSION_HARD_KEYWORDS):
        if "demo" in text.lower() or "데모" in text.lower():
            # Demo is a conversion signal, not necessarily a dependency.
            pass
    return categories


def _quality_critical_requirements(text: str) -> list[dict[str, str]]:
    lowered = text.lower()
    requirements: list[dict[str, str]] = []
    seen: set[str] = set()
    for pattern, label in _QUALITY_CRITICAL_PATTERNS:
        if pattern.lower() in lowered and label not in seen:
            requirements.append({
                "requirement": label,
                "source_signal": pattern,
                "rule": "quality_critical_requirement",
                "placeholder_policy": "preview_only",
                "completion_criterion": "Final implementation must use an approved/source-confirmed asset or explicitly revised requirement, not a generic substitute.",
            })
            seen.add(label)
    if ("photo" in lowered or "사진" in lowered) and ("core" in lowered or "핵심" in lowered) and not requirements:
        requirements.append({
            "requirement": "Core photography is quality-critical to the requested experience.",
            "source_signal": "core photo",
            "rule": "quality_critical_requirement",
            "placeholder_policy": "preview_only",
            "completion_criterion": "Final implementation must use approved photography or an explicit requirement change.",
        })
    return requirements


def dynamic_required_fields(payload: dict[str, Any]) -> list[str]:
    """Return dynamic required field names for a risk payload or partial contract."""
    categories = payload.get("risk_categories") or []
    fields: list[str] = []
    for category in categories:
        for field in _FIELD_BY_CATEGORY.get(str(category), ()):  # conversion handled below
            if field not in fields:
                fields.append(field)

    text = _flatten_text(payload)
    if "conversion_business" in categories and _has_any(text, _CONVERSION_HARD_KEYWORDS):
        fields.append("conversion_path")

    if payload.get("quality_critical_requirements") and "asset_source" not in fields:
        fields.insert(0, "asset_source")

    return fields


def _completion_criteria(answers: dict[str, Any], fields: list[str], qcr: list[dict[str, str]]) -> list[str]:
    goal = str(answers.get("goal") or "the stated goal").strip() or "the stated goal"
    criteria = [
        f"The final experience must directly support: {goal}.",
        "Core project, audience, goal, and vibe are reflected in content hierarchy and visual direction.",
    ]
    for field in fields:
        criteria.append(f"Dynamic requirement '{field}' is answered and traceable in the final implementation.")
    for requirement in qcr:
        criteria.append(requirement["completion_criterion"])
    criteria.append("No placeholder remains as a final substitute for a quality-critical or core requirement.")
    return criteria


def render_risk_summary(payload: dict[str, Any], locale: str = "en-US") -> str:
    categories = payload.get("risk_categories") or []
    missing = payload.get("missing_dynamic_required_fields") or []
    readiness = payload.get("readiness") or {}
    if locale.lower().startswith("ko"):
        return (
            f"위험 범주: {', '.join(categories) if categories else '없음'}\n"
            f"누락된 동적 필수 항목: {', '.join(missing) if missing else '없음'}\n"
            f"전략: {readiness.get('strategy', 'unknown')} / 미리보기: {readiness.get('preview', 'unknown')} / "
            f"구현: {readiness.get('implementation', 'unknown')}\n"
            f"경계: {payload.get('placeholder_boundary', _PLACEHOLDER_BOUNDARY)}"
        )
    return (
        f"Risk categories: {', '.join(categories) if categories else 'none'}\n"
        f"Missing dynamic required fields: {', '.join(missing) if missing else 'none'}\n"
        f"Readiness: strategy={readiness.get('strategy', 'unknown')}, "
        f"preview={readiness.get('preview', 'unknown')}, implementation={readiness.get('implementation', 'unknown')}\n"
        f"Boundary: {payload.get('placeholder_boundary', _PLACEHOLDER_BOUNDARY)}"
    )


def analyze_risk_readiness(answers: dict[str, Any], intent: dict[str, Any] | None = None) -> dict[str, Any]:
    answers = dict(answers or {})
    intent = dict(intent or {}) if intent else None
    combined_text = _flatten_text({"answers": answers, "intent": intent or {}})
    risk_categories = _detect_categories(answers, intent)
    qcr = _quality_critical_requirements(combined_text)

    partial = {"risk_categories": risk_categories, "quality_critical_requirements": qcr, "answers": answers, "intent": intent or {}}
    required = dynamic_required_fields(partial)
    missing = [field for field in required if not _present(answers.get(field)) and not _present((intent or {}).get(field))]

    core_missing = [field for field in CORE_FIELDS if not _present(answers.get(field))]
    if core_missing:
        strategy = "blocked"
        preview = "blocked"
        implementation = "blocked"
        status = "core_fields_missing"
    elif missing:
        strategy = "ready"
        preview = "ready_with_placeholders"
        implementation = "blocked"
        status = "implementation_blocked"
    elif risk_categories or qcr:
        strategy = "ready"
        preview = "ready"
        implementation = "ready_with_assumptions"
        status = "ready_with_assumptions"
    else:
        strategy = "ready"
        preview = "ready"
        implementation = "ready"
        status = "ready"

    safe_assumptions = [
        "Strategy may proceed from stated project, audience, goal, and vibe." if not core_missing else "No strategy assumption is safe until core fields are answered.",
    ]
    if missing:
        safe_assumptions.append("Preview may use clearly labeled placeholders only to show structure, scale, or interaction intent.")
    elif risk_categories or qcr:
        safe_assumptions.append("Implementation may proceed only if detected dependencies are satisfied by supplied answers or explicit approvals.")

    unsafe_assumptions = [
        "Do not treat a generic substitute as equivalent to a missing quality-critical requirement.",
        "Do not replace required product photos or core visual assets with a generic gradient in final implementation.",
    ]
    if missing:
        unsafe_assumptions.append("Do not implement final production UI by substituting missing dynamic requirements with invented assets, behaviors, licenses, or runtime choices.")
    if core_missing:
        unsafe_assumptions.append("Do not infer missing core fields without user confirmation.")

    stop_conditions: list[str] = []
    if core_missing:
        stop_conditions.append(f"Stop: core fields missing: {', '.join(core_missing)}.")
    if missing:
        stop_conditions.append(f"Stop before implementation: missing dynamic required fields: {', '.join(missing)}.")
        stop_conditions.append(_SUBSTITUTE_STOP)
    if qcr:
        stop_conditions.append("Stop before final implementation if quality-critical assets are unavailable, unlicensed, or replaced by placeholders.")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "risk_categories": risk_categories,
        "quality_critical_requirements": qcr,
        "dynamic_required_fields": required,
        "missing_dynamic_required_fields": missing,
        "readiness": {
            "strategy": strategy,
            "preview": preview,
            "implementation": implementation,
            "status": status,
        },
        "safe_assumptions": safe_assumptions,
        "unsafe_assumptions": unsafe_assumptions,
        "placeholder_boundary": _PLACEHOLDER_BOUNDARY,
        "stop_conditions": stop_conditions,
        "risk_summary": "",
        "completion_criteria": _completion_criteria(answers, required, qcr),
    }
    payload["risk_summary"] = render_risk_summary(payload, locale=str(answers.get("locale") or "en-US"))
    return payload


__all__ = ["analyze_risk_readiness", "render_risk_summary", "dynamic_required_fields"]
