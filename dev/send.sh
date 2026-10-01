#!/usr/bin/env bash
# Sends one unauthenticated Teams-like message activity to the local bridge. Usage: dev/send.sh "text" [conversation-id]
text=${1:-Hallo}; conv=${2:-conv_local_1}
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" -X POST -H 'Content-Type: application/json' \
  -d "{\"type\":\"message\",\"id\":\"in_$RANDOM\",\"channelId\":\"msteams\",\"serviceUrl\":\"http://127.0.0.1:5001/\",\"from\":{\"id\":\"user1\",\"name\":\"User\"},\"recipient\":{\"id\":\"28:bot\",\"name\":\"Bot\"},\"conversation\":{\"id\":\"$conv\",\"conversationType\":\"personal\"},\"locale\":\"de-DE\",\"text\":\"$text\"}" \
  "http://localhost:${PORT:-3978}/api/messages"
