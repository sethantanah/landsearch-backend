import re


def to_float(value: str):
    converted_value = value
    try:
        numbers = re.findall(r"\d+\.?\d*", value)
        match = re.match(r"\d+\.?\d*", numbers[0])
        if match:
            converted_value = float(match.group())
    except Exception:
        return converted_value

    else:
        return converted_value
