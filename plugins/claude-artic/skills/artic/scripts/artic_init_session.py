#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from locale_contract import detect_locale_from_text, language_contract
from risk_readiness import analyze_risk_readiness as analyze_risk_readiness_contract

SESSION_PATH = Path(".artic") / "init-session.json"
REQUIRED_FIELDS = ["project", "audience", "goal", "vibe"]
OPTIONAL_FIELDS = ["references", "stack", "avoid", "accessibility", "asset_policy"]
DYNAMIC_REQUIRED_FIELDS = [
    "asset_source",
    "interaction_model",
    "brand_constraints",
    "conversion_details",
    "performance_accessibility",
    "asset_policy",
    "license_policy",
]
CORE_ANSWER_FIELDS = set(REQUIRED_FIELDS + OPTIONAL_FIELDS)
CONSTRAINT_FIELD_HINTS = ("constraint", "constraints", "brand", "avoid", "asset_policy", "license_policy")

QUESTION_SPECS: dict[str, dict[str, str]] = {
    "project": {
        "intent": "Understand what product/service this homepage is for.",
        "en-US": "What product/service is this homepage for?",
        "ko-KR": "어떤 제품/서비스의 홈페이지를 만들려고 하나요?",
        "ja-JP": "どのような製品/サービスのホームページを作りますか？",
        "zh-CN": "这是哪个产品/服务的主页？",
        "zh-TW": "這是哪個產品/服務的首頁？",
    },
    "audience": {
        "intent": "Identify the target users.",
        "en-US": "Who is the target user?",
        "ko-KR": "주 타깃 사용자는 누구인가요? 예: 스타트업 대표, 세일즈팀, HR팀",
        "ja-JP": "主なターゲットユーザーは誰ですか？",
        "zh-CN": "主要目标用户是谁？",
        "zh-TW": "主要目標使用者是誰？",
    },
    "goal": {
        "intent": "Identify the primary conversion goal.",
        "en-US": "What is the primary conversion goal?",
        "ko-KR": "가장 중요한 전환 목표는 무엇인가요? 예: 가입, 데모 요청, 구매, 문의",
        "ja-JP": "最も重要なコンバージョン目標は何ですか？",
        "zh-CN": "最重要的转化目标是什么？",
        "zh-TW": "最重要的轉換目標是什麼？",
    },
    "vibe": {
        "intent": "Capture desired emotional/visual impression.",
        "en-US": "What emotional impression should the page create?",
        "ko-KR": "페이지가 어떤 인상을 주면 좋겠나요? 예: 쉽고 신뢰감 있게, 고급스럽게, 친근하게",
        "ja-JP": "ページにどんな印象を持たせたいですか？",
        "zh-CN": "希望页面给人什么感觉？",
        "zh-TW": "希望頁面帶來什麼感覺？",
    },
    "stack": {
        "intent": "Capture implementation stack.",
        "en-US": "What tech stack should implementation target?",
        "ko-KR": "구현 기술 스택은 무엇인가요? 예: React Tailwind, Next.js, Vue",
        "ja-JP": "実装予定の技術スタックは何ですか？",
        "zh-CN": "目标技术栈是什么？",
        "zh-TW": "目標技術棧是什麼？",
    },
    "asset_policy": {
        "intent": "Clarify whether external assets may be used or only referenced as principles.",
        "en-US": "May Artic search/use owned or clearly licensed public assets, or should external sources stay as reference principles only?",
        "ko-KR": "소유한 에셋 또는 라이선스 확인 가능한 공개 에셋을 검색/사용해도 되나요, 아니면 외부 소스는 원칙 참고로만 사용할까요?",
        "ja-JP": "所有アセットまたはライセンス確認済みの公開アセットを検索/使用してよいですか、それとも外部ソースは原則の参考のみにしますか？",
        "zh-CN": "是否可以搜索/使用自有资产或可验证授权的公开资产，还是外部来源仅作为原则参考？",
        "zh-TW": "是否可以搜尋/使用自有資產或可驗證授權的公開資產，或外部來源只作為原則參考？",
    },
    "asset_source": {
        "intent": "Identify source and availability of required visual/3D assets.",
        "en-US": "What is the source for required images, video, or 3D assets (owned files, generated placeholders, or licensed public assets)?",
        "ko-KR": "필요한 이미지/영상/3D 에셋은 어디서 오나요? 자체 보유 파일, 임시 플레이스홀더, 라이선스 확인 가능한 공개 에셋 중 무엇인가요?",
    },
    "interaction_model": {
        "intent": "Clarify implementation-critical interaction behavior.",
        "en-US": "How should key interactions work, including mouse/touch/keyboard behavior and fallbacks?",
        "ko-KR": "핵심 상호작용은 어떻게 동작해야 하나요? 마우스/터치/키보드 조작과 대체 경험까지 알려주세요.",
    },
    "brand_constraints": {
        "intent": "Capture brand/legal constraints that affect design execution.",
        "en-US": "What brand, legal, tone, color, logo, or copy constraints must the design follow?",
        "ko-KR": "디자인이 따라야 할 브랜드/법무/톤/색상/로고/문구 제약은 무엇인가요?",
    },
    "brand_assets": {
        "intent": "Capture brand assets and brand-system constraints.",
        "en-US": "What logo, color, font, or brand-system assets must the design follow?",
        "ko-KR": "디자인이 따라야 할 로고, 색상, 폰트, 브랜드 시스템 에셋은 무엇인가요?",
    },
    "conversion_details": {
        "intent": "Clarify conversion path details.",
        "en-US": "What exact CTA, form fields, destination, or success criteria should the conversion flow use?",
        "ko-KR": "전환 흐름의 정확한 CTA, 폼 필드, 이동 경로, 성공 기준은 무엇인가요?",
    },
    "conversion_path": {
        "intent": "Clarify conversion path details.",
        "en-US": "What exact CTA, form fields, destination, trust requirements, or success criteria should the conversion flow use?",
        "ko-KR": "전환 흐름의 정확한 CTA, 폼 필드, 이동 경로, 신뢰 조건, 성공 기준은 무엇인가요?",
    },
    "performance_accessibility": {
        "intent": "Clarify performance and accessibility constraints for risky media or interaction.",
        "en-US": "What performance and accessibility requirements apply (load budget, reduced motion, keyboard support, alt/fallback content)?",
        "ko-KR": "성능/접근성 요구는 무엇인가요? 로딩 예산, reduced motion, 키보드 지원, 대체 콘텐츠를 알려주세요.",
    },
    "performance_accessibility_plan": {
        "intent": "Clarify performance and accessibility constraints for risky media or interaction.",
        "en-US": "What performance and accessibility plan applies (load budget, reduced motion, keyboard support, alt/fallback content)?",
        "ko-KR": "성능/접근성 계획은 무엇인가요? 로딩 예산, reduced motion, 키보드 지원, 대체 콘텐츠를 알려주세요.",
    },
    "license_policy": {
        "intent": "Clarify licensing and attribution obligations.",
        "en-US": "What license and attribution policy should Artic follow for any third-party assets or references?",
        "ko-KR": "제3자 에셋/레퍼런스의 라이선스와 출처 표기는 어떤 정책을 따라야 하나요?",
    },
    "license_clearance": {
        "intent": "Clarify licensing and attribution obligations.",
        "en-US": "What license clearance and attribution policy should Artic follow for any third-party assets or references?",
        "ko-KR": "제3자 에셋/레퍼런스의 라이선스 확인과 출처 표기는 어떤 정책을 따라야 하나요?",
    },
}

