"""Render both static language editions from shared layouts and message catalogs."""

from html import escape
import json
from pathlib import Path
import posixpath
import re

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PUBLIC = "https://starcloud530.github.io/pixelforge-demos/"
SLOT = re.compile(r"{{\s*([\w.:-]+)\s*}}")


def render(template, values):
    return SLOT.sub(lambda match: values[match[1]], template)


def relative(target, current):
    return posixpath.relpath(target or ".", current or ".") + "/"


def render_site(destination):
    media = json.loads((ROOT / "demos/studio-media.json").read_text())
    images = {
        "media:" + name: escape(media["base"] + name + "?rev=" + entry["sha256"][:16])
        for name, entry in media["objects"].items()
    }
    icons = re.findall(r'<symbol id="([\w-]+)"', (SITE / "assets/icons.svg").read_text())
    base = (SITE / "templates/base.html").read_text()
    scene = (SITE / "templates/scene.html").read_text()
    locales = {lang: json.loads((SITE / "locales" / f"{lang}.json").read_text()) for lang in ("en", "zh")}
    if locales["en"].keys() != locales["zh"].keys():
        raise ValueError("English and Chinese message keys differ")
    for lang, messages in locales.items():
        prefix, other = ("", "zh/") if lang == "en" else ("zh/", "")
        for page in ("", "gallery/"):
            route = prefix + page
            assets = relative("assets", route).rstrip("/")
            values = {
                **images, **{key: escape(value) for key, value in messages.items()},
                "lang": lang, "otherLang": "zh" if lang == "en" else "en",
                "otherName": "中文" if lang == "en" else "English",
                "homeUrl": relative(prefix, route), "galleryUrl": relative(prefix + "gallery", route),
                "docsUrl": "/pixelforge-ai/" + prefix, "assets": assets,
                "alternate": relative(other + page, route), "canonical": PUBLIC + route,
                "canonicalEn": PUBLIC + page, "canonicalZh": PUBLIC + "zh/" + page,
                "galleryCurrent": 'aria-current="page"' if page else "",
                "playerScript": f'<script type="module" src="{assets}/player.js"></script>' if page else "",
            }
            for icon in icons:
                values["icon:" + icon] = (
                    f'<svg class="ui-icon icon-{icon}" aria-hidden="true" focusable="false">'
                    f'<use href="{assets}/icons.svg#{icon}"></use></svg>'
                )
            values["title"] = values["galleryTitle" if page else "homeTitle"]
            values["description"] = values["galleryDescription" if page else "homeDescription"]
            values["sceneViewer"] = render(scene, values)
            values["body"] = render((SITE / page / "index.html").read_text(), values)
            output = destination / route / "index.html"
            output.parent.mkdir(parents=True, exist_ok=True)
            html = render(base, values)
            if "{{" in html or "}}" in html:
                raise ValueError(f"Unresolved template in {output}")
            output.write_text(html)
