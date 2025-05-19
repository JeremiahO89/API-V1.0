from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.dependents import db_dependency, user_dependency
from api.models import Expense
from api.schemas import ExpenseCreate  # assuming you have schemas defined
from typing import List

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"]
)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense: ExpenseCreate,
    current_user: user_dependency,
    db: db_dependency
):
    new_expense = Expense(
        name=expense.name,
        amount=expense.amount,
        user_id=current_user["id"]
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense


@router.get("/", response_model=List[ExpenseCreate])
async def get_my_expenses(
    current_user: user_dependency,
    db: db_dependency
):
    expenses = db.query(Expense).filter(Expense.user_id == current_user["id"]).all()
    return expenses
