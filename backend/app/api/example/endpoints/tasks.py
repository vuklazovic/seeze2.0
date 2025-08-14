from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models
from app.schemas import task as schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.Task])
def read_tasks(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve tasks.
    """
    tasks = crud.task.get_multi_by_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return tasks


@router.post("/", response_model=schemas.Task)
def create_task(
    *,
    db: Session = Depends(deps.get_db),
    task_in: schemas.TaskCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new task.
    """
    # Verify project exists and user has access
    project = crud.project.get(db=db, id=task_in.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    if not crud.project.is_owner(db=db, db_obj=project, owner_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions",
        )
    
    task = crud.task.create(db=db, obj_in=task_in)
    return task


@router.put("/{task_id}", response_model=schemas.Task)
def update_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    task_in: schemas.TaskUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update task.
    """
    task = crud.task.get(db=db, id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    # Check if user has access to the project
    project = crud.project.get(db=db, id=task.project_id)
    if not crud.project.is_owner(db=db, db_obj=project, owner_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions",
        )
    task = crud.task.update(db=db, db_obj=task, obj_in=task_in)
    return task


@router.get("/{task_id}", response_model=schemas.Task)
def read_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get task by ID.
    """
    task = crud.task.get(db=db, id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    # Check if user has access to the project
    project = crud.project.get(db=db, id=task.project_id)
    if not crud.project.is_owner(db=db, db_obj=project, owner_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions",
        )
    return task


@router.delete("/{task_id}")
def delete_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete task.
    """
    task = crud.task.get(db=db, id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    # Check if user has access to the project
    project = crud.project.get(db=db, id=task.project_id)
    if not crud.project.is_owner(db=db, db_obj=project, owner_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions",
        )
    crud.task.remove(db=db, id=task_id)
    return {"message": "Task deleted successfully"} 