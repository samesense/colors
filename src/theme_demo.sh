#!/usr/bin/env bash

i_theme_name="${1:-TEST THEME}"
n_theme_name="${2:-TEST THEME}"

clear

# Terminal width (fallback 80)
cols=$(tput cols 2>/dev/null || echo 80)

# Draw a full-width colored '=' bar using a palette of 256-color indexes
draw_bar() {
  local width="$1"; shift
  local palette=("$@")
  local n=${#palette[@]}
  local i c
  for ((i=0;i<width;i++)); do
    c=${palette[i % n]}
    printf "\e[38;5;%sm=\e[0m" "$c"
  done
  echo
}

# Palettes (tweak to taste)
nv_palette=(196 202 208 214 220 190 118 51 39 63 129)   # rainbow-ish for Neovim
it_palette=(99 105 111 117 123 159 153 147 141 135)     # cool blues for iTerm/Ghostty

echo
draw_bar "$cols" "${nv_palette[@]}"
printf " Neovim Theme Demo for: \033[1m%s\033[0m\n" "$n_theme_name"
draw_bar "$cols" "${nv_palette[@]}"

echo
draw_bar "$cols" "${it_palette[@]}"
printf " iTerm Theme Demo for: \033[1m%s\033[0m\n" "$i_theme_name"
draw_bar "$cols" "${it_palette[@]}"

echo
echo "=== 16 ANSI Colors ==="
for i in {0..15}; do
    printf "\e[48;5;${i}m%3s\e[0m " $i
done
echo

echo
echo "=== Color Boxes ==="
for fg in 30 31 32 33 34 35 36 37; do
  for bg in 40 41 42 43 44 45 46 47; do
    printf "\033[%s;%sm %2s \033[0m" "$fg" "$bg" "X"
  done
  echo
done
