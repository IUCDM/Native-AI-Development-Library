"""Build the Hugging Face dataset for the Spiral of Radiance.

OUT gets:
  README.md                 the dataset card (hf/README.md)
  <the Spiral folder>       project instructions, project index, 24 frameworks,
                            ABOUT, LICENSE, reading and prompt guides, Start Here PDF
  data/principles.jsonl     one row per principle (532), in spiral order

Usage: python hf/build.py OUT  (run by .github/workflows/sync-huggingface.yml)
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SPIRAL = "03-Spiral-of-Radiance"
OUT = Path(sys.argv[1]).resolve()


def decode(raw: bytes) -> str:
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


files = subprocess.run(
    ["git", "ls-files", SPIRAL], cwd=REPO, capture_output=True, text=True, check=True
).stdout.split("\n")
files = [f for f in files if f]

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
for f in files:
    shutil.copy2(REPO / f, OUT / Path(f).name)
shutil.copy2(REPO / "hf" / "README.md", OUT / "README.md")

# Titles from Section 16 of the project index
index = decode((REPO / SPIRAL / "00-1_projectindex.md").read_bytes())
titles = dict(re.findall(r"^- \| (\S+-p\d+) \| Lines L\d+-L\d+ \| (.*?) \|\s*$", index, re.M))

rows = []
for fw_file in sorted(p for p in (REPO / SPIRAL).glob("[01][0-9]-[0-9]_*.md") if not p.name.startswith("00")):
    text = decode(fw_file.read_bytes()).replace("\r\n", "\n")
    lines = text.split("\n")
    head = dict(
        (k.strip(), v.strip())
        for k, v in (l.split(":", 1) for l in lines[:8] if ":" in l)
    )
    code = head["FRAMEWORK_CODE"].strip("[]")
    phase = head["GLOBAL_PHASE_ORDER"]
    for m in re.finditer(r'<PRINCIPLE id="([^"]+)">\n(.*?)</PRINCIPLE>', text, re.S):
        pid = m.group(1)
        start = text.count("\n", 0, m.start()) + 1
        end = text.count("\n", 0, m.end()) + 1
        rows.append({
            "code": pid,
            "framework": code,
            "framework_title": head["FRAMEWORK_TITLE"],
            "file": fw_file.name,
            "phase": phase,
            "framework_order": int(head["GLOBAL_FRAMEWORK_ORDER"]),
            "position": int(pid.rsplit("-p", 1)[1]),
            "title": titles.get(pid, ""),
            "lines": f"L{start}-L{end}",
            "text": m.group(2).strip(),
        })

assert len(rows) == 532, len(rows)
missing = [r["code"] for r in rows if not r["title"]]
assert not missing, missing

(OUT / "data").mkdir()
with open(OUT / "data" / "principles.jsonl", "w", encoding="utf-8") as fh:
    for r in rows:
        fh.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"{len(files)} files copied, {len(rows)} principles in data/principles.jsonl")
