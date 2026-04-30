import argparse
import html
import json
import re
import zipfile
from pathlib import Path

QUESTION_RE = re.compile(r"^(?:Question\s*)?(\d{1,3})[\).\s:-]+(.+)", re.IGNORECASE)
CHOICE_RE = re.compile(r"^([A-E])[\).\s:-]+(.+)")
ANSWER_RE = re.compile(r"^(?:Question\s*)?(\d{1,3})[\).\s:-]+(?:Answer\s*)?([A-E])(?:\b|[\).\s:-])?(.*)", re.IGNORECASE)
RATIONALE_RE = re.compile(r"^(?:Rationale|Explanation)[:\s-]+(.+)", re.IGNORECASE)

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

def parse_questions(paths: list[Path]) -> list[dict]:
    questions, current = [], None
    domain = "Uncategorized"
    for path in paths:
        for line in docx_paragraphs(path):
            if re.search(r"basic sciences", line, re.I): domain = "Basic Sciences"
            elif re.search(r"equipment", line, re.I): domain = "Equipment, Instrumentation, and Technology"
            elif re.search(r"general principles", line, re.I): domain = "General Principles of Anesthesia"
            elif re.search(r"surgical|special populations", line, re.I): domain = "Surgical Procedures and Special Populations"
            elif re.search(r"mock exam|comprehensive", line, re.I): domain = "Mock Exam"
            qm, cm = QUESTION_RE.match(line), CHOICE_RE.match(line)
            if qm and not cm:
                if current: questions.append(current)
                number, stem = qm.groups()
                current = {"id": f"Q{int(number):03d}", "domain": domain, "stem": stem.strip(), "choices": {}, "answer": "", "rationale": ""}
            elif current and cm:
                key, text = cm.groups(); current["choices"][key.upper()] = text.strip()
            elif current and line:
                field = "rationale" if current["choices"] else "stem"
                current[field] = (current[field] + " " + line).strip()
    if current: questions.append(current)
    return questions

def parse_answers(path: Path) -> dict[str, dict]:
    answers, current_id = {}, None
    for line in docx_paragraphs(path):
        am = ANSWER_RE.match(line)
        if am:
            number, answer, tail = am.groups()
            current_id = f"Q{int(number):03d}"
            answers[current_id] = {"answer": answer.upper(), "rationale": tail.strip()}
        elif current_id and (rm := RATIONALE_RE.match(line)):
            answers[current_id]["rationale"] = rm.group(1).strip()
        elif current_id and line:
            answers[current_id]["rationale"] = (answers[current_id].get("rationale", "") + " " + line).strip()
    return answers

def main() -> None:
    parser = argparse.ArgumentParser(description="Convert CRNA NCE Word docs into app-ready JSON.")
    parser.add_argument("--questions", nargs="+", required=True)
    parser.add_argument("--answers")
    parser.add_argument("--out", default="data/questions.json")
    args = parser.parse_args()
    questions = parse_questions([Path(p) for p in args.questions])
    if args.answers:
        answers = parse_answers(Path(args.answers))
        for question in questions:
            if question["id"] in answers:
                question.update({k: v for k, v in answers[question["id"]].items() if v})
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"questions": questions}, indent=2), encoding="utf-8")
    print(f"Wrote {len(questions)} questions to {out}")

if __name__ == "__main__":
    main()
