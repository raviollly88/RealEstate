"""Собирает web/index.html: вшивает data/complexes.csv в шаблон (страница работает без сервера)."""
from pathlib import Path

root = Path(__file__).resolve().parent.parent
csv_text = (root / "data" / "complexes.csv").read_text(encoding="utf-8").replace("\\", "\\\\").replace("`", "\\`")
html = (root / "web" / "template.html").read_text(encoding="utf-8").replace("__CSV__", csv_text)
(root / "web" / "index.html").write_text(html, encoding="utf-8")
print("web/index.html собран")
