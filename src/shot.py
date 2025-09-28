import re
import shlex
import subprocess
import time
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "ghostty" / "config"
GHOSTTY_APP = "/Applications/Ghostty.app"  # adjust if installed elsewhere


def write_theme(new_theme: str):
    """Update the theme line in the Ghostty config."""
    text = CONFIG_PATH.read_text()
    # Either replace theme line or append
    if re.search(r"^\s*theme\s*=", text, flags=re.MULTILINE):
        text = re.sub(
            r"^\s*theme\s*=.*$", f'theme = "{new_theme}"', text, flags=re.MULTILINE
        )
    else:
        text += f'\ntheme = "{new_theme}"\n'
    CONFIG_PATH.write_text(text)
    print(f"Set theme in config to: {new_theme}")


def reload_ghostty():
    """Attempt to reload Ghostty so config changes take effect."""
    # Option A: kill & restart (brutal but straightforward)
    subprocess.run(["pkill", "-f", "Ghostty"])
    time.sleep(1)
    subprocess.run(["open", "-a", "Ghostty"])
    # Option B: send a “reload config” keypress or AppleScript, if Ghostty supports that
    # (Not guaranteed to exist)


def get_ghostty_window_id() -> str:
    script = r"""
    tell application "Ghostty" to activate
    tell application "System Events"
        tell process "Ghostty"
            set win_id to id of front window
        end tell
    end tell
    return win_id
    """
    out = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return out.stdout.strip()


def take_screenshot(theme_name: str, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    fname = outdir / f"{theme_name}.png"
    # -x = capture frontmost window
    subprocess.run(["screencapture", "-x", str(fname)])
    print(f"Saved screenshot for {theme_name}")


def run_command_in_ghostty(cmd: str):
    """Send a command string to Ghostty via AppleScript."""
    script = f"""
    tell application "Ghostty"
        activate
        tell application "System Events"
            keystroke "{cmd}"
            key code 36 -- Return
        end tell
    end tell
    """
    subprocess.run(["osascript", "-e", script])


def run_demo_in_ghostty(theme_name: str):
    script = f"""
    tell application "Ghostty" to activate
    tell application "System Events"
        keystroke "bash ~/projects/colors/src/theme_demo.sh {theme_name}"
        key code 36 -- Return
    end tell
    """
    subprocess.run(["osascript", "-e", script])


def resize_ghostty(width=1000, height=1100):
    script = f"""
    tell application "System Events"
        tell application process "Ghostty"
            set size of front window to {{ {width}, {height} }}
        end tell
    end tell
    """
    subprocess.run(["osascript", "-e", script])


def cycle_themes(theme_list, outdir: str, delay=1.0):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for theme in theme_list:
        print("=== Theme:", theme)
        write_theme(theme)
        reload_ghostty()
        # wait for UI to settle (rendering, window appear)
        time.sleep(delay + 0.5)
        # run_command_in_ghostty(f'bash ~/projects/colors/src/theme_demo.sh "{theme}"')
        # run_command_in_ghostty("l ~/projects/colors/src/")
        resize_ghostty()
        time.sleep(delay + 0.1)
        run_demo_in_ghostty(theme)
        time.sleep(delay + 0.5)
        take_screenshot(theme, outdir)
        time.sleep(delay + 0.5)


if __name__ == "__main__":
    my_themes = [
        "Catppuccin Mocha",
        "Tomorrow Night Blue",
        "Everblush",
        "Snazzy Soft",
        # ... 48 more
    ]
    cycle_themes(my_themes, outdir="../data/interim/screenshots", delay=2.0)
