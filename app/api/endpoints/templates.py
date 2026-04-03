from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.api.dependencies import get_db
from app.models.template import NotificationTemplate
from app.schemas.template import TemplateCreate, TemplateResponse

router = APIRouter()

@router.post("/", response_model=TemplateResponse, status_code=201)
async def register_template(payload: TemplateCreate, db: AsyncSession = Depends(get_db)):
    """Add a new reusable Jinja2 template to the library."""
    # Check for duplicate names
    res = await db.execute(select(NotificationTemplate).where(NotificationTemplate.name == payload.name))
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="A template with this name already exists")
        
    tpl = NotificationTemplate(
        name=payload.name,
        subject=payload.subject,
        body=payload.body,
        allowed_channels=",".join(payload.allowed_channels)
    )
    db.add(tpl)
    await db.commit()
    await db.refresh(tpl)
    return tpl

@router.get("/", response_model=List[TemplateResponse])
async def list_templates(db: AsyncSession = Depends(get_db)):
    """List all available templates in the collection."""
    res = await db.execute(select(NotificationTemplate).order_by(NotificationTemplate.created_at.desc()))
    return res.scalars().all()

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch a specific template's raw body and config."""
    res = await db.execute(select(NotificationTemplate).where(NotificationTemplate.id == template_id))
    tpl = res.scalars().first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tpl

@router.delete("/{template_id}", status_code=204)
async def remove_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a template from the library by ID."""
    res = await db.execute(select(NotificationTemplate).where(NotificationTemplate.id == template_id))
    tpl = res.scalars().first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    await db.delete(tpl)
    await db.commit()
