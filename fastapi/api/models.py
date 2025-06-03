from sqlalchemy import Column, Integer, Float, String, ForeignKey, Boolean, Date, DateTime, JSON, func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    plaid_accounts = relationship("PlaidAccount", back_populates="user", cascade="all, delete-orphan")
    balances = relationship("PlaidBalance", back_populates="user", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    category = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    type = Column(String, nullable=False)  # "income" or "expense"
    date = Column(Date, nullable=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    user = relationship("User", back_populates="transactions")


class PlaidAccount(Base):
    __tablename__ = "plaid_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String, unique=True, nullable=False)
    item_id = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    institution_id = Column(String, ForeignKey("plaid_institutions.institution_id"), nullable=False)
    
    institution = relationship("PlaidInstitution", back_populates="accounts")
    balances = relationship("PlaidBalance", back_populates="plaid_account", cascade="all, delete-orphan")
    user = relationship("User", back_populates="plaid_accounts")


class PlaidInstitution(Base):
    __tablename__ = "plaid_institutions"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(String, unique=True, index=True)  # e.g. "ins_109508"
    name = Column(String) # e.g. "Bank of America"
    url = Column(String, nullable=True) # e.g. "https://www.bankofamerica.com"
    primary_color = Column(String, nullable=True) 
    logo = Column(String, nullable=True)  # Base64 string
    oauth = Column(Boolean, default=False) # Do they require OAuth?
    products = Column(JSON, nullable=True)  # e.g. ["auth", "transactions"]
    country_codes = Column(JSON, nullable=True)  # e.g. ["US"]
    status = Column(JSON, nullable=True)  # optional: service availability

    accounts = relationship("PlaidAccount", back_populates="institution")

class PlaidBalance(Base):
    __tablename__ = "plaid_balances"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String, nullable=False) #Banking Account ID (Checking, Savings, etc.)
    name = Column(String)
    type = Column(String)
    subtype = Column(String)
    available = Column(Float, nullable=True) #e.g 
    current = Column(Float, nullable=False)
    limit = Column(Float, nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    item_id  = Column(String, ForeignKey("plaid_accounts.item_id"), index=True, nullable=False, onupdate="CASCADE") #Bank's ID
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    user = relationship("User", back_populates="balances")
    plaid_account = relationship("PlaidAccount", back_populates="balances")



