# Finance Agent Integration

## Overview

The Finance Agent has been successfully integrated into the multi-agent system to handle financial operations and spending tracking. This agent manages payment history with the following key features:

### Key Features

- **Expense Management**: Add, view, update, and delete expenses
- **Category Classification**: Organize expenses into Food, Transportation, and Miscellaneous
- **Date-based Filtering**: Filter expenses by date ranges
- **Total Spending Calculation**: Calculate total spending with optional date filters
- **Database Integration**: All data is stored in NeonDB Payment History table

### Database Schema

The `payment_history` table includes the following fields:

- `id`: Primary key
- `user_id`: User identifier (optional)
- `summary`: Short description of the expense
- `amount`: Expense amount in VND
- `category`: Expense type (Food, Transportation, Miscellaneous)
- `date`: Date of transaction
- `created_at`: Record creation timestamp
- `updated_at`: Record update timestamp
- `is_deleted`: Soft delete flag

### Available Tools

The Finance Agent provides the following tools:

1. **add_expense**: Add a new expense
   - Parameters: summary, amount, category, date, user_id
   - Returns: Success status and expense details

2. **get_expense_history**: Retrieve expense history
   - Parameters: user_id, limit
   - Returns: List of expenses

3. **get_expenses_by_category**: Filter expenses by category
   - Parameters: category, user_id
   - Returns: Filtered list of expenses

4. **get_expenses_by_date_range**: Get expenses within date range
   - Parameters: start_date, end_date, user_id
   - Returns: Expenses within specified range

5. **get_total_spending**: Calculate total spending
   - Parameters: user_id, start_date, end_date
   - Returns: Total amount and statistics

6. **delete_expense**: Soft delete an expense
   - Parameters: expense_id, user_id
   - Returns: Success status

7. **update_expense**: Update expense information
   - Parameters: expense_id, summary, amount, category, date, user_id
   - Returns: Updated expense details

### Integration with Multi-Agent System

The Finance Agent is fully integrated with the existing multi-agent system:

1. **Supervisor Integration**: The supervisor agent routes finance-related requests to the finance agent
2. **Tool Registration**: All finance tools are registered with the supervisor
3. **Database Service**: PaymentHistoryService handles all database operations
4. **Error Handling**: Comprehensive error handling and validation

### Usage Examples

#### Adding an Expense
```
Query: "Thêm chi tiêu: Ăn trưa tại nhà hàng, 150000 VND, Food, 2024-01-15"
Response: [Finance Agent] Chi tiêu đã được thêm thành công...
```

#### Viewing Expense History
```
Query: "Xem lịch sử chi tiêu của tôi"
Response: [Finance Agent] Đây là lịch sử chi tiêu của bạn...
```

#### Getting Expenses by Category
```
Query: "Xem chi tiêu theo danh mục Food"
Response: [Finance Agent] Chi tiêu theo danh mục Food...
```

#### Calculating Total Spending
```
Query: "Tính tổng chi tiêu trong tháng này"
Response: [Finance Agent] Tổng chi tiêu trong tháng này là...
```

#### Getting Expenses by Date Range
```
Query: "Xem chi tiêu từ 2024-01-15 đến 2024-01-20"
Response: [Finance Agent] Chi tiêu trong khoảng thời gian từ 2024-01-15 đến 2024-01-20...
```

### Agent Information Display

All responses now include agent information in the format `[Agent Name] Response`:

- `[Finance Agent]` - For finance-related operations
- `[Calendar Agent]` - For calendar-related operations  
- `[Supervisor Agent]` - For general queries and routing

### System Architecture

```
User Request
    ↓
Supervisor Agent
    ↓
Finance Agent (if finance-related)
    ↓
PaymentHistoryService
    ↓
NeonDB (payment_history table)
```

### Configuration

The Finance Agent requires the following environment variables:

- `OPENAI_API_KEY`: For AI model access
- `NEON_DATABASE_URL`: For database connection

### Testing

Run the test script to verify integration:

```bash
python test_finance_integration.py
```

Or run the examples:

```bash
python examples/finance_examples.py
```

### Error Handling

The Finance Agent includes comprehensive error handling:

- Input validation for all parameters
- Database connection error handling
- Category validation (must be Food, Transportation, or Miscellaneous)
- Date format validation (YYYY-MM-DD)
- User permission checks

### Future Enhancements

Potential future enhancements include:

- Budget tracking and alerts
- Expense analytics and reporting
- Receipt image processing
- Multi-currency support
- Export functionality
- Recurring expense management
