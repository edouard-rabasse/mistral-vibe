from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Vertical
from textual.message import Message
from textual.widgets import Input

from vibe.cli.textual_ui.widgets.no_markup_static import NoMarkupStatic


class LearnPanelApp(Container):
    """Bottom panel: shows latest question, lets user answer, then reveals the answer."""

    can_focus = True
    can_focus_children = True

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "close", "Close", show=False),
    ]

    class Closed(Message):
        pass

    def __init__(self, questions_file: Path, learn_mode: bool) -> None:
        super().__init__(id="learnpanel-app")
        self.questions_file = questions_file
        self.learn_mode = learn_mode
        self._correct_answer = ""
        self._has_question = False

    def _get_latest_qa(self) -> tuple[str, str] | None:
        if not self.questions_file.exists():
            return None
        text = self.questions_file.read_text(encoding="utf-8").strip()
        if not text:
            return None
        blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        for block in reversed(blocks):
            question = ""
            answer = ""
            for line in block.splitlines():
                if line.startswith("<Question>"):
                    question = line.removeprefix("<Question>").strip()
                elif line.startswith("<Answer>"):
                    answer = line.removeprefix("<Answer>").strip()
            if question:
                return question, answer
        return None

    def compose(self) -> ComposeResult:
        with Vertical(id="learnpanel-content"):
            yield NoMarkupStatic("", id="learnpanel-header", classes="learnpanel-header")
            yield NoMarkupStatic("", id="learnpanel-question", classes="learnpanel-question")
            yield NoMarkupStatic("Your answer:", id="learnpanel-input-label", classes="learnpanel-label")
            yield Input(placeholder="Type your answer and press Enter…", id="learnpanel-input")
            yield NoMarkupStatic("", id="learnpanel-separator", classes="learnpanel-separator")
            yield NoMarkupStatic("", id="learnpanel-correct-label", classes="learnpanel-label")
            yield NoMarkupStatic("", id="learnpanel-answer", classes="learnpanel-answer")
            yield NoMarkupStatic("Enter  submit   Esc  close", classes="learnpanel-help")

    async def on_mount(self) -> None:
        self._update_display()
        try:
            self.query_one("#learnpanel-input", Input).focus()
        except Exception:
            self.focus()

    def _update_display(self) -> None:
        header = self.query_one("#learnpanel-header", NoMarkupStatic)
        question_widget = self.query_one("#learnpanel-question", NoMarkupStatic)
        input_label = self.query_one("#learnpanel-input-label", NoMarkupStatic)
        input_widget = self.query_one("#learnpanel-input", Input)
        separator = self.query_one("#learnpanel-separator", NoMarkupStatic)
        correct_label = self.query_one("#learnpanel-correct-label", NoMarkupStatic)
        answer_widget = self.query_one("#learnpanel-answer", NoMarkupStatic)

        # Reset reveal section
        separator.update("")
        correct_label.update("")
        answer_widget.update("")

        if not self.learn_mode:
            header.update("Learn mode is disabled — use /learn to enable it")
            question_widget.update("")
            input_label.display = False
            input_widget.display = False
            self._has_question = False
            return

        qa = self._get_latest_qa()
        if qa is None:
            header.update("No question yet — complete a turn in learn mode to generate one")
            question_widget.update("")
            input_label.display = False
            input_widget.display = False
            self._has_question = False
            return

        question, self._correct_answer = qa
        self._has_question = True
        header.update("Latest question")
        question_widget.update(f"Q  {question}")
        input_label.display = True
        input_widget.display = True

    def _reveal_answer(self) -> None:
        separator = self.query_one("#learnpanel-separator", NoMarkupStatic)
        correct_label = self.query_one("#learnpanel-correct-label", NoMarkupStatic)
        answer_widget = self.query_one("#learnpanel-answer", NoMarkupStatic)
        separator.update("─" * 40)
        correct_label.update("Correct answer:")
        answer_widget.update(f"A  {self._correct_answer}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if not self._has_question:
            return
        event.stop()
        self._reveal_answer()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.action_close()
            event.stop()

    def action_close(self) -> None:
        self.post_message(self.Closed())
