# 光体•星际频道 · 栏目格式统一规范 v1.0

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
2. 运行 `python source/build_spa.py`（自动：CSS 漂移检查 → 去重 → 注入 logo/favicon/SEO → 刷新首页日期与更新日志 → 生成 `source/光体频道.html`、根目录 `index.html` 和 `rss.xml`）
3. 运行 `node test/browser-test.js`（需先起本地服务，38 项断言）
4. 提交推送到 GitHub（GitHub Pages 自动部署）

## 8. 内容性质标注（hero-notice）

探索解读类频道（ch05-ch12）的 hero 区必须有 `.hero-notice` 标注，声明内容性质：
- ch05 UFO：官方披露与科研观测为可核实信息，推想性解读仅为观点
- ch06 星际文明 / ch07 人类文明 / ch08 史前文明：假说与推演，非事实结论/非定论
- ch09 高维典籍：文化解读，不构成科学结论
- ch10 养生 / ch11 身心疗愈：不构成医疗建议，不适请就医
- ch12 显化能量："能量"为隐喻框架，非物理事实

ch01-ch04（事实资讯/方法论）无需标注。样式定义在首页源全局 CSS，频道页不重复定义。

## 9. 站级组件（只在首页源定义，构建时全局生效）

- **站内搜索**：`#search-box`（首页频道网格前），跨12频道过滤 `.news-card`，点击结果跳转定位；JS 在 build_spa.py 的 spa_js 中
- **更新日志**：`#update-log` + `#log-list`，构建时自动把当天日期置顶（去重，保留14条）= 历史归档
- **关于本站**：`#about`，含编辑规范 / 内容分级 / 数据来源 / 免责声明四块
- **RSS**：构建生成根目录 `rss.xml`（12条目随每日构建刷新）；页脚"RSS订阅"指向相对地址 `rss.xml`（本地与线上都可访问）；`<head>` 有 `rel="alternate"` 自动发现

## 10. 卡片外壳统一规则

- 新闻/趋势类条目一律用标准 news-card 解剖（第3条）
- ch04 选题卡：外壳用 `news-card topic-card`、头部用标准 news-head 解剖，`topic-section` 内容区（推荐标题/适合平台/推荐理由/内容角度/开头钩子/简要大纲/文案内容）保留
- ch04 TOP3 榜单：外壳用 `news-card top3-card`
- 禁止 `class="badge tag badge-pN"` 混写——优先级徽章只用 `badge badge-pN`
- 禁止 `item-header/item-num/item-title/item-body` 私有别名（ch08 已归一）


## 11. 频道内导航与阅读辅助（构建时自动注入，勿手改）

构建脚本会为每个频道页自动生成以下结构，**内容更新时不要删除或改写**：

- **频道切换条** `.channel-switch` + `.ch-chip`（12个芯片，当前频道 `.active` 高亮；移动端可横向滑动）——让用户在任意频道一键换台，不必回首页
- **阅读信息条** `.channel-page-info`：`本频道 N 条内容 · 约 X 分钟读完 · 内容日期 YYYY.MM.DD`（N/时长由构建统计，日期取该频道 hero-date）
- **上下频道翻页** `.channel-pager`（首尾循环）
- **返回首页** `.channel-page-back`、**复制本页链接** `.channel-page-copy`
- **全局**：阅读进度条 `.read-progress`、右下悬浮 `.fab-stack`（🔗 常驻复制链接 / ↑ 滚动后出现回到顶部）、轻提示 `.site-toast`、`/` 键聚焦搜索

## 12. 站内搜索规范

- 索引范围：全部 `.channel-page .news-card`（12频道全覆盖，当前 205 条）
- 结果必须显示**真实命中总数**（不是显示上限），超过 30 条时标注"显示前 30 条"
- 命中关键词必须用 `<mark>` 高亮（标题与摘要）
- 键盘：`↑↓` 选择、`Enter` 打开、`Esc` 关闭清空、`/` 聚焦
- 点击结果要**精确定位到那一张卡片**并加 `.hit-flash` 闪示，不能只跳到频道首页

## 13. 日期一致性（重要）

- 首页 `nav-date`、`#log-list` 置顶条目、频道页信息条日期 **一律以内容日期为准**（取各频道 hero-date 的众数），**不得**用构建日期
- 若某天没有产出新内容，站点应如实显示旧日期（宁可显示滞后，也不谎报"今日已更新"）
- 更新日志由构建脚本**回写源文件** `光体频道_source.html`，逐日累积保留14条，构成真实历史归档
- `rss.xml` 的 item 标题与 guid 同样使用内容日期，避免空跑时重复推送

## 14. 体积与性能红线

- 内联图片一律使用压缩版 `logo_inline.jpg`（256px，约18KB）；高清 `logo.jpg`（1080px）只用于 `og:image`
- 单文件体积红线 **≤ 760 KB**（当前约 705 KB）；超过即检查是否有重复内联大图
- 禁止在频道源里硬编码 base64 图片（构建会自动替换，但源文件不应新增）

## 15. 容器结构红线（2026-09-14 事故复盘）

**事故**：ch01 在第一个板块 `.judgment` 之后多出一个 `</div>`，导致 `.container` 提前闭合。因所有内容样式都写成 `.container .news-card` / `.container .news-num` 形式，第二个板块起（economy/conflict/tech/society/climate/summary）整段落在容器之外 → **完全丢失样式**：无卡片边框与背景、编号回落成 16px 正文、正文通栏贴边。由于 div 开闭总数仍然配平，旧有的平衡校验无法发现。

