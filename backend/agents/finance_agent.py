"""
Finance Agent for managing spending history and financial data
"""

from typing import List, Any, Optional, Dict
from langchain_openai import ChatOpenAI
from .base_agent import BaseAgent
from langchain_core.tools import tool
from datetime import datetime
from services.payment_history_service import PaymentHistoryService
import pytz
import json
from langsmith import traceable
import asyncio
import re
TIMEZONE = 'Asia/Ho_Chi_Minh'
VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")
def get_now_vietnam():
    return datetime.now(VN_TZ)

now = get_now_vietnam().isoformat()
# Global payment service for tool access
_payment_service = None

# Standalone tool functions
@tool
@traceable(name="tools.finance.add_expense")
def add_expense(
    summary: str, 
    amount: float, 
    category: str, 
    date: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add new expense to payment history.
    current date is : {now}
    Args:
        summary: Brief description of the expense
        amount: Expense amount (will be converted to VND)
        category: Expense category (Food, Transportation, Miscellaneous)
        date: Transaction date (YYYY-MM-DD)
        user_id: User ID (optional)
    
    Returns:
        Dict containing the added expense information
    """
    try:
        # Validate category
        valid_categories = ["Food", "Transportation", "Miscellaneous"]
        if category not in valid_categories:
            return {
                "success": False,
                "error": f"Category must be one of: {', '.join(valid_categories)}"
            }
        
        # Validate date format
        try:
            expense_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return {
                "success": False,
                "error": "Date must be in YYYY-MM-DD format"
            }
        
        # Convert amount to VND (assuming input is in VND already)
        amount_vnd = float(amount)
        
        # Save to database (using ThreadPoolExecutor to avoid event loop conflicts)
        import asyncio
        import concurrent.futures
        
        if _payment_service:
            def run_async():
                return asyncio.run(_payment_service.add_expense(
                    summary=summary,
                    amount=amount_vnd,
                    category=category,
                    date=expense_date,
                    user_id=user_id
                ))
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async)
                expense = future.result()
            
            if expense:
                return {
                    "success": True,
                    "message": "Expense added successfully",
                    "expense": expense.to_dict()
                }
            else:
                return {
                    "success": False,
                    "error": "Unable to save expense to database"
                }
        else:
            return {
                "success": False,
                "error": "Payment service not initialized"
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error adding expense: {str(e)}"
        }

@tool
@traceable(name="tools.finance.add_multiple_expenses")
def add_multiple_expenses(
    expenses_text: str,
    date: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add multiple expenses from a description string.
    
    Args:
        expenses_text: String describing multiple expenses (e.g., "20k tiền ăn, 50k tiền xăng, 60k tiền giặt")
        date: Transaction date (YYYY-MM-DD)
        user_id: User ID (optional)
    
    Returns:
        Dict containing expense addition results
    """
    try:
        # Validate date format
        try:
            expense_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return {
                "success": False,
                "error": "Date must be in YYYY-MM-DD format"
            }
        
        if not _payment_service:
            return {
                "success": False,
                "error": "Payment service not initialized"
            }
        
        # Parse multiple expenses from text
        # Pattern to match: "amount description" (e.g., "20k tiền ăn", "50k tiền xăng")
        expense_pattern = r'(\d+(?:\.\d+)?)\s*(k|K|000)?\s*([^,]+?)(?=,\s*\d|$)'
        matches = re.findall(expense_pattern, expenses_text)
        
        if not matches:
            return {
                "success": False,
                "error": "Unable to parse expenses from text. Please use format: '20k tiền ăn, 50k tiền xăng'"
            }
        
        results = []
        success_count = 0
        
        for match in matches:
            amount_str, unit, description = match
            
            # Convert amount to VND
            amount = float(amount_str)
            if unit in ['k', 'K', '000'] or amount < 1000:
                amount_vnd = amount * 1000
            else:
                amount_vnd = amount
            
            # Determine category based on keywords
            description_lower = description.lower().strip()
            if any(keyword in description_lower for keyword in ['ăn', 'cơm', 'thức ăn', 'food', 'restaurant', 'nhà hàng']):
                category = "Food"
            elif any(keyword in description_lower for keyword in ['xăng', 'xe', 'bus', 'taxi', 'grab', 'transportation', 'đi lại']):
                category = "Transportation"
            else:
                category = "Miscellaneous"
            
            # Add expense to database
            try:
                # Use asyncio.run in a thread to avoid event loop conflicts
                import concurrent.futures
                
                def run_async():
                    return asyncio.run(_payment_service.add_expense(
                        summary=description.strip(),
                        amount=amount_vnd,
                        category=category,
                        date=expense_date,
                        user_id=user_id
                    ))
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async)
                    expense = future.result()
                
                if expense:
                    results.append({
                        "summary": description.strip(),
                        "amount": amount_vnd,
                        "category": category,
                        "success": True
                    })
                    success_count += 1
                else:
                    results.append({
                        "summary": description.strip(),
                        "amount": amount_vnd,
                        "category": category,
                        "success": False,
                        "error": "Unable to save to database"
                    })
            except Exception as e:
                results.append({
                    "summary": description.strip(),
                    "amount": amount_vnd,
                    "category": category,
                    "success": False,
                    "error": f"Lỗi: {str(e)}"
                })
        
        return {
            "success": success_count > 0,
            "message": f"Successfully added {success_count}/{len(matches)} expenses",
            "total_expenses": len(matches),
            "successful_expenses": success_count,
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error adding multiple expenses: {str(e)}"
        }

