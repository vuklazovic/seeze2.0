from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models
from app.schemas import project as schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.Project])
def read_projects(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve projects.
    """
    projects = crud.project.get_multi_by_owner(
        db=db, owner_id=current_user.id, skip=skip, limit=limit
    )
    return projects


@router.post("/", response_model=schemas.Project)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: schemas.ProjectCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new project.
    """
    project = crud.project.create_with_owner(
        db=db, obj_in=project_in, owner_id=current_user.id
    )
    return project


@router.put("/{project_id}", response_model=schemas.Project)
def update_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    project_in: schemas.ProjectUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update project.
    """
    project = crud.project.get(db=db, id=project_id)
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
    project = crud.project.update(db=db, db_obj=project, obj_in=project_in)
    return project


@router.get("/{project_id}", response_model=schemas.Project)
def read_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get project by ID.
    """
    project = crud.project.get(db=db, id=project_id)
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
    return project


@router.delete("/{project_id}")
def delete_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete project.
    """
    project = crud.project.get(db=db, id=project_id)
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
    crud.project.remove(db=db, id=project_id)
    return {"message": "Project deleted successfully"} 