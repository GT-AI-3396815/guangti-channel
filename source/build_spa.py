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
            merged_extra_css += f"{selector.strip()} {{ {declarations.strip()} }}\n"

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
  // 隐藏主页
  var homeSection = document.getElementById('home-section');
  if (homeSection) homeSection.classList.add('hidden');
  
  // 隐藏所有频道页面
  var allPages = document.querySelectorAll('.channel-page');
  for (var i = 0; i < allPages.length; i++) {
    allPages[i].classList.remove('active');
  }
  
  // 显示目标频道
  var targetPage = document.getElementById('page-' + chId);
  if (targetPage) {
    targetPage.classList.add('active');
    window.scrollTo(0, 0);
  }
  
  // 更新URL hash
  try {
    location.hash = '#' + chId;
  } catch(e) {}
}

// 返回首页
function showHome() {
  // 隐藏所有频道页面
  var allPages = document.querySelectorAll('.channel-page');
  for (var i = 0; i < allPages.length; i++) {
    allPages[i].classList.remove('active');
  }
  
  // 显示主页
  var homeSection = document.getElementById('home-section');
  if (homeSection) homeSection.classList.remove('hidden');
  
  window.scrollTo(0, 0);
  
  try {
    location.hash = '#home';
  } catch(e) {}
}

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

# 提取head
head_match = re.search(r"(<head>.*?</head>)", home_content, re.S | re.I)
head_html = head_match.group(1) if head_match else ""

# 在 </style> 前插入额外CSS和SPA CSS
if "</style>" in head_html:
    head_html = head_html.replace(
        "</style>", f"{merged_extra_css}\n{spa_css}\n</style>"
    )

# 提取body
body_match = re.search(r"<body[^>]*>(.*?)</body>", home_content, re.S | re.I)
body_html = body_match.group(1).strip() if body_match else ""

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

print(f"\n[DONE] SPA版已生成: {output_path}")
print(f"  大小: {len(final_html.encode('utf-8')) / 1024:.1f} KB")
print(f"  栏目: 12个频道页面包裹在channel-page容器中")
print(f"  交互: 点击频道卡片 -> showChannel() -> 显示对应栏目")
print(f"  返回: 点击返回首页 -> showHome() -> 回到主页")
