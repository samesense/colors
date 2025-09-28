"""Automate screenshots."""

import os
import re
import shlex
import subprocess
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd

CONFIG_PATH = Path.home() / ".config" / "ghostty" / "config"
GHOSTTY_APP = "/Applications/Ghostty.app"


def ensure_tmux_demo(nvim_theme):
    """Setup tmux and nvim. ex rusty"""
    env = dict(**os.environ)
    env.pop("TMUX", None)  # avoid nesting issues

    # Kill any existing session
    subprocess.run("tmux kill-session -t demo 2>/dev/null", shell=True, env=env)

    subprocess.run(["tmux", "new-session", "-d", "-s", "demo"], env=env)
    subprocess.run(["tmux", "split-window", "-v", "-p", "50", "-t", "demo"], env=env)

    demo_file = "~/projects/colors/src/shot.py"
    subprocess.run(
        [
            "tmux",
            "send-keys",
            "-t",
            "demo:.1",
            f"NVIM_THEME='{nvim_theme}' nvim {demo_file}",
            "C-m",
        ],
        env=env,
    )


def set_ghostty_font(size=22):
    cfg = CONFIG_PATH.read_text().splitlines()
    new_cfg = []
    replaced = False
    for line in cfg:
        if line.strip().startswith("font-size"):
            new_cfg.append(f"font-size = {size}")
            replaced = True
        else:
            new_cfg.append(line)
    if not replaced:
        new_cfg.append(f"font-size = {size}")
    CONFIG_PATH.write_text("\n".join(new_cfg) + "\n")
    print(f"🔠 Set Ghostty font size = {size}")


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


# def reload_ghostty():
#     """Attempt to reload Ghostty so config changes take effect."""
#     # Option A: kill & restart (brutal but straightforward)
#     subprocess.run(["pkill", "-f", "Ghostty"])
#     time.sleep(1)
#     subprocess.run(["open", "-a", "Ghostty", "--args", "--title", '"ThemeDemo"'])
# Option B: send a “reload config” keypress or AppleScript, if Ghostty supports that
# (Not guaranteed to exist)


def reload_ghostty(title="ThemeDemo"):
    """Kill and restart Ghostty, then set the window title."""
    # Kill existing Ghostty
    subprocess.run(["pkill", "-f", "Ghostty"])
    time.sleep(1)

    # Launch fresh Ghostty
    subprocess.run(["open", "-a", "Ghostty"])
    time.sleep(1)

    # Set window title using ANSI escape sequence
    script = f"""
    tell application "Ghostty" to activate
    tell application "System Events"
        keystroke "tmux attach -t demo || tmux new -s demo"
        key code 36 -- Return
    end tell
    """
    subprocess.run(["osascript", "-e", script])


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


# def screenshot_ghostty(outfile: Path):
#     # bring Ghostty to the front
#     subprocess.run(["osascript", "-e", 'tell application "Ghostty" to activate'])
#     # take a screenshot of the *frontmost window*
#     subprocess.run(["screencapture", "-x", str(outfile)])
#     print(f"✅ Saved screenshot: {outfile}")


def screenshot_ghostty(outfile: Path):
    cmd = "yabai -m query --windows | jq -r '.[] | select(.app==\"Ghostty\") | .id' | head -n 1"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    win_id = result.stdout.strip()

    if not win_id:
        raise RuntimeError("⚠️ No Ghostty window found")

    subprocess.run(["screencapture", f"-l{win_id}", str(outfile)], check=True)
    print(f"✅ Saved screenshot: {outfile}")


# def screenshot_ghostty(outfile: Path, title="ThemeDemo"):
#     # Get Ghostty window ID via yabai + jq
#     cmd = f'yabai -m query --windows | jq -r \'.[] | select(.app=="Ghostty" and .title=="{title}") | .id\''
#     result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
#     win_id = result.stdout.strip()
#
#     if not win_id or win_id == "null":
#         raise RuntimeError(
#             "⚠️ Could not find Ghostty window ID. Is it running with --title set?"
#         )
#
#     # Take screenshot of that window only
#     subprocess.run(["screencapture", f"-l{win_id}", str(outfile)], check=True)
#
#     print(f"✅ Saved screenshot to {outfile}")


# def screenshot_ghostty(outfile: Path):
#     script = """
#     tell application "System Events"
#         if exists (process "Ghostty") then
#             tell process "Ghostty"
#                 if exists (front window) then
#                     set winBounds to bounds of front window
#                     return winBounds
#                 end if
#             end tell
#         end if
#     end tell
#     return "ERROR"
#     """
#     result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
#     bounds_str = result.stdout.strip()
#     if bounds_str == "ERROR" or not bounds_str:
#         print("⚠️ Could not get Ghostty window bounds, falling back to full screen.")
#         subprocess.run(["screencapture", str(outfile)])
#         return
#
#     # Parse coordinates into x,y,w,h
#     x, y, w, h = map(int, bounds_str.split(", "))
#     subprocess.run(["screencapture", "-R", f"{x},{y},{w},{h}", str(outfile)])
#     print(f"✅ Saved screenshot: {outfile}")


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