**防御（已内置，勿删）**：
- `build_spa.py` 的 `[STRUCT-GUARD]`：逐频道解析 `<div class="container">` … 配平闭合位置，强制要求
  1. `container` 闭合点必须在 `<footer class="footer">` 之前；
  2. 所有 `<section class="section">` 必须落在 `container` 闭合点**之内**；
  3. 整文件 `<div>`/`</div>` 配平。
  任一不满足 → `raise SystemExit("[STRUCT] 频道容器结构错误，拒绝构建…")`。
- 判断方法：`python -c "import re;h=open('chXX.html',encoding='utf-8').read();print(len(re.findall(r'<div\b',h))-len(re.findall(r'</div>',h)))"` 应为 **0**。

**排版叠加层（typo layer）**：`build_spa.py` 在 `spa_css` 之后追加一层可读性覆盖，源码顺序靠后故优先级更高：
- `.news-head` 改为 `justify-content:flex-start; align-items:baseline; gap:14px`，编号与标题紧贴（旧 `space-between` 会把二者撑到两端、中间留大片空白）；
- `.news-num{min-width:auto}`、`.news-headline{flex:1 1 auto; min-width:0}`；
- 正文 `font-size:15px; line-height:1.95; text-align:justify; text-justify:inter-ideograph`，摘要/解析/正文 `max-width:64em` 防止超宽通栏；
- `.news-detail > strong:first-child` 提升为块级金色小标签；
- 内置 `@media (max-width:768px)` 移动端收敛。

**字体阻塞**：`<style>` 顶部的 `@import url(https://fonts…)` 会阻塞其后**全部** CSS 应用直到字体 CDN 响应/失败（表现为 FOUC）。构建已自动剥离 `@import`，改为 `<link rel="stylesheet" … media="print" onload="this.media='all'">` + `<noscript>` 兜底，并在 typo 层补中文系统字体 fallback。**不要在频道源里重新引入 `@import`。**

**每日更新自检**：构建输出中 `[CHECK] blocking @import: 0`、`font link present >= 2`、`typo layer: 1`、`news-head flex fix >= 1`、`[STRUCT-GUARD] … OK` 必须全部符合预期。

## 16. 站点完备性 / 分享 / 无障碍规范（2026-09-20 增补）

**站点周边文件（全部由 build_spa.py 自动生成，勿手改；部署时必须一并上传）**
| 文件 | 作用 | 生成规则 |
|---|---|---|
| `robots.txt` | 允许全站抓取 + 指向 sitemap | 固定 |
| `sitemap.xml` | 首页 + 12 个 `#chNN`，`lastmod` 取内容日期 | 每日刷新 |
| `site.webmanifest` | 支持"添加到主屏"（standalone） | 固定 |
| `404.html` | 轻量独立错误页（约 1.7KB），**不要整份复制 SPA** | 固定 |
| `og-cover.jpg` | 社交分享大图 1200×630 | 品牌资产，已生成 |
| `apple-touch-icon.png` | iOS 主屏图标 180×180 | 品牌资产，已生成 |

**分享元数据**：`og:image` 指向根目录 `og-cover.jpg`（不要指 `source/logo.jpg`），必须带 `og:image:width/height/alt`；`twitter:card` 用 `summary_large_image`；另需 `og:locale`、`og:site_name`、`theme-color`。

**RSS 规范**：每个 `<item>` 必须有 `<pubDate>`（内容日期 09:00 +0800，**缺失会让阅读器显示"未知日期"**）；`<channel>` 需含 `<atom:link rel="self">`、`<ttl>`、`<generator>`。

**无障碍**：
- 标题层级不得跳跃（h1→h3）。栏目用 `.section-label` 代替 h2 时，构建会自动补一个 `<h2 class="sr-only">`；`.sr-only` 样式在 typo 层。
- 移动端（≤768px）独立链接的触摸高度 ≥32px（`.nav-meta a`、`.footer-links a`）；正文段落内的行内链接豁免（WCAG 2.5.8）。
- 移动端最小字号 ≥11px（`.en` 11.5px、`.channel-status.live` 11px）。
- 所有 `<img>` 必须有 `alt`；图标按钮必须有 `aria-label`。

**内容归一化（构建层兜底，源文件也别写错）**：
- 折叠重复信源前缀：`信源：信源：` → `信源：`（曾出现 12 处）。
- 事实类频道（ch01-ch05）每条卡片"来源"行应给真实机构 + 日期，并**尽量附可点击原文/官方链接**；构建会打印 `[SOURCE-CHECK]` 报告可点击率。**严禁编造 URL**——搜不到就只写机构名。

**审计脚本（都在 `test/`，可重复使用）**
- `audit-static.py` — 占位符/锚点/结构/日期/重复标题/外链清单（纯静态）
- `audit-runtime.cjs` — 深链/复制链接/搜索/无障碍/移动端/性能
- `audit-focus.cjs` — 搜索正确性、复制链接一致性、返回键、字体开销、标题层级、小点击目标
- `verify-fixes.cjs` — 站点文件可达性、manifest、404 页、移动端、字体、深链
- `verify-live.cjs` — 对线上 GitHub Pages 跑完整 12 频道与元数据校验
- `make-assets.py` — 重新生成 `og-cover.jpg` / `apple-touch-icon.png`

**已知取舍**：中文 webfont 走 `fonts.loli.net`（Google Fonts 镜像），CSS 约 1MB（gzip 后 ~30KB）、925 条 @font-face，实际按 unicode-range 只拉取用到的子集（约 35 个 woff2）。已做：非阻塞 `<link media=print onload>` + `<noscript>` 兜底 + 系统字体 fallback + 只声明用到的字重。断网/被墙时自动回落系统字体，不影响可用性。
