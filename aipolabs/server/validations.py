from fastapi import HTTPException, status

from aipolabs.common.db import sql_models
from aipolabs.common.enums import Visibility


def validate_project_access(project: sql_models.Project, app: sql_models.App) -> None:
    # TODO: unify access control logic
    if project.visibility_access == Visibility.PUBLIC and app.visibility != Visibility.PUBLIC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project does not have access to this app.",
        )
