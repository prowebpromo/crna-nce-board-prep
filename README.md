# CRNA NCE Board-Prep System

Interactive CRNA NCE board-prep app with practice mode, timed exam mode, rationale review, confidence flags, and progress tracking.

## GitHub Pages

This app is static and can run on GitHub Pages. No backend is required.

1. Open `Settings` -> `Pages` in this repository.
2. Under `Build and deployment`, choose `GitHub Actions`.
3. The workflow at `.github/workflows/pages.yml` publishes the site.

The app stores study progress in each browser's local storage. Keep the full CRNA question bank in a private repo unless you are comfortable publishing that content.

## Question Bank

Use the Library tab to import JSON in this shape:

```json
{
  "questions": [
    {
      "id": "Q001",
      "domain": "Basic Sciences",
      "stem": "Question text",
      "choices": { "A": "Choice A", "B": "Choice B", "C": "Choice C", "D": "Choice D" },
      "answer": "A",
      "rationale": "Why the answer is correct."
    }
  ]
}
```

_Last deploy trigger: 2026-04-30._
