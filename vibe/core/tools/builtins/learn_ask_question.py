from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import ClassVar, cast

from pydantic import BaseModel, Field, model_validator

from vibe.core.tools.base import (
    BaseTool,
    BaseToolConfig,
    BaseToolState,
    InvokeContext,
    ToolError,
    ToolPermission,
)
from vibe.core.tools.ui import ToolCallDisplay, ToolResultDisplay, ToolUIData
from vibe.core.types import ToolResultEvent

# ---------------------------------------------------------------------------
# Question models
# ---------------------------------------------------------------------------


class MultipleChoiceQuestion(BaseModel):
    question: str
    choices: list[str] = Field(min_length=2, max_length=4)
    correct_answer: str

    @model_validator(mode="after")
    def correct_answer_in_choices(self) -> MultipleChoiceQuestion:
        if self.correct_answer not in self.choices:
            msg = f"correct_answer {self.correct_answer!r} must be in choices"
            raise ValueError(msg)
        return self


class OpenEndedQuestion(BaseModel):
    question: str
    answer: str  # reference answer


class LearnQuestion(BaseModel):
    multiple_choice: MultipleChoiceQuestion | None = None
    open_ended: OpenEndedQuestion | None = None

    @model_validator(mode="after")
    def exactly_one_type(self) -> LearnQuestion:
        has_mc = self.multiple_choice is not None
        has_oe = self.open_ended is not None
        if has_mc == has_oe:
            msg = "Exactly one of multiple_choice or open_ended must be set"
            raise ValueError(msg)
        return self


# ---------------------------------------------------------------------------
# Tool args / result
# ---------------------------------------------------------------------------


class LearnAskQuestionArgs(BaseModel):
    questions: list[LearnQuestion] = Field(min_length=1, max_length=10)


class LearnQuestionResult(BaseModel):
    question: str
    question_type: str  # "multiple_choice" or "open_ended"
    user_answer: str
    correct_answer: str
    was_correct: bool


class LearnAskQuestionResult(BaseModel):
    results: list[LearnQuestionResult]


# ---------------------------------------------------------------------------
# Tool config & class
# ---------------------------------------------------------------------------


class LearnAskQuestionConfig(BaseToolConfig):
    permission: ToolPermission = ToolPermission.ALWAYS


class LearnAskQuestion(
    BaseTool[
        LearnAskQuestionArgs,
        LearnAskQuestionResult,
        LearnAskQuestionConfig,
        BaseToolState,
    ],
    ToolUIData[LearnAskQuestionArgs, LearnAskQuestionResult],
):
    description: ClassVar[str] = (
        "Present one or more quiz questions to the user during a learn session "
        "and collect their answers. Questions can be multiple-choice or open-ended."
    )

    @classmethod
    def format_call_display(cls, args: LearnAskQuestionArgs) -> ToolCallDisplay:
        count = len(args.questions)
        return ToolCallDisplay(summary=f"Asking {count} learn question{'s' if count != 1 else ''}")

    @classmethod
    def get_result_display(cls, event: ToolResultEvent) -> ToolResultDisplay:
        if event.error:
            return ToolResultDisplay(success=False, message=event.error)

        if not isinstance(event.result, LearnAskQuestionResult):
            return ToolResultDisplay(success=True, message="Quiz completed")

        result = event.result
        correct = sum(1 for r in result.results if r.was_correct)
        total = len(result.results)
        return ToolResultDisplay(success=True, message=f"{correct}/{total} correct")

    @classmethod
    def get_status_text(cls) -> str:
        return "Waiting for quiz answers"

    async def run(
        self, args: LearnAskQuestionArgs, ctx: InvokeContext | None = None
    ) -> AsyncGenerator[LearnAskQuestionResult, None]:
        if ctx is None or ctx.user_input_callback is None:
            raise ToolError(
                "User input not available. This tool requires an interactive UI."
            )

        result = await ctx.user_input_callback(args)
        yield cast(LearnAskQuestionResult, result)
