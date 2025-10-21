from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    consent: bool

class MagicLinkRequest(BaseModel):
    email: EmailStr

class SessionStart(BaseModel):
    initial_response: str

class AnswerSubmit(BaseModel):
    item_id: int
    answer: str
    latency_ms: Optional[int] = None

class ItemCreate(BaseModel):
    stem: str
    type: str
    competency: str
    difficulty_b: float = 1.0
    discrimination_a: float = 0.5
    choices: Optional[List[str]] = None
    answer_key: Optional[str] = None
    rubric: Optional[Dict[str, Any]] = None
    tags: Optional[str] = None
    active: bool = True
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed_types = ['mcq', 'scenario', 'prompt_writing', 'open_ended']
        if v not in allowed_types:
            raise ValueError(f'Type must be one of {allowed_types}')
        return v

class ItemUpdate(BaseModel):
    stem: Optional[str] = None
    type: Optional[str] = None
    competency: Optional[str] = None
    difficulty_b: Optional[float] = None
    discrimination_a: Optional[float] = None
    choices: Optional[List[str]] = None
    answer_key: Optional[str] = None
    rubric: Optional[Dict[str, Any]] = None
    tags: Optional[str] = None
    active: Optional[bool] = None
