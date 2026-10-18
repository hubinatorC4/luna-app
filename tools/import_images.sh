#!/bin/bash
# Kopiuje obrazy z /workspace do katalogu aplikacji (zmniejszone do 960 px).
# Nazwy: luna_outfit_<id>.jpg, luna_pose_<id>.jpg, luna_body_<id>.jpg  (id jak w catalog.py)
set -e
cd "$(dirname "$0")/.."
SRC=${1:-/workspace}
FF=$(command -v ffmpeg || python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
mkdir -p static/catalog/luna
shopt -s nullglob
for f in "$SRC"/luna_outfit_*.jpg "$SRC"/luna_pose_*.jpg "$SRC"/luna_body_*.jpg "$SRC"/luna_outfit_*.png "$SRC"/luna_pose_*.png "$SRC"/luna_body_*.png; do
  b=$(basename "$f"); b=${b#luna_}; b=${b%.*}
  "$FF" -v error -y -i "$f" -vf "scale='min(960,iw)':-2" -q:v 4 "static/catalog/luna/$b.jpg"
  echo "zaimportowano: $b.jpg"
done
