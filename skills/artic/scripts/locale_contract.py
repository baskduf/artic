#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Any

SUPPORTED_LOCALES = {
    "en-US": "English",
    "ko-KR": "Korean",
    "ja-JP": "Japanese",
    "zh-CN": "Simplified Chinese",
    "zh-TW": "Traditional Chinese (Taiwan)",
}

DEFAULT_PRESERVE_TERMS = ["DESIGN.md", "AI-native", "Artic", "WCAG AA"]

_HANGUL_RE = re.compile(r"[가-힣]")
_JAPANESE_KANA_RE = re.compile(r"[ぁ-ゟ゠-ヿ]")
_CJK_RE = re.compile(r"[一-龥]")
_TRADITIONAL_HINT_RE = re.compile(r"[繁體臺灣設計參考應用]")
_SIMPLIFIED_HINT_RE = re.compile(r"[简体设计参考应用]")


def normalize_locale(locale: str | None) -> str:
    if not locale:
        return "en-US"
    value = locale.strip()
    aliases = {
        "ko": "ko-KR",
        "kr": "ko-KR",
        "korean": "ko-KR",
        "한국어": "ko-KR",
        "ja": "ja-JP",
        "jp": "ja-JP",
        "japanese": "ja-JP",
        "日本語": "ja-JP",
        "zh": "zh-CN",
        "cn": "zh-CN",
        "zh-cn": "zh-CN",
        "zh-tw": "zh-TW",
        "tw": "zh-TW",
        "en": "en-US",
        "english": "en-US",
    }
    return aliases.get(value.lower(), value if value in SUPPORTED_LOCALES else "en-US")


def detect_locale_from_text(text: str, explicit_locale: str | None = None) -> str:
    if explicit_locale:
        return normalize_locale(explicit_locale)
    if _HANGUL_RE.search(text):
        return "ko-KR"
    if _JAPANESE_KANA_RE.search(text):
        return "ja-JP"
    if _CJK_RE.search(text):
        if _TRADITIONAL_HINT_RE.search(text) and not _SIMPLIFIED_HINT_RE.search(text):
            return "zh-TW"
        return "zh-CN"
    return "en-US"


def language_contract(
    locale: str,
    tone: str | None = None,
    preserve_terms: list[str] | None = None,
    bilingual_terms: bool = False,
) -> dict[str, Any]:
    normalized = normalize_locale(locale)
    default_tone = {
        "en-US": "clear, professional, product-focused",
        "ko-KR": "친근하지만 전문적인 제품/디자인 대화체",
        "ja-JP": "明確で専門的なプロダクト/デザイン会話調",
        "zh-CN": "清晰、专业、偏产品设计的对话语气",
        "zh-TW": "清楚、專業、偏產品設計的對話語氣",
    }.get(normalized, "clear, professional, product-focused")
    return {
        "locale": normalized,
        "output_language": SUPPORTED_LOCALES.get(normalized, normalized),
        "tone": tone or default_tone,
        "preserve_terms": preserve_terms or DEFAULT_PRESERVE_TERMS,
        "bilingual_terms": bilingual_terms,
    }
