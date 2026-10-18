#!/bin/bash
# Luna – szybkie wdrożenie: commit + push na GitHub (Render buduje z gałęzi main).
# Użycie: ./deploy.sh "Opis zmian"
set -e
cd "$(dirname "$0")"
MSG=${1:-"Aktualizacja $(date '+%Y-%m-%d %H:%M')"}
[ -x tools/import_images.sh ] && tools/import_images.sh >/dev/null || true
git add -A
git diff --cached --quiet && { echo "Brak zmian do wdrożenia."; exit 0; }
git commit -m "$MSG"
git push origin main
echo "Wypchnięto. Jeśli Render nie ma połączonego GitHuba, uruchom wdrożenie ręcznie (Render → Manual Deploy)."
echo "Pamiętaj: przy nowej wersji podbij VERSION w static/sw.js i server.py – użytkownicy zobaczą „Dostępna nowa wersja – odśwież”."
