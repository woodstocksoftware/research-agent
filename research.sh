#!/bin/bash
# Research Agent CLI
# Usage: ./research.sh "your topic here"

TOPIC="$1"

if [ -z "$TOPIC" ]; then
  echo "Usage: ./research.sh \"your topic here\""
  exit 1
fi

echo "🔍 Researching: $TOPIC"
echo "⏳ This takes 2-3 minutes..."
echo ""

# Create payload
echo "{\"body\": \"{\\\"topic\\\": \\\"$TOPIC\\\"}\"}" > /tmp/payload.json

# Invoke Lambda
aws lambda invoke \
  --function-name research-agent-dev \
  --cli-read-timeout 300 \
  --cli-binary-format raw-in-base64-out \
  --payload file:///tmp/payload.json \
  /tmp/response.json > /dev/null 2>&1

# Extract and display the report
python3 << PYTHON
import json
with open('/tmp/response.json') as f:
    data = json.load(f)
    body = json.loads(data['body'])
    print(body['report'])
    print("\n" + "="*60)
    print(f"📊 Findings: {body['findings_count']} | Sources: {body['sources_count']} | Iterations: {body['iterations']}")
PYTHON
