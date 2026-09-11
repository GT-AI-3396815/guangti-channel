#!/usr/bin/env python3
"""
光体频道单文件SPA版：13个文件合并为1个自包含HTML
- 打开显示首页（12个频道卡片）
- 点击频道卡片"切换页面"显示该频道内容
- 栏目内容默认隐藏，互不干扰
- 每个栏目有返回首页按钮
- 零外部依赖
"""

import re, os, base64

workdir = os.path.dirname(os.path.abspath(__file__))

# === 读取logo并转为base64 ===
logo_path = f"{workdir}/logo.jpg"
logo_base64 = ""
if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        logo_data = f.read()
    logo_base64 = f"data:image/jpeg;base64,{base64.b64encode(logo_data).decode()}"
    print(f"[OK] Logo embedded: {len(logo_data)} bytes -> {len(logo_base64)} chars")
else:
    print(f"[WARN] logo.jpg not found at {logo_path}")
channels = ["ch%02d" % i for i in range(1, 13)]
channel_names = [
    "每日全球新闻",
    "每日AI热点",
    "每日商业趋势",
    "每日自媒体选题推荐",
    "每日UFO热点",
    "每日星际文明解读",
    "每日人类文明解读",
    "每日史前文明解读",
    "每日高维智慧典籍精读",
    "每日养生指南",
    "每日身心调频疗愈指南",
    "每日显化能量实操",
]

# ============================================================
# 步骤1：读取干净源文件（非自身输出，避免循环依赖）
# ============================================================
with open(f"{workdir}/光体频道_source.html", "r", encoding="utf-8") as f:
    home_content = f.read()

# 首页导航日期自动更新为构建当天（部署任务缺失时保证日期不滞后）
import datetime as _dt
_date_dot = _dt.date.today().strftime("%Y.%m.%d")
home_content = re.sub(
    r'<span class="nav-date">[^<]*</span>',
    f'<span class="nav-date">{_date_dot}</span>',
    home_content,
)
print(f"[OK] Home nav-date set to {_date_dot}")

# 更新日志：确保当天日期在列表顶部（去重，保留最近14条，构成历史归档）
_log_tag = _dt.date.today().strftime("%Y.%m.%d")
_log_m = re.search(r'(<ul class="log-list" id="log-list">)(.*?)(</ul>)', home_content, re.S)
if _log_m:
    _inner = _log_m.group(2)
    if f'<span class="log-date">{_log_tag}</span>' not in _inner:
        _lis = re.findall(r"<li>.*?</li>", _inner, re.S)
        _new_li = f'<li><span class="log-date">{_log_tag}</span><span class="log-note">12个频道每日整编更新，研判分析与要点速览同步刷新</span></li>'
        _inner = "\n      " + _new_li + "".join("\n      " + li for li in _lis[:13])
        home_content = (
            home_content[:_log_m.start()]
            + _log_m.group(1)
            + _inner
            + "\n    "
            + _log_m.group(3)
            + home_content[_log_m.end():]
        )
        print(f"[OK] Update log: prepended {_log_tag}")
else:
    print("[WARN] log-list not found in home source (update log skipped)")

# 自动更新首页日期（替换硬编码日期为当天日期）
# 日期更新由部署任务处理，构建脚本不做日期替换以保持版面稳定

# 提取首页 <style>
home_style_match = re.search(r"<style[^>]*>(.*?)</style>", home_content, re.S | re.I)
home_style = home_style_match.group(1) if home_style_match else ""

# ============================================================
# 步骤2：提取频道内容
# ============================================================
merged_extra_css = ""
channel_pages = []

