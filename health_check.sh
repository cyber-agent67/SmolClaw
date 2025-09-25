#!/bin/bash
# health_check.sh
echo "🔍 Checking C++ Web Server health..."

response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:18080/)
if [ $response -eq 200 ]; then
    echo "✅ Server is healthy (HTTP $response)"
    echo "📝 Response: $(curl -s http://localhost:18080/)"
    exit 0
else
    echo "❌ Server is not responding (HTTP $response)"
    echo "💡 Make sure the server is running on port 18080"
    exit 1
fi

