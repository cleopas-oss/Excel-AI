import json


def extract_json_from_text(text: str):
    """
    Robust JSON extraction using bracket matching.
    Handles nested JSON safely.
    """

    if not text:
        return None

    start = text.find("{")
    if start == -1:
        return None

    stack = 0

    for i in range(start, len(text)):
        if text[i] == "{":
            stack += 1
        elif text[i] == "}":
            stack -= 1

            if stack == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None

    return None

