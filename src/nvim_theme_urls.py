import pandas as pd
from playwright.sync_api import sync_playwright

url = "https://github.com/topics/neovim-colorscheme"
themes = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)

    # Keep clicking "Load more" until it's gone
    while page.locator("text=Load more").is_visible():
        page.locator("text=Load more").click()
        page.wait_for_timeout(1500)  # wait for new repos to load

    # Extract repo links
    repo_links = page.locator("article h3 a")
    count = repo_links.count()
    for i in range(count):
        name = repo_links.nth(i).inner_text().strip()
        href = "https://github.com" + repo_links.nth(i).get_attribute("href")
        themes.append((name, href))

    browser.close()

# Save to CSV
df = pd.DataFrame(themes, columns=["name", "url"])
df.to_csv("../data/interim/urls/neovim_colorschemes.csv", index=False)
print(f"Saved {len(df)} repos to neovim_colorschemes.csv")
