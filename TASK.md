I want you to setup the learning agent. The agent should be the model described in learning_config_app.py.

When the user does control + L, it should open a window with those settings in

- vibe\cli\textual_ui

#learnpanel-app {
    width: 100%;
    height: auto;
    background: transparent;
    border: solid ansi_green;
    padding: 0 1;
    margin: 0;
}

#learnpanel-content {
    width: 100%;
    height: auto;
}

.learnpanel-header {
    height: auto;
    text-style: bold;
    color: ansi_green;
    margin-bottom: 1;
}

.learnpanel-question {
    height: auto;
    color: ansi_default;
    text-style: bold;
    margin-bottom: 1;
}

.learnpanel-label {
    height: auto;
    color: ansi_bright_black;
    margin-top: 1;
}

#learnpanel-input {
    width: 100%;
    height: auto;
    background: transparent;
    border: none;
    border-left: wide ansi_green;
    padding: 0 0 0 1;
    color: ansi_default;
}

.learnpanel-separator {
    height: auto;
    color: ansi_bright_black;
    margin-top: 1;
}

.learnpanel-answer {
    height: auto;
    color: ansi_green;
    margin-top: 0;
}

.learnpanel-help {
    height: auto;
    color: ansi_bright_black;
    margin-top: 1;
}


dans learn_panel_app.py


from__future__import annotations

from pathlib import Path

from typing import ClassVar

from textual import events

from textual.app import ComposeResult

from textual.binding import Binding, BindingType

from textual.containers import Container, Vertical

from textual.message import Message

from textual.widgets import Input

from vibe.cli.textual_ui.widgets.no_markup_static import NoMarkupStatic

classLearnPanelApp(Container):

    """Bottom panel: shows latest question, lets user answer, then reveals the answer."""

    can_focus =True

    can_focus_children =True

    BINDINGS: ClassVar[list[BindingType]] = [

    Binding("escape", "close", "Close", show=False),

    ]

    classClosed(Message):

    pass

    def__init__(self, questions_file: Path, learn_mode: bool) -> None:

    super().__init__(id="learnpanel-app")

    self.questions_file = questions_file

    self.learn_mode = learn_mode

    self._correct_answer =""

    self._has_question =False

    def_get_latest_qa(self) -> tuple[str, str] |None:

    ifnotself.questions_file.exists():

    returnNone

    text =self.questions_file.read_text(encoding="utf-8").strip()

    ifnot text:

    returnNone

    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]

    for block inreversed(blocks):

    question =""

    answer =""

    for line in block.splitlines():

    if line.startswith("`<Question>`"):

    question = line.removeprefix("`<Question>`").strip()

    elif line.startswith("`<Answer>`"):

    answer = line.removeprefix("`<Answer>`").strip()

    if question:

    return question, answer

    returnNone

    defcompose(self) -> ComposeResult:

    with Vertical(id="learnpanel-content"):

    yield NoMarkupStatic("", id="learnpanel-header", classes="learnpanel-header")

    yield NoMarkupStatic("", id="learnpanel-question", classes="learnpanel-question")

    yield NoMarkupStatic("Your answer:", id="learnpanel-input-label", classes="learnpanel-label")

    yield Input(placeholder="Type your answer and press Enter…", id="learnpanel-input")

    yield NoMarkupStatic("", id="learnpanel-separator", classes="learnpanel-separator")

    yield NoMarkupStatic("", id="learnpanel-correct-label", classes="learnpanel-label")

    yield NoMarkupStatic("", id="learnpanel-answer", classes="learnpanel-answer")

    yield NoMarkupStatic("Enter  submit   Esc  close", classes="learnpanel-help")

    asyncdefon_mount(self) -> None:

    self._update_display()

    try:

    self.query_one("#learnpanel-input", Input).focus()

    exceptException:

    self.focus()

    def_update_display(self) -> None:

    header =self.query_one("#learnpanel-header", NoMarkupStatic)

    question_widget =self.query_one("#learnpanel-question", NoMarkupStatic)

    input_label =self.query_one("#learnpanel-input-label", NoMarkupStatic)

    input_widget =self.query_one("#learnpanel-input", Input)

    separator =self.query_one("#learnpanel-separator", NoMarkupStatic)

    correct_label =self.query_one("#learnpanel-correct-label", NoMarkupStatic)

    answer_widget =self.query_one("#learnpanel-answer", NoMarkupStatic)

    # Reset reveal section

    separator.update("")

    correct_label.update("")

    answer_widget.update("")

    ifnotself.learn_mode:

    header.update("Learn mode is disabled — use /learn to enable it")

    question_widget.update("")

    input_label.display =False

    input_widget.display =False

    self._has_question =False

    return

    qa =self._get_latest_qa()

    if qa isNone:

    header.update("No question yet — complete a turn in learn mode to generate one")

    question_widget.update("")

    input_label.display =False

    input_widget.display =False

    self._has_question =False

    return

    question, self._correct_answer = qa

    self._has_question =True

    header.update("Latest question")

    question_widget.update(f"Q  {question}")

    input_label.display =True

    input_widget.display =True

    def_reveal_answer(self) -> None:

    separator =self.query_one("#learnpanel-separator", NoMarkupStatic)

    correct_label =self.query_one("#learnpanel-correct-label", NoMarkupStatic)

    answer_widget =self.query_one("#learnpanel-answer", NoMarkupStatic)

    separator.update("─"*40)

    correct_label.update("Correct answer:")

    answer_widget.update(f"A  {self._correct_answer}")

    defon_input_submitted(self, event: Input.Submitted) -> None:

    ifnotself._has_question:

    return

    event.stop()

    self._reveal_answer()

    defon_key(self, event: events.Key) -> None:

    if event.key =="escape":

    self.action_close()

    event.stop()

    defaction_close(self) -> None:

    self.post_message(self.Closed())