_STYLE_HINT_RE = re.compile(r"토스|신뢰|고급|깔끔|스타트업|모바일|saas|premium|trust|clean|mobile|startup", re.IGNORECASE)
_LABELED_ANSWER_RE = re.compile(
    r"(?:^|[.;\n]\s*)(project|product|service|audience|target user|target users|goal|conversion goal|vibe|impression|style|stack|tech stack|references?|avoid|accessibility|asset policy)\s*:\s*(.*?)(?=(?:[.;\n]\s*)(?:project|product|service|audience|target user|target users|goal|conversion goal|vibe|impression|style|stack|tech stack|references?|avoid|accessibility|asset policy)\s*:|$)",
    re.IGNORECASE | re.DOTALL,
)
_LABELED_FIELD_MAP = {
    "project": "project",
    "product": "project",
    "service": "project",
    "audience": "audience",
    "target user": "audience",
    "target users": "audience",
    "goal": "goal",
    "conversion goal": "goal",
    "vibe": "vibe",
    "impression": "vibe",
    "style": "vibe",
    "stack": "stack",
    "tech stack": "stack",
    "reference": "references",
    "references": "references",
    "avoid": "avoid",
    "accessibility": "accessibility",
    "asset policy": "asset_policy",
}


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def session_path(root: Path) -> Path:
    return root / SESSION_PATH