for i, ch in enumerate(channels):
    fname = f"{workdir}/{ch}.html"
    with open(fname, "r", encoding="utf-8") as f:
        content = f.read()

    # --- 自动更新栏目页面日期（注释掉：日期由部署任务处理）---
    # content = re.sub(
    #     r'<span class="nav-date">[^<]*</span>',
    #     f'<span class="nav-date">{date_dot}</span>',
    #     content,
    # )
    # content = re.sub(
    #     r'<div class="hero-date">[^<]*</div>',
    #     f'<div class="hero-date">{date_slash}</div>',
    #     content,
    # )
    # content = re.sub(r"(\d{4}年\d{1,2}月\d{1,2}日)", date_cn, content)
    # content = re.sub(r"星期[一二三四五六日]", weekday_cn, content)
    # --- END 日期更新 ---

    # --- 提取频道独特CSS ---
    style_match = re.search(r"<style[^>]*>(.*?)</style>", content, re.S | re.I)
    ch_style = style_match.group(1) if style_match else ""
    rules = re.findall(r"([.#][^{,\s][^{}]*?)\s*\{([^}]*)\}", ch_style, re.S)
    for selector, declarations in rules:
        sel_key = selector.strip().split(",")[0].strip()
        # 排除通用选择器
        if sel_key not in ["*", "html", "body"] and len(sel_key) > 1:
            # 声明压成单行：保证"一条规则=一行"，行去重才安全
            decl_single = re.sub(r"\s+", " ", declarations.strip())
            merged_extra_css += f"{selector.strip()} {{ {decl_single} }}\n"


    # --- 提取body内容 ---
    body_match = re.search(r"<body[^>]*>(.*?)</body>", content, re.S | re.I)
    body_html = body_match.group(1).strip() if body_match else ""

    # --- 清理body ---
    # 1. 移除 ambient
    ambient_inline = '<div class="ambient"><div class="orb orb-1"></div><div class="orb orb-2"></div><div class="orb orb-3"></div></div>'
    body_html = body_html.replace(ambient_inline, "")
    body_html = re.sub(r'<div class="orb orb-[123]"\s*></div>\s*', "", body_html)
    body_html = re.sub(r'<div class="ambient">\s*</div>\s*', "", body_html)

    # 2. 移除 starfield
    body_html = re.sub(r'<div\s+class="starfield"[^>]*></div>\s*', "", body_html)

    # 3. 移除导航栏
    body_html = re.sub(
        r'<nav\s+class="nav"[^>]*>.*?</nav>\s*', "", body_html, flags=re.S | re.I
    )

    # 4. 移除 footer
    body_html = re.sub(
        r'<footer\s+class="footer"[^>]*>.*?</footer>\s*',
        "",
        body_html,
        flags=re.S | re.I,
    )

    # 5. 移除 float-back
    body_html = re.sub(
        r'<a\s+[^>]*class="float-back"[^>]*>.*?</a>\s*',
        "",
        body_html,
        flags=re.S | re.I,
    )

    # 6. 移除 script（只移除频道页面自身的星空动画脚本）
    # 注意：不能移除所有script，否则SPA导航脚本也会被误删
    # 频道页面的script都是星空动画脚本（位于body末尾），特征：
    # 1. 包含 document.getElementById('starfield') 或 starfield
    # 2. 不包含 showChannel / showHome
    # 我们只移除匹配这些特征的 script 标签
    def should_remove_script(match):
        script_content = match.group(0)
        # 如果script内容包含SPA函数名，保留它
        if "showChannel" in script_content or "showHome" in script_content:
            return script_content  # 保留
        # 如果script内容包含 starfield，这是频道页面的星空动画，移除
        if "starfield" in script_content or "sf=" in script_content:
            return ""  # 移除
        # 其他未知script，默认保留（安全起见）
        return script_content  # 保留

    body_html = re.sub(
        r"<script[^>]*>.*?</script>\s*",
        should_remove_script,
        body_html,
        flags=re.S | re.I,
    )

    # 7. 移除ch02统计概览面板
    if ch == "ch02":
        # 移除包含"统计概览"的标题标签（h1-h6）
        body_html = re.sub(
            r"<h[1-6][^>]*>\s*统计概览\s*</h[1-6]>\s*",
            "",
            body_html,
            flags=re.S | re.I,
        )
        # 移除标题div嵌套结构
        body_html = re.sub(
            r"<div[^>]*>\s*<div[^>]*>\s*统计概览\s*</div>.*?</div>\s*",
            "",
            body_html,
            flags=re.S | re.I,
        )
        # 移除统计网格和卡片
        body_html = re.sub(
            r'<div\s+class="stats-grid"[^>]*>.*?</div>\s*',
            "",
            body_html,
            flags=re.S | re.I,
        )
        body_html = re.sub(
            r'<div\s+class="stat-card"[^>]*>.*?</div>\s*',
            "",
            body_html,
            flags=re.S | re.I,
        )
        body_html = re.sub(
            r'<div\s+class="hero-stats"[^>]*>.*?</div>\s*',
            "",
            body_html,
            flags=re.S | re.I,
        )

    # 8. 移除所有频道中的图片元素（保留source中的logo，保留UI图标svg）
    body_html = re.sub(r"<img[^>]*>\s*", "", body_html, flags=re.S | re.I)

    # 9. 修复返回首页链接：光体频道.html -> #home
    body_html = body_html.replace(
        'href="光体频道.html"', 'href="#home" onclick="showHome(); return false;"'
    )

    # --- 包装为频道页面容器 ---
    page_html = (
        f'<div class="channel-page" id="page-{ch}" data-channel="{ch}">\n'
        f'  <div class="channel-page-header">\n'
        f'    <div class="channel-page-back" onclick="showHome()">\n'
        f'      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">\n'
        f'        <path d="M19 12H5M12 19l-7-7 7-7"/>\n'
        f"      </svg>\n"
        f"      <span>返回首页</span>\n"
        f"    </div>\n"
        f'    <div class="channel-page-title">{channel_names[i]}</div>\n'
        f"  </div>\n"
        f'  <div class="channel-page-content">\n'
        f"{body_html}\n"
        f"  </div>\n"
        f"</div>"
    )

    channel_pages.append(page_html)

