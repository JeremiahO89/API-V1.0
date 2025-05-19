from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.dependents import db_dependency, user_dependency
from api.schemas import Transaction, TransactionCreate, TransactionUpdate
from api.models import Transaction as TransactionModel
from typing import List

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)

@router.get("/", response_model=List[Transaction])
async def get_my_transactions(
    current_user: user_dependency,
    db: db_dependency
):
    transactions = db.query(TransactionModel).filter(TransactionModel.user_id == current_user["id"]).all()
    return transactions

@router.post("/", response_model=Transaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    current_user: user_dependency,
    db: db_dependency
):
    new_transaction = TransactionModel(
        name=transaction.name,
        category=transaction.category,
        amount=transaction.amount,
        type=transaction.type,
        date=transaction.date,
        user_id=current_user["id"]
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

@router.patch("/{transaction_id}", response_model=Transaction, status_code=status.HTTP_200_OK)
async def update_transaction(
    transaction_id: int,
    transaction: TransactionUpdate,
    current_user: user_dependency,
    db: db_dependency
):
    existing = db.query(TransactionModel).filter(
        TransactionModel.id == transaction_id,
        TransactionModel.user_id == current_user["id"]
    ).first()

    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    if transaction.name is not None:
        existing.name = transaction.name
    if transaction.category is not None:
        existing.category = transaction.category
    if transaction.amount is not None:
        existing.amount = transaction.amount
    if transaction.type is not None:
        existing.type = transaction.type
    if transaction.date is not None:
        existing.date = transaction.date

    db.commit()
    db.refresh(existing)
    return existing

@router.delete("/{transaction_id}", response_model=Transaction, status_code=status.HTTP_200_OK)
async def delete_transaction(
    transaction_id: int,
    current_user: user_dependency,
    db: db_dependency
):
    existing = db.query(TransactionModel).filter(
        TransactionModel.id == transaction_id,
        TransactionModel.user_id == current_user["id"]
    ).first()

    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    db.delete(existing)
    db.commit()
    return existing
