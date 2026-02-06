#\!/bin/bash
URL="http://host.docker.internal:8000/mcp"
BODY='{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'

echo "=== Test 1: With Accept header ==="
curl -s -X POST "$URL" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "X-API-Key: qms-internal" -H "Authorization: Bearer internal-trusted" -d "$BODY"
echo ""

echo "=== Test 2: Without Accept header ==="
curl -s -X POST "$URL" -H "Content-Type: application/json" -H "X-API-Key: qms-internal" -H "Authorization: Bearer internal-trusted" -d "$BODY"
echo ""
