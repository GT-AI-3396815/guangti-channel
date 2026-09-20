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
# 内联进 HTML 的用压缩版 logo_inline.jpg（256px，约18KB）；
# og:image / 社交分享仍指向高清原图 logo.jpg，两者兼顾体积与分享质量。
logo_path = f"{workdir}/logo.jpg"
logo_inline_path = f"{workdir}/logo_inline.jpg"
_inline_src = logo_inline_path if os.path.exists(logo_inline_path) else logo_path
logo_base64 = ""
if os.path.exists(_inline_src):
    with open(_inline_src, "rb") as f:
        logo_data = f.read()
    logo_base64 = f"data:image/jpeg;base64,{base64.b64encode(logo_data).decode()}"
    print(
        f"[OK] Logo embedded ({os.path.basename(_inline_src)}): "
        f"{len(logo_data)} bytes -> {len(logo_base64)} chars"
    )
else:
    print(f"[WARN] logo not found at {_inline_src}")
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
# 频道简称：用于频道页顶部切换条（完整名太长，手机上放不下）
channel_short = [
    "新闻", "AI", "商业", "选题", "UFO", "星际",
    "文明", "史前", "典籍", "养生", "疗愈", "显化",
]

# ============================================================
# 步骤1：读取干净源文件（非自身输出，避免循环依赖）
# ============================================================
with open(f"{workdir}/光体频道_source.html", "r", encoding="utf-8") as f:
    home_content = f.read()

# 首页导航日期与更新日志：一律以「内容日期」为准（各频道 hero-date 的众数），
# 而不是构建日期——这样万一某天没有产出新内容，站点会如实显示真实日期，不谎报今天已更新。
import datetime as _dt
_date_dot = _dt.date.today().strftime("%Y.%m.%d")

_channel_files_cache = {}
_dates_pool = []
for _ch in channels:
    with open(f"{workdir}/{_ch}.html", "r", encoding="utf-8") as _f:
        _cached = _f.read()
    _channel_files_cache[_ch] = _cached
    _dm = re.search(r'class="hero-date"[^>]*>\s*(\d{4})\s*/\s*(\d{2})\s*/\s*(\d{2})', _cached)
    if _dm:
        _dates_pool.append(f"{_dm.group(1)}.{_dm.group(2)}.{_dm.group(3)}")
if _dates_pool:
    _cnt = {}
    for _d in _dates_pool:
        _cnt[_d] = _cnt.get(_d, 0) + 1
    _content_date = max(_cnt.items(), key=lambda kv: kv[1])[0]
else:
    _content_date = _date_dot
print(f"[OK] Content date detected: {_content_date} (build day {_date_dot}, {len(_dates_pool)} channels)")

home_content = re.sub(
    r'<span class="nav-date">[^<]*</span>',
    f'<span class="nav-date">{_content_date}</span>',
    home_content,
)
print(f"[OK] Home nav-date set to {_content_date}")

# 首页源里可能残留硬编码的高清 logo base64（1080px，约110KB）；
# 统一替换为压缩版内联图，避免单文件体积膨胀（幂等）。
if logo_base64:
    home_content, _n_logo = re.subn(
        r'data:image/jpeg;base64,[A-Za-z0-9+/=]+', lambda m: logo_base64, home_content
    )
    if _n_logo:
        print(f"[OK] Home hardcoded logo base64 -> compressed inline ({_n_logo} place(s))")

