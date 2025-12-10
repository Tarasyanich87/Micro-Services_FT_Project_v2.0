"""
All models for database (SQLAlchemy) and API (Pydantic).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from .base import Base, TimestampMixin

# --- Password Hashing ---
ph = PasswordHasher()

# --- SQLAlchemy ORM Models ---


class User(Base, TimestampMixin):
    """User SQLAlchemy model."""

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    def set_password(self, password: str):
        self.hashed_password = ph.hash(password)

    def verify_password(self, password: str) -> bool:
        try:
            return ph.verify(self.hashed_password, password)
        except VerifyMismatchError:
            return False


class Bot(Base, TimestampMixin):
    """Bot SQLAlchemy model."""

    __tablename__ = "bots"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    strategy_name = Column(String(100), nullable=False)
    exchange = Column(String(50), nullable=False)
    stake_currency = Column(String(10), nullable=False)
    stake_amount = Column(Float, nullable=False)
    max_open_trades = Column(Integer, default=3, nullable=False)
    config = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(String(20), default="stopped", nullable=False)
    pid = Column(Integer, nullable=True)
    port = Column(Integer, nullable=True)
    restart_required = Column(Boolean, default=False, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    freqai_model_id = Column(Integer, ForeignKey("freqai_models.id"), nullable=True)
    total_trades = Column(Integer, default=0, nullable=False)
    profitable_trades = Column(Integer, default=0, nullable=False)
    total_profit = Column(Float, default=0.0, nullable=False)
    max_drawdown = Column(Float, default=0.0, nullable=False)


class Strategy(Base, TimestampMixin):
    """Strategy SQLAlchemy model."""

    __tablename__ = "strategies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    code = Column(Text, nullable=False)
    parameters = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    version = Column(String(20), default="1.0.0", nullable=False)
    tags = Column(JSON, nullable=False, default=list)


class AuditLog(Base, TimestampMixin):
    """Audit log SQLAlchemy model."""

    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    username = Column(String(50), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    http_method = Column(String(10), nullable=False, index=True)
    path = Column(String(255), nullable=False, index=True)
    status_code = Column(Integer, nullable=False, index=True)
    action = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)


class FreqAIModel(Base, TimestampMixin):
    """FreqAI Model SQLAlchemy model."""

    __tablename__ = "freqai_models"
    id = Column(Integer, primary_key=True, index=True)
    celery_task_id = Column(String(100), nullable=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    file_path = Column(String(255), nullable=True)  # Can be null during training
    model_metadata = Column(JSON, nullable=True)  # For storing metrics, etc.
    status = Column(
        String(20), default="pending", nullable=False
    )  # pending, queued, training, completed, failed
    backtest_results = Column(JSON, nullable=True)  # For storing backtesting results
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)


class StrategyBacktestResult(Base, TimestampMixin):
    """Strategy Backtest Result SQLAlchemy model."""

    __tablename__ = "strategy_backtest_results"
    id = Column(Integer, primary_key=True, index=True)
    celery_task_id = Column(String(100), nullable=True, index=True)
    strategy_name = Column(String(100), nullable=False)
    bot_config = Column(JSON, nullable=False)  # The config used for the backtest
    status = Column(
        String(20), default="pending", nullable=False
    )  # pending, queued, running, completed, failed
    results = Column(JSON, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)


# --- Pydantic Schemas ---


# Pydantic Schemas for User
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None
    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# Pydantic Schemas for Bot
class BotStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class BotBase(BaseModel):
    name: str
    description: Optional[str] = None
    freqai_model_id: Optional[int] = None
    strategy_name: str
    exchange: str
    stake_currency: str
    stake_amount: float
    max_open_trades: int = 3
    config: Dict[str, Any] = {}


class BotCreate(BotBase):
    pass


class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    freqai_model_id: Optional[int] = None
    strategy_name: Optional[str] = None
    exchange: Optional[str] = None
    stake_currency: Optional[str] = None
    stake_amount: Optional[float] = None
    max_open_trades: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    status: Optional[BotStatus] = None
    pid: Optional[int] = None
    port: Optional[int] = None
    restart_required: Optional[bool] = None


class BotResponse(BotBase):
    id: int
    is_active: bool
    status: BotStatus
    pid: Optional[int] = None
    port: Optional[int] = None
    restart_required: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_trades: int
    profitable_trades: int
    total_profit: float
    max_drawdown: float
    model_config = {"from_attributes": True}


class BotStatusResponse(BaseModel):
    bot_name: str
    status: BotStatus
    pid: Optional[int] = None
    uptime: Optional[float] = None  # in seconds
    active_trades: int = 0
    total_trades: int = 0
    profit: float = 0.0
    last_update: datetime
    error_message: Optional[str] = None


# Pydantic Schemas for Strategy
class StrategyBase(BaseModel):
    name: str
    description: Optional[str] = None
    code: str
    parameters: Dict[str, Any] = {}
    version: str = "1.0.0"
    tags: List[str] = []


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(StrategyBase):
    name: Optional[str] = None
    code: Optional[str] = None
    is_active: Optional[bool] = None


class StrategyResponse(StrategyBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# Pydantic Schemas for FreqAIModel
class FreqAIModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    model_metadata: Optional[Dict[str, Any]] = None


class FreqAIModelCreate(FreqAIModelBase):
    pass


# Pydantic Schemas for FreqAIModel
class FreqAIModelStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"


class FreqAIModelResponse(FreqAIModelBase):
    id: int
    celery_task_id: Optional[str] = None
    file_path: Optional[str] = None
    status: FreqAIModelStatus
    backtest_results: Optional[Dict[str, Any]] = None
    created_at: datetime
    model_config = {"from_attributes": True}


# Pydantic Schemas for StrategyBacktestResult
class BacktestStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StrategyBacktestResultBase(BaseModel):
    strategy_name: str
    bot_config: Dict[str, Any]


class StrategyBacktestResultCreate(StrategyBacktestResultBase):
    pass


class StrategyBacktestResultResponse(StrategyBacktestResultBase):
    id: int
    celery_task_id: Optional[str] = None
    status: BacktestStatus
    results: Optional[Dict[str, Any]] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class HyperoptResult(Base, TimestampMixin):
    """Hyperopt Result SQLAlchemy model."""

    __tablename__ = "hyperopt_results"
    id = Column(Integer, primary_key=True, index=True)
    celery_task_id = Column(String(100), nullable=True, index=True)
    strategy_name = Column(String(100), nullable=False)
    bot_config = Column(JSON, nullable=False)
    status = Column(
        String(20), default="pending", nullable=False
    )  # pending, queued, running, completed, failed
    results = Column(JSON, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)


# Pydantic Schemas for HyperoptResult
class HyperoptStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class HyperoptResultBase(BaseModel):
    strategy_name: str
    bot_config: Dict[str, Any]


class HyperoptResultCreate(HyperoptResultBase):
    pass


class HyperoptResultResponse(HyperoptResultBase):
    id: int
    celery_task_id: Optional[str] = None
    status: HyperoptStatus
    results: Optional[Dict[str, Any]] = None
    created_at: datetime
    model_config = {"from_attributes": True}