@tool
@traceable(name="tools.finance.get_expense_history")
def get_expense_history(
    user_id: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """Get user's expense history.
    
    Args:
        user_id: User ID (optional)
        limit: Maximum number of records
    
    Returns:
        Dict containing list of expenses
    """
    try:
        import asyncio
        import concurrent.futures
        
        if _payment_service:
            def run_async():
                return asyncio.run(_payment_service.get_expense_history(
                    user_id=user_id,
                    limit=limit
                ))
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async)
                expenses = future.result()
            
            return {
                "success": True,
                "expenses": [expense.to_dict() for expense in expenses],
                "total_count": len(expenses)
            }
        else:
            return {
                "success": False,
                "error": "Payment service not initialized"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error retrieving expense history: {str(e)}"
        }

@tool
@traceable(name="tools.finance.get_total_spending")
def get_total_spending(
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """Calculate total spending.
    
    Args:
        user_id: User ID (optional)
        start_date: Start date (YYYY-MM-DD, optional)
        end_date: End date (YYYY-MM-DD, optional)
    
    Returns:
        Dict containing total spending and statistics
    """
    try:
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        import asyncio
        import concurrent.futures
        
        if _payment_service:
            def run_async():
                return asyncio.run(_payment_service.get_total_spending(
                    user_id=user_id,
                    start_date=start_date_obj,
                    end_date=end_date_obj
                ))
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async)
                total_amount = future.result()
            
            return {
                "success": True,
                "total_amount": total_amount,
                "currency": "VND",
                "period": f"{start_date} to {end_date}" if start_date and end_date else "All time",
                "user_id": user_id
            }
        else:
            return {
                "success": False,
                "error": "Payment service not initialized"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error calculating total spending: {str(e)}"
        }

@tool
@traceable(name="tools.finance.get_spending_timeseries")
def get_spending_timeseries(
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """Get time series data (daily) of total spending for charting.

    Returns JSON with fields: labels (dates), values (amounts)
    """
    try:
        start_date_obj = None
        end_date_obj = None
        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

        import asyncio
        import concurrent.futures
        
        if _payment_service:
            def run_async():
                return asyncio.run(_payment_service.get_daily_timeseries(
                    user_id=user_id,
                    start_date=start_date_obj,
                    end_date=end_date_obj
                ))
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async)
                series = future.result()
            labels = [p["date"] for p in series]
            values = [p["amount"] for p in series]
            return {
                "success": True,
                "labels": labels,
                "values": values,
                "unit": "VND"
            }
        return {"success": False, "error": "Payment service not initialized"}
    except Exception as e:
        return {"success": False, "error": f"Error retrieving timeseries: {str(e)}"}

@tool
@traceable(name="tools.finance.get_spending_timeseries_by_category")
def get_spending_timeseries_by_category(
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """Get time series data by category (one line per category)."""
    try:
        start_date_obj = None
        end_date_obj = None
        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

        import asyncio
        import concurrent.futures
        
        if _payment_service:
            def run_async():
                return asyncio.run(_payment_service.get_daily_timeseries_by_category(
                    user_id=user_id,
                    start_date=start_date_obj,
                    end_date=end_date_obj
                ))
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async)
                cat_map = future.result()
            # unify labels
            label_set = set()
            for series in cat_map.values():
                for p in series:
                    label_set.add(p["date"])
            labels = sorted(label_set)
            series_list = []
            for cat, series in cat_map.items():
                values_map = {p["date"]: p["amount"] for p in series}
                values = [values_map.get(d, 0) for d in labels]
                series_list.append({"category": cat, "values": values})
            return {"success": True, "labels": labels, "series": series_list, "unit": "VND"}
        return {"success": False, "error": "Payment service not initialized"}
    except Exception as e:
        return {"success": False, "error": f"Error retrieving timeseries by category: {str(e)}"}

