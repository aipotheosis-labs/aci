from datetime import datetime

from pydantic import BaseModel


class WebsiteEvaluationPublic(BaseModel):
    """
    Public schema for website evaluation results.

    Used to return structured evaluation data to users, including
    the URL that was evaluated, the evaluation result content,
    and when the evaluation was completed.
    """

    url: str
    result: str
    evaluated_at: datetime  # Will be WebsiteEvaluation.updated_at
