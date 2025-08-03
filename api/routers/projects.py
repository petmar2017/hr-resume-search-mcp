"""Project management router for API Builder functionality."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..database import get_db
from ..models import Project, Endpoint, User
from ..schemas import ProjectCreate, ProjectResponse, EndpointCreate, EndpointResponse
from ..auth import get_current_active_user

router = APIRouter(
    prefix="/api/v1/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new project"""
    # Check if project with slug already exists
    existing = db.query(Project).filter(Project.slug == project.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project with this slug already exists"
        )
    
    db_project = Project(
        name=project.name,
        slug=project.slug,
        description=project.description,
        owner_id=current_user.id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all projects for the current user"""
    projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific project"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project


# Endpoint management
@router.post("/{project_id}/endpoints", response_model=EndpointResponse)
async def create_endpoint(
    project_id: int,
    endpoint: EndpointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new endpoint in a project"""
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db_endpoint = Endpoint(
        path=endpoint.path,
        method=endpoint.method,
        name=endpoint.name,
        description=endpoint.description,
        project_id=project_id,
        auth_required=endpoint.auth_required,
        rate_limit=endpoint.rate_limit
    )
    db.add(db_endpoint)
    db.commit()
    db.refresh(db_endpoint)
    return db_endpoint


# Global endpoints route
@router.post("/endpoints", response_model=EndpointResponse)
async def create_global_endpoint(
    endpoint: EndpointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a global endpoint not tied to a specific project"""
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


@router.put("/endpoints/{endpoint_id}", response_model=EndpointResponse)
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


@router.delete("/endpoints/{endpoint_id}")
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