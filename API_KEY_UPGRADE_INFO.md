# AviationStack API Key Information

## Current Situation

**API Key:** `e20e7bed45a2ceacb137580a8dae223f`
**Plan:** Free Tier

### Free Tier Limitations:
- ❌ Cannot query specific dates with `flight_date` parameter
- ✅ Returns recent flights only (last 24-48 hours)
- ✅ 100 API requests per month
- ❌ No historical data access

### Current Error:
When requesting flight on specific date (e.g., 2026-03-06):
```
❌ Error: Flight KL1234 not found for 2026-03-06. 
Available: 2026-03-15, 2026-03-16. 
Note: Free tier shows recent flights only.

💡 Alternative Options:
1. Check available dates: 2026-03-15, 2026-03-16
2. Use manual entry: Tell me your flight delay details
3. Upgrade API plan for historical data access
```

## Solution: Upgrade to Paid Plan

### Option 1: Basic Plan ($9.99/month)
- ✅ Historical flight data access
- ✅ `flight_date` parameter supported
- ✅ 10,000 API requests/month
- ✅ Real-time and historical data

### Option 2: Professional Plan ($49.99/month)
- ✅ Everything in Basic
- ✅ 100,000 API requests/month
- ✅ Premium support

### How to Upgrade:

1. **Visit:** https://aviationstack.com/product
2. **Choose Plan:** Basic or Professional
3. **Get New API Key:** After upgrade, you'll receive a new API key
4. **Update Code:** Replace the API key in `flight_verifier.py`:

```python
# In flight_verifier.py, line 19:
DEFAULT_ACCESS_KEY = "your_new_paid_api_key_here"
```

Or set environment variable:
```bash
export AVIATIONSTACK_API_KEY="your_new_paid_api_key_here"
```

## Alternative: Use Manual Entry Mode

The chatbot supports manual entry for any flight, any date:

**User says:**
"My flight KL1234 from Amsterdam to Barcelona on 2026-03-06 was delayed 5 hours"

**Chatbot responds:**
✅ Calculates EU261 eligibility based on input
✅ Works for any date (past, present, future)
✅ No API limitations

## Recommendation

For production use with historical data queries:
1. **Upgrade to Basic Plan** ($9.99/month)
2. **Keep manual entry mode** as fallback
3. **Update API key** in environment variable (not hardcoded)

This gives users two options:
- Quick lookup for recent flights (free)
- Manual entry for historical flights (no cost)
- Or upgrade for full historical API access

