Use `learn_ask_question` during learn sessions to quiz the user on codebase knowledge, coding patterns, or current tasks.

## When to Use

- During an active learn session triggered by the user
- When the learn panel is open and ready to display questions
- To quiz the user based on their configured content categories and question format preferences

## Question Format

Each `LearnQuestion` must contain **exactly one** of:
- `multiple_choice`: A question with 2-4 choices and a `correct_answer` that must be one of the choices
- `open_ended`: A question with a reference `answer` for self-evaluation

Each question also requires:
- `skill`: A free-form string describing the competency being tested (e.g. `"git"`, `"python"`, `"design_patterns"`, `"async_programming"`)
- `difficulty`: One of `"easy"`, `"medium"`, or `"hard"`

```json
{
  "questions": [
    {
      "multiple_choice": {
        "question": "What does `git rebase` do?",
        "choices": [
          "Merges branches by creating a merge commit",
          "Replays commits on a new base",
          "Permanently deletes a branch"
        ],
        "correct_answer": "Replays commits on a new base"
      },
      "skill": "git",
      "difficulty": "easy"
    },
    {
      "open_ended": {
        "question": "Explain the purpose of a `.gitignore` file.",
        "answer": "A .gitignore file tells Git which files or directories to ignore and not track."
      },
      "skill": "git",
      "difficulty": "easy"
    }
  ]
}
```

## Key Constraints

- **Questions count**: 1-10 per call, typically 5
- **MC choices**: 2-4 per question
- **MC correct_answer**: Must exactly match one of the `choices` strings
- **Exactly one type**: Each `LearnQuestion` must set either `multiple_choice` or `open_ended`, not both
- **skill**: Free-form string describing the competency tested
- **difficulty**: Must be one of `"easy"`, `"medium"`, `"hard"`

## Tips

1. Respect the user's learn config settings: `learn_questions_format` (Multiple choice / Open-ended / Mixed) and content category toggles (codebase, coding patterns, current tasks)
2. Vary question difficulty within a session
3. For open-ended questions, provide a clear reference answer that helps the user self-evaluate
4. Avoid repeating questions the user has already seen in the current session
