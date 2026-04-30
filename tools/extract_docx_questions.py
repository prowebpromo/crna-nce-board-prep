import argparse
import html
import json
import re
import zipfile
from pathlib import Path

QUESTION_ID_RE = re.compile(r"^Q(\d{3})$", re.IGNORECASE)
CHOICE_RE = re.compile(r"^([A-E])[\).:-]\s*(.+)")
ANSWER_RE = re.compile(r"^Answer:\s*([A-E])", re.IGNORECASE)

def docx_paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as docx:
        xml = docx.read("word/document.xml").decode("utf-8")
    out = []
    for paragraph in re.findall(r"<w:p[\s\S]*?</w:p>", xml):
        runs = re.findall(r"<w:t[^>]*>(.*?)</w:t>", paragraph)
        text = html.unescape("".join(runs)).strip()
        if text:
            out.append(text)
    return out

def domain_from_path(path: Path) -> str:
    name = path.name.lower()
    if "stage2" in name or "basicsciences" in name:
        return "Basic Sciences"
    if "stage3" in name or "equipment" in name:
        return "Equipment, Instrumentation, and Technology"
    if "stage4" in name or "generalprinciples" in name:
        return "General Principles of Anesthesia"
    if "stage5" in name or "surgical" in name:
        return "Surgical Procedures and Special Populations"
    return "Uncategorized"

def parse_questions(paths: list[Path]) -> list[dict]:
    questions = []
    current = None
    for path in paths:
        domain = domain_from_path(path)
        state = "seeking"
        meta_seen = 0
        for line in docx_paragraphs(path):
            qid = QUESTION_ID_RE.match(line)
            choice = CHOICE_RE.match(line)
            answer = ANSWER_RE.match(line)
            if qid:
                if current:
                    questions.append(current)
                current = {"id": f"Q{int(qid.group(1)):03d}", "domain": domain, "title": "", "difficulty": "", "format": "", "stem": "", "choices": {}, "answer": "", "rationale": ""}
                state = "metadata"
                meta_seen = 0
                continue
            if not current:
                continue
            if answer:
                current["answer"] = answer.group(1).upper()
                state = "rationale"
                continue
            if line.lower().startswith("reasoning skill:"):
                current["reasoning_skill"] = line.split(":", 1)[1].strip()
                state = "rationale"
                continue
            if state == "metadata":
                meta_seen += 1
                if meta_seen == 1:
                    current["title"] = line
                elif meta_seen == 2:
                    current["difficulty"] = line
                elif meta_seen == 3:
                    current["format"] = line
                else:
                    current["stem"] = (current["stem"] + " " + line).strip()
                    state = "stem"
            elif state != "rationale" and choice:
                key, text = choice.groups()
                current["choices"][key.upper()] = text.strip()
                state = "choices"
            elif state == "rationale" or current["choices"]:
                current["rationale"] = (current["rationale"] + " " + line).strip()
            else:
                current["stem"] = (current["stem"] + " " + line).strip()
    if current:
        questions.append(current)
    return questions

def main() -> None:
    parser = argparse.ArgumentParser(description="Convert CRNA NCE staged Word docs into app-ready JSON.")
    parser.add_argument("--questions", nargs="+", required=True)
    parser.add_argument("--out", default="data/questions.json")
    args = parser.parse_args()
    questions = parse_questions([Path(p) for p in args.questions])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"questions": questions}, indent=2), encoding="utf-8")
    print(f"Wrote {len(questions)} questions to {out}")

if __name__ == "__main__":
    main()
