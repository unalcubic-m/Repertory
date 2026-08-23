import unicodedata

CATALOGUE_PREFIXES = ("bwv", "k", "rv", "d", "op", "no")


def normalize_answer(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    converted: list[str] = []
    for character in value:
        if character.isdecimal():
            converted.append(str(unicodedata.decimal(character)))
        else:
            converted.append(character)

    folded = "".join(converted).casefold()
    normalized: list[str] = []
    for character in folded:
        category = unicodedata.category(character)
        if character in {"'", "\u2019", "\u02bc", "`"}:
            continue
        if category.startswith(("P", "S")):
            normalized.append(" ")
        else:
            normalized.append(character)
    result = " ".join("".join(normalized).split())

    for prefix in CATALOGUE_PREFIXES:
        if result.startswith(prefix) and len(result) > len(prefix):
            suffix = result[len(prefix) :]
            if suffix[0].isdigit():
                result = f"{prefix} {suffix}"
    return result


def match_answer(part: object, submitted: str) -> tuple[bool, str | None]:
    normalized = normalize_answer(submitted)
    canonical = normalize_answer(part.canonical_answer)  # type: ignore[attr-defined]
    if normalized == canonical:
        return True, part.canonical_answer  # type: ignore[attr-defined]
    for alias in part.aliases.filter(active=True):  # type: ignore[attr-defined]
        if alias.normalized_value == normalized:
            return True, alias.value
    return False, None
