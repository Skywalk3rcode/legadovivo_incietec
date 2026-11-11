from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.sql_models import User, UserRole, LegacyPlan, ActivationRule, AuditLog

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.TITULAR
    titular_id: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: Optional[UserRole] = UserRole.TITULAR
    is_active: bool

    class Config:
        from_attributes = True


class LegacyPlanCreate(BaseModel):
    activation_rule: ActivationRule = ActivationRule.MANUAL_CONFIRMATION
    emergency_contact_email: Optional[EmailStr] = None
    notes: Optional[str] = None


class LegacyPlanResponse(BaseModel):
    id: str
    titular_id: str
    is_activated: bool
    activation_rule: ActivationRule
    emergency_contact_email: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Crea un usuario titular o beneficiario en PostgreSQL."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="El correo ya se encuentra registrado.")

    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=f"hash_{user_in.password}", # Simplificado para demo
        role=user_in.role,
        titular_id=user_in.titular_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Si es titular, inicializar su Plan de Legado
    if new_user.role == UserRole.TITULAR:
        plan = LegacyPlan(titular_id=new_user.id)
        db.add(plan)
        db.commit()

    return new_user


@router.post("/{titular_id}/activate-plan", response_model=LegacyPlanResponse)
def activate_legacy_plan(titular_id: str, db: Session = Depends(get_db)):
    """Activa el plan de legado tras confirmación o deceso."""
    plan = db.query(LegacyPlan).filter(LegacyPlan.titular_id == titular_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de legado no encontrado.")

    plan.is_activated = True
    plan.activated_at = datetime.utcnow()

    # Registrar en auditoría
    audit = AuditLog(
        user_id=titular_id,
        action="LEGACY_PLAN_ACTIVATED",
        details="El plan ha sido activado. Los beneficiarios ahora pueden acceder al chat."
    )
    db.add(audit)
    db.commit()
    db.refresh(plan)

    return plan