# ============================================================
# 步骤2.5：CSS 统一性守卫 + 去重
# 同一选择器在不同频道有不同定义（剥离 @media 后比对）= 格式漂移 → 构建失败；
# 完全相同的规则只保留一份，防止体积膨胀和覆盖顺序问题。
# ============================================================
import collections as _collections

def _strip_media(css_text):
    # 递归剥离 @media/@supports 外壳，只留规则本体
    prev = None
    while prev != css_text:
        prev = css_text
        css_text = re.sub(r"@(media|supports)[^{]*\{([\s\S]*?)\}\s*\}",
                          lambda m: m.group(2), css_text)
    return css_text

# 每个频道： selector -> 定义体集合；同一选择器的定义集合必须跨频道一致
_per_ch = {}
for _ch_name in channels:
    with open(f"{workdir}/{_ch_name}.html", "r", encoding="utf-8") as _f:
        _c = _f.read()
    _sm = re.search(r"<style[^>]*>(.*?)</style>", _c, re.S | re.I)
    if not _sm:
        continue
    _defs = _collections.defaultdict(set)
    for _sel, _body in re.findall(r"([.#][^{,\s][^{}]*?)\s*\{([^}]*)\}", _strip_media(_sm.group(1)), re.S):
        _key = re.sub(r"\s+", " ", _sel.strip())
        _defs[_key].add(re.sub(r"\s+", "", _body))
    _per_ch[_ch_name] = _defs

_ref_ch = None
for _key in sorted({k for d in _per_ch.values() for k in d}):
    _ref = None
    for _ch_name in channels:
        if _ch_name not in _per_ch or _key not in _per_ch[_ch_name]:
            continue
        _bodies = frozenset(_per_ch[_ch_name][_key])
        if _ref is None:
            _ref = (_ch_name, _bodies)
        elif _bodies != _ref[1]:
            _diff = list(_bodies ^ _ref[1])[0]
            raise SystemExit(
                f"[CSS漂移] 选择器 {_key!r} 在 {_ch_name} 与 {_ref[0]} 定义不一致，拒绝构建。\n"
                f"  差异: {_diff[:150]}\n"
                f"  请按 STYLE_GUIDE.md 统一后重试。"
            )
