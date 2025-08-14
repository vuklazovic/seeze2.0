from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models
from app.schemas import organization as schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.Organization])
def read_organizations(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve organizations.
    """
    organizations = crud.organization.get_multi_by_owner(
        db=db, owner_id=current_user.id, skip=skip, limit=limit
    )
    return organizations


@router.post("/", response_model=schemas.Organization)
def create_organization(
    *,
    db: Session = Depends(deps.get_db),
    organization_in: schemas.OrganizationCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new organization.
    """
    organization = crud.organization.create_with_owner(
        db=db, obj_in=organization_in, owner_id=current_user.id
    )
    return organization


@router.put("/{organization_id}", response_model=schemas.Organization)
def update_organization(
    *,
    db: Session = Depends(deps.get_db),
    organization_id: int,
    organization_in: schemas.OrganizationUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update organization.
    """
    organization = crud.organization.get(db=db, id=organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    if not crud.organization.is_owner(db=db, db_obj=organization, owner_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions",
        )
    organization = crud.organization.update(db=db, db_obj=organization, obj_in=organization_in)
    return organization


@router.get("/{organization_id}", response_model=schemas.Organization)
def read_organization(
    *,
    db: Session = Depends(deps.get_db),
    organization_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get organization by ID.
    """
    organization = crud.organization.get(db=db, id=organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    if not crud.organization.is_owner(db=db, db_obj=organization, owner_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions",
        )
    return organization


@router.delete("/{organization_id}")
def delete_organization(
    *,
    db: Session = Depends(deps.get_db),
    organization_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete organization.
    """
    organization = crud.organization.get(db=db, id=organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    if not crud.organization.is_owner(db=db, db_obj=organization, owner_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions",
        )
    crud.organization.remove(db=db, id=organization_id)
    return {"message": "Organization deleted successfully"} 