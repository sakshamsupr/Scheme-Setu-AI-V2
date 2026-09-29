from __future__ import annotations

import json
import re
from typing import Any

try:
    from google import genai
except Exception:  # pragma: no cover
    genai = None

from .config import GEMINI_API_KEY, GEMINI_MODEL
from .rag import retrieve, build_context
from .data_store import match_schemes, nearby_partners
from .finance import calculate


STATE_NAMES = [
    "Uttar Pradesh", "Rajasthan", "Madhya Pradesh", "Maharashtra", "Delhi", "Gujarat", "Haryana",
    "Punjab", "Bihar", "Jharkhand", "Chhattisgarh", "Uttarakhand", "Himachal Pradesh", "West Bengal",
    "Odisha", "Tamil Nadu", "Kerala", "Karnataka", "Telangana", "Andhra Pradesh", "Assam", "Goa",
    "Jharkhand", "Chandigarh", "Jammu and Kashmir", "Ladakh"
]

STATE_ALIASES = {
    "up": "Uttar Pradesh", "u.p.": "Uttar Pradesh",
    "mp": "Madhya Pradesh", "m.p.": "Madhya Pradesh",
    "rj": "Rajasthan", "mh": "Maharashtra", "dl": "Delhi",
    "hr": "Haryana", "pb": "Punjab", "gj": "Gujarat", "uk": "Uttarakhand",
    "ap": "Andhra Pradesh", "ts": "Telangana",
}

BUSINESS_TERMS = {
    "manufacturing": "Manufacturing", "manufacture": "Manufacturing", "factory": "Manufacturing",
    "service": "Services", "services": "Services", "trading": "Trading", "retail": "Trading",
    "shop": "Trading", "handicraft": "Handicrafts", "handicrafts": "Handicrafts", "artisan": "Handicrafts",
    "farming": "Farming", "agriculture": "Farming", "agri": "Farming", "dairy": "Dairy",
    "education": "Education", "transport": "Transport", "auto": "Transport", "e-rickshaw": "Transport",
    "tailoring": "Services", "silai": "Services", "stitching": "Services", "sewing": "Services"
}

SYSTEM = """You are Scheme Setu AI, a multilingual financial-scheme navigation copilot for India.
Use retrieved context for factual scheme claims. Never invent eligibility, amounts, rates, deadlines or application status.
When a user is only greeting or chatting casually, respond normally without requiring retrieval.
When a user provides profile information, acknowledge what was captured and continue naturally; do not pretend that they asked a knowledge question.
Use tools/actions conceptually: scheme search, comparison, calculation, partner location, documents and navigation.
If a factual claim cannot be verified from the supplied context, say so clearly.
Answer in the language/style used by the user. Keep answers practical and concise."""


def _has_any(t: str, phrases: list[str]) -> bool:
    return any(p in t for p in phrases)


