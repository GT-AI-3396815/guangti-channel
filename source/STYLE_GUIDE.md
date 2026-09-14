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
