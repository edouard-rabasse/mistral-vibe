from __future__ import annotations

import enum
import logging
import random
from typing import Any, ClassVar

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Input

from vibe.cli.textual_ui.widgets.no_markup_static import NoMarkupStatic

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mock data & helpers
# ---------------------------------------------------------------------------

MOCK_QUESTIONS: list[dict[str, Any]] = [
    {
        "type": "multiple_choice",
        "question": "What does `git rebase` do?",
        "choices": [
            "Merges branches",
            "Replays commits on a new base",
            "Deletes a branch",
            "Creates a tag",
        ],
        "correct_answer": "Replays commits on a new base",
    },
    {
        "type": "open_ended",
        "question": "Explain what a Python decorator does.",
        "answer": "A decorator wraps a function to extend its behavior without modifying it.",
    },
    {
        "type": "multiple_choice",
        "question": "Which command stages all changes for commit?",
        "choices": [
            "git commit -a",
            "git add .",
            "git push",
            "git stash",
        ],
        "correct_answer": "git add .",
    },
]

ENCOURAGEMENTS = [
    "Great effort! Every question makes you sharper.",
    "Keep it up! Practice is the key to mastery.",
    "Nice work! You're building solid foundations.",
    "Well done! Consistency beats perfection.",
    "Good session! Come back soon to reinforce what you learned.",
]


def mock_ask_questions() -> list[dict[str, Any]]:
    """Return a list of mock questions."""
    return list(MOCK_QUESTIONS)


def mock_save_context(
    question: str, user_answer: str, correct_answer: str, was_correct: bool
) -> None:
    """No-op mock – would persist learning context in a real implementation."""
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

    MAX_OPTIONS: ClassVar[int] = 4
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

    # ── lifecycle ────────────────────────────────────────────────────

    def __init__(self) -> None:
        super().__init__(id="learnpanel-app")
        self._questions = mock_ask_questions()
        self._question_idx = 0
        self._phase = Phase.ASKING
        self._user_answer: str = ""
        # history of answered questions: idx -> (user_answer, was_correct)
        self._answered: dict[int, tuple[str, bool]] = {}

        # widgets – populated in compose
        self._title_widget: NoMarkupStatic | None = None
        self._question_widget: NoMarkupStatic | None = None
        self._option_widgets: list[NoMarkupStatic] = []
        self._input_widget: Input | None = None
        self._feedback_widget: NoMarkupStatic | None = None
        self._validation_option_widgets: list[NoMarkupStatic] = []
        self._help_widget: NoMarkupStatic | None = None

    # ── properties ───────────────────────────────────────────────────

    @property
    def _current_q(self) -> dict[str, Any]:
        return self._questions[self._question_idx]

    @property
    def _is_mc(self) -> bool:
        return self._current_q["type"] == "multiple_choice"

    @property
    def _correct_answer(self) -> str:
        if self._is_mc:
            return self._current_q["correct_answer"]
        return self._current_q["answer"]

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

    async def on_mount(self) -> None:
        self._update_display()
        self.focus()

    # ── rendering ────────────────────────────────────────────────────

    def _update_display(self) -> None:
        if self._phase == Phase.SUMMARY:
            self._render_summary()
            return
        if self._phase == Phase.REVIEWING:
            self._render_review()
            return

        q = self._current_q
        progress = f"[{self._question_idx + 1}/{len(self._questions)}] "
        if self._question_widget:
            self._question_widget.update(progress + q["question"])

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
                short_q = q["question"]
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
        q = self._current_q
        progress = f"[{self._question_idx + 1}/{len(self._questions)}] "
        if self._question_widget:
            self._question_widget.update(progress + q["question"])

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

    # ── MC asking ────────────────────────────────────────────────────

    def _show_mc_options(self) -> None:
        choices = self._current_q.get("choices", [])
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
        choices = self._current_q.get("choices", [])
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
        if self._is_mc:
            self._help_widget.update("Enter next question  ESC close")
        else:
            self._help_widget.update("Up/Down select  Enter confirm  ESC close")

    # ── navigation ───────────────────────────────────────────────────

    def _watch_selected_option(self) -> None:
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
            return len(self._current_q.get("choices", []))
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
            choices = self._current_q.get("choices", [])
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
            question=self._current_q["question"],
            user_answer=self._user_answer,
            correct_answer=self._correct_answer,
            was_correct=was_correct,
        )

        self._answered[self._question_idx] = (self._user_answer, was_correct)

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

    def _start_new_session(self) -> None:
        """Reset everything and start a fresh set of questions."""
        self._questions = mock_ask_questions()
        self._question_idx = 0
        self._phase = Phase.ASKING
        self._user_answer = ""
        self._answered = {}
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
            # From summary, go to the nearest answered question in the given direction
            if direction < 0:
                target = len(self._questions) - 1
            else:
                target = 0

        if target < 0 or target >= len(self._questions):
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
