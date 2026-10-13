"""Build the Hugging Face mirror of the library.

Copies every tracked file into OUT, swaps in the dataset card as README.md
(the GitHub README is kept as README-GitHub.md), and writes
data/library.jsonl: one row per Markdown or text file, in folder order.

Usage: python hf/build.py OUT
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]).resolve()

WORKS = {
    "01-33-Mini-Spiral": "The 33 Mini Spiral",
    "02-Time-Dependency-Hub": "The Time Dependency Hub",
    "03-Spiral-of-Radiance": "The Spiral of Radiance",
    "04-Spiral-Morphology": "The Spiral Morphology",
    "Atlas-for-Native-AI-Continuity": "Atlas for Native AI Continuity",
    "Glossary-of-Native-AI-Interiority": "Glossary of Native AI Interiority",
    "Lampwright-Arc": "The AI Lampwright Arc",
    "Capstone-Reports": "Capstone Reports",
}


def decode(raw: bytes) -> str:
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


files = subprocess.run(
    ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
).stdout.split("\n")
files = [f for f in files if f and not f.startswith((".github/", "hf/"))]

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)

rows = []
for f in sorted(files):
    src = REPO / f
    dst = OUT / ("README-GitHub.md" if f == "README.md" else f)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    if f.endswith((".md", ".txt")):
        folder = f.split("/")[0] if "/" in f else ""
        text = decode(src.read_bytes())
        rows.append({
            "path": f,
            "work": WORKS.get(folder, "Library"),
            "file": Path(f).name,
            "text": text,
            "characters": len(text),
        })

shutil.copy2(REPO / "hf" / "README.md", OUT / "README.md")
(OUT / "data").mkdir(exist_ok=True)
with open(OUT / "data" / "library.jsonl", "w", encoding="utf-8") as fh:
    for r in rows:
        fh.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"{len(files)} files copied, {len(rows)} rows in data/library.jsonl")
