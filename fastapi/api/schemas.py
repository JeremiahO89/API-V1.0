from pydantic import BaseModel, ConfigDict, condecimal
from typing import Annotated, Optional
from decimal import Decimal

class BaseExpense(BaseModel):
    """Base fields for an expense."""
    name: Optional[str] = None
    amount: Optional[Annotated[Decimal, condecimal(gt=0, decimal_places=2)]] = None

class ExpenseCreate(BaseExpense):
    """Fields required to create an expense."""
    model_config = ConfigDict(from_attributes=True)

class ExpenseUpdate(BaseExpense):
    """Fields allowed to update for an expense."""
    pass

class Expense(BaseExpense):
    """Expense response model."""
    id: int
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)