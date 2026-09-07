# 光体频道 · 栏目格式统一规范 v1.0

> 所有频道页（ch01-ch12）与每日新增内容必须遵守本规范。
> 构建脚本 `build_spa.py` 内置 CSS 漂移守卫：同一选择器跨频道定义不一致时**拒绝构建**。

## 1. 页面骨架（固定不变）

```
<body>
  ambient(orb×3) + starfield        ← 背景层，构建时自动移除
  nav.nav                            ← 顶栏：logo + 频道名 + 日期
  section.hero                       ← 头图：eyebrow / title / sub / date / desc
  main > 内容板块
  footer.footer
  a.float-back                       ← 构建时自动移除
</body>
```

## 2. 栏目标题（三选一，整页统一）

**A 型（默认，新闻/趋势类）：**
```html
<div class="section-header">
  <span class="section-icon">🌐</span>   <!-- 必须 span，emoji 图标 -->
  <div>
    <h2 class="section-title"><span class="bar"></span>中文标题<span class="en"> · English Title</span></h2>
    <div class="section-subtitle">一句话说明</div>
  </div>
</div>
```

**B 型（清单/精读类）：** `section-label` 眉题 + `h2.section-title`（同上格式）+ `p.section-desc`。
眉题内：`<span class="section-label-text">大写英文眉题</span><span class="section-label-line"></span>`（必须 span）。

**编号变体：** icon 位可换成 `<span class="section-num">01</span>`（必须 span，不能用 div）。

标题硬规则：
- `section-title` 内部必须以 `<span class="bar"></span>` 开头
- 英文副标格式固定：`<span class="en"> · English</span>`（· 前有空格）
- 标题标签一律 `<h2>`（不允许 div.section-title）

## 3. 新闻卡片（标准解剖）

```html
<div class="news-card">
  <div class="news-head">
    <span class="news-num">01</span>
    <div class="news-headline">标题文字</div>
  </div>
  <div class="news-tags"><span class="tag">标签</span><span class="badge badge-p0">P0</span></div>
  <p class="news-summary">一段话摘要</p>
  <div class="news-analysis">研判分析</div>
  <div class="news-source">来源：XXX · 2026年X月X日</div>
</div>
```

- 禁用私有别名类：~~civ-card / civ-number / civ-headline / civ-summary / civ-analysis / civ-tag / civ-source / civ-detail / card-title-row~~（已全部归一到 news-* / .tag）
- 标签芯片用 `.tag`，优先级徽章用 `.badge.badge-pN`（P0 最高）

## 4. 徽章与优先级

| 类 | 用途 |
|----|------|
| `badge badge-p0/p1/p2/p3` | 重要性分级（P0 最高），禁止 ~~tag-pN~~ 写法 |
| `tag` | 内容主题标签 |

## 5. 研判块（每板块必配）

每个板块末尾必须有一个研判块：
```html
<div class="judgment">
  <strong class="key">趋势研判与建议</strong><br/>
  研判正文（三条主线 + 建议关注点）
</div>
```

## 6. 日期与文字

- 日期格式：正文 `2026年9月7日`，hero `2026 / 09 / 07`，导航 `2026.09.07`（构建时自动刷新为当天）
- 中文正文用 Noto Serif SC（全局已配），数字/英文点缀用 Cormorant Garamond
- 禁止出现"等"字省略列表项；每条内容必须有具体来源

## 7. 新增内容流程

1. 编辑对应 `source/chNN.html`（只改 body 内容区，保持骨架）
2. 运行 `python source/build_spa.py`（自动：CSS 漂移检查 → 去重 → 注入 logo/favicon → 刷新首页日期 → 生成 `source/光体频道.html` 和根目录 `index.html`）
3. 运行 `node test/browser-test.js`（需先起本地服务，28 项断言）
4. 提交推送到 GitHub（GitHub Pages 自动部署）
