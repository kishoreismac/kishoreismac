"""Fetch public Credly badges without browser dependencies."""

import html
import json
import os
from pathlib import Path
import re
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

START = "<!--START_SECTION:badges-->"
END = "<!--END_SECTION:badges-->"


def profile_username(profile):
    username = profile.strip()
    if "://" in username:
        url = urlparse(username)
        match = re.fullmatch(r"/users/([A-Za-z0-9._-]+)(?:/badges(?:/credly)?|/edit/badges/credly)?/?", url.path)
        if url.scheme != "https" or url.netloc not in ("credly.com", "www.credly.com") or not match:
            raise ValueError("Use a Credly URL such as https://www.credly.com/users/your-name/badges")
        username = match.group(1)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", username):
        raise ValueError("CREDLY_PROFILE must be a profile URL or username, not an email address.")
    return username


def fetch_badges(username):
    badges = {}
    page = 1
    while True:
        url = f"https://www.credly.com/users/{quote(username, safe='')}/badges.json?page={page}"
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "Credly-Profile-Badges"})
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
        data = payload["data"]
        if not isinstance(data, list):
            raise ValueError("Credly returned an unexpected badge response.")
        for badge in data:
            if badge.get("public") is True and badge.get("state") == "accepted":
                badges[badge["id"]] = badge
        if page >= int(payload["metadata"]["total_pages"]):
            break
        if not data or page >= 1000:
            raise ValueError("Credly pagination did not complete; README was not changed.")
        page += 1
    if not badges:
        raise ValueError("No public Credly badges found. Check the username and profile/badge visibility. README was not changed.")
    return sorted(badges.values(), key=lambda b: (b.get("issued_at_date") or "", b["id"]), reverse=True)


def render_badges(badges, limit=50):
    lines = []
    for badge in badges[:limit] if limit else badges:
        title = html.escape(badge["badge_template"]["name"], quote=True)
        image = badge.get("image_url") or badge["badge_template"]["image_url"]
        if urlparse(image).scheme != "https" or urlparse(image).hostname != "images.credly.com":
            raise ValueError("Credly returned an unexpected badge image URL.")
        link = f"https://www.credly.com/badges/{quote(badge['id'], safe='')}/public_url"
        lines.append(f'<a href="{link}"><img src="{html.escape(image, quote=True)}" alt="{title}" title="{title}" width="100" height="100" /></a>')
    if not lines:
        raise ValueError("No badges to render; README was not changed.")
    return "\n".join(lines)


def update_readme(readme, badges):
    if readme.count(START) != 1 or readme.count(END) != 1 or readme.index(START) >= readme.index(END):
        raise ValueError("README must contain exactly one ordered pair of badge section markers.")
    before, rest = readme.split(START)
    _, after = rest.split(END)
    return before + START + "\n" + render_badges(badges) + "\n" + END + after


def main():
    username = profile_username(os.environ.get("CREDLY_PROFILE", "kiran-kumar-nune"))
    path = Path(__file__).resolve().parents[2] / "README.md"
    readme = path.read_bytes().decode("utf-8")
    badges = fetch_badges(username)
    updated = update_readme(readme, badges)
    if updated != readme:
        path.write_bytes(updated.encode("utf-8"))
    print(f"Fetched {len(badges)} public badges for {username}; displaying {min(len(badges), 10)} in README.md.")


if __name__ == "__main__":
    main()
