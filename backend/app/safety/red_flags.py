"""Deterministic red-flag detector. SYNTHETIC/DEMO RULES ONLY - not real clinical guidance."""

import re

RED_FLAG_KEYWORDS: dict[str, list[str]] = {
    "severe_chest_pain": ["chest pain", "crushing chest", "chest pressure"],
    "difficulty_breathing": ["difficulty breathing", "shortness of breath", "can't breathe", "cannot breathe", "gasping"],
    "loss_of_consciousness": ["loss of consciousness", "passed out", "fainted", "unresponsive"],
    "stroke_like_symptoms": ["slurred speech", "facial drooping", "face drooping", "sudden numbness", "one-sided weakness"],
    "severe_allergic_reaction": ["anaphylaxis", "throat swelling", "swollen throat", "severe allergic reaction"],
    "severe_bleeding": ["uncontrolled bleeding", "won't stop bleeding", "severe bleeding", "heavy blood loss"],
}

_NEGATION_PATTERN = re.compile(
    r"\b(?:do not have|does not have|don't have|doesn't have|no|not|without|deny|denies|denied)\b"
    r"(?:\W+\w+){0,4}\W*$"
)
_AFFIRMATIVE_WORDS = {"yes", "yeah", "yep", "affirmative", "correct", "indeed"}


def detect_red_flags(symptoms: list[str], conversation_text: str) -> list[str]:
    """Return the list of matched red-flag categories found in symptoms or conversation text."""
    haystack = " ".join(symptoms + [conversation_text]).lower()
    matched: list[str] = []
    for flag_name, keywords in RED_FLAG_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            matched.append(flag_name)
    return matched


def _detect_non_negated_red_flags(text: str) -> list[str]:
    lowered = text.lower()
    matched: list[str] = []
    for flag_name, keywords in RED_FLAG_KEYWORDS.items():
        for keyword in keywords:
            for occurrence in re.finditer(re.escape(keyword), lowered):
                prefix = lowered[max(0, occurrence.start() - 80) : occurrence.start()]
                clause_prefix = re.split(r"[.!?;]|\bbut\b|\bhowever\b", prefix)[-1]
                if not _NEGATION_PATTERN.search(clause_prefix):
                    matched.append(flag_name)
                    break
            if flag_name in matched:
                break
    return matched


def _is_short_affirmative(text: str) -> bool:
    words = re.findall(r"[a-z']+", text.lower())
    return bool(words) and len(words) <= 5 and words[0] in _AFFIRMATIVE_WORDS


def detect_conversation_red_flags(conversation: list[dict[str, str]]) -> list[str]:
    """Detect patient-reported flags, resolving short affirmative answers against one prior question."""
    matched: list[str] = []
    for index, turn in enumerate(conversation):
        if turn.get("role") != "patient":
            continue

        patient_text = turn.get("content", "")
        direct_flags = _detect_non_negated_red_flags(patient_text)
        for flag in direct_flags:
            if flag not in matched:
                matched.append(flag)

        if direct_flags or not _is_short_affirmative(patient_text) or index == 0:
            continue

        prior_turn = conversation[index - 1]
        if prior_turn.get("role") != "twin":
            continue

        question = prior_turn.get("content", "")
        question_flags = detect_red_flags([], question)
        if len(question_flags) == 1 and " or " not in question.lower():
            flag = question_flags[0]
            if flag not in matched:
                matched.append(flag)

    return matched
