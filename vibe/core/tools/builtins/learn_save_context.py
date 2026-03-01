from __future__ import annotations

from collections.abc import AsyncGenerator
import logging
from typing import ClassVar

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
        yield LearnSaveContextResult(saved=True)
