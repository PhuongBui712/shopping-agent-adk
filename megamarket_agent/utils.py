import uuid


def generate_id_from_str(text: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, text))
