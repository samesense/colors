# magick ../data/interim/screenshots/*.png \
#   -resize 1080x1920^ -gravity center -extent 1080x1920 \
#   ../data/interim/shot_tmp/final_%03d.png
#
# ffmpeg -framerate 1/3 -i ../data/interim/shot_tmp/final_%03d.png \
#   -c:v libx264 -r 30 -pix_fmt yuv420p \
#   -vf "scale=1080:1920,format=yuv420p" \
#   ../data/interim/demo.mp4
#
ffmpeg -pattern_type glob -framerate 1/3 -i "../data/interim/screenshots/*.png" \
  -c:v libx264 -r 30 -pix_fmt yuv420p \
  -vf "scale=1080:1920,format=yuv420p" \
  ../data/interim/demo.mp4
