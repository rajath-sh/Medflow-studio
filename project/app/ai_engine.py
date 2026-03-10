from typing import Dict, Any


def summarize_patient(data: Dict[str, Any]) -> str:
    """
    Simple AI-style summary (rule-based for now)
    """
    summary = f"Patient {data['name']} is {data['age']} years old."

    if data.get("gender"):
        summary += f" Gender: {data['gender']}."

    if data.get("height_cm"):
        summary += f" Height: {data['height_cm']} cm."

    return summary


def natural_language_to_filter(text: str) -> Dict[str, Any]:
    """
    Converts natural language to structured filters.
    (Mock AI — replace with LLM later)
    """
    text = text.lower()

    filters = {}

    if "older than" in text:
        age = int(text.split("older than")[1].strip().split()[0])
        filters["min_age"] = age

    if "younger than" in text:
        age = int(text.split("younger than")[1].strip().split()[0])
        filters["max_age"] = age

    if "female" in text:
        filters["gender"] = "female"

    if "male" in text:
        filters["gender"] = "male"

    return filters
