# 维护说明

本仓库用于发布手稿页面。每次在 `raw/` 新增一个 `*.txt` 后，用 `tools` 更新页面即可。

## 新增文章流程

1) 在 `raw/` 新建一个 `*.txt`，内容格式：

- 第 1 行：标题
- 第 2 行：日期（`YYYY-MM-DD`）
- 第 3 行起：正文（每行一个段落，空行会跳过）

2) 生成对应的 `notes/*.html` 并更新首页：

```bash
python tools/generate_notes.py
```

3) 分类（可选）：打开新生成的 `notes/*.html`，在 `<p class="meta">` 中加上标签文字（如“随画/废话/漫画”）。未填写时默认归为“随笔”。

4) 重新生成列表页与最近更新区块：

```bash
python tools/rebuild.py
```

完成后，`index.html`、`all.html`、`archive.html` 会被更新。

## 主题（themes）

主题入口和空主题块可以用脚本新增；主题内的文章列表仍由 `themes.html` 手动维护。

### 把新文章加入已有主题

1) 先确保文章已生成到 `notes/*.html`。
2) 打开 `themes.html`，在目标主题的 `<section class="card" id="...">` 内新增一条 `<li>`，格式与现有条目一致。
备注：`themes.html` 为手动维护，改完直接保存即可；无需运行 `python tools/rebuild.py`（该脚本只更新 `index.html` 的最近更新及 `all.html` / `archive.html`）。

### 新增一个主题

运行：

```bash
python tools/rebuild.py --add-theme "Nonsense"
```

这条命令会自动完成三件事：

1) 在 `themes.html` 顶部的主题导航区（`<div class="quick">`）新增一个 pill：

```html
<a class="pill" href="#Nonsense">Nonsense</a>
```

2) 在 `themes.html` 中新增一个空主题区块，`id` 和 pill 的 `href` 一致：

```html
<section class="card" id="Nonsense">
  <h2>Nonsense</h2>
  <ul class="list">
    <!-- 手动维护 -->
  </ul>
</section>
```

3) 在 `index.html` 首页主题区新增入口，保证首页能看到这个主题：

```html
<a class="block" href="./themes.html#Nonsense">
  <div class="block-title">Nonsense</div>
</a>
```

命令可以重复运行；如果对应入口或区块已经存在，脚本会自动跳过，不会重复插入。

新增主题后，如果要把文章放进这个主题，仍然打开 `themes.html`，在对应 `<section id="Nonsense">` 的 `<ul class="list">` 内手动添加 `<li>`。

## 常见问题

- 日期格式必须是 `YYYY-MM-DD`，否则脚本会提示跳过。
- 已生成过的文章不会重复生成（脚本是幂等的）。
- 想新增分类标签时，先在 `tools/rebuild.py` 的 `KNOWN_TAGS` 中加入新标签，再运行 `python tools/rebuild.py`。