def extract_profile_patch(text: str) -> dict[str, Any]:
    t = text.lower()
    patch: dict[str, Any] = {}

    age_patterns = [
        r"(?:age|umar|umr|meri umar|meri age|my age)\s*(?:is|hai|=|:)?\s*(\d{1,3})",
        r"\b(\d{1,3})\s*(?:years?|yrs?|saal|वर्ष|साल)\b",
        r"(?:उम्र|उमर)\s*(?:है|हूँ|हूं|=|:)?\s*(\d{1,3})",
    ]
    for pat in age_patterns:
        m = re.search(pat, t, flags=re.IGNORECASE)
        if m:
            age = int(m.group(1))
            if 13 <= age <= 100:
                patch["age"] = age
                break

    if _has_any(t, ["female", "woman", "women", "ladki", "ladki hu", "mahila", "महिला", "लड़की"]):
        patch["gender"] = "Female"
    elif _has_any(t, ["male", "man", "ladka", "purush", "पुरुष", "लड़का"]):
        patch["gender"] = "Male"

    for cat in ["SC", "ST", "OBC", "General"]:
        if re.search(rf"\b{re.escape(cat.lower())}\b", t):
            patch["category"] = cat
            break
    if "अनुसूचित जाति" in t or "anusuchit jati" in t:
        patch["category"] = "SC"
    elif "अनुसूचित जनजाति" in t or "anusuchit jan jati" in t:
        patch["category"] = "ST"
    elif "अन्य पिछड़ा वर्ग" in t or "obc" in t:
        patch["category"] = "OBC"

    for state in sorted(STATE_NAMES, key=len, reverse=True):
        if state.lower() in t:
            patch["state"] = state
            break
    if "state" not in patch:
        # Two-letter state codes are only accepted when they are used as a
        # standalone location token; avoid false positives such as "ka" in
        # Hinglish phrases ("5 lakh ka EMI").
        original = text
        explicit_location = re.search(
            r"(?:state|from|se|mein|me|in)\s*[:=-]?\s*([A-Za-z.]+)",
            original,
            flags=re.IGNORECASE,
        )
        if explicit_location:
            candidate = explicit_location.group(1).strip().lower()
            if candidate in STATE_ALIASES:
                patch["state"] = STATE_ALIASES[candidate]
        if "state" not in patch:
            for alias in ("up", "mp", "rj", "mh", "dl", "hr", "pb", "gj", "uk", "ap", "ts"):
                if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", t):
                    patch["state"] = STATE_ALIASES[alias]
                    break

    for k, v in sorted(BUSINESS_TERMS.items(), key=lambda x: len(x[0]), reverse=True):
        if k in t:
            patch["business_type"] = v
            break

    loan_patterns = [
        r"(?:loan|funding|amount|paise|rupaye|rupees|₹|लोन|रुपये|रुपए)\s*(?:of|ka|ki|chahiye|around|approx|approximately|=|:)?\s*₹?\s*([0-9]+(?:\.[0-9]+)?)(?:\s*(lakh|lac|lakhs|crore|cr|लाख|करोड़))?",
        r"₹\s*([0-9]+(?:\.[0-9]+)?)(?:\s*(lakh|lac|lakhs|crore|cr|लाख|करोड़))?",
        r"\b([0-9]+(?:\.[0-9]+)?)\s*(lakh|lac|lakhs|crore|cr|लाख|करोड़)\b",
    ]
    for pat in loan_patterns:
        m = re.search(pat, t, flags=re.IGNORECASE)
        if not m:
            continue
        try:
            value = float(m.group(1))
            unit = (m.group(2) or "").lower()
            if unit in {"lakh", "lac", "lakhs", "लाख"}:
                value *= 100000
            elif unit in {"crore", "cr", "करोड़"}:
                value *= 10000000
            elif value < 1000 and ("lakh" in t or "lac" in t or "लाख" in t):
                value *= 100000
            patch["loan_amount"] = value
            break
        except Exception:
            pass

    income_patterns = [
        r"(?:income|aay|annual income|family income|आय|income hai)\s*(?:is|hai|=|:)?\s*₹?\s*([0-9]+(?:\.[0-9]+)?)(?:\s*(lakh|lac|lakhs|crore|cr|लाख|करोड़))?",
    ]
    for pat in income_patterns:
        m = re.search(pat, t, flags=re.IGNORECASE)
        if m:
            try:
                value = float(m.group(1))
                unit = (m.group(2) or "").lower()
                if unit in {"lakh", "lac", "lakhs", "लाख"}:
                    value *= 100000
                elif unit in {"crore", "cr", "करोड़"}:
                    value *= 10000000
                patch["income"] = value
                break
            except Exception:
                pass

    return patch


