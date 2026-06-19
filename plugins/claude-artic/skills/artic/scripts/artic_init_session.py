#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from locale_contract import detect_locale_from_text, language_contract

SESSION_PATH = Path(".artic") / "init-session.json"
REQUIRED_FIELDS = ["project", "audience", "goal", "vibe"]
OPTIONAL_FIELDS = ["references", "stack", "avoid", "accessibility"]

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
}

_STYLE_HINT_RE = re.compile(r"토스|신뢰|고급|깔끔|스타트업|모바일|saas|premium|trust|clean|mobile|startup", re.IGNORECASE)


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
    lowered = text.lower()
    if "ai 회의록" in lowered or "회의록" in text:
        answers["project"] = "AI 회의록 서비스"
    if "데모" in text:
        answers["goal"] = "데모 요청"
    elif "가입" in text:
        answers["goal"] = "가입"
    elif "문의" in text:
        answers["goal"] = "문의"
    if _STYLE_HINT_RE.search(text):
        answers["vibe"] = text.strip()
    return answers


def missing_required_fields(answers: dict[str, str]) -> list[str]:
    return [field for field in REQUIRED_FIELDS if not str(answers.get(field, "")).strip()]


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
    session = {
        "schema_version": 1,
        "status": "ready" if not missing else "collecting",
        "language": lang,
        "answers": merged_answers,
        "missing": missing,
        "last_question_ids": missing[:4],
    }
    write_session(root, session)
    return session


def render_questions(session: dict[str, Any], limit: int = 4) -> list[str]:
    raw_language = session.get("language")
    language: dict[str, Any] = raw_language if isinstance(raw_language, dict) else {}
    locale = str(language.get("locale") or "en-US")
    questions: list[str] = []
    for field in session.get("missing", [])[:limit]:
        spec = QUESTION_SPECS.get(str(field), {})
        questions.append(spec.get(locale) or spec.get("en-US") or str(field))
    return questions


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
    args = argparse.Namespace(
        root=str(root),
        project=str(answers["project"]),
        audience=str(answers["audience"]),
        goal=str(answers["goal"]),
        vibe=str(answers["vibe"]),
        references=str(answers.get("references", "")),
        stack=str(answers.get("stack", "unspecified")),
        accessibility=str(answers.get("accessibility", "WCAG AA")),
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
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