print(f"[CSS-GUARD] {len(_per_ch)} channels x {len(_per_ch[channels[0]])} selectors, drift=0")

# 去重：完全相同的规则行只保留一份
_deduped_css = ""
_seen_rules = set()
for _rule_line in merged_extra_css.splitlines():
    if _rule_line not in _seen_rules:
        _seen_rules.add(_rule_line)
        _deduped_css += _rule_line + "\n"
merged_extra_css = _deduped_css
print(f"[CSS-GUARD] drift=0, rules deduped -> {len(_seen_rules)} unique rules, {len(merged_extra_css)/1024:.1f} KB")

# ============================================================
# 步骤3：构建SPA版HTML
# ============================================================

# SPA专用CSS
spa_css = """
/* === SPA LAYOUT === */
.channel-page {
  display: none;
  min-height: 100vh;
  background: var(--bg-void);
}

.channel-page.active {
  display: block;
}

.channel-page-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg-deep);
  border-bottom: 1px solid var(--border-subtle);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  backdrop-filter: blur(12px);
}

.channel-page-back {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--gold);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s;
  white-space: nowrap;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
  user-select: none;
  -webkit-user-select: none;
}

.channel-page-back:hover {
  background: var(--gold-faint);
}

.channel-page-back svg {
  width: 20px;
  height: 20px;
}

.channel-page-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 18px;
  font-weight: 600;
  color: var(--gold-bright);
  letter-spacing: 2px;
  flex: 1;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.channel-page-content {
  padding: 24px 0 60px;
}

/* 强制覆盖：导航栏全宽布局 */
.nav-inner {
  max-width: none !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
  width: 100% !important;
}

/* 强制覆盖：日期推到最右边 */
.nav-meta {
  margin-left: auto !important;
}

/* 主页容器 */
#home-section {
  display: block;
}

#home-section.hidden {
  display: none;
}

/* 频道切换动画 */
.channel-page.active {
  animation: pageIn 0.4s ease-out;
}

@keyframes pageIn {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .channel-page-header {
    padding: 12px 16px;
  }
  .channel-page-title {
    font-size: 15px;
  }
  .channel-page-back {
    padding: 6px 10px;
    font-size: 13px;
  }
  .channel-page-back svg {
    width: 18px;
    height: 18px;
  }
  .channel-page-content {
    padding: 16px 0 40px;
  }
}
"""

# SPA专用JS
spa_js = """
<script>
// === SPA CHANNEL NAVIGATION ===

// 显示指定频道
function showChannel(chId) {
  if (!chId) return;
  var targetPage = document.getElementById('page-' + chId);
  if (!targetPage) return; // 不存在的频道直接忽略，避免白屏

  // 幂等保护：已在目标频道时只同步hash，避免hashchange循环
  if (targetPage.classList.contains('active')) {
    try {
      if (location.hash !== '#' + chId) location.hash = '#' + chId;
    } catch(e) {}
    return;
  }

  // 隐藏主页
  var homeSection = document.getElementById('home-section');
  if (homeSection) homeSection.classList.add('hidden');
  
  // 隐藏所有频道页面
  var allPages = document.querySelectorAll('.channel-page');
  for (var i = 0; i < allPages.length; i++) {
    allPages[i].classList.remove('active');
  }
  
  // 显示目标频道
  targetPage.classList.add('active');
  window.scrollTo(0, 0);
  
  // 更新URL hash
  try {
    location.hash = '#' + chId;
  } catch(e) {}
}

// 返回首页
function showHome() {
  var homeSection = document.getElementById('home-section');

  // 幂等保护：已在首页时只同步hash，避免hashchange循环
  if (homeSection && !homeSection.classList.contains('hidden')) {
    try {
      if (location.hash !== '#home' && location.hash !== '') location.hash = '#home';
    } catch(e) {}
    return;
  }

  // 隐藏所有频道页面
  var allPages = document.querySelectorAll('.channel-page');
  for (var i = 0; i < allPages.length; i++) {
    allPages[i].classList.remove('active');
  }
  
  // 显示主页
  if (homeSection) homeSection.classList.remove('hidden');
  
  window.scrollTo(0, 0);
  
  try {
    location.hash = '#home';
  } catch(e) {}
}

// 监听hash变化：支持浏览器返回键、深度链接、无效hash兜底回首页
window.addEventListener('hashchange', function() {
  var h = location.hash.replace('#', '');
  if (h && h !== 'home' && document.getElementById('page-' + h)) {
    showChannel(h);
  } else {
    showHome();
  }
});

// 页面加载时添加LIVE徽章 + 检查URL hash
document.addEventListener('DOMContentLoaded', function() {
  // 为每个卡片添加LIVE徽章
  var cards = document.getElementsByClassName('channel-card');
  for (var i = 0; i < cards.length; i++) {
    var card = cards[i];
    card.style.cursor = 'pointer';
    var badge = document.createElement('span');
    badge.className = 'channel-status live';
    badge.textContent = 'LIVE';
    card.appendChild(badge);
  }
  
  // 检查URL hash
  var hash = window.location.hash.replace('#', '');
  if (hash && hash !== 'home') {
    showChannel(hash);
  }
});
</script>
"""

