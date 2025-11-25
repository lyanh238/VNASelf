"""
Payment History model for Neon Database
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, BigInteger, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class PaymentHistory(Base):
    """Model for storing payment history in Neon Database."""
    
    __tablename__ = "payment_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    summary = Column(Text, nullable=False)  # Short description of the expense
    amount = Column(Float, nullable=False)  # Expense amount in VND
    category = Column(String(50), nullable=False, index=True)  # Food, Transportation, Miscellaneous
    date = Column(DateTime, nullable=False, index=True)  # Date of transaction
    
    # Timestamp fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<PaymentHistory(id={self.id}, summary={self.summary}, amount={self.amount}, category={self.category}, date={self.date})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "summary": self.summary,
            "amount": self.amount,
            "category": self.category,
            "date": self.date.isoformat() if self.date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_deleted": self.is_deleted
        }
    
    @classmethod
    def get_current_timestamp(cls):
        """Get current timestamp in milliseconds."""
        return int(datetime.now().timestamp() * 1000)
