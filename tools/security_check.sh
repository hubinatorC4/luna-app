#!/bin/bash
# Luna – lokalny audyt bezpieczeństwa (darmowe narzędzia). Użycie: tools/security_check.sh [URL]
set -u
cd "$(dirname "$0")/.."
URL=${1:-https://luna-voice-coach.onrender.com}
command -v bandit >/dev/null || pip install -q bandit pip-audit
echo "== bandit (średnie i wysokie)"; bandit -r . -x ./tests,./tools -ll -q || true
echo "== pip-audit"; pip-audit -r requirements.txt || true
command -v gitleaks >/dev/null && { echo "== gitleaks"; gitleaks git . --redact || true; }
echo "== nagłówki $URL"; curl -sI "$URL/" | grep -iE "strict-transport|content-security|x-content-type|referrer-policy|permissions-policy|x-frame|cross-origin|^server" || true
echo "== security.txt"; curl -s "$URL/.well-known/security.txt" | head -3
echo "== Mozilla Observatory"; curl -s -X POST "https://observatory-api.mdn.mozilla.net/api/v2/scan?host=${URL#https://}" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('grade'),d.get('score'))" || true
