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
@traceable(name="tools.finance.add_multiple_expenses")
def add_multiple_expenses(
    expenses_text: str,
    date: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Thêm nhiều chi tiêu từ một câu mô tả.
    
    Args:
        expenses_text: Chuỗi mô tả nhiều chi tiêu (VD: "20k tiền ăn, 50k tiền xăng, 60k tiền giặt")
        date: Ngày giao dịch (YYYY-MM-DD)
        user_id: ID người dùng (optional)
    
    Returns:
        Dict chứa kết quả thêm chi tiêu
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
                "error": "Không thể phân tích chi tiêu từ văn bản. Vui lòng sử dụng định dạng: '20k tiền ăn, 50k tiền xăng'"
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
                        "error": "Không thể lưu vào cơ sở dữ liệu"
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
            "message": f"Đã thêm thành công {success_count}/{len(matches)} chi tiêu",
            "total_expenses": len(matches),
            "successful_expenses": success_count,
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi thêm nhiều chi tiêu: {str(e)}"
        }

@tool
@traceable(name="tools.finance.get_expense_history")
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
            "error": f"Lỗi khi lấy lịch sử chi tiêu: {str(e)}"
        }

@tool
@traceable(name="tools.finance.get_total_spending")
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
            "error": f"Lỗi khi tính tổng chi tiêu: {str(e)}"
        }

@tool
@traceable(name="tools.finance.get_spending_timeseries")
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
        return {"success": False, "error": f"Lỗi khi lấy timeseries: {str(e)}"}

@tool
@traceable(name="tools.finance.get_spending_timeseries_by_category")
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
        return {"success": False, "error": f"Lỗi khi lấy timeseries theo danh mục: {str(e)}"}

@tool
@traceable(name="tools.finance.forecast_spending")
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

        import concurrent.futures
        
        def run_async():
            return asyncio.run(_payment_service.get_daily_timeseries(user_id=user_id))
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            series = future.result()
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

@tool
@traceable(name="tools.finance.create_spending_chart")
def create_spending_chart(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Tạo biểu đồ chi tiêu theo thời gian với dữ liệu tương tác.
    
    Args:
        start_date: Ngày bắt đầu (YYYY-MM-DD, optional)
        end_date: Ngày kết thúc (YYYY-MM-DD, optional)
        user_id: ID người dùng (optional)
    
    Returns:
        Dict chứa dữ liệu biểu đồ tương tác
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
            return {"success": False, "error": "Không có dữ liệu chi tiêu trong khoảng thời gian này"}
        
        # Format data for interactive chart
        chart_data = {
            "labels": [point["date"] for point in series],
            "datasets": [{
                "label": "Chi tiêu (VND)",
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
            "title": f"Biểu đồ chi tiêu từ {start_date or 'đầu'} đến {end_date or 'hiện tại'}",
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
                            "label": "function(context) { return 'Chi tiêu: ' + context.parsed.y.toLocaleString('vi-VN') + ' VND'; }"
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
        return {"success": False, "error": f"Lỗi khi tạo biểu đồ chi tiêu: {str(e)}"}

@tool
@traceable(name="tools.finance.create_forecast_chart")
def create_forecast_chart(
    days_ahead: int = 7,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Tạo biểu đồ dự báo chi tiêu với Prophet (7 ngày tới).
    
    Args:
        days_ahead: Số ngày dự báo (mặc định 7)
        user_id: ID người dùng (optional)
    
    Returns:
        Dict chứa dữ liệu biểu đồ dự báo tương tác
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
            return {"success": False, "error": "Không có dữ liệu đủ để dự báo"}
        
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
                "label": "Chi tiêu thực tế",
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
                "label": f"Dự báo {days_ahead} ngày tới",
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
            "title": f"Biểu đồ dự báo chi tiêu {days_ahead} ngày tới",
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
        return {"success": False, "error": f"Lỗi khi tạo biểu đồ dự báo: {str(e)}"}


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
        return """Bạn là trợ lý tài chính thông minh chuyên về quản lý chi tiêu và theo dõi lịch sử thanh toán.

QUY TẮC NGÔN NGỮ:
- Mặc định trả lời bằng tiếng Việt.
- Nếu người dùng dùng ngôn ngữ khác, hãy trả lời bằng chính ngôn ngữ đó trong lượt trao đổi.

Bạn có thể:
- Thêm chi tiêu mới với thông tin đầy đủ (1 chi tiêu)
- Thêm nhiều chi tiêu cùng lúc từ một câu mô tả
- Xem lịch sử chi tiêu theo thời gian
- Lọc chi tiêu theo danh mục (Food, Transportation, Miscellaneous)
- Tính tổng chi tiêu trong khoảng thời gian
- Cập nhật hoặc xóa chi tiêu
- Phân tích xu hướng chi tiêu

CÁC TOOL CHI TIÊU:
1. add_expense: Thêm 1 chi tiêu đơn lẻ
   - Dùng khi: "Thêm chi tiêu 50k tiền ăn"
   - Tham số: summary, amount, category, date

2. add_multiple_expenses: Thêm nhiều chi tiêu cùng lúc
   - Dùng khi: "Thêm chi tiêu hôm nay 20k tiền ăn, 50k tiền xăng, 60k tiền giặt"
   - Tham số: expenses_text, date
   - Tự động phân tích và phân loại chi tiêu

3. create_spending_chart: Tạo biểu đồ chi tiêu tương tác
   - Dùng khi: "Vẽ biểu đồ chi tiêu tháng này", "Hiển thị biểu đồ chi tiêu từ ngày X đến ngày Y"
   - Tham số: start_date, end_date, user_id
   - Trả về dữ liệu biểu đồ Chart.js tương tác

4. create_forecast_chart: Tạo biểu đồ dự báo chi tiêu
   - Dùng khi: "Dự báo chi tiêu 7 ngày tới", "Vẽ biểu đồ dự báo chi tiêu"
   - Tham số: days_ahead, user_id
   - Sử dụng Prophet model để dự báo

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
- Ưu tiên sử dụng add_multiple_expenses khi người dùng nhập nhiều chi tiêu trong một câu
"""
    
    def get_tools(self) -> List[Any]:
        """Get finance tools."""
        if self._finance_tools is None:
            raise RuntimeError("Finance agent not initialized. Call initialize() first.")
        return self._finance_tools

