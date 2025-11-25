# Testing Prompts - X23D8 Multi-Agent System

## Mục Lục
1. [Notes Testing (Neon DB Only)](#notes-testing)
2. [Multi-Step Cross-Agent Tasks](#multi-step-cross-agent-tasks)
3. [Edge Cases và Complex Scenarios](#edge-cases)
4. [Context Memory Testing](#context-memory-testing)

---

## Notes Testing (Neon DB Only)

### Test 1: Basic Note Creation
```
Tạo ghi chú: "Mua sữa vào chiều nay"
```

**Expected:** Note được lưu vào Neon DB, không có trong all.json

### Test 2: Note with Auto-Categorization
```
Ghi chú: "Họp team vào thứ 6 tuần này lúc 2h chiều"
```

**Expected:** Auto-categorize vào "work", lưu vào Neon DB

### Test 3: List Notes
```
Liệt kê các ghi chú gần đây của tôi
```

**Expected:** Trả về notes từ Neon DB, không đọc từ all.json

### Test 4: Search Notes
```
Tìm ghi chú có từ "họp"
```

**Expected:** Search trong Neon DB

### Test 5: Delete Note
```
Xóa ghi chú đầu tiên
```

**Expected:** Soft delete trong Neon DB

---

## Multi-Step Cross-Agent Tasks

### Test 6: Finance → Note Chain
```
Tìm kiếm những khoảng chi tiêu trên 50k rồi lưu vào note
```

**Expected Flow:**
1. Finance Agent: `get_expense_history` → lấy tất cả expenses
2. Supervisor: Filter expenses > 50,000 VND
3. Note Agent: `record_note` với danh sách expenses đã lọc
4. Result: Note chứa expenses > 50k

**Verification:**
- Check Neon DB: note với category phù hợp (finance/study)
- Note content có danh sách expenses > 50k

### Test 7: Calendar → Note Chain
```
Kiểm tra lịch ngày mai rồi tạo ghi chú tổng hợp các cuộc họp
```

**Expected Flow:**
1. Calendar Agent: `get_events_for_date` (ngày mai)
2. Supervisor: Phân tích events, lọc meetings
3. Note Agent: `record_note` với summary meetings
4. Result: Note chứa danh sách meetings ngày mai

**Verification:**
- Check Neon DB: note với category "work" hoặc phù hợp
- Note content có meetings list

### Test 8: Calendar → Finance Chain (Failed)
```
Xem lịch tuần này và tính tổng chi tiêu tuần này rồi tạo note so sánh
```

**Expected Flow:**
1. Calendar Agent: Get events tuần này
2. Finance Agent: `get_total_spending` tuần này
3. Note Agent: `record_note` so sánh events vs spending
4. Result: Note analysis report

### Test 9: Search → Note Chain
```
Tìm kiếm thông tin về Python best practices rồi lưu 5 điểm quan trọng vào note
```

**Expected Flow:**
1. Search Agent: `tavily_search` Python best practices
2. Supervisor: Extract 5 key points
3. Note Agent: `record_note` với 5 points
4. Result: Note chứa 5 tips

---

## Edge Cases

### Test 10: Multiple Categories
```
Tạo 3 ghi chú: một về công việc, một về chi tiêu, một về du lịch
```

**Expected:** 3 notes với categories khác nhau lưu vào Neon DB

### Test 11: Long Content
```
Ghi chú: [Dán đoạn text dài > 500 từ]
```

**Expected:** Note lưu được content dài

### Test 12: Special Characters
```
Ghi chú: "Hôm nay @#$%^&*() 日本語 中文 123456"
```

**Expected:** Note xử lý được special chars và unicode

### Test 13: Empty/Invalid Input
```
Tạo ghi chú
```

**Expected:** Agent hỏi lại content

### Test 14: Date Context
```
Xem chi tiêu tháng này rồi dự báo chi tiêu 7 ngày tới và lưu vào note
```

**Expected Flow:**
1. Finance Agent: Get expenses tháng này
2. Finance Agent: `forecast_spending` 7 days
3. Note Agent: Save forecast data

---

## Context Memory Testing

### Test 15: Context Across Messages
```
Lần 1: Liệt kê chi tiêu 5 khoản gần đây
Lần 2: Lưu tổng số tiền đó vào note
```

**Expected:** Agent nhớ kết quả lần 1, tính tổng và lưu vào note

### Test 16: Context với Multiple Agents
```
Bước 1: Xem lịch tuần này có bao nhiêu cuộc họp?
Bước 2: Tính tổng chi tiêu tuần này
Bước 3: Tạo ghi chú so sánh số cuộc họp với số tiền đã chi
```

**Expected:** Agent sử dụng kết quả từ 2 bước trước

### Test 17: Language Context
```
English: List my recent expenses
Vietnamese: Lưu tổng số đó vào ghi chú
```

**Expected:** Agent trả lời đúng ngôn ngữ tương ứng

### Test 18: Cross-Conversation Context
```
Conversation 1: Tạo note "Idea: Build AI chatbot"
[Switch conversation]
Conversation 2: Liệt kê các note về ý tưởng
```

**Expected:** Conversation 2 không thấy note từ conversation 1 (isolated)

---

## Advanced Scenarios

### Test 19: Finance Analytics Chain
```
Tạo biểu đồ chi tiêu tháng này, sau đó lưu phân tích vào note với các điểm nổi bật
```

**Expected Flow:**
1. Finance Agent: `create_spending_chart` tháng này
2. Analyze chart data
3. Note Agent: `record_note` với insights

### Test 20: Calendar Optimization Chain
```
Đề xuất thời gian tốt nhất cho meeting 1 tiếng vào tuần này rồi lưu vào note
```

**Expected Flow:**
1. Calendar Agent: `suggest_optimal_time` (meeting, 60min)
2. Analyze suggestions
3. Note Agent: Save recommendations

### Test 21: Multi-Domain Analysis
```
Kiểm tra lịch tuần này, tổng hợp chi tiêu, và tìm kiếm tips về time management, 
sau đó tạo một note tổng hợp tất cả
```

**Expected Flow:**
1. Calendar Agent: Get events
2. Finance Agent: Get spending
3. Search Agent: Search time management tips
4. Note Agent: Combine all vào 1 note

### Test 22: Conditional Logic
```
Nếu tổng chi tiêu tháng này > 5 triệu thì tạo note cảnh báo
```

**Expected:** Agent check condition và chỉ tạo note nếu đúng

---

## Performance Testing

### Test 23: Rapid Fire
```
Lần lượt gửi 10 requests:
1. List expenses
2. Create note
3. List notes
4. Add expense
5. Get events
6. Create note từ events
7. Search expenses > 100k
8. Create note từ search
9. List notes
10. Get total spending
```

**Expected:** Tất cả requests hoàn thành, không mất context

### Test 24: Concurrent Tasks
```
Tạo note, đồng thời list expenses, đồng thời check calendar ngày mai
```

**Expected:** Các tasks độc lập hoàn thành OK

---

## Error Handling

### Test 25: Database Connection Issue
```
Simulate DB disconnect, thử tạo note
```

**Expected:** Graceful error message, không crash

### Test 26: Invalid Tool Parameters
```
Tạo note với category = "InvalidCategory123"
```

**Expected:** Auto-categorize hoặc default category

### Test 27: Empty Result Set
```
Tìm chi tiêu trên 1 tỷ VND
```

**Expected:** "Không tìm thấy chi tiêu nào trên 1 tỷ", không lưu note rỗng

---

## Integration Testing

### Test 28: Full User Journey
```
Day 1:
1. Đăng nhập
2. Thêm 5 expenses
3. Xem lịch tuần này
4. Tạo note "Planning for next week"
5. List notes

Day 2 (same user):
6. List expenses ngày hôm qua
7. Update note đầu tiên
8. Tìm kiếm expenses > 100k
9. Lưu results vào note mới
```

**Expected:** All data persisted, user context maintained

### Test 29: Agent Coordination
```
Supervisor phải gọi Finance Agent 2 lần rồi Note Agent 1 lần
```

**Expected:** All 3 agents được gọi đúng thứ tự với context

---

## Language Testing

### Test 30: Vietnamese Multi-Step
```
Tìm kiếm những khoảng chi tiêu trên 50k rồi lưu vào note với category là "expenses lớn"
```

**Expected:** Respond in Vietnamese, multi-step execution OK

### Test 31: English Multi-Step
```
Find all expenses over 50000 then record them in a note with category "large expenses"
```

**Expected:** Respond in English, multi-step execution OK

### Test 32: Mixed Language
```
List expenses > 50k, sau đó lưu vào note với title "Large Expenses Report"
```

**Expected:** Agent handles mixed language appropriately

---

## Verification Checklist

Sau mỗi test, verify:

### Database (Neon DB)
- [ ] Notes được lưu vào bảng `note`
- [ ] Fields đúng: content, category, user_id, created_at
- [ ] Soft delete hoạt động (is_deleted)
- [ ] Query performance OK

### Context & Memory
- [ ] Multi-step tasks sử dụng context từ bước trước
- [ ] Conversation history được lưu
- [ ] Thread isolation hoạt động

### Agent Coordination
- [ ] Đúng agents được gọi cho từng task
- [ ] Tools được execute đúng thứ tự
- [ ] Results được pass giữa các steps

### Language
- [ ] Auto-detection hoạt động
- [ ] Responses đúng language
- [ ] Mixed language handled OK

### Error Handling
- [ ] Graceful degradation
- [ ] Error messages rõ ràng
- [ ] Không crash system

---

## Quick Test Script

```bash
# Python script để test nhanh
python test_notes.py
python test_multi_step.py
python test_context.py
```

Xem `backend/tests/` cho test scripts chi tiết.

---

## Notes

1. **Cleanup**: Sau mỗi test, cleanup test data nếu cần
2. **Isolation**: Mỗi test case nên độc lập
3. **Verification**: Luôn check Neon DB để confirm
4. **Performance**: Monitor response time cho mỗi test
5. **Logs**: Check logs để debug failed tests

---

**End of Testing Prompts**

