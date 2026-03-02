from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import ClassVar

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Vertical
from textual.message import Message
import yaml

from vibe.cli.textual_ui.widgets.no_markup_static import NoMarkupStatic

_MAX_STAT_ROWS = 18
_DAYS_SHOWN = 7
_MAX_BAR_WIDTH = 12


class UserMemoryStatsApp(Container):
    """Read-only panel displaying statistics from .vibe/usermemory.yaml."""

    can_focus = True
    can_focus_children = False

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("left", "prev_week", "Prev week", show=False),
        Binding("right", "next_week", "Next week", show=False),
    ]

    class UserMemoryStatsClosed(Message):
        """Posted when the user dismisses the stats panel."""

    def __init__(self) -> None:
        super().__init__(id="usermemorystats-app")
        self._stat_widgets: list[NoMarkupStatic] = []
        self._week_offset: int = 0  # 0 = current week, 1 = one week back, etc.

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
        def _get_ts(entry: dict) -> str:
            return str(entry.get("answered_at") or entry.get("timestamp") or "")

        timestamps = [_get_ts(e) for e in skills if _get_ts(e)]
        last_activity = max(timestamps) if timestamps else "—"

        easy = difficulty_counts.get("easy", 0)
        medium = difficulty_counts.get("medium", 0)
        hard = difficulty_counts.get("hard", 0)
        skill_parts = "  ".join(
            f"{skill}: {count}" for skill, count in skill_counts.most_common()
        )

        # Build daily counts across all entries
        day_counts: dict[str, int] = defaultdict(int)
        for entry in skills:
            ts = _get_ts(entry)
            if ts:
                try:
                    day_counts[ts[:10]] += 1
                except Exception:
                    pass

        # Determine the 7-day window based on current offset
        today = date.today()
        end_day = today - timedelta(weeks=self._week_offset)
        days = [
            (end_day - timedelta(days=i)).isoformat()
            for i in range(_DAYS_SHOWN - 1, -1, -1)
        ]
        max_count = max((day_counts.get(d, 0) for d in days), default=1) or 1

        # Chart header with navigation hint
        if self._week_offset == 0:
            week_label = "this week"
        elif self._week_offset == 1:
            week_label = "last week"
        else:
            week_label = f"{self._week_offset} weeks ago"
        nav_hint = "←" if self._week_offset < 52 else " "
        nav_hint_right = "→" if self._week_offset > 0 else " "
        chart_header = (
            f"  Correct answers/day  {nav_hint_right} {week_label} {nav_hint}"
        )

        chart_lines: list[str] = [chart_header]
        for day_str in days:
            count = day_counts.get(day_str, 0)
            bar_len = round(count / max_count * _MAX_BAR_WIDTH)
            bar = "█" * bar_len if bar_len > 0 else "·"
            month_day = day_str[5:].replace("-", "/")  # "MM/DD"
            count_label = str(count) if count > 0 else ""
            chart_lines.append(f"  {month_day} {bar} {count_label}".rstrip())

        return [
            f"  Correct answered:  {total}",
            "",
            f"  Difficulty:  Easy: {easy}  Medium: {medium}  Hard: {hard}",
            "",
            f"  Skills:  {skill_parts}",
            "",
            f"  Last activity:  {last_activity}",
            "",
            *chart_lines,
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
            yield NoMarkupStatic("← → weeks  ESC close", classes="settings-help")

    def on_mount(self) -> None:
        self._refresh_display()
        self.focus()

    def _refresh_display(self) -> None:
        lines = self._load_stats()
        for i, widget in enumerate(self._stat_widgets):
            if i < len(lines):
                widget.update(lines[i])
                widget.display = True
            else:
                widget.update("")
                widget.display = False

    def action_prev_week(self) -> None:
        if self._week_offset < 52:
            self._week_offset += 1
            self._refresh_display()

    def action_next_week(self) -> None:
        if self._week_offset > 0:
            self._week_offset -= 1
            self._refresh_display()

    def action_close(self) -> None:
        self.post_message(self.UserMemoryStatsClosed())

    def on_blur(self, event: events.Blur) -> None:
        self.call_after_refresh(self.focus)
