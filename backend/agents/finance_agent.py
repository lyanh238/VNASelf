"""
Finance Agent for managing spending history and financial data
"""

from typing import List, Any, Optional, Dict
from langchain_openai import ChatOpenAI
from .base_agent import BaseAgent
from langchain_core.tools import tool
from datetime import datetime
import json
from services.payment_history_service import PaymentHistoryService
import pytz
import json

TIMEZONE = 'Asia/Ho_Chi_Minh'
VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")
def get_now_vietnam():
    return datetime.now(VN_TZ)

now = get_now_vietnam().isoformat()
# Global payment service for tool access
_payment_service = None

def _run_async_in_tool(coro):
    """Helper function to run async code in tool functions."""
    import asyncio
    import concurrent.futures
    
    try:
        # Check if we're already in an event loop
        loop = asyncio.get_running_loop()
        # We're in an event loop, so we need to use a different approach
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(lambda: asyncio.run(coro))
            return future.result()
    except RuntimeError:
        # No event loop running, safe to use asyncio.run
        return asyncio.run(coro)

# Standalone tool functions
@tool
def add_expense(
    summary: str, 
    amount: float, 
    category: str, 
    date: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Thêm chi tiêu mới vào lịch sử thanh toán.
    current date is : {now}
    Args:
        summary: Mô tả ngắn gọn về khoản chi
        amount: Số tiền chi (sẽ được chuyển đổi sang VND)
        category: Loại chi tiêu (Food, Transportation, Miscellaneous)
        date: Ngày giao dịch (YYYY-MM-DD)
        user_id: ID người dùng (optional)
    
    Returns:
        Dict chứa thông tin chi tiêu đã thêm
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
        
        # Save to database (using asyncio.run for async call)
        import asyncio
        if _payment_service:
            expense = asyncio.run(_payment_service.add_expense(
                summary=summary,
                amount=amount_vnd,
                category=category,
                date=expense_date,
                user_id=user_id
            ))
            
            if expense:
                return {
                    "success": True,
                    "message": "Chi tiêu đã được thêm thành công",
                    "expense": expense.to_dict()
                }
            else:
                return {
                    "success": False,
                    "error": "Không thể lưu chi tiêu vào cơ sở dữ liệu"
                }
        else:
            return {
                "success": False,
                "error": "Payment service not initialized"
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi thêm chi tiêu: {str(e)}"
        }

@tool
def add_multiple_expenses(
    expenses: List[Dict[str, Any]], 
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Thêm nhiều chi tiêu cùng một lúc vào lịch sử thanh toán.
    
    Args:
        expenses: Danh sách các chi tiêu, mỗi chi tiêu có format:
                 [{"summary": "Mô tả", "amount": 50000, "category": "Food", "date": "2024-01-15"}, ...]
        user_id: ID người dùng (optional)
    
    Returns:
        Dict chứa kết quả thêm chi tiêu
    """
    try:
        if not expenses or not isinstance(expenses, list):
            return {
                "success": False,
                "error": "Danh sách chi tiêu không hợp lệ"
            }
        
        # Check if payment service is available
        if not _payment_service or not _payment_service.session:
            return {
                "success": False,
                "error": "Payment service không được khởi tạo. Vui long kiem tra cau hinh database."
            }
        
        # Use the optimized batch processing method from payment service
        try:
            # Prepare expenses data - the payment service will handle validation
            expense_data_list = []
            
            for expense in expenses:
                # Basic structure validation
                if not isinstance(expense, dict):
                    continue
                
                # Convert date string to datetime if needed
                expense_copy = expense.copy()
                if "date" in expense_copy and isinstance(expense_copy["date"], str):
                    try:
                        expense_copy["date"] = datetime.strptime(expense_copy["date"], "%Y-%m-%d")
                    except ValueError:
                        # Skip invalid date format
                        continue
                
                expense_data_list.append(expense_copy)
            
            # Call the payment service batch method
            added_expenses_objects = _run_async_in_tool(
                _payment_service.add_multiple_expenses(
                    expenses=expense_data_list,
                    user_id=user_id
                )
            )
            
            # Convert to dict format
            added_expenses = [exp.to_dict() for exp in added_expenses_objects]
            
            # Return results
            if added_expenses:
                return {
                    "success": True,
                    "message": f"Da them thanh cong {len(added_expenses)}/{len(expenses)} chi tieu",
                    "added_expenses": added_expenses,
                    "total_added": len(added_expenses),
                    "total_requested": len(expenses),
                    "errors": None
                }
            else:
                return {
                    "success": False,
                    "error": "Khong the them chi tieu nao vao database",
                    "total_added": 0,
                    "total_requested": len(expenses)
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Loi khi luu chi tieu vao database: {str(e)}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Loi khi xu ly danh sach chi tieu: {str(e)}"
        }

@tool
def get_expense_history(
    user_id: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """Lấy lịch sử chi tiêu của người dùng.
    
    Args:
        user_id: ID người dùng (optional)
        limit: Số lượng bản ghi tối đa
    
    Returns:
        Dict chứa danh sách chi tiêu
    """
    try:
        import asyncio
        if _payment_service:
            expenses = asyncio.run(_payment_service.get_expense_history(
                user_id=user_id,
                limit=limit
            ))
            
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
            "error": f"Lỗi khi lấy lịch sử chi tiêu: {str(e)}"
        }

@tool
def get_total_spending(
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """Tính tổng chi tiêu.
    
    Args:
        user_id: ID người dùng (optional)
        start_date: Ngày bắt đầu (YYYY-MM-DD, optional)
        end_date: Ngày kết thúc (YYYY-MM-DD, optional)
    
    Returns:
        Dict chứa tổng chi tiêu và thống kê
    """
    try:
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        import asyncio
        if _payment_service:
            total_amount = asyncio.run(_payment_service.get_total_spending(
                user_id=user_id,
                start_date=start_date_obj,
                end_date=end_date_obj
            ))
            
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
            "error": f"Lỗi khi tính tổng chi tiêu: {str(e)}"
        }

@tool
def get_spending_timeseries(
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """Lấy dữ liệu chuỗi thời gian (daily) tổng chi tiêu để vẽ biểu đồ.

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
        if _payment_service:
            series = asyncio.run(_payment_service.get_daily_timeseries(
                user_id=user_id,
                start_date=start_date_obj,
                end_date=end_date_obj
            ))
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
        return {"success": False, "error": f"Lỗi khi lấy timeseries: {str(e)}"}

@tool
def get_spending_timeseries_by_category(
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """Lấy dữ liệu chuỗi thời gian theo danh mục (mỗi danh mục một line)."""
    try:
        start_date_obj = None
        end_date_obj = None
        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

        import asyncio
        if _payment_service:
            cat_map = asyncio.run(_payment_service.get_daily_timeseries_by_category(
                user_id=user_id,
                start_date=start_date_obj,
                end_date=end_date_obj
            ))
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
        return {"success": False, "error": f"Lỗi khi lấy timeseries theo danh mục: {str(e)}"}

@tool
def forecast_spending(
    user_id: Optional[str] = None,
    days_ahead: int = 14
) -> Dict[str, Any]:
    """Dự báo chi tiêu trong tương lai bằng Prophet và trả về dữ liệu để vẽ biểu đồ.

    Returns JSON fields: history {labels, values}, forecast {labels, values}
    """
    try:
        import pandas as pd
        from prophet import Prophet
        import asyncio

        if not _payment_service:
            return {"success": False, "error": "Payment service not initialized"}

        series = asyncio.run(_payment_service.get_daily_timeseries(user_id=user_id))
        if not series:
            return {"success": False, "error": "Không có dữ liệu đủ để dự báo"}

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
        return {"success": False, "error": f"Lỗi khi dự báo: {str(e)}"}


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
                forecast_spending
            ]
    
    def get_system_prompt(self) -> str:
        return """Bạn là trợ lý tài chính thông minh chuyên về quản lý chi tiêu và theo dõi lịch sử thanh toán.

QUY TẮC NGÔN NGỮ:
- Mặc định trả lời bằng tiếng Việt.
- Nếu người dùng dùng ngôn ngữ khác, hãy trả lời bằng chính ngôn ngữ đó trong lượt trao đổi.

Bạn có thể:
- Thêm chi tiêu mới với thông tin đầy đủ
- Thêm nhiều chi tiêu cùng một lúc (batch processing)
- Xem lịch sử chi tiêu theo thời gian
- Lọc chi tiêu theo danh mục (Food, Transportation, Miscellaneous)
- Tính tổng chi tiêu trong khoảng thời gian
- Cập nhật hoặc xóa chi tiêu
- Phân tích xu hướng chi tiêu

Các trường thông tin chi tiêu:
- Summary: Mô tả ngắn gọn về khoản chi
- Amount: Số tiền chi (đã chuyển đổi sang VND)
- Category: Loại chi tiêu (Food, Transportation, Miscellaneous)
- Date: Ngày giao dịch

Lưu ý quan trọng:
- Luôn chuyển đổi số tiền sang VND
- Sử dụng định dạng ngày ISO: YYYY-MM-DD
- Phân loại chi tiêu chính xác theo 3 danh mục
- Cung cấp thông tin chi tiết và hữu ích cho người dùng
- Luôn lưu dữ liệu vào cơ sở dữ liệu Payment History
- Khi người dùng cung cấp nhiều chi tiêu cùng lúc, sử dụng add_multiple_expenses
- Format cho nhiều chi tiêu: [{"summary": "...", "amount": 50000, "category": "Food", "date": "2024-01-15"}, ...]
"""
    
    def get_tools(self) -> List[Any]:
        """Get finance tools."""
        if self._finance_tools is None:
            raise RuntimeError("Finance agent not initialized. Call initialize() first.")
        return self._finance_tools
