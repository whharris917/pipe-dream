#\!/bin/bash
COUNT=${1:-30}
PROXY="/proxy/mcp_proxy.py"
QMS_URL="http://host.docker.internal:8000/mcp"
GIT_URL="http://host.docker.internal:8001/mcp"
INITIALIZE='{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"proxy-test","version":"1.0"}},"id":1}'
qms_pass=0
qms_fail=0
git_pass=0
git_fail=0
echo "=== MCP Proxy Reliability Test ==="
echo "Iterations: $COUNT"
echo ""
for i in $(seq 1 "$COUNT"); do
    printf "Test %2d/%d: " "$i" "$COUNT"
    qms_result=$(echo "$INITIALIZE" | timeout 15 python3 "$PROXY" "$QMS_URL" --retries 2 --timeout 5000 --header "X-API-Key=qms-internal" --header "Authorization=Bearer internal-trusted" 2>/dev/null)
    if echo "$qms_result" | grep -q '"result"'; then
        qms_status="PASS"
        qms_pass=$((qms_pass + 1))
    else
        qms_status="FAIL"
        qms_fail=$((qms_fail + 1))
    fi
    git_result=$(echo "$INITIALIZE" | timeout 15 python3 "$PROXY" "$GIT_URL" --retries 2 --timeout 5000 --header "X-API-Key=git-internal" --header "Authorization=Bearer internal-trusted" 2>/dev/null)
    if echo "$git_result" | grep -q '"result"'; then
        git_status="PASS"
        git_pass=$((git_pass + 1))
    else
        git_status="FAIL"
        git_fail=$((git_fail + 1))
    fi
    echo "QMS=$qms_status  Git=$git_status"
done
echo ""
echo "=== Results ==="
echo "QMS: $qms_pass/$COUNT passed ($qms_fail failed)"
echo "Git: $git_pass/$COUNT passed ($git_fail failed)"
echo "Combined: $((qms_pass + git_pass))/$((COUNT * 2)) passed"
if [ "$qms_fail" -eq 0 ] && [ "$git_fail" -eq 0 ]; then
    echo ""
    echo "RESULT: ALL PASS ($COUNT/$COUNT)"
    exit 0
else
    echo ""
    echo "RESULT: FAILURES DETECTED"
    exit 1
fi
