from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, TypedDict

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Vertical
from textual.message import Message
from textual.widgets import Static

from vibe.cli.textual_ui.widgets.no_markup_static import NoMarkupStatic

if TYPE_CHECKING:
    from vibe.core.config import VibeConfig


class SettingDefinition(TypedDict):
    key: str
    label: str
    type: str
    options: list[str]


_CONTENT_CHILDREN: list[SettingDefinition] = [
    {
        "key": "learn_content_codebase",
        "label": "Codebase understanding",
        "type": "cycle",
        "options": ["On", "Off"],
    },
    {
        "key": "learn_content_coding_patterns",
        "label": "Coding patterns",
        "type": "cycle",
        "options": ["On", "Off"],
    },
    {
        "key": "learn_content_current_tasks",
        "label": "Current tasks",
        "type": "cycle",
        "options": ["On", "Off"],
    },
]

# Max visible rows: 4 top-level + 3 children = 7
_MAX_ROWS = 7


class LearnConfigApp(Container):
    can_focus = True
    can_focus_children = False

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("space", "toggle_setting", "Toggle", show=False),
        Binding("enter", "cycle", "Next", show=False),
    ]

    class LearnConfigClosed(Message):
        def __init__(self, changes: dict[str, str | bool]) -> None:
            super().__init__()
            self.changes = changes

    def __init__(self, config: VibeConfig) -> None:
        super().__init__(id="learnconfig-app")
        self.config = config
        self.selected_index = 0
        self.changes: dict[str, str] = {}
        self._content_expanded = False

        self._top_settings: list[SettingDefinition] = [
            {
                "key": "learn_questions_format",
                "label": "Questions format",
                "type": "cycle",
                "options": ["Multiple choice", "Open-ended", "Both"],
            },
            {
                "key": "_content_group",
                "label": "Questions content",
                "type": "group",
                "options": [],
            },
            {
                "key": "learn_model",
                "label": "Model",
                "type": "cycle",
                "options": [m.alias for m in self.config.models],
            },
            {
                "key": "_update_user_memory",
                "label": "Update user memory",
                "type": "action",
                "options": [],
            },
        ]

        self.title_widget: Static | None = None
        self.setting_widgets: list[Static] = []
        self.help_widget: Static | None = None

    def _visible_rows(self) -> list[SettingDefinition | tuple[str, SettingDefinition]]:
        """Return the flat list of visible rows.

        Top-level settings are returned as SettingDefinition.
        Content children (when expanded) are returned as ("child", SettingDefinition).
        """
        rows: list[SettingDefinition | tuple[str, SettingDefinition]] = []
        for s in self._top_settings:
            rows.append(s)
            if s["key"] == "_content_group" and self._content_expanded:
                for child in _CONTENT_CHILDREN:
                    rows.append(("child", child))
        return rows

    def _content_summary(self) -> str:
        """One-line summary of enabled content types."""
        labels: list[str] = []
        for child in _CONTENT_CHILDREN:
            key = child["key"]
            if key in self.changes:
                val = self.changes[key]
            else:
                raw = getattr(self.config, key, True)
                val = "On" if raw else "Off"
            if val == "On":
                labels.append(child["label"])
        return ", ".join(labels) if labels else "None"

    def compose(self) -> ComposeResult:
        with Vertical(id="learnconfig-content"):
            self.title_widget = NoMarkupStatic("Learn Settings", classes="settings-title")
            yield self.title_widget

            yield NoMarkupStatic("")

            for _ in range(_MAX_ROWS):
                widget = NoMarkupStatic("", classes="settings-option")
                self.setting_widgets.append(widget)
                yield widget

            yield NoMarkupStatic("")

            self.help_widget = NoMarkupStatic(
                "↑↓ navigate  Space/Enter toggle  ESC exit", classes="settings-help"
            )
            yield self.help_widget

    def on_mount(self) -> None:
        self._update_display()
        self.focus()

    def _get_display_value(self, setting: SettingDefinition) -> str:
        key = setting["key"]
        if key in self.changes:
            return self.changes[key]
        raw_value = getattr(self.config, key, "")
        if isinstance(raw_value, bool):
            return "On" if raw_value else "Off"
        return str(raw_value)

    def _update_display(self) -> None:
        rows = self._visible_rows()

        for i, widget in enumerate(self.setting_widgets):
            widget.remove_class("settings-cursor-selected")
            widget.remove_class("settings-value-cycle-selected")
            widget.remove_class("settings-value-cycle-unselected")

            if i >= len(rows):
                widget.update("")
                widget.display = False
                continue

            widget.display = True
            row = rows[i]
            is_selected = i == self.selected_index

            if isinstance(row, tuple):
                # Child row
                _, child_setting = row
                cursor = "  › " if is_selected else "    "
                value = self._get_display_value(child_setting)
                text = f"{cursor}{child_setting['label']}: {value}"
            else:
                # Top-level row
                cursor = "› " if is_selected else "  "
                if row["type"] == "group":
                    arrow = "▼" if self._content_expanded else "▶"
                    summary = self._content_summary()
                    text = f"{cursor}{row['label']} {arrow}  {summary}"
                elif row["type"] == "action":
                    text = f"{cursor}{row['label']} →"
                else:
                    value = self._get_display_value(row)
                    text = f"{cursor}{row['label']}: {value}"

            widget.update(text)

            if is_selected:
                widget.add_class("settings-value-cycle-selected")
            else:
                widget.add_class("settings-value-cycle-unselected")

    def action_move_up(self) -> None:
        rows = self._visible_rows()
        self.selected_index = (self.selected_index - 1) % len(rows)
        self._update_display()

    def action_move_down(self) -> None:
        rows = self._visible_rows()
        self.selected_index = (self.selected_index + 1) % len(rows)
        self._update_display()

    def action_toggle_setting(self) -> None:
        rows = self._visible_rows()
        row = rows[self.selected_index]

        if isinstance(row, tuple):
            # Child toggle
            _, child_setting = row
            self._cycle_setting(child_setting)
            return

        if row["type"] == "group":
            self._content_expanded = not self._content_expanded
            # Clamp index if collapsing removed rows
            visible = self._visible_rows()
            if self.selected_index >= len(visible):
                self.selected_index = len(visible) - 1
            self._update_display()
            return

        if row["type"] == "action":
            self._handle_action(row)
            return

        self._cycle_setting(row)

    def _handle_action(self, setting: SettingDefinition) -> None:
        if setting["key"] == "_update_user_memory":
            vibe_dir = Path.cwd() / ".vibe"
            memory_file = vibe_dir / "usermemory.yaml"
            vibe_dir.mkdir(exist_ok=True)
            if not memory_file.exists():
                memory_file.touch()
            if sys.platform == "darwin":
                subprocess.Popen(["open", str(memory_file)])
            elif sys.platform == "win32":
                subprocess.Popen(["start", str(memory_file)], shell=True)
            else:
                subprocess.Popen(["xdg-open", str(memory_file)])

    def _cycle_setting(self, setting: SettingDefinition) -> None:
        key: str = setting["key"]
        current: str = self._get_display_value(setting)
        options: list[str] = setting["options"]
        try:
            current_idx = options.index(current)
            next_idx = (current_idx + 1) % len(options)
            new_value = options[next_idx]
        except (ValueError, IndexError):
            new_value = options[0] if options else current

        self.changes[key] = new_value
        self._update_display()

    def action_cycle(self) -> None:
        self.action_toggle_setting()

    def _convert_changes_for_save(self) -> dict[str, str | bool]:
        result: dict[str, str | bool] = {}
        for key, value in self.changes.items():
            if value in {"On", "Off"}:
                result[key] = value == "On"
            else:
                result[key] = value
        return result

    def action_close(self) -> None:
        self.post_message(self.LearnConfigClosed(changes=self._convert_changes_for_save()))

    def on_blur(self, event: events.Blur) -> None:
        self.call_after_refresh(self.focus)
