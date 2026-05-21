"""Claude-powered clinical phrase → terminology code mapper.

Uses tool_use for structured output and prompt caching on the system prompt.
"""
from typing import TypedDict

import anthropic

MODEL = "claude-sonnet-4-6"

_SYSTEM_PROMPT = """You are a medical terminology expert specializing in clinical coding.
Your task is to map clinical phrases, symptoms, diagnoses, medications, and medical concepts
to standard medical terminology codes.

Available code systems:
- SNOMED CT  (http://snomed.info/sct)                         — clinical concepts, diagnoses, findings, procedures, body structures
- LOINC      (http://loinc.org)                               — lab tests, clinical observations, measurements, panels
- ICD-10-CM  (http://hl7.org/fhir/sid/icd-10-cm)             — diagnosis codes for documentation and billing
- RxNorm     (http://www.nlm.nih.gov/research/umls/rxnorm)    — medications, drug ingredients, clinical drugs

Guidelines:
- Prefer SNOMED CT for clinical findings, disorders, procedures, and anatomical concepts.
- Prefer LOINC for laboratory tests and clinical measurements.
- Prefer ICD-10-CM when a billing diagnosis code is most appropriate.
- Prefer RxNorm for drug names, ingredients, and medication concepts.
- Assign confidence 0.9-1.0 only when you are certain of the exact code.
- Assign confidence 0.6-0.89 for likely but not fully certain mappings.
- Assign confidence below 0.6 only as a last resort.
- Return up to the requested number of suggestions ordered by confidence descending.
- Include a brief reasoning for each suggestion."""

_TOOL = {
    "name": "suggest_terminology_codes",
    "description": "Return structured medical terminology code suggestions for a clinical phrase.",
    "input_schema": {
        "type": "object",
        "properties": {
            "suggestions": {
                "type": "array",
                "description": "Ordered list of terminology suggestions, highest confidence first.",
                "items": {
                    "type": "object",
                    "properties": {
                        "system": {
                            "type": "string",
                            "description": "Canonical code system URL.",
                            "enum": [
                                "http://snomed.info/sct",
                                "http://loinc.org",
                                "http://hl7.org/fhir/sid/icd-10-cm",
                                "http://www.nlm.nih.gov/research/umls/rxnorm",
                            ],
                        },
                        "code": {
                            "type": "string",
                            "description": "The terminology code, e.g. '44054006' or 'E11.9'.",
                        },
                        "display": {
                            "type": "string",
                            "description": "Human-readable display name for the code.",
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Confidence score 0.0-1.0.",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Brief explanation for why this code was chosen.",
                        },
                    },
                    "required": ["system", "code", "display", "confidence"],
                },
            }
        },
        "required": ["suggestions"],
    },
}


class TermSuggestion(TypedDict):
    system: str
    code: str
    display: str
    confidence: float
    reasoning: str


_TRANSLATE_TOOL = {
    "name": "suggest_concept_translation",
    "description": "Suggest equivalent concepts in a target terminology system.",
    "input_schema": {
        "type": "object",
        "properties": {
            "suggestions": {
                "type": "array",
                "description": "Translations ordered by confidence descending.",
                "items": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "display": {"type": "string"},
                        "mapping_type": {
                            "type": "string",
                            "enum": ["equivalent", "wider-than", "narrower-than", "related-to"],
                        },
                        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "reasoning": {"type": "string"},
                    },
                    "required": ["code", "display", "mapping_type", "confidence"],
                },
            }
        },
        "required": ["suggestions"],
    },
}

_SYSTEM_LABELS = {
    "http://snomed.info/sct": "SNOMED CT",
    "http://loinc.org": "LOINC",
    "http://hl7.org/fhir/sid/icd-10-cm": "ICD-10-CM",
    "http://www.nlm.nih.gov/research/umls/rxnorm": "RxNorm",
}


class TranslateSuggestion(TypedDict):
    code: str
    display: str
    mapping_type: str
    confidence: float
    reasoning: str


async def translate_concept(
    source_system: str,
    source_code: str,
    source_display: str,
    target_system: str,
    api_key: str,
) -> list[TranslateSuggestion]:
    """Ask Claude to translate a concept from one terminology system to another."""
    client = anthropic.AsyncAnthropic(api_key=api_key)

    src_label = _SYSTEM_LABELS.get(source_system, source_system)
    tgt_label = _SYSTEM_LABELS.get(target_system, target_system)

    prompt = (
        f"Translate this medical concept from {src_label} to {tgt_label}:\n\n"
        f"Source system: {source_system}\n"
        f"Source code:   {source_code}\n"
        f"Display name:  {source_display}\n\n"
        f"Target system: {target_system} ({tgt_label})\n\n"
        "Return the best equivalent concept(s) in the target system with mapping types and confidence scores."
    )

    response = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        tools=[_TRANSLATE_TOOL],
        tool_choice={"type": "tool", "name": "suggest_concept_translation"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "suggest_concept_translation":
            raw = block.input.get("suggestions", [])
            return [
                TranslateSuggestion(
                    code=s["code"],
                    display=s["display"],
                    mapping_type=s.get("mapping_type", "equivalent"),
                    confidence=float(s["confidence"]),
                    reasoning=s.get("reasoning", ""),
                )
                for s in raw
            ]
    return []


async def map_phrase(
    phrase: str,
    api_key: str,
    resource: str | None = None,
    field: str | None = None,
    max_suggestions: int = 5,
) -> list[TermSuggestion]:
    """Call Claude to map a clinical phrase to terminology codes.

    Returns a list of suggestions ordered by confidence descending.
    """
    client = anthropic.AsyncAnthropic(api_key=api_key)

    context = ""
    if resource and field:
        context = f"\nContext: this code will be used for the FHIR {resource}.{field} field."

    user_content = (
        f"Map this clinical phrase to medical terminology codes: \"{phrase}\"{context}\n"
        f"Return up to {max_suggestions} suggestions."
    )

    response = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "suggest_terminology_codes"},
        messages=[{"role": "user", "content": user_content}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "suggest_terminology_codes":
            raw = block.input.get("suggestions", [])
            return [
                TermSuggestion(
                    system=s["system"],
                    code=s["code"],
                    display=s["display"],
                    confidence=float(s["confidence"]),
                    reasoning=s.get("reasoning", ""),
                )
                for s in raw[:max_suggestions]
            ]

    return []
