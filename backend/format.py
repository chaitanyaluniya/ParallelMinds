import re


def strip_md(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text


def fmt_summary(text: str) -> str:
    text = strip_md(text)
    for label in ["ONE-LINE:", "BULLETS:", "PARAGRAPH:"]:
        text = re.sub(rf"\s*{re.escape(label)}", f"\n\n{label}\n", text, flags=re.I)
    return re.sub(r"\n{3,}", "\n\n", text).strip()