def read_session(root: Path) -> dict[str, Any]:
    path = session_path(root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing init session: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid init session JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return payload


def write_session(root: Path, session: dict[str, Any]) -> None:
    write(session_path(root), json.dumps(session, indent=2, ensure_ascii=False) + "\n")


def extract_answers_from_text(text: str) -> dict[str, str]:
    answers: dict[str, str] = {}
    for match in _LABELED_ANSWER_RE.finditer(text):
        raw_key = match.group(1).lower().strip()
        field = _LABELED_FIELD_MAP.get(raw_key)
        value = match.group(2).strip(" .;\n\t")
        if field and value:
            answers[field] = value
    lowered = text.lower()
    if "ai 회의록" in lowered or "회의록" in text:
        answers.setdefault("project", "AI 회의록 서비스")
    if "데모" in text:
        answers.setdefault("goal", "데모 요청")
    elif "가입" in text:
        answers.setdefault("goal", "가입")
    elif "문의" in text:
        answers.setdefault("goal", "문의")
    if _STYLE_HINT_RE.search(text) and "vibe" not in answers:
        answers["vibe"] = text.strip()
    return answers


def missing_required_fields(answers: dict[str, str]) -> list[str]:
    return [field for field in REQUIRED_FIELDS if not str(answers.get(field, "")).strip()]


def _answer_corpus(answers: dict[str, str]) -> str:
    return "\n".join(str(value) for value in answers.values() if value).lower()


def analyze_risk_readiness(answers: dict[str, str], missing_core: list[str]) -> dict[str, Any]:
    """Return the canonical Artic risk/readiness contract for dynamic init follow-ups."""
    payload = analyze_risk_readiness_contract(answers)
    if missing_core:
        payload["missing_core_fields"] = list(missing_core)
        payload["readiness"] = {"strategy": "blocked", "preview": "blocked", "implementation": "blocked", "status": "core_fields_missing"}
        payload["ready_for_strategy"] = False
        payload["ready_for_preview"] = False
        payload["ready_for_implementation"] = False
        payload["implementation_blocked"] = True
    return payload


def create_or_update_session(root: Path, user_text: str, explicit_locale: str | None = None, answers: dict[str, str] | None = None) -> dict[str, Any]:
    existing: dict[str, Any]
    if session_path(root).exists():
        existing = read_session(root)
    else:
        existing = {}

    raw_previous_answers = existing.get("answers")
    previous_answers: dict[str, Any] = raw_previous_answers if isinstance(raw_previous_answers, dict) else {}
    merged_answers = {str(key): str(value) for key, value in previous_answers.items() if value}
    merged_answers.update(extract_answers_from_text(user_text))
    if answers:
        merged_answers.update({key: value for key, value in answers.items() if value})

    raw_previous_language = existing.get("language")
    previous_language: dict[str, Any] = raw_previous_language if isinstance(raw_previous_language, dict) else {}
    locale = detect_locale_from_text(user_text, explicit_locale) if explicit_locale or not previous_language else str(previous_language.get("locale") or "en-US")
    lang = language_contract(
        locale,
        tone=str(previous_language.get("tone") or "") or None,
        preserve_terms=list(previous_language.get("preserve_terms", [])) if isinstance(previous_language.get("preserve_terms"), list) else None,
        bilingual_terms=bool(previous_language.get("bilingual_terms", False)),
    )
    missing = missing_required_fields(merged_answers)
    risk_answers = dict(merged_answers)
    if risk_answers.get("stack") and not risk_answers.get("technical_runtime"):
        risk_answers["technical_runtime"] = risk_answers["stack"]
    elif not risk_answers.get("technical_runtime"):
        vibe_text = str(risk_answers.get("vibe") or "")
        if re.search(r"runtime|런타임|webgl|model-viewer|3d", vibe_text, re.IGNORECASE):
            risk_answers["technical_runtime"] = vibe_text
    if risk_answers.get("asset_policy") and not risk_answers.get("license_clearance"):
        risk_answers["license_clearance"] = risk_answers["asset_policy"]
    interaction_answer = str(risk_answers.get("interaction_model") or "")
    if interaction_answer and not risk_answers.get("performance_accessibility_plan"):
        if re.search(r"reduced motion|reduced-motion|keyboard|키보드|대체|fallback|alt|접근성|성능|load|loading", interaction_answer, re.IGNORECASE):
            risk_answers["performance_accessibility_plan"] = interaction_answer
    risk_readiness = analyze_risk_readiness(risk_answers, missing)
    canonical_missing_dynamic = [str(field) for field in risk_readiness.get("missing_dynamic_required_fields", [])]
    missing_dynamic = list(canonical_missing_dynamic)
    if "license_clearance" in canonical_missing_dynamic and "asset_policy" not in missing_dynamic:
        missing_dynamic.append("asset_policy")
    if "asset_source" in canonical_missing_dynamic and not merged_answers.get("asset_policy") and "asset_policy" not in missing_dynamic:
        missing_dynamic.append("asset_policy")
    last_question_ids = (missing + missing_dynamic)[:6]
    session = {
        "schema_version": 1,
        "status": "ready" if not missing else "collecting",
        "language": lang,
        "answers": merged_answers,
        "missing": missing,
        "risk_readiness": risk_readiness,
        "missing_dynamic_required_fields": missing_dynamic,
        "readiness": {key: risk_readiness["readiness"].get(key) for key in ("strategy", "preview", "implementation")},
        "last_question_ids": last_question_ids,
    }
    write_session(root, session)
    return session


def render_questions(session: dict[str, Any], limit: int = 4) -> list[str]:
    raw_language = session.get("language")
    language: dict[str, Any] = raw_language if isinstance(raw_language, dict) else {}
    locale = str(language.get("locale") or "en-US")
    raw_ids = session.get("last_question_ids")
    if isinstance(raw_ids, list) and raw_ids:
        field_ids = [str(field) for field in raw_ids]
    else:
        field_ids = [str(field) for field in session.get("missing", [])]
        field_ids.extend(str(field) for field in session.get("missing_dynamic_required_fields", []) if str(field) not in field_ids)
    questions: list[str] = []
    for field in field_ids[:limit]:
        spec = QUESTION_SPECS.get(str(field), {})
        questions.append(spec.get(locale) or spec.get("en-US") or str(field))
    return questions


def render_optional_questions(session: dict[str, Any]) -> list[str]:
    raw_language = session.get("language")
    language: dict[str, Any] = raw_language if isinstance(raw_language, dict) else {}
    raw_answers = session.get("answers")
    answers: dict[str, Any] = raw_answers if isinstance(raw_answers, dict) else {}
    locale = str(language.get("locale") or "en-US")
    questions: list[str] = []
    for field in OPTIONAL_FIELDS:
        if str(answers.get(field, "")).strip():
            continue
        spec = QUESTION_SPECS.get(field)
        if spec:
            questions.append(spec.get(locale) or spec.get("en-US") or field)
    return questions


def split_custom_answers(answers: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    requirements: dict[str, str] = {}
    constraints: dict[str, str] = {}
    for key, value in answers.items():
        text = str(value).strip()
        if not text or key in CORE_ANSWER_FIELDS:
            continue
        target = constraints if any(hint in key.lower() for hint in CONSTRAINT_FIELD_HINTS) else requirements
        target[str(key)] = text
    return requirements, constraints


def render_ready_summary(session: dict[str, Any]) -> str:
    raw_language = session.get("language")
    language: dict[str, Any] = raw_language if isinstance(raw_language, dict) else {}
    raw_answers = session.get("answers")
    answers: dict[str, Any] = raw_answers if isinstance(raw_answers, dict) else {}
    locale = str(language.get("locale") or "en-US")
    raw_risk = session.get("risk_readiness")
    risk: dict[str, Any] = raw_risk if isinstance(raw_risk, dict) else {}
    raw_readiness = session.get("readiness")
    readiness: dict[str, Any] = raw_readiness if isinstance(raw_readiness, dict) else {}
    risk_level = str(risk.get("risk_level") or "low")
    missing_dynamic = [str(field) for field in session.get("missing_dynamic_required_fields", [])]
    signal_names = [str(row.get("signal")) for row in risk.get("signals", []) if isinstance(row, dict) and row.get("signal")]
    if locale.startswith("ko"):
        lines = [
            "필수 정보는 충분히 모였습니다.",
            "",
            "현재 수집된 핵심:",
            f"- 제품: {answers.get('project', '')}",
            f"- 타깃: {answers.get('audience', '')}",
            f"- 목표: {answers.get('goal', '')}",
            f"- 무드: {answers.get('vibe', '')}",
            "",
            f"리스크 요약: {risk_level}"
            + (f" ({', '.join(signal_names[:4])})" if signal_names else ""),
        ]
        if missing_dynamic:
            lines.extend([
                f"구현 차단: 전략 문서는 시작할 수 있지만 실제 구현은 추가 확인이 필요합니다: {', '.join(missing_dynamic)}.",
                "플레이스홀더/원칙 참고 경계는 유지되며, 에셋 사용을 명시적으로 허용하지 않으면 외부 소스는 원칙 참고로만 사용합니다.",
            ])
        elif readiness.get("implementation") == "blocked":
            lines.extend([
                "구현 차단: 핵심 품질 요구가 플레이스홀더나 낮은 품질 대체물에 의존하고 있어 구현 전에 해결해야 합니다.",
                "플레이스홀더/원칙 참고 경계는 유지되며, 필요한 입력을 검증할 때까지 프로덕션 구현으로 진행하지 않습니다.",
            ])
        elif readiness.get("implementation") == "ready_with_assumptions":
            lines.append("구현 준비: 진행 가능하지만 성능/접근성 세부값은 보수적 기본값으로 가정합니다.")
        lines.extend([
            "",
            "더 다듬고 싶으면 레퍼런스, 피해야 할 스타일, 브랜드/에셋 제약을 추가로 알려주세요.",
            "에셋 사용을 명시적으로 허용하지 않으면 외부 소스는 원칙 참고로만 사용합니다.",
            "문서 생성을 시작하려면 `@artic start`를 실행하세요.",
        ])
    else:
        lines = [
            "The required Artic intake is ready.",
            "",
            "Captured answers:",
            f"- Project: {answers.get('project', '')}",
            f"- Audience: {answers.get('audience', '')}",
            f"- Goal: {answers.get('goal', '')}",
            f"- Vibe: {answers.get('vibe', '')}",
            "",
            f"Risk summary: {risk_level}"
            + (f" ({', '.join(signal_names[:4])})" if signal_names else ""),
        ]
        if missing_dynamic:
            lines.extend([
                f"Implementation blocker: strategy docs may proceed, but implementation needs follow-up on: {', '.join(missing_dynamic)}.",
                "Placeholder/reference boundaries remain active; external assets stay reference-principles only unless explicitly allowed.",
            ])
        elif readiness.get("implementation") == "blocked":
            lines.extend([
                "Implementation blocker: a quality-critical requirement depends on a placeholder or lower-quality substitute.",
                "Placeholder/reference boundaries remain active; do not proceed to production implementation until the required input is verified.",
            ])
        elif readiness.get("implementation") == "ready_with_assumptions":
            lines.append("Implementation readiness: ready with conservative performance/accessibility assumptions.")
        lines.extend([
            "",
            "Add references, avoided styles, brand constraints, or asset policy if you want to refine the brief.",
            "If you do not explicitly allow asset usage, external sources stay reference-principles only.",
            "To generate Artic design docs, run `@artic start`.",
        ])
    return "\n".join(lines)


def is_ready(session: dict[str, Any]) -> bool:
    return not session.get("missing")


def finalize_session(root: Path, limit: int = 5) -> dict[str, Any]:
    session = read_session(root)
    if not is_ready(session):
        raise ValueError("init session is missing required fields: " + ", ".join(str(item) for item in session.get("missing", [])))
    raw_answers = session.get("answers")
    answers: dict[str, Any] = raw_answers if isinstance(raw_answers, dict) else {}
    raw_lang = session.get("language")
    lang: dict[str, Any] = raw_lang if isinstance(raw_lang, dict) else {}
    requirements, constraints = split_custom_answers(answers)
    args = argparse.Namespace(
        root=str(root),
        project=str(answers["project"]),
        audience=str(answers["audience"]),
        goal=str(answers["goal"]),
        vibe=str(answers["vibe"]),
        references=str(answers.get("references", "")),
        stack=str(answers.get("stack", "unspecified")),
        accessibility=str(answers.get("accessibility", "WCAG AA")),
        requirement=[f"{key}={value}" for key, value in requirements.items()],
        constraint=[f"{key}={value}" for key, value in constraints.items()],
        asset_policy=str(answers.get("asset_policy", "")),
        locale=str(lang.get("locale", "en-US")),
        tone=str(lang.get("tone", "clear, professional, product-focused")),
        preserve_term=list(lang.get("preserve_terms", [])) if isinstance(lang.get("preserve_terms"), list) else [],
        bilingual_terms=bool(lang.get("bilingual_terms", False)),
        limit=limit,
        catalog=str(Path(__file__).resolve().parents[1] / "references" / "source-catalog.json"),
    )
    from artic_init import create_init_outputs

    payload = create_init_outputs(root, args)
    session["status"] = "initialized"
    session["missing"] = []
    write_session(root, session)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage an Artic conversational init session.")
    parser.add_argument("--root", required=True)
    parser.add_argument("--text", default="")
    parser.add_argument("--locale", default=None)
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    try:
        if args.finalize:
            payload = finalize_session(Path(args.root), limit=args.limit)
        else:
            session = create_or_update_session(Path(args.root), args.text, explicit_locale=args.locale)
            payload = {**session, "questions": render_questions(session)}
            if is_ready(session):
                payload["ready_summary"] = render_ready_summary(session)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
