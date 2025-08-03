"""Global endpoint management router."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Endpoint, User
from ..schemas import EndpointCreate, EndpointResponse
from ..auth import get_current_active_user

router = APIRouter(
    prefix="/api/v1/endpoints",
    tags=["endpoints"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=EndpointResponse)
async def create_endpoint(
    endpoint: EndpointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new endpoint"""
    db_endpoint = Endpoint(
        path=endpoint.path,
        method=endpoint.method,
        name=endpoint.name,
        description=endpoint.description,
        project_id=endpoint.project_id,
        auth_required=endpoint.auth_required,
        rate_limit=endpoint.rate_limit
    )
    db.add(db_endpoint)
    db.commit()
    db.refresh(db_endpoint)
    return db_endpoint


@router.get("/", response_model=List[EndpointResponse])
async def list_endpoints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all endpoints"""
    endpoints = db.query(Endpoint).all()
    return endpoints


@router.get("/{endpoint_id}", response_model=EndpointResponse)
async def get_endpoint(
    endpoint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific endpoint"""
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found"
        )
    return endpoint


@router.put("/{endpoint_id}", response_model=EndpointResponse)
async def update_endpoint(
    endpoint_id: int,
    endpoint_update: EndpointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an endpoint"""
    db_endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not db_endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found"
        )
    
    # Update fields
    db_endpoint.path = endpoint_update.path
    db_endpoint.method = endpoint_update.method
    db_endpoint.name = endpoint_update.name
    db_endpoint.description = endpoint_update.description
    db_endpoint.auth_required = endpoint_update.auth_required
    db_endpoint.rate_limit = endpoint_update.rate_limit
    
    db.commit()
    db.refresh(db_endpoint)
    return db_endpoint


@router.delete("/{endpoint_id}")
async def delete_endpoint(
    endpoint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an endpoint"""
    db_endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not db_endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found"
        )
    
    db.delete(db_endpoint)
    db.commit()
    return {"message": "Endpoint deleted successfully"}