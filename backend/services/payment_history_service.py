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
from collections import defaultdict

from config import Config
from history.payment_history import PaymentHistory, Base

class PaymentHistoryService:
    """Service for managing payment history in Neon Database."""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection."""
        if self._initialized:
            return
        
        try:
            if Config.NEON_DATABASE_URL:
                self.engine = create_engine(Config.NEON_DATABASE_URL)
                self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
                # Check if payment_history table exists, if not create it
                try:
                    Base.metadata.create_all(self.engine)
                    print("[OK] Payment History Service connected to Neon Database")
                except Exception as e:
                    print(f"WARNING: Table creation warning: {str(e)}")
                    # Table may already exist
                    print("[OK] Payment History Service connected to existing payment_history table")
            else:
                print("WARNING: NEON_DATABASE_URL not set - payment history will not be saved")
            
            
            self._initialized = True
            
        except Exception as e:
            print(f"[ERROR] Error initializing payment history service: {str(e)}")
            # Don't raise error, just disable payment history
            self._initialized = True
    
    def get_session(self) -> Optional[Session]:
        # Legacy support if you want a short-lived session outside
        if not self.SessionLocal:
            return None
        return self.SessionLocal()
    
    async def add_expense(
        self, 
        summary: str, 
        amount: float, 
        category: str, 
        date: datetime,
        user_id: Optional[str] = "X2D35"
    ) -> Optional[PaymentHistory]:
        user_id =  "X2D35"
        if not self.SessionLocal:
            return None
        try:
            valid_categories = ["Food", "Transportation", "Miscellaneous"]
            if category not in valid_categories:
                raise ValueError(f"Category must be one of: {', '.join(valid_categories)}")
            expense = PaymentHistory(
                user_id=user_id, summary=summary, amount=amount, category=category, date=date
            )
            with self.SessionLocal() as session:
                with session.begin():
                    session.add(expense)
                    session.flush()
                    session.refresh(expense)
                    return expense
        except SQLAlchemyError as e:
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
        if not self.SessionLocal:
            return []
        try:
            with self.SessionLocal() as session:
                query = session.query(PaymentHistory).filter(PaymentHistory.is_deleted == False)
                if user_id:
                    query = query.filter(PaymentHistory.user_id == user_id)
                expenses = query.order_by(PaymentHistory.date.desc()).offset(offset).limit(limit).all()
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
        if not self.SessionLocal:
            return []
        try:
            with self.SessionLocal() as session:
                query = session.query(PaymentHistory).filter(PaymentHistory.category == category).filter(PaymentHistory.is_deleted == False)
                if user_id:
                    query = query.filter(PaymentHistory.user_id == user_id)
                expenses = query.order_by(PaymentHistory.date.desc()).offset(offset).limit(limit).all()
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
        if not self.SessionLocal:
            return []
        try:
            with self.SessionLocal() as session:
                query = session.query(PaymentHistory).filter(PaymentHistory.date >= start_date).filter(PaymentHistory.date <= end_date).filter(PaymentHistory.is_deleted == False)
                if user_id:
                    query = query.filter(PaymentHistory.user_id == user_id)
                expenses = query.order_by(PaymentHistory.date.desc()).offset(offset).limit(limit).all()
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
        if not self.SessionLocal:
            return 0.0
        try:
            with self.SessionLocal() as session:
                query = session.query(PaymentHistory.amount).filter(PaymentHistory.is_deleted == False)
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

    async def get_daily_timeseries(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        if not self.SessionLocal:
            return []
        try:
            with self.SessionLocal() as session:
                query = session.query(PaymentHistory)
                if user_id:
                    query = query.filter(PaymentHistory.user_id == user_id)
                if start_date:
                    query = query.filter(PaymentHistory.date >= start_date)
                if end_date:
                    query = query.filter(PaymentHistory.date <= end_date)
                query = query.filter(PaymentHistory.is_deleted == False)

                rows = query.all()
                bucket: defaultdict[str, float] = defaultdict(float)
                for row in rows:
                    d = row.date.date().isoformat() if isinstance(row.date, datetime) else str(row.date)
                    bucket[d] += float(row.amount or 0)

                series = [{"date": k, "amount": v} for k, v in bucket.items()]
                series.sort(key=lambda x: x["date"])  # ascending
                return series
        except SQLAlchemyError as e:
            print(f"Error building timeseries: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error building timeseries: {str(e)}")
            return []

    async def get_daily_timeseries_by_category(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        if not self.SessionLocal:
            return {}
        try:
            with self.SessionLocal() as session:
                query = session.query(PaymentHistory)
                if user_id:
                    query = query.filter(PaymentHistory.user_id == user_id)
                if start_date:
                    query = query.filter(PaymentHistory.date >= start_date)
                if end_date:
                    query = query.filter(PaymentHistory.date <= end_date)
                query = query.filter(PaymentHistory.is_deleted == False)

                rows = query.all()
                buckets: Dict[str, defaultdict[str, float]] = {}
                for row in rows:
                    cat = row.category or "Unknown"
                    if cat not in buckets:
                        buckets[cat] = defaultdict(float)
                    d = row.date.date().isoformat() if isinstance(row.date, datetime) else str(row.date)
                    buckets[cat][d] += float(row.amount or 0)

                result: Dict[str, List[Dict[str, Any]]] = {}
                for cat, by_date in buckets.items():
                    series = [{"date": k, "amount": v} for k, v in by_date.items()]
                    series.sort(key=lambda x: x["date"])  # ascending by date
                    result[cat] = series
                return result
        except SQLAlchemyError as e:
            print(f"Error building timeseries by category: {str(e)}")
            return {}
        except Exception as e:
            print(f"Unexpected error building timeseries by category: {str(e)}")
            return {}
    
    async def delete_expense(self, expense_id: int, user_id: Optional[str] = None) -> bool:
        if not self.SessionLocal:
            return False
        try:
            with self.SessionLocal() as session:
                query = session.query(PaymentHistory).filter(PaymentHistory.id == expense_id).filter(PaymentHistory.is_deleted == False)
                if user_id:
                    query = query.filter(PaymentHistory.user_id == user_id)
                expense = query.first()
                if expense:
                    expense.is_deleted = True
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            session.rollback()
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
        if not self.SessionLocal:
            return None
        try:
            with self.SessionLocal() as session:
                query = session.query(PaymentHistory).filter(PaymentHistory.id == expense_id).filter(PaymentHistory.is_deleted == False)
                if user_id:
                    query = query.filter(PaymentHistory.user_id == user_id)
                expense = query.first()
                if not expense:
                    return None
                if summary is not None:
                    expense.summary = summary
                if amount is not None:
                    expense.amount = amount
                if category is not None:
                    valid_categories = ["Food", "Transportation", "Miscellaneous"]
                    if category not in valid_categories:
                        raise ValueError(f"Category must be one of: {', '.join(valid_categories)}")
                    expense.category = category
                if date is not None:
                    expense.date = date
                session.commit()
                session.refresh(expense)
                return expense
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error updating expense: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error updating expense: {str(e)}")
            return None
    
    async def close(self):
        """Close database connection."""
        try:
            if self.engine:
                self.engine.dispose()
            print("[OK] Payment History Service closed")
        except Exception as e:
            print(f"Error closing payment history service: {str(e)}")
