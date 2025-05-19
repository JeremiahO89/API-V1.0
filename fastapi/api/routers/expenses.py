from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.dependents import db_dependency, user_dependency
from api.schemas import Expense
from api.models import Expense as ExpenseModel
from api.schemas import ExpenseCreate, ExpenseUpdate  # assuming you have schemas defined
from typing import List

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"]
)

@router.get("/", response_model=List[Expense])
async def get_my_expenses(
    current_user: user_dependency,
    db: db_dependency
):
    expenses = db.query(ExpenseModel).filter(ExpenseModel.user_id == current_user["id"]).all()
    return expenses


@router.post("/", response_model=Expense, status_code=status.HTTP_201_CREATED)
async def create_expense(
    current_user: user_dependency,
    db: db_dependency
):
    new_expense = ExpenseModel(
        name=None,
        amount=None,
        user_id=current_user["id"] )
    
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense

@router.patch("/{expense_id}", status_code=status.HTTP_200_OK)
async def update_expense(
    expense_id: int,
    expense: ExpenseUpdate,
    current_user: user_dependency,
    db: db_dependency
):
    existing_expense = db.query(ExpenseModel).filter(ExpenseModel.id == expense_id, ExpenseModel.user_id == current_user["id"]).first()
    if not existing_expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    if expense.name is not None:
        existing_expense.name = expense.name
    if expense.amount is not None:
        existing_expense.amount = expense.amount

    db.commit()
    db.refresh(existing_expense)
    return existing_expense

@router.delete("/{expense_id}", response_model=Expense, status_code=status.HTTP_200_OK)
async def delete_expense(
    expense_id: int,
    current_user: user_dependency,
    db: db_dependency
):
    existing_expense = db.query(ExpenseModel).filter(ExpenseModel.id == expense_id, ExpenseModel.user_id == current_user["id"]).first()
    if not existing_expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    db.delete(existing_expense)
    db.commit()
    return existing_expense



