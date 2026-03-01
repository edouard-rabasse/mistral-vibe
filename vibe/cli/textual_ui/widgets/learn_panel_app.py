from __future__ import annotations

import enum
import logging
import random
from typing import TYPE_CHECKING, ClassVar, Self

if TYPE_CHECKING:
    from vibe.core.config import VibeConfig

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Input

from vibe.cli.textual_ui.widgets.no_markup_static import NoMarkupStatic
from vibe.core.tools.builtins.learn_ask_question import (
    LearnQuestion,
    LearnQuestionResult,
    MultipleChoiceQuestion,
    OpenEndedQuestion,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mock data & helpers
# ---------------------------------------------------------------------------

# Each entry is (content_category, LearnQuestion) — category is mock-only
# filtering metadata not part of the LearnQuestion model.
MOCK_QUESTIONS: list[tuple[str, LearnQuestion]] = [
    # ── codebase / multiple_choice ──────────────────────────────────
    (
        "codebase",
        LearnQuestion(multiple_choice=MultipleChoiceQuestion(
            question="What does `git rebase` do?",
            choices=[
                "Merges branches by creating a merge commit",
                "Replays commits on a new base",
                "Permanently deletes a branch",
                "Creates an annotated tag",
            ],
            correct_answer="Replays commits on a new base",
        ), skill="git", difficulty="easy"),
    ),
    (
        "codebase",
        LearnQuestion(multiple_choice=MultipleChoiceQuestion(
            question="Which command stages all changes for the next commit?",
            choices=[
                "git commit -a",
                "git add .",
                "git push",
                "git stash",
            ],
            correct_answer="git add .",
        ), skill="git", difficulty="easy"),
    ),
    (
        "codebase",
        LearnQuestion(multiple_choice=MultipleChoiceQuestion(
            question="What does `git stash pop` do?",
            choices=[
                "Deletes the stash permanently",
                "Applies the most recent stash and removes it from the stash list",
                "Creates a new stash from staged changes only",
                "Pushes the current branch to the remote",
            ],
            correct_answer="Applies the most recent stash and removes it from the stash list",
        ), skill="git", difficulty="medium"),
    ),
    (
        "codebase",
        LearnQuestion(multiple_choice=MultipleChoiceQuestion(
            question="In a typical Python project, what is the purpose of `__init__.py`?",
            choices=[
                "It configures the test runner",
                "It marks a directory as a Python package",
                "It stores environment variables",
                "It lists all public API symbols for external use",
            ],
            correct_answer="It marks a directory as a Python package",
        ), skill="python", difficulty="easy"),
    ),
    # ── codebase / open_ended ───────────────────────────────────────
    (
        "codebase",
        LearnQuestion(open_ended=OpenEndedQuestion(
            question="What is the difference between `git merge` and `git rebase`?",
            answer=(
                "`git merge` integrates changes by creating a merge commit, preserving "
                "the full history. `git rebase` rewrites history by replaying commits "
                "on top of another branch, producing a linear history."
            ),
        ), skill="git", difficulty="medium"),
    ),
    (
        "codebase",
        LearnQuestion(open_ended=OpenEndedQuestion(
            question="Explain the purpose of a `.gitignore` file.",
            answer=(
                "A `.gitignore` file tells Git which files or directories to ignore and "
                "not track. This commonly includes build artifacts, IDE settings, and "
                "secrets such as `.env` files."
            ),
        ), skill="git", difficulty="easy"),
    ),
    (
        "codebase",
        LearnQuestion(open_ended=OpenEndedQuestion(
            question="What does `git cherry-pick` do and when would you use it?",
            answer=(
                "`git cherry-pick` applies the changes introduced by an existing commit "
                "onto the current branch. It is useful when you want to bring a specific "
                "fix from one branch into another without merging the entire branch."
            ),
        ), skill="git", difficulty="hard"),
    ),
    # ── coding_patterns / multiple_choice ───────────────────────────
    (
        "coding_patterns",
        LearnQuestion(multiple_choice=MultipleChoiceQuestion(
            question="What does a Python decorator do?",
            choices=[
                "Compiles a function to native code",
                "Wraps a function to extend or modify its behavior",
                "Converts a class into a singleton",
                "Pins a module's public API",
            ],
            correct_answer="Wraps a function to extend or modify its behavior",
        ), skill="python", difficulty="easy"),
    ),
    (
        "coding_patterns",
        LearnQuestion(multiple_choice=MultipleChoiceQuestion(
            question="Which design pattern ensures a class has only one instance?",
            choices=[
                "Factory",
                "Observer",
                "Singleton",
                "Strategy",
            ],
            correct_answer="Singleton",
        ), skill="design_patterns", difficulty="easy"),
    ),
    (
        "coding_patterns",
        LearnQuestion(multiple_choice=MultipleChoiceQuestion(
            question="What is the primary purpose of dependency injection?",
            choices=[
                "To speed up module import time",
                "To decouple a class from the creation of its dependencies",
                "To enforce strict typing at runtime",
                "To automatically generate unit tests",
            ],
            correct_answer="To decouple a class from the creation of its dependencies",
        ), skill="design_patterns", difficulty="medium"),
    ),
    (
        "coding_patterns",
        LearnQuestion(multiple_choice=MultipleChoiceQuestion(
            question="In the context of async Python, what does `await` do?",
            choices=[
                "Blocks the OS thread until the coroutine finishes",
                "Suspends the current coroutine and yields control to the event loop",
                "Creates a new thread for the coroutine",
                "Forces garbage collection before continuing",
            ],
            correct_answer="Suspends the current coroutine and yields control to the event loop",
        ), skill="async_programming", difficulty="medium"),
    ),
    # ── coding_patterns / open_ended ────────────────────────────────
    (
        "coding_patterns",
        LearnQuestion(open_ended=OpenEndedQuestion(
            question="Explain what a Python decorator does and give a common use-case.",
            answer=(
                "A decorator is a function that takes another function as input, wraps it "
                "to add behavior, and returns the wrapped function. Common use-cases include "
                "logging, caching (e.g., `@lru_cache`), access control, and timing."
            ),
        ), skill="python", difficulty="medium"),
    ),
    (
        "coding_patterns",
        LearnQuestion(open_ended=OpenEndedQuestion(
            question="What is the difference between a generator and a regular function in Python?",
            answer=(
                "A generator uses `yield` instead of `return` and produces values lazily "
                "one at a time, suspending execution between calls. A regular function runs "
                "to completion and returns a single value."
            ),
        ), skill="python", difficulty="medium"),
    ),
    (
        "coding_patterns",
        LearnQuestion(open_ended=OpenEndedQuestion(
            question="Explain the Open/Closed Principle from SOLID.",
            answer=(
                "The Open/Closed Principle states that software entities should be open for "
                "extension but closed for modification. You add new behavior by extending "
                "(e.g., subclassing or composing) rather than changing existing code."
            ),
        ), skill="design_patterns", difficulty="hard"),
    ),
    # ── current_tasks / multiple_choice ─────────────────────────────
    (
        "current_tasks",
        LearnQuestion(multiple_choice=MultipleChoiceQuestion(
            question="What Textual widget class does `LearnPanelApp` extend?",
            choices=[
                "Widget",
                "App",
                "Container",
                "Screen",
            ],
            correct_answer="Container",
        ), skill="textual", difficulty="easy"),
    ),
    (
        "current_tasks",
        LearnQuestion(multiple_choice=MultipleChoiceQuestion(
            question="In Textual, which method must a widget implement to declare its child widgets?",
            choices=[
                "__init__",
                "compose",
                "on_mount",
                "render",
            ],
            correct_answer="compose",
        ), skill="textual", difficulty="easy"),
    ),
    (
        "current_tasks",
        LearnQuestion(multiple_choice=MultipleChoiceQuestion(
            question="Which config field controls the learn question format in this project?",
            choices=[
                "learn_mode",
                "learn_questions_format",
                "question_type",
                "learn_format_setting",
            ],
            correct_answer="learn_questions_format",
        ), skill="project_config", difficulty="medium"),
    ),
    (
        "current_tasks",
        LearnQuestion(multiple_choice=MultipleChoiceQuestion(
            question="What does `reactive` provide in a Textual widget?",
            choices=[
                "Async task scheduling",
                "Automatic re-rendering when a value changes",
                "Database persistence of widget state",
                "CSS class toggling",
            ],
            correct_answer="Automatic re-rendering when a value changes",
        ), skill="textual", difficulty="medium"),
    ),
    # ── current_tasks / open_ended ───────────────────────────────────
    (
        "current_tasks",
        LearnQuestion(open_ended=OpenEndedQuestion(
            question="Describe the lifecycle phases of a quiz session in LearnPanelApp.",
            answer=(
                "The panel moves through four phases: ASKING (user sees the question and "
                "selects or types an answer), VALIDATING (user sees correct/incorrect "
                "feedback and self-marks open-ended answers), SUMMARY (results for all "
                "questions are shown), and REVIEWING (read-only playback of individual "
                "answered questions from the summary)."
            ),
        ), skill="project_architecture", difficulty="hard"),
    ),
    (
        "current_tasks",
        LearnQuestion(open_ended=OpenEndedQuestion(
            question="Why is it important to track seen questions across sessions in LearnPanelApp?",
            answer=(
                "Without tracking, every new session would show the same filtered questions. "
                "Tracking ensures the user sees new questions each session and only cycles "
                "back to earlier ones after the entire pool is exhausted."
            ),
        ), skill="project_architecture", difficulty="medium"),
    ),
    (
        "current_tasks",
        LearnQuestion(open_ended=OpenEndedQuestion(
            question="What is the role of the `_switch_from_input` method in the Textual app?",
            answer=(
                "`_switch_from_input` hides or removes the current bottom widget, mounts the "
                "new widget into the bottom container, updates `_current_bottom_app`, and "
                "gives focus to the newly mounted widget."
            ),
        ), skill="textual", difficulty="hard"),
    ),
]

ENCOURAGEMENTS = [
    "Great effort! Every question makes you sharper.",
    "Keep it up! Practice is the key to mastery.",
    "Nice work! You're building solid foundations.",
    "Well done! Consistency beats perfection.",
    "Good session! Come back soon to reinforce what you learned.",
]


def _question_type(cat: str, q: LearnQuestion) -> str:
    """Return 'multiple_choice' or 'open_ended' for filtering."""
    return "multiple_choice" if q.multiple_choice is not None else "open_ended"


def mock_ask_questions(
    questions_format: str,
    active_categories: set[str],
    seen_indices: set[int],
) -> tuple[list[LearnQuestion], set[int]]:
    """Return filtered questions, avoiding repetition across sessions.

    Filters MOCK_QUESTIONS by type (from questions_format) and content_category
    (from active_categories), excludes already-seen indices, and shuffles the
    result. If all matching questions have been seen, resets automatically so
    the user always gets a non-empty list.

    Returns a tuple of (selected_questions, updated_seen_indices).
    """
    if questions_format == "Multiple choice":
        allowed_types = {"multiple_choice"}
    elif questions_format == "Open-ended":
        allowed_types = {"open_ended"}
    else:
        allowed_types = {"multiple_choice", "open_ended"}

    candidates = [
        (idx, q)
        for idx, (cat, q) in enumerate(MOCK_QUESTIONS)
        if _question_type(cat, q) in allowed_types and cat in active_categories
    ]

    if not candidates:
        return [], seen_indices

    unseen = [(idx, q) for idx, q in candidates if idx not in seen_indices]
    if not unseen:
        seen_indices = set()
        unseen = candidates

    random.shuffle(unseen)
    unseen = unseen[:5]
    selected = [q for _, q in unseen]
    new_seen = seen_indices | {idx for idx, _ in unseen}
    return selected, new_seen


def mock_save_context(
    question: str, user_answer: str, correct_answer: str, was_correct: bool
) -> None:
    """No-op mock -- would persist learning context in a real implementation."""
    logger.debug(
        "save_context: q=%r user=%r correct=%r ok=%s",
        question,
        user_answer,
        correct_answer,
        was_correct,
    )


# ---------------------------------------------------------------------------
# Quiz state
# ---------------------------------------------------------------------------


class Phase(enum.Enum):
    ASKING = "asking"
    VALIDATING = "validating"
    SUMMARY = "summary"
    REVIEWING = "reviewing"  # read-only review of a past question from summary


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class LearnPanelApp(Container):
    """Interactive quiz panel for the learn feature."""

    MAX_OPTIONS: ClassVar[int] = 5
    _SUMMARY_QUESTION_MAX_LEN: ClassVar[int] = 70

    can_focus = True
    can_focus_children = True

    selected_option: reactive[int] = reactive(0)

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("enter", "submit", "Submit", show=False),
        Binding("escape", "close", "Close", show=False),
    ]

    class Closed(Message):
        pass

    class QuestionAnswered(Message):
        """Posted after the summary is reached, carrying all quiz results."""

        def __init__(self, results: list[LearnQuestionResult]) -> None:
            super().__init__()
            self.results = results

    # ── lifecycle ────────────────────────────────────────────────────

    def __init__(self, config: VibeConfig) -> None:
        super().__init__(id="learnpanel-app")
        self._config = config
        self._seen_question_indices: set[int] = set()
        self._questions: list[LearnQuestion]
        self._questions, self._seen_question_indices = mock_ask_questions(
            questions_format=self._config.learn_questions_format,
            active_categories=self._active_categories(),
            seen_indices=self._seen_question_indices,
        )
        self._question_idx = 0
        self._phase = Phase.ASKING
        self._user_answer: str = ""
        # history of answered questions: idx -> (user_answer, was_correct)
        self._answered: dict[int, tuple[str, bool]] = {}
        self._results: list[LearnQuestionResult] = []

        # widgets -- populated in compose
        self._title_widget: NoMarkupStatic | None = None
        self._question_widget: NoMarkupStatic | None = None
        self._option_widgets: list[NoMarkupStatic] = []
        self._input_widget: Input | None = None
        self._feedback_widget: NoMarkupStatic | None = None
        self._validation_option_widgets: list[NoMarkupStatic] = []
        self._help_widget: NoMarkupStatic | None = None

    # ── helpers ──────────────────────────────────────────────────────

    def _active_categories(self) -> set[str]:
        """Return active content category strings based on current config."""
        categories: set[str] = set()
        if self._config.learn_content_codebase:
            categories.add("codebase")
        if self._config.learn_content_coding_patterns:
            categories.add("coding_patterns")
        if self._config.learn_content_current_tasks:
            categories.add("current_tasks")
        return categories

    # ── properties ───────────────────────────────────────────────────

    @property
    def _current_q(self) -> LearnQuestion:
        return self._questions[self._question_idx]

    @property
    def _is_mc(self) -> bool:
        return self._current_q.multiple_choice is not None

    @property
    def _q_text(self) -> str:
        if self._current_q.multiple_choice is not None:
            return self._current_q.multiple_choice.question
        assert self._current_q.open_ended is not None
        return self._current_q.open_ended.question

    @property
    def _q_choices(self) -> list[str]:
        if self._current_q.multiple_choice is not None:
            return self._current_q.multiple_choice.choices
        return []

    @property
    def _correct_answer(self) -> str:
        if self._current_q.multiple_choice is not None:
            return self._current_q.multiple_choice.correct_answer
        assert self._current_q.open_ended is not None
        return self._current_q.open_ended.answer

    @property
    def _all_answered(self) -> bool:
        return len(self._answered) == len(self._questions)

    # ── compose ──────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Vertical(id="learnpanel-content"):
            self._title_widget = NoMarkupStatic(
                "Learn Panel", classes="learnpanel-header"
            )
            yield self._title_widget

            self._question_widget = NoMarkupStatic("", classes="learnpanel-question")
            yield self._question_widget

            # MC option slots
            for _ in range(self.MAX_OPTIONS):
                w = NoMarkupStatic("", classes="learnpanel-option")
                self._option_widgets.append(w)
                yield w

            # open-ended input
            self._input_widget = Input(
                placeholder="Type your answer...", id="learnpanel-input"
            )
            yield self._input_widget

            # feedback area
            self._feedback_widget = NoMarkupStatic("", classes="learnpanel-feedback")
            yield self._feedback_widget

            # validation selector (Correct / Incorrect) for open-ended
            for _ in range(2):
                w = NoMarkupStatic("", classes="learnpanel-option")
                self._validation_option_widgets.append(w)
                yield w

            self._help_widget = NoMarkupStatic("", classes="learnpanel-help")
            yield self._help_widget

    def focus(self, scroll_visible: bool = True) -> Self:
        """Override focus to redirect to the input widget for open-ended questions."""
        if self._phase == Phase.ASKING and not self._is_mc and self._input_widget:
            self._input_widget.focus(scroll_visible=scroll_visible)
            return self
        return super().focus(scroll_visible=scroll_visible)

    async def on_mount(self) -> None:
        self._update_display()

    # ── rendering ────────────────────────────────────────────────────

    def _render_empty(self) -> None:
        if self._question_widget:
            self._question_widget.update(
                "No questions to display. Change settings with /learn"
            )
        self._hide_mc_options()
        self._hide_input()
        self._hide_feedback()
        self._hide_validation_options()
        if self._help_widget:
            self._help_widget.update("ESC close")

    def _update_display(self) -> None:
        if self._phase == Phase.SUMMARY:
            self._render_summary()
            return
        if self._phase == Phase.REVIEWING:
            self._render_review()
            return

        if not self._questions:
            self._render_empty()
            return

        progress = f"[{self._question_idx + 1}/{len(self._questions)}] "
        if self._question_widget:
            self._question_widget.update(progress + self._q_text)

        if self._phase == Phase.ASKING:
            self._render_asking()
        elif self._phase == Phase.VALIDATING:
            self._render_validating()

    def _render_asking(self) -> None:
        if self._is_mc:
            self._show_mc_options()
            self._hide_input()
        else:
            self._hide_mc_options()
            self._show_input()

        self._hide_feedback()
        self._hide_validation_options()
        self._update_help_asking()

    def _render_validating(self) -> None:
        if self._is_mc:
            self._show_mc_validation()
            self._hide_input()
            self._hide_validation_options()
        else:
            self._hide_mc_options()
            self._hide_input()
            self._show_open_ended_validation()

        self._update_help_validating()

    def _render_summary(self) -> None:
        correct_count = sum(1 for _, was_correct in self._answered.values() if was_correct)
        total = len(self._questions)

        if self._question_widget:
            self._question_widget.update(f"Results: {correct_count}/{total}")

        # Show per-question results in the option widgets
        for i, w in enumerate(self._option_widgets):
            if i < total:
                q = self._questions[i]
                user_ans, was_correct = self._answered.get(i, ("", False))
                mark = "v" if was_correct else "x"
                short_q = self._q_text_for(q)
                if len(short_q) > self._SUMMARY_QUESTION_MAX_LEN:
                    short_q = short_q[:self._SUMMARY_QUESTION_MAX_LEN - 3] + "..."
                w.update(f"  {mark}  Q{i + 1}. {short_q}")
                w.display = True
                w.remove_class(
                    "learnpanel-option-selected",
                    "learnpanel-correct",
                    "learnpanel-incorrect",
                )
                w.add_class("learnpanel-correct" if was_correct else "learnpanel-incorrect")
            else:
                w.update("")
                w.display = False

        self._hide_input()
        self._hide_validation_options()

        encouragement = random.choice(ENCOURAGEMENTS)
        if self._feedback_widget:
            self._feedback_widget.update(encouragement)
            self._feedback_widget.display = True
            self._feedback_widget.remove_class("learnpanel-correct", "learnpanel-incorrect")

        if self._help_widget:
            self._help_widget.update("Left/Right review questions  Enter new session  ESC close")

    def _render_review(self) -> None:
        """Read-only review of an answered question from the summary."""
        progress = f"[{self._question_idx + 1}/{len(self._questions)}] "
        if self._question_widget:
            self._question_widget.update(progress + self._q_text)

        user_answer, was_correct = self._answered[self._question_idx]
        self._user_answer = user_answer

        if self._is_mc:
            self._show_mc_validation()
            self._hide_input()
            self._hide_validation_options()
        else:
            self._hide_mc_options()
            self._hide_input()
            self._show_open_ended_review(was_correct)

        if self._help_widget:
            self._help_widget.update("Left/Right review questions  Enter back to summary  ESC close")

    # ── static helpers ──────────────────────────────────────────────

    @staticmethod
    def _q_text_for(q: LearnQuestion) -> str:
        """Extract question text from a LearnQuestion."""
        if q.multiple_choice is not None:
            return q.multiple_choice.question
        assert q.open_ended is not None
        return q.open_ended.question

    # ── MC asking ────────────────────────────────────────────────────

    def _show_mc_options(self) -> None:
        choices = self._q_choices
        for i, w in enumerate(self._option_widgets):
            if i < len(choices):
                is_sel = i == self.selected_option
                cursor = "> " if is_sel else "  "
                w.update(f"{cursor}{i + 1}. {choices[i]}")
                w.display = True
                w.remove_class("learnpanel-option-selected")
                if is_sel:
                    w.add_class("learnpanel-option-selected")
            else:
                w.update("")
                w.display = False

    def _hide_mc_options(self) -> None:
        for w in self._option_widgets:
            w.update("")
            w.display = False

    # ── MC validation ────────────────────────────────────────────────

    def _show_mc_validation(self) -> None:
        choices = self._q_choices
        correct = self._correct_answer
        user_choice = self._user_answer

        for i, w in enumerate(self._option_widgets):
            if i < len(choices):
                choice = choices[i]
                if choice == correct:
                    w.update(f"  {i + 1}. {choice}  [correct]")
                    w.remove_class("learnpanel-option-selected")
                    w.add_class("learnpanel-correct")
                elif choice == user_choice and user_choice != correct:
                    w.update(f"  {i + 1}. {choice}  [wrong]")
                    w.remove_class("learnpanel-option-selected")
                    w.add_class("learnpanel-incorrect")
                else:
                    w.update(f"  {i + 1}. {choice}")
                    w.remove_class("learnpanel-option-selected")
                    w.remove_class("learnpanel-correct")
                    w.remove_class("learnpanel-incorrect")
                w.display = True
            else:
                w.update("")
                w.display = False

        was_correct = user_choice == correct
        if self._feedback_widget:
            result_text = "Correct!" if was_correct else "Incorrect."
            self._feedback_widget.update(result_text)
            self._feedback_widget.display = True
            self._feedback_widget.remove_class("learnpanel-correct", "learnpanel-incorrect")
            self._feedback_widget.add_class(
                "learnpanel-correct" if was_correct else "learnpanel-incorrect"
            )

    # ── open-ended validation ────────────────────────────────────────

    def _show_open_ended_validation(self) -> None:
        correct = self._correct_answer
        if self._feedback_widget:
            self._feedback_widget.update(
                f"Your answer: {self._user_answer}\nCorrect answer: {correct}"
            )
            self._feedback_widget.display = True
            self._feedback_widget.remove_class("learnpanel-correct", "learnpanel-incorrect")

        labels = ["Correct", "Incorrect"]
        color_classes = ["learnpanel-correct", "learnpanel-incorrect"]
        for i, w in enumerate(self._validation_option_widgets):
            is_sel = i == self.selected_option
            cursor = "> " if is_sel else "  "
            w.update(f"{cursor}{labels[i]}")
            w.display = True
            w.remove_class("learnpanel-option-selected", "learnpanel-correct", "learnpanel-incorrect")
            w.add_class(color_classes[i])
            if is_sel:
                w.add_class("learnpanel-option-selected")

    def _show_open_ended_review(self, was_correct: bool) -> None:
        """Read-only display of an open-ended answer after validation."""
        correct = self._correct_answer
        if self._feedback_widget:
            result_label = "Correct!" if was_correct else "Incorrect."
            self._feedback_widget.update(
                f"Your answer: {self._user_answer}\n"
                f"Correct answer: {correct}\n"
                f"{result_label}"
            )
            self._feedback_widget.display = True
            self._feedback_widget.remove_class("learnpanel-correct", "learnpanel-incorrect")
            self._feedback_widget.add_class(
                "learnpanel-correct" if was_correct else "learnpanel-incorrect"
            )

        self._hide_validation_options()

    def _hide_validation_options(self) -> None:
        for w in self._validation_option_widgets:
            w.update("")
            w.display = False

    # ── input helpers ────────────────────────────────────────────────

    def _show_input(self) -> None:
        if self._input_widget:
            self._input_widget.value = ""
            self._input_widget.display = True
            self._input_widget.focus()

    def _hide_input(self) -> None:
        if self._input_widget:
            self._input_widget.display = False

    def _hide_feedback(self) -> None:
        if self._feedback_widget:
            self._feedback_widget.update("")
            self._feedback_widget.display = False

    # ── help text ────────────────────────────────────────────────────

    def _update_help_asking(self) -> None:
        if not self._help_widget:
            return
        if self._is_mc:
            self._help_widget.update("Up/Down navigate  Enter select  ESC close")
        else:
            self._help_widget.update("Type answer, Enter submit  ESC close")

    def _update_help_validating(self) -> None:
        if not self._help_widget:
            return
        is_last = len(self._answered) == len(self._questions) - 1
        if self._is_mc:
            enter_label = "Enter summary" if is_last else "Enter next question"
            self._help_widget.update(f"{enter_label}  ESC close")
        else:
            enter_label = "Enter summary" if is_last else "Enter confirm"
            self._help_widget.update(f"Up/Down select  {enter_label}  ESC close")

    # ── navigation ───────────────────────────────────────────────────

    def _watch_selected_option(self) -> None:
        if not self._questions:
            return
        if self._phase == Phase.ASKING and self._is_mc:
            self._show_mc_options()
        elif self._phase == Phase.VALIDATING and not self._is_mc:
            self._show_open_ended_validation()

    def action_move_up(self) -> None:
        if self._input_widget and self._input_widget.has_focus:
            return
        total = self._total_options()
        if total > 0:
            self.selected_option = (self.selected_option - 1) % total

    def action_move_down(self) -> None:
        if self._input_widget and self._input_widget.has_focus:
            return
        total = self._total_options()
        if total > 0:
            self.selected_option = (self.selected_option + 1) % total

    def _total_options(self) -> int:
        if self._phase == Phase.ASKING and self._is_mc:
            return len(self._q_choices)
        if self._phase == Phase.VALIDATING and not self._is_mc:
            return 2  # Correct / Incorrect
        return 0

    # ── submit / enter ───────────────────────────────────────────────

    def action_submit(self) -> None:
        if self._phase == Phase.ASKING:
            self._submit_answer()
        elif self._phase == Phase.VALIDATING:
            self._confirm_validation()
        elif self._phase == Phase.SUMMARY:
            self._start_new_session()
        elif self._phase == Phase.REVIEWING:
            self._go_to_summary()

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        if self._phase == Phase.ASKING and not self._is_mc:
            self._submit_answer()

    def _submit_answer(self) -> None:
        if self._is_mc:
            choices = self._q_choices
            if 0 <= self.selected_option < len(choices):
                self._user_answer = choices[self.selected_option]
            else:
                return
        else:
            if self._input_widget:
                self._user_answer = self._input_widget.value.strip()
            if not self._user_answer:
                return

        self._phase = Phase.VALIDATING
        self.selected_option = 0
        self.focus()
        self._update_display()

    def _confirm_validation(self) -> None:
        if self._is_mc:
            was_correct = self._user_answer == self._correct_answer
        else:
            was_correct = self.selected_option == 0  # 0 = Correct

        mock_save_context(
            question=self._q_text,
            user_answer=self._user_answer,
            correct_answer=self._correct_answer,
            was_correct=was_correct,
        )

        self._answered[self._question_idx] = (self._user_answer, was_correct)

        self._results.append(LearnQuestionResult(
            question=self._q_text,
            question_type="multiple_choice" if self._is_mc else "open_ended",
            user_answer=self._user_answer,
            correct_answer=self._correct_answer,
            was_correct=was_correct,
            skill=self._current_q.skill,
            difficulty=self._current_q.difficulty,
        ))

        if self._all_answered:
            self._go_to_summary()
        else:
            self._advance_question()

    def _advance_question(self) -> None:
        # Find next unanswered question
        for i in range(len(self._questions)):
            if i not in self._answered:
                self._question_idx = i
                break

        self._phase = Phase.ASKING
        self.selected_option = 0
        self._user_answer = ""

        # clean up CSS classes from previous question
        for w in self._option_widgets:
            w.remove_class("learnpanel-correct", "learnpanel-incorrect")

        self._update_display()

    def _go_to_summary(self) -> None:
        self._phase = Phase.SUMMARY
        self.selected_option = 0
        self.focus()

        # clean up CSS classes
        for w in self._option_widgets:
            w.remove_class("learnpanel-correct", "learnpanel-incorrect")

        self._update_display()
        self.post_message(self.QuestionAnswered(list(self._results)))

    def _start_new_session(self) -> None:
        """Reset quiz state and pick a fresh, non-repeating set of questions."""
        self._questions, self._seen_question_indices = mock_ask_questions(
            questions_format=self._config.learn_questions_format,
            active_categories=self._active_categories(),
            seen_indices=self._seen_question_indices,
        )
        self._question_idx = 0
        self._phase = Phase.ASKING
        self._user_answer = ""
        self._answered = {}
        self._results = []
        self.selected_option = 0

        for w in self._option_widgets:
            w.remove_class("learnpanel-correct", "learnpanel-incorrect")

        self.focus()
        self._update_display()

    # ── history navigation (only from SUMMARY / REVIEWING) ───────────

    def _navigate_review(self, direction: int) -> None:
        """Navigate to an answered question from summary/review."""
        target = self._question_idx + direction

        if self._phase == Phase.SUMMARY:
            # From summary, only left arrow enters review (starting from last question)
            if direction < 0:
                target = len(self._questions) - 1
            else:
                return

        if target < 0:
            return

        # Right arrow past the last question goes back to summary
        if target >= len(self._questions):
            if direction > 0 and self._phase == Phase.REVIEWING:
                self._go_to_summary()
            return

        if target in self._answered:
            self._question_idx = target
            self._phase = Phase.REVIEWING
            self.selected_option = 0

            for w in self._option_widgets:
                w.remove_class("learnpanel-correct", "learnpanel-incorrect")

            self.focus()
            self._update_display()

    # ── key handling ─────────────────────────────────────────────────

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.action_close()
            event.stop()
        elif event.key in {"left", "right"}:
            if self._input_widget and self._input_widget.has_focus:
                return
            if self._phase in {Phase.SUMMARY, Phase.REVIEWING}:
                direction = -1 if event.key == "left" else 1
                self._navigate_review(direction)
                event.stop()

    def action_close(self) -> None:
        self.post_message(self.Closed())

    # ── blur handling ────────────────────────────────────────────────

    def on_blur(self, _event: events.Blur) -> None:
        self.call_after_refresh(self._refocus_if_needed)

    def on_input_blurred(self, _event: Input.Blurred) -> None:
        self.call_after_refresh(self._refocus_if_needed)

    def _refocus_if_needed(self) -> None:
        if self.has_focus or (self._input_widget and self._input_widget.has_focus):
            return
        self.focus()
