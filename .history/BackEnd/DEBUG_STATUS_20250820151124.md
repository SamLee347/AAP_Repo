Testing category prediction with debug output

Issue: Category predictions are returning numbers (6) instead of category names ("Books")

Test plan:
1. Start both backend and frontend servers ✅
2. Test category prediction API directly ⬜
3. Check debug output in backend logs ⬜
4. Verify frontend displays correct category name ⬜

Current status:
- Backend running on port 5000 ✅
- Frontend running on port 3001 ✅
- Database populated with test data ✅
- Fixed issue: `item.Price` → `orders[0].Price` ✅

Next steps:
- Direct API test using simple_test.py
- Check backend logs for debug messages
- Verify fallback mapping is working