# 更新日志：把「内容日期」记入列表顶部并回写源文件，让它逐日累积成真正的历史归档
# （只在出现更新的日期时才写入，且保留最近14条；幂等）
_log_m = re.search(r'(<ul class="log-list" id="log-list">)(.*?)(</ul>)', home_content, re.S)
if _log_m:
    _log_head, _log_inner, _log_tail = _log_m.group(1), _log_m.group(2), _log_m.group(3)
    _existing = re.findall(r'<span class="log-date">([^<]*)</span>', _log_inner)
    _newest = max(_existing) if _existing else ""
    if _content_date not in _existing and _content_date > _newest and _content_date <= _date_dot:
        _lis = re.findall(r"<li>.*?</li>", _log_inner, re.S)
        _new_li = (
            f'<li><span class="log-date">{_content_date}</span>'
            f'<span class="log-note">12个频道每日整编更新，研判分析与要点速览同步刷新</span></li>'
        )
        _rebuilt = _log_head + "\n      " + _new_li + "".join(
            "\n      " + li for li in _lis[:13]
        ) + "\n    " + _log_tail
        home_content = home_content[:_log_m.start()] + _rebuilt + home_content[_log_m.end():]

        # 回写源文件（否则更新日志每次构建都会重置，形不成归档）
        _src_path = f"{workdir}/光体频道_source.html"
        with open(_src_path, "r", encoding="utf-8") as _f:
            _src_text = _f.read()
        if _log_head + _log_inner + _log_tail in _src_text:
            _src_text = _src_text.replace(_log_head + _log_inner + _log_tail, _rebuilt, 1)
            with open(_src_path, "w", encoding="utf-8") as _f:
                _f.write(_src_text)
            print(f"[OK] Update log: {_content_date} prepended & persisted (archive grows)")
        else:
            print(f"[WARN] Update log: {_content_date} prepended in memory only")
    else:
        print(f"[INFO] Update log unchanged (content date {_content_date}, {len(_existing)} entries)")
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
    content = _channel_files_cache.get(ch)
    if content is None:
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

    # --- 内容归一化 + 语义修正（每日重写易复现，故在构建层兜底） ---
    # a) 折叠重复的信源前缀："信源：信源：" → "信源："（ch06 曾一次出现 12 处）
    _dup_n = len(re.findall(r"(信源|来源|出处)：\s*\1：", body_html))
    if _dup_n:
        body_html = re.sub(r"(信源|来源|出处)：\s*\1：", r"\1：", body_html)
        content = re.sub(r"(信源|来源|出处)：\s*\1：", r"\1：", content)
        print(f"[NORMALIZE] {ch}: 折叠重复信源前缀 {_dup_n} 处")

    # b) 标题层级：栏目用 .section-label 代替 h2 时会形成 h1→h3 跳跃（读屏/SEO 不友好）。
    #    整页无 h2 但存在 h3 卡片标题时，在容器顶部补一个视觉隐藏的 h2。
    if "<h3" in body_html and "<h2" not in body_html:
        _lb = re.search(r'class="section-label-text"[^>]*>(.*?)</span>', body_html, re.S)
        # 源文件里的 label 已做过 HTML 转义，这里只去标签、不再二次转义
        _label = re.sub(r"<[^>]+>", "", _lb.group(1)).strip() if _lb else ""
        _h2_text = _label or channel_names[i]
        body_html = body_html.replace(
            '<div class="container">',
            f'<div class="container">\n<h2 class="sr-only">{_h2_text}</h2>',
            1,
        )
        print(f"[A11Y] {ch}: 补视觉隐藏 h2「{_label or channel_names[i]}」修正标题层级")

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

    # --- 频道切换条（12个频道横向芯片，当前频道高亮；移动端可横向滑动）---
    _chip_items = []
    for _j, _c in enumerate(channels):
        _chip_cls = "ch-chip active" if _c == ch else "ch-chip"
        _chip_items.append(
            f'<a class="{_chip_cls}" href="#{_c}" data-target="{_c}" '
            f"onclick=\"showChannel('{_c}');return false;\">"
            f'<span class="ch-chip-num">{_j + 1:02d}</span>{channel_short[_j]}</a>'
        )
    channel_switch = (
        '<div class="channel-switch" role="navigation" aria-label="频道切换">'
        + "".join(_chip_items)
        + "</div>"
    )

    # --- 阅读信息条：本频道条目数 / 预计阅读时长 / 内容日期（与该频道 hero 保持一致）---
    _card_ct = len(re.findall(r'class="[^"]*news-card', body_html))
    _plain = re.sub(r"<[^>]+>", "", body_html)
    _chars = len(re.sub(r"\s+", "", _plain))
    _readmin = max(1, round(_chars / 400))
    _ch_dm = re.search(r'class="hero-date"[^>]*>\s*(\d{4})\s*/\s*(\d{2})\s*/\s*(\d{2})', content)
    _ch_date = (
        f"{_ch_dm.group(1)}.{_ch_dm.group(2)}.{_ch_dm.group(3)}" if _ch_dm else _content_date
    )
    channel_info = (
        '<div class="channel-page-info">'
        f"<span>本频道 {_card_ct} 条内容</span>"
        '<span class="cpi-dot">·</span>'
        f"<span>约 {_readmin} 分钟读完</span>"
        '<span class="cpi-dot">·</span>'
        f"<span>内容日期 {_ch_date}</span>"
        "</div>"
    )

    # --- 上一频道 / 下一频道（首尾循环）---
    _pi = (i - 1) % len(channels)
    _ni = (i + 1) % len(channels)
    channel_pager = (
        '<div class="channel-pager">'
        f'<a class="pager-btn prev" href="#{channels[_pi]}" '
        f"onclick=\"showChannel('{channels[_pi]}');return false;\">"
        f'<span class="pager-dir">← 上一频道</span>'
        f'<span class="pager-name">{channel_names[_pi]}</span></a>'
        f'<a class="pager-btn next" href="#{channels[_ni]}" '
        f"onclick=\"showChannel('{channels[_ni]}');return false;\">"
        f'<span class="pager-dir">下一频道 →</span>'
        f'<span class="pager-name">{channel_names[_ni]}</span></a>'
        "</div>"
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
        f'    <button class="channel-page-copy" type="button" onclick="copyPageLink()" '
        f'title="复制本页链接" aria-label="复制本页链接">\n'
        f'      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">\n'
        f'        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>\n'
        f'        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>\n'
        f"      </svg>\n"
        f"    </button>\n"
        f"    {channel_switch}\n"
        f"  </div>\n"
        f'  <div class="channel-page-content">\n'
        f"{channel_info}\n"
        f"{body_html}\n"
        f"  </div>\n"
        f"{channel_pager}\n"
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
# 步骤2.6：容器结构守卫（防"半页裸奔"事故）
# 每个频道正文的板块都必须在 <div class="container"> 内部，container 必须在 <footer> 之前闭合。
# 事故复盘：ch01 曾多出一个 </div> 提前关闭 container，使「全球经济」及之后 6 个板块
# 全部落在 container 之外 → 所有 `.container ...` 内容样式失效，线上第 2 屏开始变成
# 无边框、无徽章、通栏长行的"纯文字"页面。div 总数平衡，所以旧的平衡检查发现不了。
# ============================================================
_struct_errors = []
for _ch_name in channels:
    with open(f"{workdir}/{_ch_name}.html", "r", encoding="utf-8") as _f:
        _c = _f.read()
    _b = _c[_c.find("<body"):] if "<body" in _c else _c
    _cm = re.search(r'<div class="container">', _b)
    if not _cm:
        _struct_errors.append(f"{_ch_name}: 找不到 <div class=\"container\">")
        continue
    _d, _closed, _start = 0, None, _cm.start()
    for _mm in re.finditer(r"<div\b[^>]*>|</div>", _b[_start:]):
        if _mm.group(0).startswith("</"):
            _d -= 1
            if _d == 0:
                _closed = _start + _mm.end()
                break
        else:
            _d += 1
    if _closed is None:
        _struct_errors.append(f"{_ch_name}: <div class=\"container\"> 未闭合")
        continue
    _foot = _b.find("<footer")
    if _foot != -1 and _closed > _foot:
        _struct_errors.append(
            f"{_ch_name}: container 闭合位置({_closed})晚于 <footer>({_foot})，footer 被包进容器"
        )
    _secs = [
        (mm.start(), mm.group(1))
        for mm in re.finditer(r'<section class="section" id="([^"]+)"', _b)
    ]
    _outside = [n for (p, n) in _secs if p > _closed]
    if _outside:
        _struct_errors.append(
            f"{_ch_name}: 板块落在 container 之外 → 样式全丢: {', '.join(_outside)}"
        )
    _bal = len(re.findall(r"<div\b", _b)) - _b.count("</div>")
    if _bal != 0:
        _struct_errors.append(f"{_ch_name}: div 不平衡 diff={_bal}")
if _struct_errors:
    raise SystemExit(
        "[STRUCT] 频道容器结构错误，拒绝构建（否则线上会出现半页无样式）:\n  - "
        + "\n  - ".join(_struct_errors)
    )
print(
    f"[STRUCT-GUARD] {len(channels)} channels: container 包裹全部板块 / 闭合于 footer 之前 / div 平衡 = OK"
)

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

/* === 频道切换条（频道页顶部，横向可滑动） === */
.channel-page-header {
  flex-wrap: wrap;
}

.channel-switch {
  flex-basis: 100%;
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 10px 0 2px;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
}

.channel-switch::-webkit-scrollbar {
  display: none;
}

.ch-chip {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: 999px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1;
  text-decoration: none;
  white-space: nowrap;
  transition: all 0.25s;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}

.ch-chip:hover {
  border-color: var(--gold);
  color: var(--gold-bright);
}

.ch-chip.active {
  background: var(--gold-faint);
  border-color: var(--gold);
  color: var(--gold-bright);
  font-weight: 600;
}

.ch-chip-num {
  font-family: 'Noto Serif SC', serif;
  font-size: 11px;
  opacity: 0.65;
  letter-spacing: 1px;
}

/* === 频道页阅读信息条 === */
.channel-page-info {
  max-width: 1080px;
  margin: 0 auto 18px;
  padding: 0 24px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.cpi-dot {
  opacity: 0.45;
}

/* === 上一频道 / 下一频道 === */
.channel-pager {
  max-width: 1080px;
  margin: 8px auto 0;
  padding: 24px;
  display: flex;
  gap: 14px;
  justify-content: space-between;
  border-top: 1px solid var(--border-subtle);
}

.pager-btn {
  flex: 1 1 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px 18px;
  border-radius: 12px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-card);
  text-decoration: none;
  transition: all 0.3s;
  -webkit-tap-highlight-color: transparent;
}

.pager-btn:hover {
  border-color: var(--gold);
  background: var(--gold-faint);
  transform: translateY(-2px);
}

.pager-btn.next {
  text-align: right;
  align-items: flex-end;
}

.pager-dir {
  font-size: 12px;
  color: var(--gold);
  letter-spacing: 1px;
}

.pager-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

/* === 频道页复制链接按钮 === */
.channel-page-copy {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--gold);
  cursor: pointer;
  transition: all 0.25s;
  -webkit-tap-highlight-color: transparent;
}