@tool
@traceable(name="tools.finance.forecast_spending")
def forecast_spending(
    user_id: Optional[str] = None,
    days_ahead: int = 14
) -> Dict[str, Any]:
    """Forecast future spending using Prophet and return data for charting.

    Returns JSON fields: history {labels, values}, forecast {labels, values}
    """
    try:
        import pandas as pd
        from prophet import Prophet
        import asyncio

        if not _payment_service:
            return {"success": False, "error": "Payment service not initialized"}

        import concurrent.futures
        
        def run_async():
            return asyncio.run(_payment_service.get_daily_timeseries(user_id=user_id))
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            series = future.result()
        if not series:
            return {"success": False, "error": "Insufficient data for forecasting"}

        df = pd.DataFrame(series)
        df.rename(columns={"date": "ds", "amount": "y"}, inplace=True)
        df["ds"] = pd.to_datetime(df["ds"])  # ensure datetime

        m = Prophet(daily_seasonality=True, weekly_seasonality=True)
        m.fit(df)
        future = m.make_future_dataframe(periods=days_ahead)
        forecast = m.predict(future)

        hist = forecast.iloc[: len(df)]
        fut = forecast.iloc[len(df) : ]

        history_labels = hist["ds"].dt.strftime("%Y-%m-%d").tolist()
        history_values = hist["yhat"].round(2).tolist()
        forecast_labels = fut["ds"].dt.strftime("%Y-%m-%d").tolist()
        forecast_values = fut["yhat"].round(2).tolist()

        return {
            "success": True,
            "history": {"labels": history_labels, "values": history_values},
            "forecast": {"labels": forecast_labels, "values": forecast_values},
            "unit": "VND"
        }
    except Exception as e:
        return {"success": False, "error": f"Error forecasting: {str(e)}"}

