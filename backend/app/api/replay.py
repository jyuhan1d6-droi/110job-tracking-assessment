from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import require_maintainer
from app.db.session import get_db
from app.models.user import User
from app.schemas.replay import ReplayRunResponse, ReplayScenario
from app.services.collection import CollectionConflictError
from app.services.replay import get_replay_scenario, list_replay_scenarios, run_replay

router = APIRouter(prefix="/replay", tags=["replay"])


@router.get("/scenarios", response_model=list[ReplayScenario])
def scenarios(_user: Annotated[User, Depends(require_maintainer)]):
    return list_replay_scenarios()


@router.get("/scenarios/{scenario_id}", response_model=ReplayScenario)
def scenario(scenario_id: str, _user: Annotated[User, Depends(require_maintainer)]):
    item = get_replay_scenario(scenario_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="回放场景不存在")
    return item


@router.post("/scenarios/{scenario_id}/runs", response_model=ReplayRunResponse)
def execute(
    scenario_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_maintainer)],
):
    try:
        return run_replay(db, scenario_id, user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except CollectionConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
