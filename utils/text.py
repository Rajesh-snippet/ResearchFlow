import re


def slugify(text: str) -> str:
    """
    Convert text into a filesystem-safe slug.
    Example:
        "Hello World!" -> "hello-world"
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")