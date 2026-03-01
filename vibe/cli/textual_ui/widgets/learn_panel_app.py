from __future__ import annotations

from typing import ClassVar

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Vertical
from textual.message import Message
from textual.widgets import Input

from vibe.cli.textual_ui.widgets.no_markup_static import NoMarkupStatic


class LearnPanelApp(Container):
    """Bottom panel: simple text input for learning notes."""

    can_focus = True
    can_focus_children = True

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "close", "Close", show=False),
    ]

    class Closed(Message):
        pass

    def __init__(self) -> None:
        super().__init__(id="learnpanel-app")

    def compose(self) -> ComposeResult:
        with Vertical(id="learnpanel-content"):
            yield NoMarkupStatic("Learn Panel", classes="learnpanel-header")
            yield NoMarkupStatic("")
            yield Input(placeholder="Type here…", id="learnpanel-input")
            yield NoMarkupStatic("")
            yield NoMarkupStatic("ESC close", classes="learnpanel-help")

    async def on_mount(self) -> None:
        try:
            self.query_one("#learnpanel-input", Input).focus()
        except Exception:
            self.focus()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.action_close()
            event.stop()

    def action_close(self) -> None:
        self.post_message(self.Closed())