# 站内搜索：跨12个频道过滤卡片，点击结果跳转并定位
spa_js += """
<script>
function siteSearch(q) {
  var box = document.getElementById('search-results');
  if (!box) return;
  q = (q || '').trim();
  if (!q) { box.style.display = 'none'; box.innerHTML = ''; return; }
  var cards = document.querySelectorAll('.channel-page .news-card');
  var out = [];
  var ql = q.toLowerCase();
  for (var i = 0; i < cards.length && out.length < 30; i++) {
    var card = cards[i];
    var page = card.closest('.channel-page');
    if (!page) continue;
    var txt = card.innerText.replace(/\\s+/g, ' ');
    var idx = txt.toLowerCase().indexOf(ql);
    if (idx < 0) continue;
    var chId = page.getAttribute('data-channel');
    var nameEl = page.querySelector('.channel-page-title');
    var name = nameEl ? nameEl.textContent : chId;
    var hl = card.querySelector('.news-headline,.item-title,.top3-title');
    var title = hl ? hl.textContent.trim() : txt.slice(0, 60);
    var snip = txt.slice(Math.max(0, idx - 20), idx + 60);
    out.push({ ch: chId, name: name, title: title, snip: snip });
  }
  var html = '';
  if (!out.length) {
    html = '<div class="search-empty">未找到与「' + q + '」相关的内容，换个关键词试试</div>';
  } else {
    for (var j = 0; j < out.length; j++) {
      html += '<div class="search-result-item" data-ch="' + out[j].ch + '" data-q="' + q + '">'
           +  '<div class="sr-channel">' + out[j].name + '</div>'
           +  '<div class="sr-title">' + out[j].title + '</div>'
           +  '<div class="sr-snip">…' + out[j].snip + '…</div></div>';
    }
  }
  box.innerHTML = html;
  box.style.display = 'block';
}
document.addEventListener('click', function (e) {
  var box = document.getElementById('search-results');
  if (!box) return;
  var item = e.target.closest ? e.target.closest('.search-result-item') : null;
  if (item) {
    var ch = item.getAttribute('data-ch');
    var q = item.getAttribute('data-q') || '';
    box.style.display = 'none';
    showChannel(ch);
    setTimeout(function () {
      var page = document.getElementById('page-' + ch);
      if (!page) return;
      var cards = page.querySelectorAll('.news-card');
      for (var i = 0; i < cards.length; i++) {
        if (cards[i].innerText.toLowerCase().indexOf(q.toLowerCase()) >= 0) {
          cards[i].scrollIntoView({ behavior: 'smooth', block: 'center' });
          break;
        }
      }
    }, 350);
  } else if (!e.target.closest || !e.target.closest('.search-box')) {
    box.style.display = 'none';
  }
});
</script>
"""

