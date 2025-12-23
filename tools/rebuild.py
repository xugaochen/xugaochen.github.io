# tools/rebuild.py
from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime
from html import unescape

ROOT = Path(__file__).resolve().parents[1]
NOTES_DIR = ROOT / "notes"

INDEX_PATH = ROOT / "index.html"
ALL_PATH = ROOT / "all.html"
ARCHIVE_PATH = ROOT / "archive.html"

RECENT_N = 8  # 首页“最近更新”显示条数

# 你现在/未来允许的标签（可随时加）
KNOWN_TAGS = ["随笔", "废话", "随画", "漫画", "段子", "英语"]

RE_H1 = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
RE_META = re.compile(r'<p[^>]*class="meta"[^>]*>(.*?)</p>', re.I | re.S)
RE_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
RE_TAG = re.compile("(" + "|".join(map(re.escape, KNOWN_TAGS)) + ")")

AUTOGEN_START = "<!-- AUTOGEN_RECENT_START -->"
AUTOGEN_END = "<!-- AUTOGEN_RECENT_END -->"


def strip_html(s: str) -> str:
    """去掉 html 标签，保留纯文本"""
    s = unescape(s)
    s = re.sub(r"<[^>]+>", "", s)
    return s.strip()


def safe_read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_post(fp: Path) -> dict:
    """
    解析 notes/*.html
    - title: <h1>...</h1>，没有则用文件名（去扩展名）
    - date: meta里YYYY-MM-DD，缺失则从文件名开头提取
    - tag: meta里出现的 KNOWN_TAGS 之一，缺失默认“随笔”
    """
    html = safe_read_text(fp)

    # title
    m = RE_H1.search(html)
    title = strip_html(m.group(1)) if m else fp.stem

    # meta
    mm = RE_META.search(html)
    meta_text = strip_html(mm.group(1)) if mm else ""

    # date: meta > filename
    md = RE_DATE.search(meta_text)
    date = md.group(1) if md else None
    if not date:
        mfn = re.match(r"(\d{4}-\d{2}-\d{2})-", fp.name)
        date = mfn.group(1) if mfn else "1970-01-01"

    # tag: meta > default
    mt = RE_TAG.search(meta_text)
    tag = mt.group(1) if mt else "随笔"

    dt = datetime.strptime(date, "%Y-%m-%d")

    return {
        "file": fp.name,
        "href": f'./notes/{fp.name}',
        "title": title,
        "date": date,
        "tag": tag,
        "dt": dt,
    }


def li(post: dict) -> str:
    # 统一输出：YYYY-MM-DD｜标题
    return f'        <li><a href="{post["href"]}">{post["date"]}｜{post["title"]}</a><span class="tag">{post["tag"]}</span></li>'


def build_all_html(posts: list[dict]) -> str:
    # 按 tag 分组：先固定顺序，再补“其他标签”
    preferred = ["随笔", "废话", "随画"]
    groups: dict[str, list[dict]] = {t: [] for t in preferred}
    others: dict[str, list[dict]] = {}

    for p in posts:
        if p["tag"] in groups:
            groups[p["tag"]].append(p)
        else:
            others.setdefault(p["tag"], []).append(p)

    # 组内按日期倒序
    for k in groups:
        groups[k].sort(key=lambda x: x["dt"], reverse=True)
    for k in others:
        others[k].sort(key=lambda x: x["dt"], reverse=True)

    pills = []
    for t in preferred:
        pills.append(f'<a class="pill" href="#{t}">{t}</a>')
    for t in sorted(others.keys()):
        pills.append(f'<a class="pill" href="#{t}">{t}</a>')
    pills_html = "\n        ".join(pills)

    sections = []
    for t in preferred:
        ul = "\n".join(li(p) for p in groups[t])
        sections.append(f"""
    <section class="card" id="{t}">
      <h2>{t}</h2>
      <ul class="list">
{ul}
      </ul>
    </section>
""".rstrip())

    for t in sorted(others.keys()):
        ul = "\n".join(li(p) for p in others[t])
        sections.append(f"""
    <section class="card" id="{t}">
      <h2>{t}</h2>
      <ul class="list">
{ul}
      </ul>
    </section>
""".rstrip())

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>查看全部｜绿色恐龙的手稿集</title>
  <link rel="stylesheet" href="./style.css" />