@tool
@traceable(name="tools.finance.create_spending_chart")
def create_spending_chart(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create interactive spending chart over time.
    
    Args:
        start_date: Start date (YYYY-MM-DD, optional)
        end_date: End date (YYYY-MM-DD, optional)
        user_id: User ID (optional)
    
    Returns:
        Dict containing interactive chart data
    """
    try:
        import asyncio
        import concurrent.futures
        
        if not _payment_service:
            return {"success": False, "error": "Payment service not initialized"}
        
        # Get timeseries data
        def run_async():
            return asyncio.run(_payment_service.get_daily_timeseries(
                user_id=user_id,
                start_date=datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None,
                end_date=datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
            ))
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            series = future.result()
        
        if not series:
            return {"success": False, "error": "No expense data in this time range"}
        
        # Format data for interactive chart
        chart_data = {
            "labels": [point["date"] for point in series],
            "datasets": [{
                "label": "Spending (VND)",
                "data": [point["amount"] for point in series],
                "borderColor": "rgb(75, 192, 192)",
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "tension": 0.1,
                "pointRadius": 6,
                "pointHoverRadius": 8
            }]
        }
        
        return {
            "success": True,
            "chart_type": "line",
            "title": f"Spending chart from {start_date or 'beginning'} to {end_date or 'now'}",
            "data": chart_data,
            "options": {
                "responsive": True,
                "interaction": {
                    "intersect": False,
                    "mode": "index"
                },
                "plugins": {
                    "tooltip": {
                        "callbacks": {
                            "label": "function(context) { return 'Spending: ' + context.parsed.y.toLocaleString('vi-VN') + ' VND'; }"
                        }
                    }
                },
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "ticks": {
                            "callback": "function(value) { return value.toLocaleString('vi-VN') + ' VND'; }"
                        }
                    }
                }
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Error creating spending chart: {str(e)}"}

@tool
@traceable(name="tools.finance.create_forecast_chart")
def create_forecast_chart(
    days_ahead: int = 7,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create spending forecast chart with Prophet (next 7 days).
    
    Args:
        days_ahead: Number of days to forecast (default 7)
        user_id: User ID (optional)
    
    Returns:
        Dict containing interactive forecast chart data
    """
    try:
        import pandas as pd
        from prophet import Prophet
        import asyncio
        import concurrent.futures
        
        if not _payment_service:
            return {"success": False, "error": "Payment service not initialized"}
        
        # Get historical data
        def run_async():
            return asyncio.run(_payment_service.get_daily_timeseries(user_id=user_id))
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            series = future.result()
        
        if not series:
            return {"success": False, "error": "Insufficient data for forecasting"}
        
        # Prepare data for Prophet
        df = pd.DataFrame(series)
        df.rename(columns={"date": "ds", "amount": "y"}, inplace=True)
        df["ds"] = pd.to_datetime(df["ds"])
        
        # Train Prophet model
        m = Prophet(daily_seasonality=True, weekly_seasonality=True)
        m.fit(df)
        
        # Create future dataframe
        future = m.make_future_dataframe(periods=days_ahead)
        forecast = m.predict(future)
        
        # Split into history and forecast
        hist = forecast.iloc[:len(df)]
        fut = forecast.iloc[len(df):]
        
        # Format data for interactive chart
        history_data = {
            "labels": hist["ds"].dt.strftime("%Y-%m-%d").tolist(),
            "datasets": [{
                "label": "Actual Spending",
                "data": hist["yhat"].round(2).tolist(),
                "borderColor": "rgb(75, 192, 192)",
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "tension": 0.1,
                "pointRadius": 4,
                "pointHoverRadius": 6
            }]
        }
        
        forecast_data = {
            "labels": fut["ds"].dt.strftime("%Y-%m-%d").tolist(),
            "datasets": [{
                "label": f"Forecast {days_ahead} days ahead",
                "data": fut["yhat"].round(2).tolist(),
                "borderColor": "rgb(255, 99, 132)",
                "backgroundColor": "rgba(255, 99, 132, 0.2)",
                "borderDash": [5, 5],
                "tension": 0.1,
                "pointRadius": 4,
                "pointHoverRadius": 6
            }]
        }
        
        # Combine data
        all_labels = history_data["labels"] + forecast_data["labels"]
        all_datasets = history_data["datasets"] + forecast_data["datasets"]
        
        combined_data = {
            "labels": all_labels,
            "datasets": all_datasets
        }
        
        return {
            "success": True,
            "chart_type": "line",
            "title": f"Spending forecast chart {days_ahead} days ahead",
            "data": combined_data,
            "options": {
                "responsive": True,
                "interaction": {
                    "intersect": False,
                    "mode": "index"
                },
                "plugins": {
                    "tooltip": {
                        "callbacks": {
                            "label": "function(context) { return context.dataset.label + ': ' + context.parsed.y.toLocaleString('vi-VN') + ' VND'; }"
                        }
                    },
                    "legend": {
                        "display": True,
                        "position": "top"
                    }
                },
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "ticks": {
                            "callback": "function(value) { return value.toLocaleString('vi-VN') + ' VND'; }"
                        }
                    }
                }
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Error creating forecast chart: {str(e)}"}


class FinanceAgent(BaseAgent):
    """Specialized agent for financial operations and spending tracking."""
    
    def __init__(self, model: ChatOpenAI, payment_service: PaymentHistoryService):
        super().__init__(model)
        self.name = "Finance Agent"
        self.payment_service = payment_service
        self._finance_tools = None
        # Store the payment service globally for tool access
        global _payment_service
        _payment_service = payment_service
    
    async def initialize(self):
        """Initialize the finance agent with tools."""
        if self._finance_tools is None:
            self._finance_tools = [
                add_expense,
                add_multiple_expenses,
                get_expense_history,
                get_total_spending,
                get_spending_timeseries,
                get_spending_timeseries_by_category,
                forecast_spending,
                create_spending_chart,
                create_forecast_chart
            ]
    
    def get_system_prompt(self) -> str:
        return """You are an intelligent financial assistant specialized in expense management and payment history tracking.

LANGUAGE RULES:
- By default, respond in Vietnamese.
- If user uses a different language, respond in that same language for the current exchange.

You can:
- Add new expenses with complete information (1 expense)
- Add multiple expenses at once from a description string
- View expense history over time
- Filter expenses by category (Food, Transportation, Miscellaneous)
- Calculate total spending in time range
- Update or delete expenses
- Analyze spending trends

EXPENSE TOOLS:
1. add_expense: Add single expense
   - Use when: "Add expense 50k for food"
   - Parameters: summary, amount, category, date

2. add_multiple_expenses: Add multiple expenses at once
   - Use when: "Add expenses today 20k food, 50k gas, 60k laundry"
   - Parameters: expenses_text, date
   - Automatically analyzes and categorizes expenses

3. create_spending_chart: Create interactive spending chart
   - Use when: "Draw spending chart this month", "Show spending chart from date X to date Y"
   - Parameters: start_date, end_date, user_id
   - Returns interactive Chart.js chart data

4. create_forecast_chart: Create spending forecast chart
   - Use when: "Forecast spending next 7 days", "Draw spending forecast chart"
   - Parameters: days_ahead, user_id
   - Uses Prophet model for forecasting

Expense information fields:
- Summary: Brief description of expense
- Amount: Expense amount (converted to VND)
- Category: Expense category (Food, Transportation, Miscellaneous)
- Date: Transaction date

Important notes:
- Always convert amounts to VND
- Use ISO date format: YYYY-MM-DD
- Accurately categorize expenses into 3 categories
- Provide detailed and useful information to users
- Always save data to Payment History database
- Prioritize using add_multiple_expenses when user enters multiple expenses in one sentence
"""
    
    def get_tools(self) -> List[Any]:
        """Get finance tools."""
        if self._finance_tools is None:
            raise RuntimeError("Finance agent not initialized. Call initialize() first.")
        return self._finance_tools