def detect_intent(text: str, profile_patch: dict[str, Any] | None = None) -> str:
    t = text.lower().strip()
    patch = profile_patch or {}

    # Greetings and lightweight chat must bypass RAG.
    normalized = re.sub(r"[^a-z0-9\u0900-\u097f\s]", " ", t)
    greeting_tokens = {
        "hi", "hello", "hey", "hii", "hlo", "hola", "namaste", "namaskar", "thanks", "thank you",
        "ok", "okay", "good morning", "good afternoon", "good evening", "good night", "नमस्ते", "हाय",
        "हेलो", "धन्यवाद", "शुक्रिया", "ठीक है"
    }
    if normalized in greeting_tokens or len(normalized.split()) <= 2 and any(x in normalized for x in greeting_tokens):
        return "greeting"

    if _has_any(t, ["emi", "installment", "repayment", "interest calculator", "loan calculation", "monthly payment", "किश्त", "ईएमआई"]):
        return "calculate_loan"
    if _has_any(t, ["nearest", "near me", "partner", "bank branch", "lender", "पास", "नज़दीक", "नजदीक", "पार्टनर"]):
        return "find_partner"
    if _has_any(t, ["compare", "comparison", "difference between", "तुलना", "अंतर"]):
        return "compare_schemes"
    if _has_any(t, ["document", "documents", "paperwork", "kagaz", "कागज", "दस्तावेज़", "दस्तावेज"]):
        return "documents"
    if _has_any(t, ["eligibility gap", "eligibility gap detector", "eligible नहीं", "eligible nhi", "am i eligible", "what is missing", "क्या कमी", "पात्रता", "योग्यता", "गैप"]):
        return "eligibility_gap"
    if _has_any(t, ["roadmap", "application roadmap", "next steps", "steps to apply", "आवेदन रोडमैप", "अगले कदम"]):
        return "roadmap"
    if _has_any(t, ["scheme", "schemes", "yojana", "loan for", "subsidy", "योजना", "लोन", "सब्सिडी"]):
        return "find_schemes"

    # Any extracted profile fields mean this is a profile/update turn unless the user
    # explicitly asked for another action above.
    if patch:
        return "update_profile"

    if _has_any(t, ["profile", "my details", "my information", "meri profile", "मेरी प्रोफाइल"]):
        return "update_profile"

    return "knowledge"


def _language_code(language: str) -> str:
    return (language or "auto").lower()

def detect_language_code(text: str) -> str:
    s = text or ""
    if re.search(r"[\u0900-\u097F]", s): return "hi-IN"
    if re.search(r"[\u0980-\u09FF]", s): return "bn-IN"
    if re.search(r"[\u0A80-\u0AFF]", s): return "gu-IN"
    if re.search(r"[\u0B80-\u0BFF]", s): return "ta-IN"
    if re.search(r"[\u0C00-\u0C7F]", s): return "te-IN"
    if re.search(r"[\u0C80-\u0CFF]", s): return "kn-IN"
    if re.search(r"[\u0D00-\u0D7F]", s): return "ml-IN"
    if re.search(r"[\u0A00-\u0A7F]", s): return "pa-IN"
    if re.search(r"[\u0900-\u097F]", s): return "hi-IN"
    return "en-IN"



def _greeting(language: str) -> str:
    lang = _language_code(language)
    if lang.startswith("hi"):
        return "नमस्ते! मैं Scheme Setu AI हूँ। आप मुझसे अपनी प्रोफ़ाइल, योजनाओं, लोन, दस्तावेज़ या नज़दीकी पार्टनर के बारे में पूछ सकते हैं।"
    if lang.startswith("bn"):
        return "নমস্কার! আমি Scheme Setu AI। আপনি আপনার প্রোফাইল, স্কিম, ঋণ, নথি বা নিকটবর্তী পার্টনার সম্পর্কে জানতে পারেন।"
    if lang.startswith("mr"):
        return "नमस्कार! मी Scheme Setu AI आहे. तुम्ही प्रोफाइल, योजना, कर्ज, कागदपत्रे किंवा जवळच्या पार्टनरबद्दल विचारू शकता."
    if lang.startswith("ta"):
        return "வணக்கம்! நான் Scheme Setu AI. உங்கள் சுயவிவரம், திட்டங்கள், கடன், ஆவணங்கள் அல்லது அருகிலுள்ள கூட்டாளி பற்றி கேளுங்கள்."
    return "Hi! I’m Scheme Setu AI. Tell me about your profile, or ask me to find schemes, calculate a loan, check documents, or locate a partner."


def _profile_summary(patch: dict[str, Any], merged: dict[str, Any], language: str) -> str:
    labels = {
        "age": "age", "gender": "gender", "category": "category", "state": "state",
        "business_type": "business type", "loan_amount": "loan amount", "income": "annual income"
    }
    parts = []
    for key in ["age", "gender", "category", "state", "business_type", "loan_amount", "income"]:
        if key not in patch:
            continue
        value = patch[key]
        if key in {"loan_amount", "income"}:
            value = f"₹{value:,.0f}"
        parts.append(f"{labels[key]}: {value}")
    if not parts:
        return "I can update your profile from what you tell me."
    joined = ", ".join(parts)
    lang = _language_code(language)
    if lang.startswith("hi"):
        return f"ठीक है — मैंने आपकी प्रोफ़ाइल में ये जानकारी अपडेट कर दी है: {joined}. अब आप मुझसे सीधे अपनी schemes, EMI, documents या partner के बारे में पूछ सकते हैं।"
    return f"Got it — I updated your profile with: {joined}. You can now ask me to find schemes, calculate EMI, check documents, or locate a partner."


