import os
import shutil
from typing import List
from uuid import uuid4
from pydantic import BaseModel

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth.dependencies import get_current_active_user as get_current_user
from ...database import get_db
from ...models import models
from management_server.models.models import Bot, FreqAIModel, FreqAIModelCreate, FreqAIModelResponse, FreqAIModelStatus
from management_server.services.freqai_service import get_freqai_service, FreqAIService

router = APIRouter()

MODELS_DIR = "freqaimodels"
os.makedirs(MODELS_DIR, exist_ok=True)


class BacktestRequest(BaseModel):
    bot_id: int


@router.post("/", response_model=FreqAIModelResponse, status_code=status.HTTP_201_CREATED)
async def upload_model(
    name: str,
    description: str = "",
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Upload a FreqAI model file.
    """
    if not file.filename.endswith(".joblib"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only .joblib files are accepted.",
        )

    # Create a unique filename to avoid collisions
    unique_filename = f"{uuid4()}_{file.filename}"
    file_path = os.path.join(MODELS_DIR, unique_filename)

    # Save the file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    # Create DB entry
    model_create = FreqAIModelCreate(name=name, description=description)
    db_model = FreqAIModel(
        **model_create.model_dump(),
        file_path=file_path,
        created_by=current_user.id,
        status=FreqAIModelStatus.COMPLETED # Consider it completed on upload
    )
    db.add(db_model)
    await db.commit()
    await db.refresh(db_model)
    return db_model


@router.get("/", response_model=List[FreqAIModelResponse])
async def get_all_models(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get a list of all uploaded FreqAI models.
    """
    result = await db.execute(select(FreqAIModel))
    models = result.scalars().all()
    return models


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Delete a FreqAI model.
    """
    result = await db.execute(select(FreqAIModel).where(FreqAIModel.id == model_id))
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )

    # Delete the file
    if os.path.exists(model.file_path):
        os.remove(model.file_path)

    # Delete from DB
    await db.delete(model)
    await db.commit()
    return


@router.post("/{model_id}/backtest", response_model=FreqAIModelResponse)
async def start_model_backtest(
    model_id: int,
    request: BacktestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    freqai_service: FreqAIService = Depends(get_freqai_service),
):
    # Fetch the model
    result = await db.execute(select(FreqAIModel).where(FreqAIModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="FreqAI model not found")

    # Fetch the bot for config
    result = await db.execute(select(Bot).where(Bot.id == request.bot_id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot for configuration not found")

    # Queue the Celery task
    task = freqai_service.create_backtest_task(
        model_id=model.id,
        bot_config=bot.config
    )

    # Update the model record
    model.celery_task_id = task.id
    model.status = FreqAIModelStatus.QUEUED
    db.add(model)
    await db.commit()
    await db.refresh(model)

    return model

# Helper select to avoid SQLModel/SQLAlchemy confusion
from sqlalchemy import select
