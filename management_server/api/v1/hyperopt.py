from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from management_server.database import get_db
from management_server.auth.dependencies import get_current_active_user
from management_server.models.models import (
    User, Bot, HyperoptResult,
    HyperoptResultCreate, HyperoptResultResponse, HyperoptStatus
)
from management_server.services.hyperopt_service import HyperoptService

router = APIRouter()

class HyperoptRequest(BaseModel):
    strategy_name: str
    bot_id: int
    epochs: int = 100
    spaces: str = "buy sell"


@router.post("/", response_model=HyperoptResultResponse)
async def start_hyperopt(
    request: HyperoptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Bot).where(Bot.id == request.bot_id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot for configuration not found")

    # Create the database record first
    hyperopt_create = HyperoptResultCreate(
        strategy_name=request.strategy_name,
        bot_config=bot.config
    )
    new_hyperopt_record = HyperoptResult(
        **hyperopt_create.model_dump(),
        status=HyperoptStatus.PENDING,
        created_by=current_user.id
    )
    db.add(new_hyperopt_record)
    await db.commit()
    await db.refresh(new_hyperopt_record)

    # Now, create and queue the Celery task
    service = HyperoptService()
    task = service.create_hyperopt_task(
        strategy_name=request.strategy_name,
        bot_config=bot.config,
        epochs=request.epochs,
        spaces=request.spaces,
        result_id=new_hyperopt_record.id
    )

    # Update the record with the Celery task ID and set status to queued
    new_hyperopt_record.celery_task_id = task.id
    new_hyperopt_record.status = HyperoptStatus.QUEUED
    db.add(new_hyperopt_record)
    await db.commit()
    await db.refresh(new_hyperopt_record)

    return new_hyperopt_record

@router.get("/results", response_model=List[HyperoptResultResponse])
async def get_all_hyperopt_results(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HyperoptResult).order_by(HyperoptResult.created_at.desc()))
    return result.scalars().all()

@router.get("/results/{result_id}", response_model=HyperoptResultResponse)
async def get_hyperopt_result(result_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HyperoptResult).where(HyperoptResult.id == result_id))
    hyperopt_record = result.scalar_one_or_none()
    if not hyperopt_record:
        raise HTTPException(status_code=404, detail="Hyperopt result not found")
    return hyperopt_record