.channel-page-copy:hover {
  background: var(--gold-faint);
  border-color: var(--gold);
}

/* === 阅读进度条 === */
.read-progress {
  position: fixed;
  top: 0;
  left: 0;
  height: 3px;
  width: 0;
  background: linear-gradient(90deg, var(--gold), var(--gold-bright));
  z-index: 3000;
  transition: width 0.08s linear;
  pointer-events: none;
}

/* === 右下角悬浮按钮（回到顶部 / 复制链接） === */
.fab-stack {
  position: fixed;
  right: 20px;
  bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 2500;
  pointer-events: none;
}

.fab {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-subtle);
  background: var(--bg-deep);
  color: var(--gold);
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
  opacity: 0;
  pointer-events: none;
  transform: translateY(10px);
  transition: opacity 0.3s, transform 0.3s, background 0.25s;
  -webkit-tap-highlight-color: transparent;
}

.fab.show,
.fab.always {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0);
}

.fab:hover {
  background: var(--gold-faint);
  border-color: var(--gold);
}

/* === 轻提示 toast === */
.site-toast {
  position: fixed;
  left: 50%;
  bottom: 92px;
  transform: translateX(-50%) translateY(12px);
  padding: 11px 22px;
  border-radius: 999px;
  background: var(--bg-deep);
  border: 1px solid var(--gold);
  color: var(--gold-bright);
  font-size: 13px;
  letter-spacing: 1px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s, transform 0.3s;
  z-index: 3200;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
}