def run_demo_in_ghostty(theme: str, nvim_theme: str):
    cmd = f'tmux send-keys -t demo "bash ~/projects/colors/src/theme_demo.sh \\"{theme}\\" \\"{nvim_theme}\\"" C-m'
    # cmd = (
    #     f'tmux send-keys -t demo:0.0 "bash ~/projects/theme_demo.sh \\"{theme}\\"" C-m'
    # )
    subprocess.run(cmd, shell=True, check=True)
    print(f"▶️ Ran demo for {theme} in tmux:demo left pane")

    # cmd = f'tmux send-keys -t demo "bash ~/projects/colors/src/theme_demo.sh \\"{theme}\\"" C-m'
    # subprocess.run(cmd, shell=True, check=True)
    # print(f"▶️ Ran demo for {theme} inside tmux")

    # script = f"""
    # tell application "Ghostty" to activate
    # tell application "System Events"
    #     keystroke "bash ~/projects/colors/src/theme_demo.sh {theme_name}"
    #     key code 36 -- Return
    # end tell
    # """
    # subprocess.run(["osascript", "-e", script])


def resize_ghostty(width=1080, height=1920):
    script = f"""
    tell application "System Events"
        tell application process "Ghostty"
            set size of front window to {{ {width}, {height} }}
        end tell
    end tell
    """
    subprocess.run(["osascript", "-e", script])


def cycle_themes(theme_dict, outdir: str, delay=1.0):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for iterm_theme in theme_dict:
        for nvim_theme in theme_dict[iterm_theme]:
            ensure_tmux_demo(nvim_theme)
            print("=== Theme:", iterm_theme)
            write_theme(iterm_theme)
            set_ghostty_font(size=20)
            reload_ghostty()
            # wait for UI to settle (rendering, window appear)
            time.sleep(delay + 0.5)
            # run_command_in_ghostty(f'bash ~/projects/colors/src/theme_demo.sh "{theme}"')
            # run_command_in_ghostty("l ~/projects/colors/src/")
            resize_ghostty()
            time.sleep(delay + 0.1)
            run_demo_in_ghostty(iterm_theme, nvim_theme)
            time.sleep(delay + 0.5)
            tname = iterm_theme.replace(" ", "_").replace("/", "_")
            n_name = nvim_theme.replace(" ", "_").replace("/", "_")
            screenshot_ghostty(
                Path("../data/interim/screenshots") / f"{tname}__{n_name}.png"
            )
            time.sleep(delay + 0.5)


def init_d():
    return defaultdict(dict)


if __name__ == "__main__":
    cols = ["nvim_name", "colorscheme_name"]
    inside_nvim_names = pd.read_csv(Path("../data/end/theme_list.csv"))[cols]
    theme_file = Path("../data/end/top50_filtered.tsv")
    df = pd.read_csv(theme_file, sep="\t")
    iterm_to_nvim = defaultdict(init_d)
    crit = df.apply(
        lambda row: (
            row["iterm_name"] == "One Half Light" and row["nvim_name"] == "onehalf"
        )
        or (row["iterm_name"] == "One Half Dark" and row["nvim_name"] == "onehalf")
        or (row["iterm_name"] == "Snazzy Soft" and row["nvim_name"] == "camila")
        or (row["iterm_name"] == "Rose Pine Moon" and row["nvim_name"] == "Sakura.nvim")
        or (row["iterm_name"] == "CGA" and row["nvim_name"] == "templeos.nvim")
        or (
            row["iterm_name"] == "Gruvbox Dark Hard"
            and row["nvim_name"] == "gruvsquirrel.nvim"
        )
        or (
            row["iterm_name"] == "Challenger Deep"
            and row["nvim_name"] == "embark-lua.nvim"
        )
        or (row["iterm_name"] == "Tomorrow Night" and row["nvim_name"] == "hybrid.nvim")
        or (
            row["iterm_name"] == "TokyoNight Storm"
            and row["nvim_name"] == "kyotonight.vim"
        )
        or (
            row["iterm_name"] == "TokyoNight Night"
            and row["nvim_name"] == "kyotonight.vim"
        )
        or (row["iterm_name"] == "TokyoNight" and row["nvim_name"] == "kyotonight.vim"),
        axis=1,
    )
    df = df[~crit]
    df = df.head(10)
    df = df.merge(
        inside_nvim_names,
        how="left",
    )
    for _, row in df.iterrows():
        iterm_to_nvim[row["iterm_name"]][row["colorscheme_name"]] = row["nvim_url"]

    cycle_themes(iterm_to_nvim, outdir="../data/interim/screenshots", delay=2.0)
