#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从 raw/*.txt 生成 notes/*.html，并把链接插入 index.html 的“最近更新”列表。

规则：
- txt 第 1 行：标题
- txt 第 2 行：日期 YYYY-MM-DD
- txt 第 3 行起：正文（每一行 = 一个段落，空行跳过）

幂等：
- notes 中已存在 html → 不生成
- index.html 中已存在该链接 → 不插入
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from html import escape
from datetime import datetime

# ========= 路径设置（关键修改点） =========

SCRIPT_DIR = Path(__file__).resolve().parent       # tools/
ROOT = SCRIPT_DIR.parent                           # 项目根目录

RAW_DIR = ROOT / "raw"
NOTES_DIR = ROOT / "notes"
INDEX_PATH = ROOT / "index.html"
CSS_REL_IN_NOTE = "../style.css"

# ========================================

INVALID_FILENAME_CHARS = r'<>:"/\\|?*\n\r\t'
INVALID_RE = re.compile(rf"[{re.escape(INVALID_FILENAME_CHARS)}]")


@dataclass(frozen=True)
class Note:
    title: str
    date: str
    body_paragraphs: list[str]
    html_filename: str
    href: str


def sanitize_filename_component(s: str) -> str:
    s = s.strip()
    s = INVALID_RE.sub("", s)
    s = re.sub(r"\s+", "-", s)
    s = s.strip(" .")
    return s or "untitled"


def parse_txt(txt_path: Path) -> Note:
    raw = txt_path.read_text(encoding="utf-8").strip("\ufeff")
    lines = raw.splitlines()

    if len(lines) < 2:
        raise ValueError("至少需要标题行 + 日期行")

    title = lines[0].strip()
    date_str = lines[1].strip()

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        raise ValueError(f"日期格式错误，应为 YYYY-MM-DD：{date_str}")

    body_lines = lines[2:]
    paragraphs = [ln.strip() for ln in body_lines if ln.strip()]

    slug = sanitize_filename_component(title)
    html_filename = f"{date_str}-{slug}.html"
    href = f"./notes/{html_filename}"

    return Note(
        title=title,
        date=date_str,
        body_paragraphs=paragraphs,
        html_filename=html_filename,
        href=href,
    )


def render_note_html(note: Note) -> str:
    paras = []
    if note.body_paragraphs:
        for p in note.body_paragraphs:
            paras.append(
                f"      <p>\n        {escape(p)}\n      </p>\n"
            )
    else:
        paras.append("      <p>（正文为空）</p>\n")

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(note.title)}</title>
  <link rel="stylesheet" href="{CSS_REL_IN_NOTE}" />
</head>
<body>
  <main class="page">

    <header class="topbar">
      <a href="../index.html">← 返回手稿集</a>
    </header>

    <article class="prose">
      <h1>{escape(note.title)}</h1>
      <p class="meta">{escape(note.date)}</p>

{''.join(paras).rstrip()}
    </article>

    <footer class="footer">
      <p>© 绿色恐龙</p>
    </footer>

  </main>
</body>
</html>
"""


def extract_recent_updates_ul(index_html: str):
    card = re.search(
        r"<section class=\"card\">.*?<h2>\s*最近更新\s*</h2>(.*?)</section>",
        index_html,
        re.S,
    )
    if not card:
        raise RuntimeError("找不到「最近更新」区块")

    card_block = card.group(0)

    ul = re.search(
        r"(<ul class=\"list\">\s*)(.*?)(\s*</ul>)",
        card_block,
        re.S,
    )
    if not ul:
        raise RuntimeError("找不到 <ul class=\"list\">")

    ul_open, ul_inner, ul_close = ul.groups()

    start = index_html.find(card_block)
    end = start + len(card_block)

    before = index_html[:start]
    after = index_html[end:]

    ul_start = card_block.find(ul_open)
    ul_end = ul_start + len(ul_open) + len(ul_inner) + len(ul_close)

    before_ul = before + card_block[:ul_start] + ul_open
    after_ul = ul_close + card_block[ul_end:] + after

    return before_ul, ul_inner, after_ul


def index_has_href(index_html: str, href: str) -> bool:
    h = href.replace("\\", "/")
    alt = h.replace("./", ".\\").replace("/", "\\")
    return h in index_html or alt in index_html


def build_li(note: Note) -> str:
    return (
        "        <li>\n"
        f"          <a href=\"{note.href}\">{note.date}｜{escape(note.title)}</a>\n"
        "          <span class=\"tag\">随笔</span>\n"
        "        </li>\n\n"
    )


def main():
    RAW_DIR.mkdir(exist_ok=True)
    NOTES_DIR.mkdir(exist_ok=True)

    txt_files = sorted(RAW_DIR.glob("*.txt"))
    if not txt_files:
        print("[info] raw/ 中没有 txt 文件")
        return

    index_html = INDEX_PATH.read_text(encoding="utf-8")

    new_notes = []

    for txt in txt_files:
        try:
            note = parse_txt(txt)
        except Exception as e:
            print(f"[skip] {txt.name} → {e}")
            continue

        out_path = NOTES_DIR / note.html_filename
        if out_path.exists():
            continue

        out_path.write_text(render_note_html(note), encoding="utf-8")
        new_notes.append(note)
        print(f"[ok] 生成 notes/{note.html_filename}")

    if not new_notes:
        print("[info] 没有新文章生成")
        return

    before_ul, ul_inner, after_ul = extract_recent_updates_ul(index_html)

    to_insert = [n for n in new_notes if not index_has_href(index_html, n.href)]
    to_insert.sort(key=lambda n: n.date, reverse=True)

    if to_insert:
        new_block = "".join(build_li(n) for n in to_insert)
        INDEX_PATH.write_text(
            before_ul + new_block + ul_inner + after_ul,
            encoding="utf-8",
        )
        print(f"[ok] index.html 插入 {len(to_insert)} 条链接")
    else:
        print("[info] index.html 已包含所有链接")


if __name__ == "__main__":
    main()
