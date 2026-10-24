#!/usr/bin/env bash
# Render start command, one free web service for two bots:
#  * @najotservis_bot   — public $PORT: webhook + request form, forwards /ishonch/... to the second bot
#  * @ishonchservis_bot — same code on local port 10001, own DB schema, restarted if it ever exits
cd "$(dirname "$0")/najot_servis"
if [ -n "$ISHONCH_BOT_TOKEN" ]; then
  export PROXY_ROUTES="ishonch=10001"
  ( while true; do
      BOT_TOKEN="$ISHONCH_BOT_TOKEN" PORT=10001 DB_SCHEMA=ishonch KEEP_AWAKE=0 \
      OWNER_USERNAMES="$ISHONCH_OWNERS" MASTER_USERNAMES="$ISHONCH_MASTERS" NOTIFY_TARGETS="$ISHONCH_NOTIFY" \
      WEBHOOK_URL="$RENDER_EXTERNAL_URL/ishonch" MINIAPP_URL="$RENDER_EXTERNAL_URL/ishonch/" \
      python -m bot
      sleep 5
    done ) &
fi
exec python -m bot