</head>
<body>
  <main class="page">

    <header class="topbar">
      <a href="./index.html">← 返回首页</a>
      <span style="opacity:.6">｜</span>
      <a href="./archive.html">按年份</a>
    </header>

    <section class="card">
      <div class="card-head">
        <h2>查看全部</h2>
        <div class="card-actions">
          <a class="smalllink" href="./archive.html">按年份 →</a>
        </div>
      </div>

      <p class="desc">按标签分区展示；也可以用浏览器搜索（Ctrl+F）找标题。</p>

      <div class="quick">
        {pills_html}
      </div>
    </section>

{chr(10).join(sections)}

    <footer class="footer">
      <p>© <span id="year"></span> xugaochen</p>
    </footer>

  </main>

  <script>
    document.getElementById("year").textContent = new Date().getFullYear();
  </script>
</body>
</html>
"""


def build_archive_html(posts: list[dict]) -> str:
    years: dict[int, list[dict]] = {}
    for p in posts:
        years.setdefault(p["dt"].year, []).append(p)

    # 年份倒序、组内倒序
    year_list = sorted(years.keys(), reverse=True)
    for y in year_list:
        years[y].sort(key=lambda x: x["dt"], reverse=True)

    pills_html = "\n        ".join([f'<a class="pill" href="#y{y}">{y}</a>' for y in year_list])

    sections = []
    for y in year_list:
        ul = "\n".join(li(p) for p in years[y])
        sections.append(f"""
    <section class="card" id="y{y}">
      <h2>{y}</h2>
      <ul class="list">
{ul}
      </ul>
    </section>
""".rstrip())

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>按年份｜绿色恐龙的手稿集</title>
  <link rel="stylesheet" href="./style.css" />
</head>
<body>
  <main class="page">

    <header class="topbar">
      <a href="./index.html">← 返回首页</a>
      <span style="opacity:.6">｜</span>
      <a href="./all.html">查看全部</a>
    </header>

    <section class="card">
      <h2>按年份</h2>
      <div class="quick">
        {pills_html}
      </div>
    </section>

{chr(10).join(sections)}

    <footer class="footer">
      <p>© <span id="year"></span> xugaochen</p>
    </footer>

  </main>

  <script>
    document.getElementById("year").textContent = new Date().getFullYear();
  </script>
</body>
</html>
"""


def patch_index_recent(index_html: str, recent_posts: list[dict]) -> str:
    if AUTOGEN_START not in index_html or AUTOGEN_END not in index_html:
        raise RuntimeError(
            "index.html 里找不到自动生成标记。\n"
            f"请在最近更新的<ul>里加入：\n{AUTOGEN_START}\n{AUTOGEN_END}"
        )

    recent_block = "\n".join(li(p) for p in recent_posts)
    replacement = f"{AUTOGEN_START}\n{recent_block}\n        {AUTOGEN_END}"

    pattern = re.escape(AUTOGEN_START) + r".*?" + re.escape(AUTOGEN_END)
    return re.sub(pattern, replacement, index_html, flags=re.S)


def main() -> None:
    if not NOTES_DIR.exists():
        raise SystemExit(f"找不到 notes 目录：{NOTES_DIR}")

    posts: list[dict] = []
    for fp in NOTES_DIR.glob("*.html"):
        # notes 目录下只要是 html 就当文章；如果你有特殊文件可在这里排除
        posts.append(parse_post(fp))

    posts.sort(key=lambda x: x["dt"], reverse=True)

    # 生成 all.html / archive.html
    ALL_PATH.write_text(build_all_html(posts), encoding="utf-8")
    ARCHIVE_PATH.write_text(build_archive_html(posts), encoding="utf-8")

    # 更新 index.html 最近更新
    index_html = safe_read_text(INDEX_PATH)
    new_index = patch_index_recent(index_html, posts[:RECENT_N])
    INDEX_PATH.write_text(new_index, encoding="utf-8")

    print("✅ rebuild 完成：index.html(最近更新)、all.html、archive.html 已更新")


if __name__ == "__main__":
    main()
