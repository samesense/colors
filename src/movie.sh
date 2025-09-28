#!/usr/bin/env bash
set -euo pipefail
# magick ../data/interim/screenshots/*.png \
#   -resize 1080x1920^ -gravity center -extent 1080x1920 \
#   ../data/interim/shot_tmp/final_%03d.png
#
# ffmpeg -framerate 1/3 -i ../data/interim/shot_tmp/final_%03d.png \
#   -c:v libx264 -r 30 -pix_fmt yuv420p \
#   -vf "scale=1080:1920,format=yuv420p" \
#   ../data/interim/demo.mp4
#
# ffmpeg -pattern_type glob -framerate 1/3 -i "../data/interim/screenshots/*.png" \
#   -c:v libx264 -r 30 -pix_fmt yuv420p \
#   -vf "scale=1080:1920,format=yuv420p" \
#   ../data/interim/demo.mp4

indir="../data/interim/screenshots"
outfile="../data/interim/demo.mp4"
tmpfile="file_list.txt"

indir_abs=$(cd "$indir"; pwd)

{
  echo "file '$indir_abs/aa.png'"
  echo "duration 3"

  ls "$indir_abs"/*.png \
    | grep -v -E 'aa.png|zz.png' \
    | sort -R \
    | while read -r f; do
        echo "file '$f'"
        echo "duration 3"
      done

  echo "file '$indir_abs/zz.png'"
  echo "duration 3"
} > "$tmpfile"

ffmpeg -y -f concat -safe 0 -i "$tmpfile" \
  -c:v libx264 -pix_fmt yuv420p \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" \
  "$outfile"

echo "🎬 Video created at $outfile"
