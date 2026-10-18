#!/bin/bash
# Co ~90 min: sync zdjęć Butiku, commit TYLKO plików Butiku, push. Wdrożenie na Renderze wywołuje agent (trigger_deploy),
# gdy pojawi się plik /workspace/shots/BUTIK_DEPLOY_PENDING. Zatrzymanie: pkill -f butik_autosync.sh
cd /workspace/luna-app
while true; do
  { date -u; python3 tools/sync_butik_images.py
    git add static/catalog/butik data/catalog_outfits.json
    if [ -n "$(git status --porcelain | grep -v -E ' (static/catalog/butik/|data/catalog_outfits.json)')" ]; then
      echo "inne niezatwierdzone zmiany w repo – pomijam tę rundę (bez commitu), żeby nie kolidować z pracą agentów"; git reset -q
    elif ! git diff --cached --quiet; then
      git -c user.name="Luna Team" -c user.email="luna-team@users.noreply.github.com" commit -qm "Butik: automatyczna synchronizacja zdjęć $(date -u +%H:%M)" -- static/catalog/butik data/catalog_outfits.json \
       && git pull -q --rebase --autostash origin main && git push -q origin main && git log --oneline -1 > /workspace/shots/BUTIK_DEPLOY_PENDING
    else echo "bez zmian"; fi; } >> /tmp/butik_autosync.log 2>&1
  sleep 5400
done