# 提取head
head_match = re.search(r"(<head>.*?</head>)", home_content, re.S | re.I)
head_html = head_match.group(1) if head_match else ""

# === SEO / 社交分享注入（幂等：先清旧再注新） ===
SITE_URL = "https://gt-ai-3396815.github.io/guangti-channel/"
SITE_NAME = "光体•星际频道"
SITE_NAME_EN = "Luminary Interstellar Channel"
SITE_DESC = (
    "光体•星际频道 Luminary Interstellar Channel：每日09:00自动更新的12频道资讯站——"
    "全球新闻、AI热点、商业趋势、自媒体选题推荐、UFO热点、星际文明解读、养生与身心疗愈。"
)
head_html = re.sub(r'<meta name="description"[^>]*>\s*', "", head_html)
head_html = re.sub(r'<meta property="og:[^>]*>\s*', "", head_html)
head_html = re.sub(r'<meta name="twitter:[^>]*>\s*', "", head_html)
head_html = re.sub(r'<link rel="canonical"[^>]*>\s*', "", head_html)
head_html = re.sub(
    r'<script type="application/ld\+json">.*?</script>\s*', "", head_html, flags=re.S
)
seo_html = f'''<meta name="description" content="{SITE_DESC}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{SITE_NAME} · {SITE_NAME_EN}">
<meta property="og:description" content="{SITE_DESC}">
<meta property="og:url" content="{SITE_URL}">
<meta property="og:image" content="{SITE_URL}source/logo.jpg">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{SITE_NAME} · {SITE_NAME_EN}">
<meta name="twitter:description" content="{SITE_DESC}">
<meta name="twitter:image" content="{SITE_URL}source/logo.jpg">
<link rel="canonical" href="{SITE_URL}">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"WebSite","name":"{SITE_NAME}","alternateName":"{SITE_NAME_EN}","url":"{SITE_URL}","description":"{SITE_DESC}","inLanguage":"zh-CN"}}
</script>
'''
head_html = head_html.replace("</head>", seo_html + "</head>")
print("[OK] SEO meta injected (description/og/twitter/canonical/JSON-LD)")

# 注入favicon（用logo，避免favicon.ico 404）
if logo_base64 and "</head>" in head_html:
    favicon_link = f'<link rel="icon" type="image/jpeg" href="{logo_base64}">\n'
    head_html = head_html.replace("</head>", favicon_link + "</head>")

# 在 </style> 前插入额外CSS和SPA CSS
if "</style>" in head_html:
    head_html = head_html.replace(
        "</style>", f"{merged_extra_css}\n{spa_css}\n</style>"
    )

# 提取body
body_match = re.search(r"<body[^>]*>(.*?)</body>", home_content, re.S | re.I)
body_html = body_match.group(1).strip() if body_match else ""

# 修复首页导航品牌链接：光体频道.html -> #home（SPA内跳回首页）
body_html = body_html.replace(
    'href="光体频道.html"', 'href="#home" onclick="showHome(); return false;"'
)

# 移除body内的script
body_html = re.sub(r"<script[^>]*>.*?</script>\s*", "", body_html, flags=re.S | re.I)

# 为每个频道卡片添加内联onclick（最可靠的点击方式，不依赖JS动态绑定）
for ch in channels:
    body_html = body_html.replace(
        'class="channel-card" data-channel="%s"' % ch,
        'class="channel-card" data-channel="%s" onclick="showChannel(\'%s\')"'
        % (ch, ch),
    )

# 包装主页为home-section
# 找到footer位置，在此之前插入频道页面
footer_pos = body_html.rfind('<footer class="footer"')
if footer_pos < 0:
    footer_pos = len(body_html)

home_section_html = body_html[:footer_pos]
footer_html = body_html[footer_pos:]

# 频道页面
all_channel_pages = "\n\n".join(channel_pages)

# 组装最终HTML
final_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
{head_html}
<body>

<div id="home-section">
{home_section_html}
{footer_html}
</div>

{all_channel_pages}

{spa_js}

