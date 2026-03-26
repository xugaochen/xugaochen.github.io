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

主题页由 `themes.html` 手动维护，不受脚本影响。

### 把新文章加入已有主题

1) 先确保文章已生成到 `notes/*.html`。
2) 打开 `themes.html`，在目标主题的 `<section class="card" id="...">` 内新增一条 `<li>`，格式与现有条目一致。
备注：`themes.html` 为手动维护，改完直接保存即可；无需运行 `python tools/rebuild.py`（该脚本只更新 `index.html` 的最近更新及 `all.html` / `archive.html`）。

### 新增一个主题

1) 在 `themes.html` 顶部的主题导航区（`<div class="quick">`）新增一个 pill：

```html
<a class="pill" href="#New Theme">New Theme</a>
```

2) 新增一个主题区块，`id` 需要和 pill 的 `href` 一致：

```html
<section class="card" id="New Theme">
  <h2>New Theme</h2>
  <ul class="list">
    <!-- 手动维护 -->
  </ul>
</section>
```

## 常见问题

- 日期格式必须是 `YYYY-MM-DD`，否则脚本会提示跳过。
- 已生成过的文章不会重复生成（脚本是幂等的）。
- 想新增分类标签时，先在 `tools/rebuild.py` 的 `KNOWN_TAGS` 中加入新标签，再运行 `python tools/rebuild.py`。
