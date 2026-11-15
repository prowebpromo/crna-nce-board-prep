import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.locator('#pStem')).not.toBeEmpty();
  expect(errors).toEqual([]);
});

test('bundled question bank has unique usable questions and answer rationales', async ({ page }) => {
  const issues = await page.evaluate(() => {
    const seen = new Set(), errors = [];
    for (const q of QUESTIONS) {
      if (!q.id || seen.has(q.id)) errors.push(`Duplicate/missing ID: ${q.id}`);
      seen.add(q.id);
      if (!q.stem || !q.domain || !q.difficulty || !q.choices[q.answer]) errors.push(`Incomplete: ${q.id}`);
      for (const letter of Object.keys(q.choices)) {
        if (!q.rationales?.[letter]?.text) errors.push(`Missing rationale: ${q.id}/${letter}`);
      }
    }
    return { count: QUESTIONS.length, errors };
  });
  expect(issues.count).toBeGreaterThan(0);
  expect(issues.errors).toEqual([]);
});

test('practice answer, flag, review and saved progress survive reload', async ({ page }) => {
  await page.locator('[data-view="practice"]').click();
  const question = await page.evaluate(() => ({ id: practiceQ.id, answer: practiceQ.answer }));
  const wrong = ['A', 'B', 'C', 'D'].find(letter => letter !== question.answer);
  await page.locator(`#pChoices [data-letter="${wrong}"]`).click();
  await page.locator('#checkBtn').click();
  await expect(page.locator('#pFeedback')).toContainText('Incorrect');
  await expect(page.locator('#pFeedback .rat-item')).toHaveCount(4);
  await page.locator('#flagBtn').click();
  await page.reload();
  const saved = await page.evaluate(id => JSON.parse(localStorage.getItem('crna-nce-v3'))[id], question.id);
  expect(saved).toMatchObject({ attempts: 1, correct: 0, lastCorrect: false, lastAnswer: wrong, flagged: true });
  await page.locator('[data-view="review"]').click();
  await expect(page.locator('#reviewList')).toContainText(question.id);
  await page.locator('#reviewFilter').selectOption('flagged');
  await expect(page.locator('#reviewList')).toContainText(question.id);
});

test('ten-question exam scores answers and saves all attempts', async ({ page }) => {
  await page.locator('[data-view="exam"]').click();
  await page.locator('#examSize').fill('10');
  await page.locator('#examSetup button[onclick="startExam()"]').click();
  await expect(page.locator('#examQTotal')).toHaveText('10');
  for (let i = 0; i < 10; i++) {
    const answer = await page.evaluate(() => examState.questions[examState.index].answer);
    await page.locator(`#eChoices [data-letter="${answer}"]`).click();
    if (i < 9) await page.locator('#examNextBtn').click();
  }
  await page.locator('#examFinishBtn').click();
  await expect(page.locator('#resultsGrid')).toContainText('100%');
  await expect(page.locator('#resultsGrid')).toContainText('10/10');
  const saved = await page.evaluate(() => Object.values(JSON.parse(localStorage.getItem('crna-nce-v3'))));
  expect(saved).toHaveLength(10);
  expect(saved.every(entry => entry.attempts === 1 && entry.correct === 1)).toBe(true);
});