</body>
</html>"""


final_html = re.sub(
    r'<div class="ambient">\s*(?:<div class="orb orb-[123]"></div>\s*)*</div>\s*',
    "",
    final_html,
)

# 嵌入logo为base64
if logo_base64:
    final_html = final_html.replace('src="logo.jpg"', f'src="{logo_base64}"')
    print(f"[OK] Replaced logo.jpg with base64 in final HTML")

# 验证
print(f"[CHECK] File size: {len(final_html.encode('utf-8')) / 1024:.1f} KB")
total_o = len(re.findall(r"<div\b", final_html, re.I))
total_c = len(re.findall(r"</div>", final_html, re.I))
print(f"[CHECK] Div balance: opens={total_o} closes={total_c} diff={total_o - total_c}")
print(f"[CHECK] channel-page divs: {final_html.count('class="channel-page"')}")
print(f"[CHECK] active class: {final_html.count('class="channel-page active"')}")
print(f"[CHECK] showChannel function: {final_html.count('function showChannel')}")
print(f"[CHECK] showHome function: {final_html.count('function showHome')}")
print(
    f"[CHECK] window.location.href: {final_html.count('window.location.href')} (should be 0)"
)
print(f"[CHECK] scrollIntoView: {final_html.count('scrollIntoView')}")

# 检查是否还有外部链接
ext_links = re.findall(r'href="[^#][^"]*\.html"', final_html)
if ext_links:
    print(f"[WARN] Found external links: {ext_links[:5]}")

# 输出
output_path = f"{workdir}/光体频道.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(final_html)

# 同步输出部署文件 index.html（仓库根目录），避免构建后忘记拷贝
deploy_path = os.path.join(os.path.dirname(workdir), "index.html")
with open(deploy_path, "w", encoding="utf-8") as f:
    f.write(final_html)

# === 生成 rss.xml（每日订阅源，随构建自动刷新） ===
import html as _html

_rss_items = []
for _i, _ch in enumerate(channels):
    with open(f"{workdir}/{_ch}.html", "r", encoding="utf-8") as _f:
        _c = _f.read()
    _hls = re.findall(
        r'class="(?:news-headline|item-title|topic-title-main)"[^>]*>(.*?)</(?:div|h3)>',
        _c,
        re.S,
    )
    _hls = [re.sub(r"<[^>]+>", "", x).strip() for x in _hls]
    _hls = [re.sub(r"\s+", " ", x) for x in _hls if x.strip()][:3]
    _summary = "；".join(_hls) if _hls else channel_names[_i]
    _rss_items.append(
        f"""    <item>
      <title>{_html.escape(channel_names[_i])}（{_date_dot.replace(".", "-")}）</title>
      <link>{SITE_URL}#ch{_ch[-2:]}</link>
      <guid isPermaLink="false">{SITE_URL}#ch{_ch[-2:]}-{_date_dot}</guid>
      <description>{_html.escape(_summary)}</description>
    </item>"""
    )

_rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{SITE_NAME} · {SITE_NAME_EN}</title>
    <link>{SITE_URL}</link>
    <description>{SITE_DESC}</description>
    <language>zh-CN</language>
    <lastBuildDate>{_dt.datetime.now(_dt.timezone(_dt.timedelta(hours=8))).strftime("%a, %d %b %Y %H:%M:%S +0800")}</lastBuildDate>
{chr(10).join(_rss_items)}
  </channel>
</rss>
"""
rss_path = os.path.join(os.path.dirname(workdir), "rss.xml")
with open(rss_path, "w", encoding="utf-8") as f:
    f.write(_rss)
print(f"[OK] RSS generated: {rss_path} ({len(_rss_items)} items)")

print(f"\n[DONE] SPA版已生成: {output_path}")
print(f"  大小: {len(final_html.encode('utf-8')) / 1024:.1f} KB")
print(f"  栏目: 12个频道页面包裹在channel-page容器中")
print(f"  交互: 点击频道卡片 -> showChannel() -> 显示对应栏目")
print(f"  返回: 点击返回首页 -> showHome() -> 回到主页")
