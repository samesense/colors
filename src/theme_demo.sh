#!/usr/bin/env bash

theme_name="${1:-TEST THEME}"

clear

echo
echo "========================================="
printf " iTerm Theme Demo for: \033[1m%s\033[0m\n" "$theme_name"
echo "========================================="
echo

#theme_name="${1:-no theme name provided}"

#printf "Theme Demo for: \033[1mTEST\033[0m\n"

# === 16 ANSI Colors ===
echo
echo "=== 16 ANSI Colors ==="
for i in {0..15}; do
    printf "\e[48;5;${i}m%3s\e[0m " $i
done
echo

# === 256 Color Palette ===
echo
echo "=== 256 Colors ==="
for i in {0..255}; do
    printf "\e[48;5;${i}m%3s\e[0m " $i
    if (( ($i + 1) % 16 == 0 )); then
        echo
    fi
done

# === Truecolor Gradient ===
echo
echo "=== Truecolor Gradient ==="
awk 'BEGIN{
  for (i=0;i<77;i++) {
    r = 255-(i*255/76); g = (i*255/76); b = 128;
    printf("\033[48;2;%d;%d;%dm ", r,g,b);
  }
  print "\033[0m"
}'

echo
echo "=== Color Boxes ==="
for fg in 30 31 32 33 34 35 36 37; do
  for bg in 40 41 42 43 44 45 46 47; do
    printf "\033[%s;%sm %2s \033[0m" "$fg" "$bg" "X"
  done
  echo
done
