#!/bin/bash

echo "=== Complete System Integration Test ==="
echo

# Test 1: Check Redis connection
echo "1. Testing Redis Connection..."
redis-cli ping
echo

# Test 2: Check hints are loaded
echo "2. Testing Hints API..."
curl -s http://localhost:8000/api/hints/categories | jq -r '.[]' | head -5
echo

# Test 3: Test suggestions with caching
echo "3. Testing Suggestions (should use cache)..."
time curl -s -X POST http://localhost:8000/api/hints/suggestions \
  -H "Content-Type: application/json" \
  -d '{"user_input": "show users with orders", "limit": 3}' | jq -r '.[] | "\(.category): \(.suggestion)"'
echo

# Test 4: Check cache stats
echo "4. Cache Statistics..."
curl -s http://localhost:8000/api/queries/cache/stats | jq '.hit_rate'
echo

# Test 5: Test enum functionality  
echo "5. Testing Enum Management..."
curl -s http://localhost:8000/api/connections/ | jq -r '.[0].name' 2>/dev/null || echo "No connections configured"
echo

echo "=== Test Complete ==="