.site-toast.show {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

/* === 搜索结果增强 === */
.search-results .sr-count {
  padding: 10px 16px 8px;
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 1px;
  border-bottom: 1px solid var(--border-subtle);
}

.search-results mark {
  background: var(--gold-faint);
  color: var(--gold-bright);
  border-radius: 3px;
  padding: 0 2px;
}

.search-result-item.active {
  background: var(--gold-faint);
}

.search-result-item.hit-flash {
  animation: hitFlash 2.2s ease-out;
}

@keyframes hitFlash {
  0% { box-shadow: 0 0 0 2px var(--gold); }
  100% { box-shadow: 0 0 0 2px transparent; }
}

/* === 搜索框快捷键提示 === */
.search-hint {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 11px;
  color: var(--text-muted);
  border: 1px solid var(--border-subtle);
  border-radius: 5px;
  padding: 2px 6px;
  pointer-events: none;
}

/* === 打印样式（存 PDF / 打印收藏） === */
@media print {
  .nav,
  .channel-page-header,
  .channel-pager,
  .fab-stack,
  .read-progress,
  .starfield,
  .ambient,
  .search-box,
  .site-toast,
  .channel-card .channel-status {
    display: none !important;
  }
  body,
  #home-section,
  .channel-page,
  .channel-page-content {
    background: #fff !important;
    color: #000 !important;
  }
  .channel-page:not(.active) {
    display: none !important;
  }
  a {
    color: #000 !important;
    text-decoration: none;
  }
}

@media (max-width: 768px) {
  .channel-page-info {
    padding: 0 16px;
    margin-bottom: 12px;
  }
  .channel-pager {
    flex-direction: column;
    padding: 20px 16px;
  }
  .pager-btn.next {
    text-align: left;
    align-items: flex-start;
  }
  .fab-stack {
    right: 14px;
    bottom: 18px;
  }
  .fab {
    width: 40px;
    height: 40px;
    font-size: 16px;
  }
  .channel-switch {
    gap: 6px;
  }
  .ch-chip {
    padding: 7px 12px;
    font-size: 12px;
  }
}
"""

# ============================================================
# 排版可读性覆盖层（全局，最后加载；只改"读起来舒不舒服"，不动页面骨架）
# 解决的问题：
#  1) .news-head 原本 justify-content:space-between，编号与标题被拉到两端，
#     中间留下一大片空白（卡片第一眼像坏了）
#  2) 正文 14px/1.8 偏小偏挤，一条新闻三段（摘要/关键细节/深度解析）连成一整面字墙
#  3) 行宽不受限，宽屏下一行 90+ 字，眼睛会跑行
#  4) 外部 webfont 失败时中文标题没有衬线回退
# ============================================================
typo_css = """
/* === TYPO / READABILITY（全局排版优化，最后加载） === */

/* 1) 卡片头部：编号与标题紧贴同一基线，消除中间巨洞 */
.container .news-head,
.container .card-head,
.container .card-header,
.container .topic-header {
  justify-content: flex-start;
  align-items: baseline;
  gap: 14px;
}
.container .news-head .news-num,
.container .card-head .card-num {
  min-width: auto;
  line-height: 1.2;
}
.container .news-headline,
.container .card-title,
.container .news-title,
.container .topic-title-main,
.container .topic-title-alt {
  flex: 1 1 auto;
  min-width: 0;
  text-align: left;
  margin-bottom: 0;
}

/* 2) 正文：15px / 1.95 行高 / 中文两端对齐 / 合理行宽（约 60 字/行） */
.container .news-summary,
.container .news-detail,
.container .news-analysis,
.container .news-body,
.container .card-body,
.container .desc,
.container .analysis,
.container .advice,
.container .secondary,
.container .topic-titles,
.container .topic-img-suggest,
.container .top3-reason,
.container .level-desc,
.container .modern,
.container .yili,
.container .shicao,
.container .judgment,
.container p,
.container li {
  font-size: 15px;
  line-height: 1.95;
  text-align: justify;
  text-justify: inter-ideograph;
  overflow-wrap: break-word;
  word-break: break-word;
}
.container .news-summary,
.container .news-detail,
.container .news-analysis,
.container .news-body,
.container .card-body {
  max-width: 64em;
}

/* 3) 三段式层级：标签独立成行，一眼看清结构 */
.container .news-detail > strong:first-child,
.container .news-analysis > strong:first-child,
.container .trend-box > strong:first-child {
  display: block;
  font-family: 'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', 'SimSun', serif;
  font-size: 12px;
  letter-spacing: 2px;
  color: var(--gold);
  margin-bottom: 8px;
  font-weight: 600;
}

/* 4) 呼吸感：卡片留白与段落节奏（桌面） */
.container .news-card,
.container .card,
.container .news-item,
.container .topic-card,
.container .yangsheng-card {
  padding: 30px 30px 26px;
}
.container .news-head {
  margin-bottom: 14px;
}
.container .news-summary {
  margin: 0 0 16px;
}
.container .news-detail {
  margin: 16px 0;
}
.container .news-analysis {
  margin: 16px 0 18px;
}
.container .news-source {
  font-size: 12px;
  padding-top: 12px;
  margin-top: 14px;
}
.container .top-row {
  margin-bottom: 16px;
}
.container .news-tags {
  margin-bottom: 14px;
}
.container .section-title {
  font-size: 26px;
}
.container .section-subtitle {
  font-size: 13.5px;
}

/* 5) 中文衬线/黑体回退：webfont 挂了也不塌 */
.hero-title,
.section-title,
.news-headline,
.news-title,
.card-title,
.topic-title-main,
.topic-title-alt,
.footer-brand,
.nav-brand-text,
.channel-page-title,
.judgment .key {
  font-family: 'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', 'SimSun', Georgia, serif;
}
body,
.hero-sub,
.footer-en {
  font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', 'Hiragino Sans GB', sans-serif;
}

/* 6) 窄屏收口气（媒体查询放在覆盖层内部，避免桌面留白规则在小屏反噬） */
@media (max-width: 768px) {
  .container .news-card,
  .container .card,
  .container .news-item,
  .container .topic-card,
  .container .yangsheng-card {
    padding: 18px 16px;
  }
  .container .news-summary,
  .container .news-detail,
  .container .news-analysis,
  .container .judgment,
  .container p,
  .container li {
    font-size: 14.5px;
    line-height: 1.9;
  }
  .container .section-title {
    font-size: 21px;
  }
  /* 窄屏：导航区/页脚的文字链太矮（19-20px）不好点，撑到 32px 触摸高度 */
  .nav-meta {
    gap: 10px;
  }
  .nav-meta a,
  .nav-meta span,
  .footer-links a {
    display: inline-flex;
    align-items: center;
    min-height: 32px;
    padding: 0 4px;
  }
  /* 窄屏下限：英文副标题 ≥11.5px，LIVE 徽章 ≥11px，避免 10px 小字看不清 */
  .en,
  .nav-brand-text .en,
  .section-title .en {
    font-size: 11.5px;
  }
  .channel-status.live,
  .channel-status {
    font-size: 11px;
  }
}

/* 7) 无障碍：视觉隐藏但供读屏/搜索引擎读取（用于补齐标题层级） */
.sr-only {
  position: absolute !important;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
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

# 站内搜索：跨12个频道过滤卡片，点击结果跳转并精确定位到那一张卡片
spa_js += """
<script>
// === 站内搜索（带索引缓存 / 计数 / 关键词高亮 / 键盘操作） ===
var __srIndex = null;
var __srActive = -1;

function __srBuildIndex() {
  if (__srIndex) return __srIndex;
  var cards = document.querySelectorAll('.channel-page .news-card');
  var out = [];
  for (var i = 0; i < cards.length; i++) {
    var card = cards[i];
    var page = card.closest ? card.closest('.channel-page') : null;
    if (!page) continue;
    // 用 textContent 而非 innerText：隐藏频道内的 innerText 取不到文本（重要 bug 修复）
    var txt = (card.textContent || '').replace(/\\s+/g, ' ').trim();
    if (!txt) continue;
    var hl = card.querySelector('.news-headline,.item-title,.top3-title');
    var nameEl = page.querySelector('.channel-page-title');
    card.setAttribute('data-si', String(i));
    out.push({
      i: i,
      ch: page.getAttribute('data-channel'),
      name: nameEl ? nameEl.textContent.trim() : page.getAttribute('data-channel'),
      title: hl ? hl.textContent.trim() : txt.slice(0, 60),
      txt: txt
    });
  }
  __srIndex = out;
  return out;
}

function __srEsc(s) {
  return String(s).replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
}

function __srMark(s, q) {
  try {
    return String(s).replace(new RegExp('(' + __srEsc(q) + ')', 'gi'), '<mark>$1</mark>');
  } catch (e) { return s; }
}

function siteSearch(q) {
  var box = document.getElementById('search-results');
  if (!box) return;
  q = (q || '').trim();
  __srActive = -1;
  if (!q) { box.style.display = 'none'; box.innerHTML = ''; return; }
  var idx = __srBuildIndex();
  var ql = q.toLowerCase();
  var hits = [];
  var totalHit = 0;
  for (var i = 0; i < idx.length; i++) {
    var pos = idx[i].txt.toLowerCase().indexOf(ql);
    if (pos < 0) continue;
    totalHit++;
    if (hits.length < 30) hits.push({ item: idx[i], pos: pos });
  }
  var html = '';
  if (!totalHit) {
    html = '<div class="search-empty">未找到与「' + q + '」相关的内容，换个关键词试试</div>';
  } else {
    html += '<div class="sr-count">共 ' + totalHit + ' 条结果'
          + (totalHit > hits.length ? '，显示前 ' + hits.length + ' 条（加长关键词可缩小范围）' : '')
          + ' · ↑↓ 选择，Enter 打开</div>';
    for (var j = 0; j < hits.length; j++) {
      var it = hits[j].item;
      var snip = it.txt.slice(Math.max(0, hits[j].pos - 18), hits[j].pos + 58);
      html += '<div class="search-result-item" data-si="' + it.i + '" data-ch="' + it.ch + '">'
           +  '<div class="sr-channel">' + it.name + '</div>'
           +  '<div class="sr-title">' + __srMark(it.title, q) + '</div>'
           +  '<div class="sr-snip">…' + __srMark(snip, q) + '…</div></div>';
    }
  }
  box.innerHTML = html;
  box.style.display = 'block';
}

// 跳转到搜索命中的那张卡片，并高亮闪一下，方便用户立刻看到
function __srJump(ch, si) {
  var box = document.getElementById('search-results');
  if (box) { box.style.display = 'none'; }
  showChannel(ch);
  setTimeout(function () {
    var card = document.querySelector('.channel-page [data-si="' + si + '"]');
    if (!card) return;
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    card.classList.add('hit-flash');
    setTimeout(function () { card.classList.remove('hit-flash'); }, 2400);
  }, 360);
}

// 鼠标点击结果
document.addEventListener('click', function (e) {
  var box = document.getElementById('search-results');
  if (!box) return;
  var item = e.target.closest ? e.target.closest('.search-result-item') : null;
  if (item) {
    __srJump(item.getAttribute('data-ch'), item.getAttribute('data-si'));
  } else if (!e.target.closest || !e.target.closest('#search-box')) {
    box.style.display = 'none';
  }
});

// 键盘操作：Esc 关闭清空 / ↑↓ 选择 / Enter 打开
document.addEventListener('keydown', function (e) {
  var input = document.getElementById('site-search');
  var box = document.getElementById('search-results');
  var home = document.getElementById('home-section');

  // “/” 快捷键聚焦搜索（在频道页会先回到首页）
  if (e.key === '/' && document.activeElement !== input) {
    var tag = (document.activeElement && document.activeElement.tagName) || '';
    if (tag !== 'INPUT' && tag !== 'TEXTAREA') {
      e.preventDefault();
      if (home && home.classList.contains('hidden')) {
        showHome();
        setTimeout(function () { if (input) input.focus(); }, 320);
      } else if (input) {
        input.focus();
      }
      return;
    }
  }

  if (!box || box.style.display === 'none') return;

  if (e.key === 'Escape') {
    box.style.display = 'none';
    if (input) { input.value = ''; input.blur(); }
    return;
  }

  var items = box.querySelectorAll('.search-result-item');
  if (!items.length) return;

  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    e.preventDefault();
    __srActive = e.key === 'ArrowDown'
      ? (__srActive + 1) % items.length
      : (__srActive - 1 + items.length) % items.length;
    for (var i = 0; i < items.length; i++) items[i].classList.toggle('active', i === __srActive);
    items[__srActive].scrollIntoView({ block: 'nearest' });
    return;
  }

  if (e.key === 'Enter') {
    e.preventDefault();
    var pick = items[__srActive >= 0 ? __srActive : 0];
    __srJump(pick.getAttribute('data-ch'), pick.getAttribute('data-si'));
  }
});
</script>
"""

# 阅读辅助：进度条 / 回到顶部 / 复制链接 / 轻提示
spa_js += """
<script>
// === 轻提示 ===
function siteToast(msg) {
  var t = document.getElementById('site-toast');
  if (!t) {
    t = document.createElement('div');
    t.id = 'site-toast';
    t.className = 'site-toast';
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t.__timer);
  t.__timer = setTimeout(function () { t.classList.remove('show'); }, 1900);
}

// === 复制本页链接 ===
function copyPageLink() {
  var url = location.href;
  var done = function () { siteToast('链接已复制，可直接分享'); };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(url).then(done, function () { __copyFallback(url, done); });
  } else {
    __copyFallback(url, done);
  }
}

function __copyFallback(text, done) {
  try {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.top = '-1000px';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    done();
  } catch (e) {
    siteToast('复制失败，请手动复制地址栏链接');
  }
}

// === 阅读进度条 + 回到顶部按钮 ===
(function () {
  var bar = document.createElement('div');
  bar.className = 'read-progress';
  document.body.appendChild(bar);

  var stack = document.createElement('div');
  stack.className = 'fab-stack';
  stack.innerHTML =
    '<button class="fab fab-copy always" type="button" title="复制本页链接" aria-label="复制本页链接">🔗</button>' +
    '<button class="fab fab-top" type="button" title="回到顶部" aria-label="回到顶部">↑</button>';
  document.body.appendChild(stack);

  var topBtn = stack.querySelector('.fab-top');
  var copyBtn = stack.querySelector('.fab-copy');
  topBtn.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
  copyBtn.addEventListener('click', copyPageLink);

  function onScroll() {
    var doc = document.documentElement;
    var max = (doc.scrollHeight - window.innerHeight);
    var pct = max > 0 ? Math.min(100, (window.scrollY / max) * 100) : 0;
    bar.style.width = pct + '%';
    // 复制链接按钮常驻（任何位置都可能想分享）；仅回到顶部随滚动出现
    topBtn.classList.toggle('show', window.scrollY > 420);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  onScroll();
})();

// === 搜索框快捷键提示（仅桌面端显示） ===
document.addEventListener('DOMContentLoaded', function () {
  var box = document.getElementById('search-box');
  if (box && !box.querySelector('.search-hint')) {
    var hint = document.createElement('span');
    hint.className = 'search-hint';
    hint.textContent = '按 / 搜索';
    box.appendChild(hint);
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
<meta property="og:locale" content="zh_CN">
<meta property="og:title" content="{SITE_NAME} · {SITE_NAME_EN}">
<meta property="og:description" content="{SITE_DESC}">
<meta property="og:url" content="{SITE_URL}">
<meta property="og:image" content="{SITE_URL}og-cover.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{SITE_NAME} · {SITE_NAME_EN}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{SITE_NAME} · {SITE_NAME_EN}">
<meta name="twitter:description" content="{SITE_DESC}">
<meta name="twitter:image" content="{SITE_URL}og-cover.jpg">
<meta name="twitter:image:alt" content="{SITE_NAME} · {SITE_NAME_EN}">
<meta name="theme-color" content="#0f1525">
<link rel="canonical" href="{SITE_URL}">
<link rel="manifest" href="site.webmanifest">
<link rel="apple-touch-icon" sizes="180x180" href="{SITE_URL}apple-touch-icon.png">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME} · 每日更新" href="rss.xml">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"WebSite","name":"{SITE_NAME}","alternateName":"{SITE_NAME_EN}","url":"{SITE_URL}","description":"{SITE_DESC}","inLanguage":"zh-CN","publisher":{{"@type":"Organization","name":"{SITE_NAME}"}}}}
</script>
'''
head_html = head_html.replace("</head>", seo_html + "</head>")
print("[OK] SEO meta injected (description/og/twitter/canonical/JSON-LD + RSS alternate)")

# 注入favicon（用logo，避免favicon.ico 404）
if logo_base64 and "</head>" in head_html:
    favicon_link = f'<link rel="icon" type="image/jpeg" href="{logo_base64}">\n'
    head_html = head_html.replace("</head>", favicon_link + "</head>")

# 在 </style> 前插入额外CSS和SPA CSS（typo_css 放最后，同级覆盖优先）
if "</style>" in head_html:
    head_html = head_html.replace(
        "</style>", f"{merged_extra_css}\n{spa_css}\n{typo_css}\n</style>"
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

# === 字体：不再用渲染阻塞的 @import ===
# @import 位于整张内联样式表的第一行，字体 CDN（fonts.loli.net）慢/被墙时会阻塞
# 其后所有规则的解析与应用 → 页面在字体返回前是一张"裸奔"的白底文档。
# 改为 <head> 里的非阻塞 <link>（media=print + onload 切换），失败也只是回落到系统字体。
FONT_HREF = (
    # 只保留 CSS 里真正用到的字重（Noto Sans SC 200 全站 0 处引用；Cormorant 300 / JetBrains 300 亦未使用）
    # 中文子集字体文件多，每减一个字重即可少一批 woff2 请求，弱网首屏更省。
    "https://fonts.loli.net/css2?family=Noto+Serif+SC:wght@300;400;600;700;900"
    "&family=Noto+Sans+SC:wght@300;400;500;700"
    "&family=Cormorant+Garamond:ital,wght@0,400;1,400"
    "&family=JetBrains+Mono:wght@400&display=swap"
)
_n_import = len(re.findall(r"@import\s+url\(", final_html))
final_html = re.sub(r"@import\s+url\([^)]*\)\s*;?", "", final_html)
font_links = (
    '<link rel="preconnect" href="https://fonts.loli.net" crossorigin>\n'
    f'<link rel="stylesheet" href="{FONT_HREF}" media="print" onload="this.media=\'all\'">\n'
    f'<noscript><link rel="stylesheet" href="{FONT_HREF}"></noscript>\n'
)
if "</head>" in final_html:
    final_html = final_html.replace("</head>", font_links + "</head>", 1)
print(
    f"[OK] Font loading de-blocked: removed {_n_import} blocking @import, "
    f"injected non-blocking <link> (+system font fallback)"
)

# === 外链安全：所有 target="_blank" 一律补 noopener noreferrer ===
def _harden_links(m):
    tag = m.group(0)
    if 'target="_blank"' not in tag:
        return tag
    if "rel=" in tag:
        def _merge(mm):
            vals = set(mm.group(1).split()) | {"noopener", "noreferrer"}
            return 'rel="' + " ".join(sorted(vals)) + '"'
        return re.sub(r'rel="([^"]*)"', _merge, tag)
    return re.sub(r"\s*/?>$", "", tag).rstrip() + ' rel="noopener noreferrer">'

_before_unsafe = len(re.findall(r'<a\b[^>]*target="_blank"(?![^>]*noopener)[^>]*>', final_html))
final_html = re.sub(r"<a\b[^>]*>", _harden_links, final_html, flags=re.I)
print(f"[OK] External link hardening: {_before_unsafe} link(s) got rel=noopener noreferrer")

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
print(f"[CHECK] channel switcher chips: {final_html.count('class=\"ch-chip')} (expect >= 144)")
print(f"[CHECK] channel pager: {final_html.count('channel-pager')} (expect >= 12)")
print(f"[CHECK] back-to-top/progress css: {final_html.count('read-progress')} (expect >= 1)")
print(f"[CHECK] search count/highlight: {final_html.count('sr-count')} (expect >= 1)")
print(f"[CHECK] RSS alternate link: {final_html.count('application/rss+xml')} (expect 1)")
print(f"[CHECK] channel-page-info: {final_html.count('channel-page-info')} (expect >= 12)")
print(f"[CHECK] blocking @import: {final_html.count('@import url(')} (expect 0)")
print(f"[CHECK] font link present: {final_html.count('fonts.loli.net')} (expect >= 2)")
print(f"[CHECK] typo layer: {final_html.count('TYPO / READABILITY')} (expect 1)")
print(f"[CHECK] news-head flex fix: {final_html.count('align-items: baseline')} (expect >= 1)")

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
# 内容日期 -> RFC822（RSS 阅读器靠 pubDate 排序/显示；缺失会显示为"未知日期"）
try:
    _cd = _dt.datetime.strptime(_content_date, "%Y.%m.%d").replace(
        hour=9, minute=0, second=0,
        tzinfo=_dt.timezone(_dt.timedelta(hours=8)),
    )
except Exception:
    _cd = _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=8)))
_rss_pubdate = _cd.strftime("%a, %d %b %Y %H:%M:%S +0800")

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
      <title>{_html.escape(channel_names[_i])}（{_content_date.replace(".", "-")}）</title>
      <link>{SITE_URL}#ch{_ch[-2:]}</link>
      <guid isPermaLink="false">{SITE_URL}#ch{_ch[-2:]}-{_content_date}</guid>
      <pubDate>{_rss_pubdate}</pubDate>
      <description>{_html.escape(_summary)}</description>
    </item>"""
    )

_rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{SITE_NAME} · {SITE_NAME_EN}</title>
    <link>{SITE_URL}</link>
    <atom:link href="{SITE_URL}rss.xml" rel="self" type="application/rss+xml"/>
    <description>{SITE_DESC}</description>
    <language>zh-CN</language>
    <ttl>60</ttl>
    <generator>guangti-channel build_spa.py</generator>
    <lastBuildDate>{_dt.datetime.now(_dt.timezone(_dt.timedelta(hours=8))).strftime("%a, %d %b %Y %H:%M:%S +0800")}</lastBuildDate>
{chr(10).join(_rss_items)}
  </channel>
</rss>
"""
rss_path = os.path.join(os.path.dirname(workdir), "rss.xml")
with open(rss_path, "w", encoding="utf-8") as f:
    f.write(_rss)
print(f"[OK] RSS generated: {rss_path} ({len(_rss_items)} items)")

# === 站点周边文件：robots / sitemap / 404 / manifest（随构建刷新，保证 SEO 与"添加到主屏"可用） ===
_root = os.path.dirname(workdir)
_iso = _content_date.replace(".", "-")

robots_txt = (
    "User-agent: *\n"
    "Allow: /\n"
    f"Sitemap: {SITE_URL}sitemap.xml\n"
)
with open(os.path.join(_root, "robots.txt"), "w", encoding="utf-8") as f:
    f.write(robots_txt)

_sitemap_urls = [f"  <url><loc>{SITE_URL}</loc><lastmod>{_iso}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>"]
for _i, _ch in enumerate(channels):
    _sitemap_urls.append(
        f"  <url><loc>{SITE_URL}#ch{_ch[-2:]}</loc><lastmod>{_iso}</lastmod>"
        f"<changefreq>daily</changefreq><priority>0.8</priority></url>"
    )
sitemap_xml = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "\n".join(_sitemap_urls) + "\n</urlset>\n"
)
with open(os.path.join(_root, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write(sitemap_xml)

manifest_json = f'''{{
  "name": "{SITE_NAME} · {SITE_NAME_EN}",
  "short_name": "{SITE_NAME}",
  "description": "{SITE_DESC}",
  "lang": "zh-CN",
  "start_url": "./index.html",
  "scope": "./",
  "display": "standalone",
  "background_color": "#0f1525",
  "theme_color": "#0f1525",
  "icons": [
    {{"src": "apple-touch-icon.png", "sizes": "180x180", "type": "image/png", "purpose": "any"}},
    {{"src": "source/logo_inline.jpg", "sizes": "256x256", "type": "image/jpeg", "purpose": "any"}}
  ]
}}
'''
with open(os.path.join(_root, "site.webmanifest"), "w", encoding="utf-8") as f:
    f.write(manifest_json)

# 404 页：GitHub Pages 会自动使用根目录 404.html。做成轻量独立页，
# 不整份复制 SPA（否则仓库白多 ~690KB），只提供回首页入口与今日内容指引。
_404_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>页面未找到 · {SITE_NAME}</title>
<style>
  :root{{color-scheme:dark}}
  body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
    background:radial-gradient(1200px 600px at 50% -10%,#1b2540 0%,#0f1525 55%,#080c16 100%);
    color:#e8ecf5;font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
    text-align:center;padding:32px}}
  .wrap{{max-width:520px}}
  .code{{font-size:64px;font-weight:700;letter-spacing:6px;color:#c9a96e;
    font-family:"Cormorant Garamond",Georgia,serif;line-height:1}}
  h1{{font-size:20px;margin:16px 0 10px;font-weight:600}}
  p{{color:#9aa6bd;font-size:14px;line-height:1.9;margin:0 0 26px}}
  a.btn{{display:inline-block;padding:12px 26px;border-radius:999px;text-decoration:none;
    background:linear-gradient(135deg,#c9a96e,#e0c791);color:#1a1206;font-weight:600;font-size:14px}}
  .links{{margin-top:18px;font-size:13px}}
  .links a{{color:#c9a96e;text-decoration:none;margin:0 10px}}
</style>
</head>
<body>
<div class="wrap">
  <div class="code">404</div>
  <h1>这个页面不存在</h1>
  <p>链接可能已失效，或地址输错了。<br>本站是单页应用，所有内容都在首页与 12 个频道里。</p>
  <a class="btn" href="./index.html">← 回到首页</a>
  <div class="links">
    <a href="./index.html#ch01">全球新闻</a>·
    <a href="./index.html#ch02">AI 热点</a>·
    <a href="./index.html#ch05">UFO 热点</a>·
    <a href="./rss.xml">RSS 订阅</a>
  </div>
</div>
</body>
</html>
'''
with open(os.path.join(_root, "404.html"), "w", encoding="utf-8") as f:
    f.write(_404_html)

print("[OK] Site files: robots.txt / sitemap.xml / site.webmanifest / 404.html")

# === 信源可点击率体检（事实类频道应逐条可核查；此处只报告不阻断） ===
_fact_ch = channels[:5] + channels[6:]  # ch01-ch05, ch07-ch12（ch06 已是全链接）
for _ch in _fact_ch:
    with open(f"{workdir}/{_ch}.html", "r", encoding="utf-8") as _f:
        _c = _f.read()
    _srcs = re.findall(r'class="news-source">(.*?)</div>', _c, re.S)
    _wl = sum(1 for _x in _srcs if "href=" in _x)
    print(f"[SOURCE-CHECK] {_ch}: 信源行 {len(_srcs)} 条，含可点击链接 {_wl} 条"
          f"（{100 * _wl / max(1, len(_srcs)):.0f}%）")

print(f"\n[DONE] SPA版已生成: {output_path}")
print(f"  大小: {len(final_html.encode('utf-8')) / 1024:.1f} KB")
print(f"  栏目: 12个频道页面包裹在channel-page容器中")
print(f"  交互: 点击频道卡片 -> showChannel() -> 显示对应栏目")
print(f"  返回: 点击返回首页 -> showHome() -> 回到主页")
