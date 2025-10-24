"""
Payment History Service for Neon Database
"""

import asyncio
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, text, and_, or_, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, date
import json

from config import Config
from models.payment_history import PaymentHistory, Base
import dotenv

class PaymentHistoryService:
    """Service for managing payment history in Neon Database."""
    
    def __init__(self):
        self.engine = None
        self.session = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection."""
        if self._initialized:
            return
        
        try:
            if Config.NEON_DATABASE_URL:
                self.engine = create_engine(Config.NEON_DATABASE_URL)
                # Check if payment_history table exists, if not create it
                try:
                    Base.metadata.create_all(self.engine)
                    print("✓ Payment History Service connected to Neon Database")
                except Exception as e:
                    print(f"⚠ Table creation warning: {str(e)}")
                    # Try to use existing table
                    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
                    self.session = SessionLocal()
                    print("✓ Payment History Service connected to existing payment_history table")
            else:
                print("⚠ NEON_DATABASE_URL not set - payment history will not be saved")
            
            if not self.session:
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
                self.session = SessionLocal()
            
            self._initialized = True
            
        except Exception as e:
            print(f"✗ Error initializing payment history service: {str(e)}")
            # Don't raise error, just disable payment history
            self._initialized = True
    
    def get_session(self) -> Optional[Session]:
        """Get database session."""
        if not self.session:
            return None
        return self.session
    
    async def add_expense(
        self, 
        summary: str, 
        amount: float, 
        category: str, 
        date: datetime,
        user_id: Optional[str] = None
    ) -> Optional[PaymentHistory]:
        """Add a new expense to payment history."""
        if not self.session:
            return None
        
        try:
            # Validate category
            valid_categories = ["Food", "Transportation", "Miscellaneous"]
            if category not in valid_categories:
                raise ValueError(f"Category must be one of: {', '.join(valid_categories)}")
            
            expense = PaymentHistory(
                user_id=user_id,
                summary=summary,
                amount=amount,
                category=category,
                date=date
            )
            
            self.session.add(expense)
            self.session.commit()
            self.session.refresh(expense)
            
            return expense
            
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error adding expense: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error adding expense: {str(e)}")
            return None
    
    async def get_expense_history(
        self, 
        user_id: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[PaymentHistory]:
        """Get expense history for a user."""
        if not self.session:
            return []
        
        try:
            query = self.session.query(PaymentHistory)\
                .filter(PaymentHistory.is_deleted == False)
            
            if user_id:
                query = query.filter(PaymentHistory.user_id == user_id)
            
            expenses = query.order_by(PaymentHistory.date.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            return expenses
            
        except SQLAlchemyError as e:
            print(f"Error getting expense history: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error getting expense history: {str(e)}")
            return []
    
    async def get_expenses_by_category(
        self, 
        category: str,
        user_id: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[PaymentHistory]:
        """Get expenses by category."""
        if not self.session:
            return []
        
        try:
            query = self.session.query(PaymentHistory)\
                .filter(PaymentHistory.category == category)\
                .filter(PaymentHistory.is_deleted == False)
            
            if user_id:
                query = query.filter(PaymentHistory.user_id == user_id)
            
            expenses = query.order_by(PaymentHistory.date.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            return expenses
            
        except SQLAlchemyError as e:
            print(f"Error getting expenses by category: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error getting expenses by category: {str(e)}")
            return []
    
    async def get_expenses_by_date_range(
        self, 
        start_date: date,
        end_date: date,
        user_id: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[PaymentHistory]:
        """Get expenses within a date range."""
        if not self.session:
            return []
        
        try:
            query = self.session.query(PaymentHistory)\
                .filter(PaymentHistory.date >= start_date)\
                .filter(PaymentHistory.date <= end_date)\
                .filter(PaymentHistory.is_deleted == False)
            
            if user_id:
                query = query.filter(PaymentHistory.user_id == user_id)
            
            expenses = query.order_by(PaymentHistory.date.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            return expenses
            
        except SQLAlchemyError as e:
            print(f"Error getting expenses by date range: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error getting expenses by date range: {str(e)}")
            return []
    
    async def get_total_spending(
        self, 
        user_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> float:
        """Calculate total spending."""
        if not self.session:
            return 0.0
        
        try:
            query = self.session.query(PaymentHistory.amount)\
                .filter(PaymentHistory.is_deleted == False)
            
            if user_id:
                query = query.filter(PaymentHistory.user_id == user_id)
            
            if start_date:
                query = query.filter(PaymentHistory.date >= start_date)
            
            if end_date:
                query = query.filter(PaymentHistory.date <= end_date)
            
            total = query.with_entities(func.sum(PaymentHistory.amount)).scalar()
            return float(total) if total else 0.0
            
        except SQLAlchemyError as e:
            print(f"Error calculating total spending: {str(e)}")
            return 0.0
        except Exception as e:
            print(f"Unexpected error calculating total spending: {str(e)}")
            return 0.0
    
    async def delete_expense(self, expense_id: int, user_id: Optional[str] = None) -> bool:
        """Soft delete an expense."""
        if not self.session:
            return False
        
        try:
            query = self.session.query(PaymentHistory)\
                .filter(PaymentHistory.id == expense_id)\
                .filter(PaymentHistory.is_deleted == False)
            
            if user_id:
                query = query.filter(PaymentHistory.user_id == user_id)
            
            expense = query.first()
            if expense:
                expense.is_deleted = True
                self.session.commit()
                return True
            
            return False
            
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error deleting expense: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error deleting expense: {str(e)}")
            return False
    
    async def update_expense(
        self, 
        expense_id: int,
        summary: Optional[str] = None,
        amount: Optional[float] = None,
        category: Optional[str] = None,
        date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> Optional[PaymentHistory]:
        """Update an expense."""
        if not self.session:
            return None
        
        try:
            query = self.session.query(PaymentHistory)\
                .filter(PaymentHistory.id == expense_id)\
                .filter(PaymentHistory.is_deleted == False)
            
            if user_id:
                query = query.filter(PaymentHistory.user_id == user_id)
            
            expense = query.first()
            if not expense:
                return None
            
            # Update fields if provided
            if summary is not None:
                expense.summary = summary
            if amount is not None:
                expense.amount = amount
            if category is not None:
                # Validate category
                valid_categories = ["Food", "Transportation", "Miscellaneous"]
                if category not in valid_categories:
                    raise ValueError(f"Category must be one of: {', '.join(valid_categories)}")
                expense.category = category
            if date is not None:
                expense.date = date
            
            self.session.commit()
            self.session.refresh(expense)
            
            return expense
            
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error updating expense: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error updating expense: {str(e)}")
            return None
    
    async def close(self):
        """Close database connection."""
        try:
            if self.session:
                self.session.close()
            if self.engine:
                self.engine.dispose()
            print("✓ Payment History Service closed")
        except Exception as e:
            print(f"Error closing payment history service: {str(e)}")
