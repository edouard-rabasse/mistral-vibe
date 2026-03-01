Use `learn_save_context` after a learn quiz session completes to persist the learning results.

## When to Use

- After the user finishes answering all questions in a learn session
- Pass through the result data collected from `learn_ask_question`

## Parameters

- `question`: The question text that was asked
- `user_answer`: The answer the user provided
- `correct_answer`: The correct/reference answer
- `was_correct`: Whether the user answered correctly
- `skill`: The skill being tested (e.g. `"git"`, `"python"`, `"design_patterns"`)
- `difficulty`: The difficulty level of the question (`"easy"`, `"medium"`, `"hard"`)

## Example

```json
{
  "question": "What does `git rebase` do?",
  "user_answer": "Replays commits on a new base",
  "correct_answer": "Replays commits on a new base",
  "was_correct": true,
  "skill": "git",
  "difficulty": "easy"
}
```

## Tips

1. Call once per answered question after the session summary
2. Include all fields accurately from the quiz results
