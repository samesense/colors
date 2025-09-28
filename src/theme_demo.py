import os
import sys

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def show_banner(label: str, theme: str, color: str = "cyan"):
    """Display a big styled panel for theme demo"""
    text = Text(f"{label}: {theme}", justify="center", style=f"bold {color}")
    panel = Panel(text, expand=True, border_style=color)
    console.print(panel)


def ansi_colors():
    console.print("\n[bold underline]16 ANSI Colors[/]\n")
    for i in range(16):
        console.print(f"[on color({i})]  {i:2} [/]", end=" ")
    console.print()


def color_boxes():
    console.print("\n[bold underline]Color Boxes[/]\n")
    for fg in range(30, 38):
        row = ""
        for bg in range(40, 48):
            row += f"\033[{fg};{bg}m X \033[0m"
        print(row)


def diff_colors():
    console.print("\n[bold underline]Diff Colors[/]\n")
    console.print("+ Added line", style="green")
    console.print("- Removed line", style="red")
    console.print("~ Modified line", style="yellow")


if __name__ == "__main__":
    i_theme = sys.argv[1] if len(sys.argv) > 1 else "iTerm Theme"
    n_theme = sys.argv[2] if len(sys.argv) > 2 else "Neovim Theme"

    os.system("clear")

    show_banner("Neovim Theme Demo for", n_theme, "magenta")
    show_banner("iTerm Theme Demo for", i_theme, "cyan")

    ansi_colors()
    color_boxes()
    diff_colors()
