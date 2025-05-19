from pydantic import BaseModel, ConfigDict, condecimal
from typing import Annotated, Optional, Literal
from datetime import date as datetime
from decimal import Decimal

class BaseTransaction(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[Annotated[Decimal, condecimal(gt=0, decimal_places=2)]] = None
    type: Optional[Literal["expense", "income"]] = None
    date: Optional[datetime] = None

class TransactionCreate(BaseTransaction):
    model_config = ConfigDict(from_attributes=True)

class TransactionUpdate(BaseTransaction):
    pass

class Transaction(BaseTransaction):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)
