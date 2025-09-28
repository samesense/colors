import os
import sys

from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

console = Console()


def theme_panel(label: str, theme: str, color: str) -> Panel:
    """Panel showing the theme name with a labeled title."""
    theme_big = "  ".join(theme.upper())  # spread letters
    text = Text(theme_big, justify="center", style=f"bold {color}")
    return Panel(
        Align.center(text, vertical="middle"),
        title=label,
        border_style=color,
        padding=(2, 6),
    )


def ansi_colors() -> Panel:
    txt = Text()
    for i in range(16):
        txt.append(f" {i:2} ", style=f"on color({i})")
    return Panel(txt, border_style="blue", title="16 ANSI Colors", padding=(1, 2))


def color_boxes() -> Panel:
    fg_colors = {
        30: "black",
        31: "red",
        32: "green",
        33: "yellow",
        34: "blue",
        35: "magenta",
        36: "cyan",
        37: "white",
    }
    bg_colors = {
        40: "on black",
        41: "on red",
        42: "on green",
        43: "on yellow",
        44: "on blue",
        45: "on magenta",
        46: "on cyan",
        47: "on white",
    }

    txt = Text()
    for fg in fg_colors:
        for bg in bg_colors:
            txt.append(" X ", style=f"{fg_colors[fg]} {bg_colors[bg]}")
        txt.append("\n")
    return Panel(txt, border_style="yellow", title="Color Boxes", padding=(1, 2))


def diff_colors() -> Panel:
    txt = Text()
    txt.append("+ Added line\n", style="green")
    txt.append("- Removed line\n", style="red")
    txt.append("~ Modified line\n", style="yellow")
    return Panel(txt, border_style="red", title="Diff", padding=(1, 2))


if __name__ == "__main__":
    i_theme = sys.argv[1] if len(sys.argv) > 1 else "iTerm Theme"
    n_theme = sys.argv[2] if len(sys.argv) > 2 else "Neovim Theme"

    os.system("clear")

    layout = Layout()
    layout.split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=1),
    )

    # Left side = visuals
    layout["left"].split_column(
        Layout(ansi_colors(), size=7),
        Layout(color_boxes(), size=12),
        Layout(diff_colors(), size=6),
    )

    # Right side = vertically centered theme panels
    right_layout = Layout()
    right_layout.split_column(
        Layout(theme_panel("NVIM THEME", n_theme, "magenta"), size=10),
        Layout(theme_panel("ITERM THEME", i_theme, "cyan"), size=10),
    )

    layout["right"].update(Align.center(right_layout, vertical="middle"))

    console.print(layout)
