from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime
import logging
from pathlib import Path
from typing import ClassVar

import yaml
from pydantic import BaseModel

from vibe.core.tools.base import (
    BaseTool,
    BaseToolConfig,
    BaseToolState,
    InvokeContext,
    ToolPermission,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool args / result
# ---------------------------------------------------------------------------


class LearnSaveContextArgs(BaseModel):
    question: str
    user_answer: str
    correct_answer: str
    was_correct: bool
    skill: str
    difficulty: str


class LearnSaveContextResult(BaseModel):
    saved: bool


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------


def _get_memory_file() -> Path:
    return Path.cwd() / ".vibe" / "usermemory.yaml"


def save_skill_to_memory(
    question: str,
    user_answer: str,
    correct_answer: str,
    was_correct: bool,
    skill: str,
    difficulty: str,
) -> None:
    """Append a learned skill entry to .vibe/usermemory.yaml."""
    memory_file = _get_memory_file()
    if not memory_file.exists():
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        data: dict = {"learned_skills": []}
    else:
        raw = yaml.safe_load(memory_file.read_text()) or {}
        data = raw if isinstance(raw, dict) else {"learned_skills": []}

    if "learned_skills" not in data:
        data["learned_skills"] = []

    data["learned_skills"].append({
        "question": question,
        "user_answer": user_answer,
        "correct_answer": correct_answer,
        "was_correct": was_correct,
        "skill": skill,
        "difficulty": difficulty,
        "timestamp": datetime.now().isoformat(),
    })

    memory_file.write_text(yaml.dump(data, default_flow_style=False))


# ---------------------------------------------------------------------------
# Tool config & class
# ---------------------------------------------------------------------------


class LearnSaveContextConfig(BaseToolConfig):
    permission: ToolPermission = ToolPermission.ALWAYS


class LearnSaveContext(
    BaseTool[
        LearnSaveContextArgs,
        LearnSaveContextResult,
        LearnSaveContextConfig,
        BaseToolState,
    ],
):
    description: ClassVar[str] = (
        "Save learning context after a quiz session. Records the question, "
        "the user's answer, the correct answer, and whether the user was correct."
    )

    async def run(
        self, args: LearnSaveContextArgs, ctx: InvokeContext | None = None
    ) -> AsyncGenerator[LearnSaveContextResult, None]:
        logger.debug(
            "save_context: q=%r user=%r correct=%r ok=%s skill=%r difficulty=%r",
            args.question,
            args.user_answer,
            args.correct_answer,
            args.was_correct,
            args.skill,
            args.difficulty,
        )
        try:
            save_skill_to_memory(
                question=args.question,
                user_answer=args.user_answer,
                correct_answer=args.correct_answer,
                was_correct=args.was_correct,
                skill=args.skill,
                difficulty=args.difficulty,
            )
        except Exception:
            logger.exception("Failed to save learning context to usermemory.yaml")
            yield LearnSaveContextResult(saved=False)
            return
        yield LearnSaveContextResult(saved=True)
