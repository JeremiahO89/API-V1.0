from pydantic import BaseModel, ConfigDict, condecimal
from typing import Annotated

class ExpenseCreate(BaseModel):
    name: str 
    amount: Annotated[float, condecimal(gt=0, decimal_places=2)]
    model_config = ConfigDict(from_attributes=True) 

class Expense(ExpenseCreate):
    id: int
    user_id: int
