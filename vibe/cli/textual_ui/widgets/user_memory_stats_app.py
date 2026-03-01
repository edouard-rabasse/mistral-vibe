from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import ClassVar

from textual import events
from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Container, Vertical
from textual.message import Message
import yaml

from vibe.cli.textual_ui.widgets.no_markup_static import NoMarkupStatic

_MAX_STAT_ROWS = 8


class UserMemoryStatsApp(Container):
    """Read-only panel displaying statistics from .vibe/usermemory.yaml."""

    can_focus = True
    can_focus_children = False

    BINDINGS: ClassVar[list[BindingType]] = []

    class UserMemoryStatsClosed(Message):
        """Posted when the user dismisses the stats panel."""

    def __init__(self) -> None:
        super().__init__(id="usermemorystats-app")
        self._stat_widgets: list[NoMarkupStatic] = []

    def _load_stats(self) -> list[str]:
        memory_file = Path.cwd() / ".vibe" / "usermemory.yaml"
        if not memory_file.exists():
            return ["  No memory file found."]

        try:
            raw = yaml.safe_load(memory_file.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return [f"  Error reading memory: {e}"]

        skills: list[dict] = raw.get("learned_skills", [])
        if not skills:
            return ["  No questions answered yet."]

        total = len(skills)
        difficulty_counts: Counter[str] = Counter(
            entry.get("difficulty", "unknown") for entry in skills
        )
        skill_counts: Counter[str] = Counter(
            entry.get("skill", "unknown") for entry in skills
        )
        timestamps = [
            entry["answered_at"] for entry in skills if "answered_at" in entry
        ]
        last_activity = max(timestamps) if timestamps else "—"

        easy = difficulty_counts.get("easy", 0)
        medium = difficulty_counts.get("medium", 0)
        hard = difficulty_counts.get("hard", 0)
        skill_parts = "  ".join(
            f"{skill}: {count}" for skill, count in skill_counts.most_common()
        )

        return [
            f"  Correct answered:  {total}",
            "",
            f"  Difficulty:  Easy: {easy}  Medium: {medium}  Hard: {hard}",
            "",
            f"  Skills:  {skill_parts}",
            "",
            f"  Last activity:  {last_activity}",
        ]

    def compose(self) -> ComposeResult:
        with Vertical(id="usermemorystats-content"):
            yield NoMarkupStatic("Memory Stats", classes="settings-title")
            yield NoMarkupStatic("")
            for _ in range(_MAX_STAT_ROWS):
                widget = NoMarkupStatic("", classes="stats-line")
                self._stat_widgets.append(widget)
                yield widget
            yield NoMarkupStatic("")
            yield NoMarkupStatic("ESC close", classes="settings-help")

    def on_mount(self) -> None:
        lines = self._load_stats()
        for i, widget in enumerate(self._stat_widgets):
            if i < len(lines):
                widget.update(lines[i])
                widget.display = True
            else:
                widget.update("")
                widget.display = False
        self.focus()

    def action_close(self) -> None:
        self.post_message(self.UserMemoryStatsClosed())

    def on_blur(self, event: events.Blur) -> None:
        self.call_after_refresh(self.focus)