def _local_calculation(profile: dict[str, Any], language: str) -> str:
    loan = float(profile.get("loan_amount") or 0)
    if loan <= 0:
        return "Tell me the loan amount you want to calculate, for example: ₹5 lakh for 5 years at 8%."
    result = calculate(loan_amount=loan, subsidy_percentage=0, interest_rate="8", tenure_years=5, moratorium_months=0)
    if _language_code(language).startswith("hi"):
        return f"₹{loan:,.0f} के लिए 8% और 5 साल के indicative example में EMI लगभग ₹{result['monthly_emi']:,.0f}/माह होगी। यह indicative calculation है; actual terms lender/scheme पर निर्भर करेंगी।"
    return f"For ₹{loan:,.0f}, using an indicative 8% rate over 5 years, the EMI is about ₹{result['monthly_emi']:,.0f}/month. Actual terms depend on the scheme and lender."


def _local_answer(message: str, profile: dict[str, Any], results: list[dict[str, Any]], intent: str, language: str) -> str:
    if intent == "greeting":
        return _greeting(effective_language)
    if intent == "update_profile":
        patch = extract_profile_patch(message)
        return _profile_summary(patch, profile, language)
    if intent == "calculate_loan":
        return _local_calculation(profile, language)
    if intent == "find_schemes":
        required = ["age", "category", "state", "business_type"]
        missing = [x for x in required if not profile.get(x)]
        if missing:
            return "I can personalize the scheme search. Please tell me your age, category, state and business type; then I’ll show the relevant matches."
        matched = match_schemes(profile, 8)
        eligible = [x for x in matched if x["eligible"]][:5]
        if eligible:
            names = ", ".join(x["scheme_name"] for x in eligible)
            return f"Based on your current profile, I found {len(eligible)} potentially relevant schemes: {names}. Open the Schemes page to explore the full match details and official source links."
        return "I couldn't find a strong personalized match in the current seed dataset. You can still browse all schemes and refine your profile."
    if intent == "eligibility_gap":
        required = ["age", "category", "state", "business_type"]
        missing = [x for x in required if not profile.get(x)]
        if missing:
            return "I can detect the gap once your profile has age, category, state and business type. You can tell me those in one sentence."
        matched = match_schemes(profile, 5)
        if matched:
            r = matched[0]
            if r.get("eligible") and not r.get("gaps"):
                return f"For {r['scheme_name']}, the current rule set shows no hard eligibility gap in your saved profile. Verify the official source before applying."
            gaps = "; ".join(r.get("gaps", [])[:4]) or "No specific hard gap was returned by the current rule set."
            return f"For the current top match, {r['scheme_name']}, the main gaps to check are: {gaps}. I can open the scheme details for the full breakdown."
        return "I couldn't detect a strong match to test yet. Add more profile details or open the scheme explorer."
    if intent == "roadmap":
        return "Choose a scheme and I can open its interactive application roadmap, where you can mark steps complete and come back later."
    if intent == "documents":
        if results:
            r = results[0]
            return f"For {r['scheme_name']}, the current dataset lists: {r.get('documents','')}. Please verify the latest checklist on the official source before applying."
        return "Tell me the scheme name and I’ll retrieve its current document checklist from the knowledge base."
    if intent == "compare_schemes":
        if results:
            return "I can compare schemes using the scheme data. Tell me the two scheme names you want compared, or ask me to compare the top matches for your profile."
        return "Tell me the two scheme names you want compared."
    if intent == "find_partner":
        return "I can open the partner locator. For a nearby result, share your location or at least your city/district."
    if results:
        r = results[0]
        return f"Here’s the most relevant information I found for {r['scheme_name']}: {r.get('description','')} Source: {r.get('apply_link','')}"
    return "I couldn’t verify an answer from the current knowledge base. Ask me about schemes, eligibility, documents, loans, or partners and I’ll use the available verified data."


