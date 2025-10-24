# VNASelf Usage Guide

This guide provides comprehensive instructions on how to use the VNASelf multi-agent system effectively.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Web Interface](#web-interface)
3. [Finance Management](#finance-management)
4. [Calendar Management](#calendar-management)
5. [Advanced Features](#advanced-features)
6. [Tips and Best Practices](#tips-and-best-practices)

## Getting Started

### Starting the Application

#### Web Interface (Recommended)
```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501`

#### Command Line Interface
```bash
python main.py
```

### First Interaction

When you first start VNASelf, you'll see a clean chat interface. The system will automatically detect which agent should handle your request based on the content of your message.

## Web Interface

### Interface Overview

The web interface provides a clean, chat-based experience:

- **Header**: VNASelf logo and restart button
- **Chat Area**: Conversation history with agent identification
- **Input Field**: Type your questions here
- **Suggestions**: Quick action buttons for common tasks

### Navigation

- **Restart Button**: Clears conversation history and starts fresh
- **Chat History**: Scroll to see previous conversations
- **Agent Indicators**: Each response shows which agent processed your request

## Finance Management

### Adding Expenses

VNASelf can help you track your spending in Vietnamese or English:

#### Basic Format
```
"Thêm chi tiêu: [description], [amount] VND, [category], [date]"
```

#### Examples
```
"Thêm chi tiêu: Ăn trưa tại nhà hàng, 150000 VND, Food, 2024-01-15"
"Thêm chi tiêu: Đi taxi về nhà, 80000 VND, Transportation, 2024-01-15"
"Thêm chi tiêu: Mua sách, 200000 VND, Miscellaneous, 2024-01-16"
```

#### Natural Language
```
"thêm vào chi tiêu của tôi hôm nay tốn 15000 VNĐ mua cơm"
"hôm nay tôi chi 50000 VND cho xăng"
```

### Viewing Expense History

#### View All Expenses
```
"Xem lịch sử chi tiêu của tôi"
"Hiển thị tất cả chi tiêu"
"Lịch sử chi tiêu"
```

#### Filter by Category
```
"Xem chi tiêu theo danh mục Food"
"Hiển thị chi tiêu Transportation"
"Chi tiêu Miscellaneous"
```

#### Filter by Date Range
```
"Xem chi tiêu từ 2024-01-15 đến 2024-01-20"
"Chi tiêu trong tháng này"
"Chi tiêu tuần trước"
```

### Calculating Totals

#### Total Spending
```
"Tính tổng chi tiêu"
"Tổng chi tiêu trong tháng này"
"Tổng chi tiêu từ ngày 1 đến ngày 31"
```

### Expense Categories

VNASelf supports three main categories:

- **Food**: Meals, groceries, restaurants
- **Transportation**: Taxi, gas, public transport
- **Miscellaneous**: Other expenses not in the above categories

## Calendar Management

### Viewing Events

#### Upcoming Events
```
"Xem lịch sắp tới"
"Hiển thị sự kiện sắp tới"
"Lịch hôm nay"
```

#### Specific Date
```
"Xem lịch ngày 2024-01-20"
"Lịch thứ 2 tuần sau"
```

### Creating Events

#### Basic Event Creation
```
"Tạo sự kiện: [title], [start_time], [end_time]"
"Tạo cuộc họp lúc 15:00 hôm nay"
"Lên lịch họp team ngày mai lúc 14:00"
```

#### Detailed Event Creation
```
"Tạo sự kiện: Họp team, 2024-01-20 14:00, 2024-01-20 15:00"
"Tạo cuộc họp với mô tả: Thảo luận dự án mới"
```

### Managing Events

#### Search Events
```
"Tìm sự kiện có từ 'họp'"
"Tìm cuộc họp tuần này"
```

#### Update Events
```
"Cập nhật sự kiện ID 123: thay đổi thời gian thành 16:00"
"Đổi tên sự kiện thành 'Họp quan trọng'"
```

#### Delete Events
```
"Xóa sự kiện ID 123"
"Xóa cuộc họp ngày mai"
```

### Conflict Resolution

When creating events, VNASelf automatically checks for conflicts:

1. **Conflict Detected**: The system will show conflicting events
2. **Resolution Options**:
   - Move the new event to a different time
   - Move the existing event to a different time
   - Delete the existing event
3. **Choose Your Preferred Solution**: The system will execute your choice

## Advanced Features

### Agent Identification

Each response shows which agent processed your request:

- `[Finance Agent]` - For finance-related operations
- `[Calendar Agent]` - For calendar-related operations
- `[Supervisor Agent]` - For general queries and routing

### Multi-Language Support

VNASelf supports both Vietnamese and English:

#### Vietnamese Examples
```
"Thêm chi tiêu: Ăn trưa, 150000 VND, Food, 2024-01-15"
"Xem lịch sắp tới"
"Tính tổng chi tiêu"
```

#### English Examples
```
"Add expense: Lunch, 150000 VND, Food, 2024-01-15"
"Show upcoming events"
"Calculate total spending"
```

### Natural Language Processing

VNASelf understands natural language queries:

```
"hôm nay tôi chi 50000 VND cho xăng"
"tạo cuộc họp lúc 3 giờ chiều"
"xem tôi có lịch gì ngày mai không"
```

## Tips and Best Practices

### Finance Management Tips

1. **Be Specific**: Include amount, category, and date for accurate tracking
2. **Use Categories**: Proper categorization helps with spending analysis
3. **Regular Updates**: Add expenses regularly for better tracking
4. **Review History**: Check your spending patterns regularly

### Calendar Management Tips

1. **Check Conflicts**: Always review conflict suggestions before confirming
2. **Use Descriptive Titles**: Clear event titles help with searching
3. **Set Reminders**: Consider setting up external reminders for important events
4. **Regular Cleanup**: Periodically review and clean up old events

### General Usage Tips

1. **Clear Communication**: Be specific about what you want to do
2. **Use Natural Language**: Don't worry about perfect formatting
3. **Check Agent Responses**: Look at which agent processed your request
4. **Restart When Needed**: Use the restart button to clear conversation history

### Troubleshooting

1. **Agent Not Responding**: Try rephrasing your request
2. **Incorrect Agent**: Be more specific about your intent
3. **Missing Data**: Ensure you've provided all required information
4. **System Errors**: Use the restart button to reset the conversation

## Examples

### Complete Finance Workflow

```
User: "Thêm chi tiêu: Ăn trưa tại nhà hàng, 150000 VND, Food, 2024-01-15"
Assistant: [Finance Agent] Chi tiêu đã được thêm thành công...

User: "Xem lịch sử chi tiêu của tôi"
Assistant: [Finance Agent] Dưới đây là lịch sử chi tiêu của bạn...

User: "Tính tổng chi tiêu trong tháng này"
Assistant: [Finance Agent] Tổng chi tiêu trong tháng này là 580,000 VND
```

### Complete Calendar Workflow

```
User: "Xem lịch sắp tới"
Assistant: [Calendar Agent] Dưới đây là lịch sắp tới của bạn...

User: "Tạo cuộc họp lúc 15:00 hôm nay"
Assistant: [Calendar Agent] Cuộc họp đã được tạo thành công...

User: "Tìm sự kiện có từ 'họp'"
Assistant: [Calendar Agent] Tìm thấy các sự kiện có từ 'họp'...
```

## Getting Help

If you need assistance:

1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review the [API Documentation](API.md)
3. Read the [Finance Agent Guide](FINANCE_AGENT.md)
4. Create an issue in the repository

---

**Happy using VNASelf!**