from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from management_server.database import get_db
from management_server.auth.dependencies import get_current_active_user
from management_server.models.models import (
    User, Bot, StrategyBacktestResult,
    StrategyBacktestResultCreate, StrategyBacktestResultResponse, BacktestStatus
)
from management_server.services.backtesting_service import BacktestingService
from management_server.services.strategy_analysis_service import StrategyAnalysisService

router = APIRouter()

STRATEGIES_DIR = Path("user_data/strategies")
STRATEGIES_DIR.mkdir(exist_ok=True)

class BacktestRequest(BaseModel):
    strategy_name: str
    bot_id: int

class StrategyCode(BaseModel):
    code: str

class StrategyAnalysisResult(BaseModel):
    parameters: Dict[str, Any]
    errors: List[str]
    valid: bool

# CRUD operations for strategy files

@router.get("/", response_model=List[str])
async def get_available_strategies():
    """Returns a list of available strategy file names."""
    return [f.stem for f in STRATEGIES_DIR.glob("*.py") if f.name != "__init__.py"]

@router.get("/{strategy_name}", response_model=StrategyCode)
async def get_strategy_code(strategy_name: str):
    """Returns the code of a specific strategy file."""
    strategy_file = STRATEGIES_DIR / f"{strategy_name}.py"
    if not strategy_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy file not found")
    return StrategyCode(code=strategy_file.read_text())

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_strategy(strategy_name: str, strategy_code: StrategyCode):
    """Creates a new strategy file."""
    strategy_file = STRATEGIES_DIR / f"{strategy_name}.py"
    if strategy_file.exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Strategy with this name already exists")
    strategy_file.write_text(strategy_code.code)
    return {"message": "Strategy created successfully"}

@router.put("/{strategy_name}", status_code=status.HTTP_200_OK)
async def update_strategy(strategy_name: str, strategy_code: StrategyCode):
    """Updates an existing strategy file."""
    strategy_file = STRATEGIES_DIR / f"{strategy_name}.py"
    if not strategy_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy file not found")
    strategy_file.write_text(strategy_code.code)
    return {"message": "Strategy updated successfully"}

@router.delete("/{strategy_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(strategy_name: str):
    """Deletes a strategy file."""
    strategy_file = STRATEGIES_DIR / f"{strategy_name}.py"
    if not strategy_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy file not found")
    strategy_file.unlink()
    return

# --- Analysis endpoint ---

@router.post("/analyze", response_model=StrategyAnalysisResult)
async def analyze_strategy_code(strategy_code: StrategyCode):
    """Analyzes and validates the given strategy code."""
    service = StrategyAnalysisService()
    result = service.analyze(strategy_code.code)
    return result

@router.post("/upload_md", response_model=StrategyCode)
async def upload_md_and_convert(file: UploadFile = File(...)):
    """
    Accepts a Markdown file, converts it to a Python strategy,
    and returns the generated code.
    """
    if not file.filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .md file.")

    try:
        md_content = await file.read()
        service = StrategyAnalysisService()
        py_code = service.convert_md_to_py(md_content.decode('utf-8'))
        return StrategyCode(code=py_code)
    except Exception as e:
        # Handle potential errors during file processing or conversion
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")


# --- Backtesting related endpoints ---

@router.post("/backtest", response_model=StrategyBacktestResultResponse)
async def start_strategy_backtest(
    request: BacktestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Bot).where(Bot.id == request.bot_id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot for configuration not found")

    backtest_create = StrategyBacktestResultCreate(
        strategy_name=request.strategy_name,
        bot_config=bot.config
    )
    new_backtest = StrategyBacktestResult(
        **backtest_create.model_dump(),
        status=BacktestStatus.PENDING,
        created_by=current_user.id
    )
    db.add(new_backtest)
    await db.commit()
    await db.refresh(new_backtest)

    service = BacktestingService()
    task = service.create_strategy_backtest_task(
        strategy_name=request.strategy_name,
        bot_config=bot.config,
        result_id=new_backtest.id
    )

    new_backtest.celery_task_id = task.id
    new_backtest.status = BacktestStatus.QUEUED
    db.add(new_backtest)
    await db.commit()
    await db.refresh(new_backtest)

    return new_backtest

@router.get("/backtest/results", response_model=List[StrategyBacktestResultResponse])
async def get_all_backtest_results(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StrategyBacktestResult).order_by(StrategyBacktestResult.created_at.desc()))
    return result.scalars().all()

@router.get("/backtest/results/{result_id}", response_model=StrategyBacktestResultResponse)
async def get_backtest_result(result_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StrategyBacktestResult).where(StrategyBacktestResult.id == result_id))
    backtest_record = result.scalar_one_or_none()
    if not backtest_record:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    return backtest_record