def _actions_for(intent: str, profile: dict[str, Any]) -> list[dict[str, str]]:
    if intent == "find_schemes":
        return [{"type": "navigate", "target": "/schemes", "label": "View matched schemes"}]
    if intent == "calculate_loan":
        return [{"type": "navigate", "target": "/calculator", "label": "Open calculator"}]
    if intent == "find_partner":
        return [{"type": "navigate", "target": "/partners", "label": "Open partner locator"}]
    if intent == "documents":
        return [{"type": "navigate", "target": "/documents", "label": "Open documents"}]
    if intent == "eligibility_gap":
        return [{"type": "navigate", "target": "/schemes", "label": "Open scheme gap checks"}]
    if intent == "roadmap":
        return [{"type": "navigate", "target": "/roadmap", "label": "Open application roadmap"}]
    if intent == "compare_schemes":
        return [{"type": "navigate", "target": "/compare", "label": "Open scheme comparison"}]
    if intent == "update_profile":
        return [{"type": "navigate", "target": "/profile", "label": "View my profile"}]
    return []


def chat(message: str, profile: dict[str, Any] | None = None, history: list[dict[str, Any]] | None = None, language: str = "auto") -> dict:
    profile = profile or {}
    history = history or []
    profile_patch = extract_profile_patch(message)
    merged_profile = {**profile, **profile_patch}
    effective_language = detect_language_code(message) if (not language or language == "auto") else language
    intent = detect_intent(message, profile_patch)

    # Critical: greetings/profile updates should not fail just because the RAG index
    # has no matching document. They are conversational turns, not knowledge retrieval.
    if intent == "greeting":
        return {
            "answer": _greeting(effective_language),
            "intent": intent,
            "retrieved": [],
            "actions": [],
            "profile_patch": {},
            "mode": "local-conversation",
        }

    if intent == "update_profile":
        return {
            "answer": _profile_summary(profile_patch, merged_profile, effective_language),
            "intent": intent,
            "retrieved": [],
            "actions": _actions_for(intent, merged_profile),
            "profile_patch": profile_patch,
            "profile": merged_profile,
            "mode": "local-profile",
        }

    # Retrieve only for knowledge-bearing turns.
    retrieval_query = message
    results = retrieve(retrieval_query, top_k=5)
    actions = _actions_for(intent, merged_profile)
    context = build_context(results)

    # Tool-oriented actions should remain deterministic first. Gemini may enrich a
    # response, but should never be required for navigation/calculation UX.
    if intent == "calculate_loan" and not GEMINI_API_KEY:
        return {
            "answer": _local_calculation(merged_profile, effective_language),
            "intent": intent,
            "retrieved": results[:5],
            "actions": actions,
            "profile_patch": profile_patch,
            "profile": merged_profile,
            "mode": "local-tool",
        }

    if GEMINI_API_KEY and genai:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = (
                f"{SYSTEM}\n\nRESPONSE LANGUAGE: {effective_language} (match the user when auto)\n\n"
                f"INTENT: {intent}\n\nUSER PROFILE:\n{json.dumps(merged_profile, ensure_ascii=False)}\n\n"
                f"RETRIEVED CONTEXT:\n{context or '[No relevant verified context retrieved]'}\n\n"
                f"CONVERSATION:\n{json.dumps(history[-8:], ensure_ascii=False)}\n\n"
                f"USER MESSAGE:\n{message}\n\n"
                "Respond naturally. If this is a scheme factual question and the retrieved context is insufficient, explicitly say you could not verify it."
            )
            response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            answer = (getattr(response, "text", "") or "").strip()
            if answer:
                return {
                    "answer": answer,
                    "intent": intent,
                    "retrieved": results[:5],
                    "actions": actions,
                    "profile_patch": profile_patch,
                    "profile": merged_profile,
                    "mode": "gemini",
                }
        except Exception as exc:
            return {
                "answer": _local_answer(message, merged_profile, results, intent, effective_language) + f"\n\n[AI provider note: {type(exc).__name__}]",
                "intent": intent,
                "retrieved": results[:5],
                "actions": actions,
                "profile_patch": profile_patch,
                "profile": merged_profile,
                "mode": "local-rag-provider-error",
                "provider_error": type(exc).__name__,
            }

    return {
        "answer": _local_answer(message, merged_profile, results, intent, effective_language),
        "intent": intent,
        "retrieved": results[:5],
        "actions": actions,
        "profile_patch": profile_patch,
        "profile": merged_profile,
        "mode": "local-rag",
    }
