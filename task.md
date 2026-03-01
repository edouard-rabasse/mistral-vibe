Remember I am currently trying to implement a learning panel. I implemented all the visual and UI for this learn panel, and an agent that generate questions, currently using only the codebase as context. The goal is now to extend the context used to generate the questions to 2 other elements: the main chat context and the usermemory.yaml.

- For the main chat context, it will remain independant from the main coding agent running in the main panel and not interfere with the coding process. It will just use the conversation to add to the context.
- For the usermemory context, this will be used by the chat to understand what skills the user already built, to better ask questions on what is not mastered yet or where only easy questions were asked.

The agent must create questions in priority on things (try to have a mix of all):
1) that were recently implemented by the main coding agent (cf main chat context)
2) on skills that the user need to master (cf usermemory)

Here is a sample of the usermemory:

learned_skills:
- correct_answer: vibe/
  difficulty: easy
  question: Which directory contains the main source code for the mistral-vibe project?
  skill: project_structure
  timestamp: '2026-03-01T14:16:08.520920'
  user_answer: vibe/
  was_correct: true
- correct_answer: It contains GitHub Actions workflows for CI/CD, such as build, test,
    and release automation.
  difficulty: medium
  question: What is the purpose of the `.github/workflows/` directory in the mistral-vibe
    project?
  skill: ci_cd_pipelines
  timestamp: '2026-03-01T14:16:33.986271'
  user_answer: test answer
  was_correct: false
