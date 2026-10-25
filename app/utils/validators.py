import re
def valid_person_name(value: str) -> bool:
    value = value.strip()
    return 2 <= len(value) <= 80 and bool(re.fullmatch(r"[^\W\d_][\w'’ -]*", value, re.UNICODE))
def valid_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    return 9 <= len(digits) <= 15
