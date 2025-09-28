import os
import sys

from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

console = Console()


def show_banner(label: str, theme: str, color: str = "cyan"):
    """Display a styled panel"""
    text = Text(f"{label}: {theme}", justify="center", style=f"bold {color}")
    panel = Panel(text, expand=True, border_style=color)
    return panel


def ansi_colors():
    txt = Text("\n16 ANSI Colors\n", style="bold underline")
    for i in range(16):
        txt.append(f"[{i:2}] ", style=f"on color({i})")
    return Panel(txt, title="ANSI Colors", border_style="blue")


def color_boxes():
    txt = Text("\nColor Boxes\n", style="bold underline")
    for fg in range(30, 38):
        for bg in range(40, 48):
            txt.append(" X ", style=f"{fg} on {bg}")
        txt.append("\n")
    return Panel(txt, title="Boxes", border_style="yellow")


def diff_colors():
    txt = Text("\nDiff Colors\n", style="bold underline")
    txt.append("\n+ Added line", style="green")
    txt.append("\n- Removed line", style="red")
    txt.append("\n~ Modified line", style="yellow")
    return Panel(txt, title="Diff", border_style="red")


def big_theme_panel(theme: str):
    """Make a big right-hand panel with centered theme name"""
    # Rich doesn’t do figlet directly; simulate with spacing + style
    big_text = Text(
        f"\n\n{theme.upper()}\n\n",
        style="bold white on black",
        justify="center",
    )
    return Panel(
        Align.center(big_text, vertical="middle"),
        border_style="magenta",
        title="NEOVIM THEME",
    )


if __name__ == "__main__":
    i_theme = sys.argv[1] if len(sys.argv) > 1 else "iTerm Theme"
    n_theme = sys.argv[2] if len(sys.argv) > 2 else "Neovim Theme"

    os.system("clear")

    layout = Layout()

    # Split left/right
    layout.split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=1),
    )

    # Stack panels vertically on left
    layout["left"].split_column(
        Layout(show_banner("iTerm Theme Demo for", i_theme, "cyan"), size=3),
        Layout(ansi_colors(), size=7),
        Layout(color_boxes(), size=10),
        Layout(diff_colors(), size=6),
    )

    # Right panel: Neovim theme big name
    layout["right"].update(big_theme_panel(n_theme))

    console.print(layout)
