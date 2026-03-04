import random, string, unicodedata

def normalize_swedish(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")

def generate_sku(name:str):
    clean_name = normalize_swedish(name)
    prefix = clean_name.replace(" ", "")[:3].upper().ljust(3, "-")
    digits = ''.join(random.choices(string.digits, k=6))

    sku = f"{prefix}{digits}"
    return sku