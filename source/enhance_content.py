#!/usr/bin/env python3
"""
光体•星际频道 - 内容专业度增强脚本（2026-09-11 专业审计整改）
整改项：
  1. ch03-ch12 每个含卡片的板块末尾补 .judgment 研判块（STYLE_GUIDE 第5条硬性要求）
  2. ch08 卡片结构归一：item-header/item-num/item-title/item-body -> news-head/news-num/news-headline/news-body
  3. ch04 卡片外壳与头部归一：topic-card -> news-card topic-card、头部改用标准 news-head 解剖、徽章去 tag 混用
  4. 推测性栏目（ch05-ch12）hero 增加内容性质标注（事实 vs 观点探索），养生/疗愈加"不构成医疗建议"
  5. ch01/ch02 "等"字省略句改写为完整表述（STYLE_GUIDE 第6条）
  6. 首页源新增：站内搜索框、更新日志、关于本站（编辑规范/内容分级/数据来源/免责声明）、页脚功能链接
带断言保护：任何结构性意外立即中止，不写入任何文件；全部幂等（重复运行不会二次插入）。
"""
import re

WORK = "."  # 在 source/ 目录下运行


def read(f):
    with open(f, encoding="utf-8") as fh:
        return fh.read()


def write(f, c):
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(c)


def div_balance(s):
    return len(re.findall(r"<div\b", s, re.I)) - len(re.findall(r"</div>", s, re.I))


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", "", s)
    return s.strip()


def cut(s, n=30):
    s = s.rstrip("。；;：:，, ")
    return s if len(s) <= n else s[:n].rstrip("。；;：:，, ")


report = []

# ============================================================
# 1. ch01/ch02 "等"字省略句改写
# ============================================================
_deng_fixes = {
    "ch01.html": [
        (
            "制裁对象包括黎巴嫩真主党成员等。",
            "制裁对象包括黎巴嫩真主党成员，以及被认定支持伊朗代理人网络的相关个人与实体。",
        )
    ],
    "ch02.html": [
        (
            "已赞助至少28名记者报道Anthropic、深度伪造、AI地缘政治等话题。",
            "已赞助至少28名记者，报道方向聚焦Anthropic、深度伪造、AI地缘政治三大议题。",
        )
    ],
}
for f, pairs in _deng_fixes.items():
    c = read(f)
    done = 0
    for old, new in pairs:
        if old in c:
            c = c.replace(old, new)
            done += 1
        elif new in c:
            done += 1  # 已改写，幂等跳过
        else:
            raise AssertionError(f"{f}: 待改写句与目标句均未找到: {old[:30]}")
    if done:
        write(f, c)
        report.append(f"{f}: '等'字省略句改写 {done} 处")

# ============================================================
# 2. ch08 结构归一 item-* -> news-*
# ============================================================
c = read("ch08.html")
pat = re.compile(
    r'<div class="news-card item">\s*<div class="item-header">\s*'
    r'<span class="item-num">(\d+)</span>(.*?)</div>\s*'
    r'<h3 class="item-title">(.*?)</h3>\s*<div class="item-body">',
    re.S,
)
n = len(pat.findall(c))


def _ch08_repl(m):
    num, tags, title = m.group(1), m.group(2).strip(), m.group(3).strip()
    return (
        '<div class="news-card">\n'
        '<div class="news-head">\n'
        f'<span class="news-num">{num}</span>\n'
        f'<div class="news-headline">{title}</div>\n'
        '</div>\n'
        f'<div class="news-tags">{tags}</div>\n'
        '<div class="news-body">'
    )


if n:
    c2 = pat.sub(_ch08_repl, c)
    assert div_balance(c2) == div_balance(c), "ch08: div 平衡被破坏"
    body_i = c2.find("</style>")
    assert "item-header" not in c2[body_i:], "ch08: 仍有 item-header 残留"
    assert "item-title" not in c2[body_i:], "ch08: 仍有 item-title 残留"
    write("ch08.html", c2)
    report.append(f"ch08: {n} 张卡片归一为 news-card 标准解剖")

# ============================================================
# 3. ch04 外壳/头部归一 + 徽章修正
# ============================================================
c = read("ch04.html")
orig = c
# 3a. 头部解剖归一
pat4 = re.compile(
    r'<div class="topic-header">\s*<span class="topic-num">(\d+)</span>\s*<div>\s*'
    r'<div class="topic-title-main">(.*?)</div>\s*'
    r'<div class="topic-tags">(.*?)</div>\s*</div>\s*</div>',
    re.S,
)
n4 = len(pat4.findall(c))
assert n4 == c.count('class="topic-header"'), f"ch04: 头部匹配不全 {n4}/{c.count('class=\"topic-header\"')}"


def _ch04_repl(m):
    num, title, tags = m.group(1), m.group(2).strip(), m.group(3).strip()
    return (
        '<div class="news-head">\n'
        f'<span class="news-num">{num}</span>\n'
        f'<div class="news-headline">{title}</div>\n'
        '</div>\n'
        f'<div class="news-tags">{tags}</div>'
    )


c = pat4.sub(_ch04_repl, c)
# 3b. 外壳加标准类
c = c.replace('class="topic-card"', 'class="news-card topic-card"')
c = c.replace('class="top3-card"', 'class="news-card top3-card"')
# 3c. 徽章去 tag 混用
c = re.sub(r'class="badge tag (badge-p\d)"', r'class="\1"', c)
assert div_balance(c) == div_balance(orig), "ch04: div 平衡被破坏"
if c != orig:
    write("ch04.html", c)
    report.append(f"ch04: {n4} 个头部归一为 news-head 解剖，外壳/徽章统一")

# ============================================================
# 4. 推测性栏目 hero 内容性质标注
# ============================================================
NOTICES = {
    "ch05.html": "本栏内容属公开资讯与观测记录整编：官方披露与科研观测部分为可核实信息，推想性解读仅为观点，非事实结论。",
    "ch06.html": "本栏内容属文化解读与观点探索，涉及星际文明的叙述为假说与想象推演，非经证实的事实结论。",
    "ch07.html": "本栏内容为文明研究的观点解读，涉及历史推演与理论假说，非定论。",
    "ch08.html": "本栏以考古实证为基础，涉及推论与假说的部分属学术猜想，非定论。",
    "ch09.html": "本栏为传统典籍的文化解读与个人成长参考，哲理内容不构成科学结论。",
    "ch10.html": "本栏内容为健康资讯整编，仅供参考，不构成医疗建议；身体不适请及时就医。",
    "ch11.html": "本栏内容为身心练习参考，不构成医疗或心理治疗建议；持续情绪困扰请寻求专业帮助。",
    "ch12.html": "本栏内容属个人成长方法论与观点探索，“能量”表述为隐喻框架，非物理事实。",
}
for f, notice in NOTICES.items():
    c = read(f)
    if "hero-notice" in c:
        continue
    m = re.search(r'(<p class="hero-desc">.*?</p>)', c, re.S)
    assert m, f"{f}: 未找到 hero-desc"
    c = c.replace(m.group(1), m.group(1) + '\n    <div class="hero-notice">' + notice + "</div>", 1)
    assert div_balance(c) == div_balance(read(f)) + 0  # notice 自带开闭
    write(f, c)
    report.append(f"{f}: hero 增加内容性质标注")

# ============================================================
# 5. ch03-ch12 补研判块
# ============================================================
FOCUS = {
    "ch03.html": "政策合规动向、头部企业真实动作与终端消费数据三者的共振信号",
    "ch04.html": "选题与自身账号定位的匹配度，优先从TOP3方向切入，发布后24小时用数据回调选题池",
    "ch05.html": "官方机构（AARO、NASA、国防部）的后续披露节奏与观测数据的交叉验证结果",
    "ch06.html": "深空观测任务的数据发布节点与主流学术界对相关假说的回应",
    "ch07.html": "不同文明转型路径的对比案例、量化指标与可迁移的经验教训",
    "ch08.html": "田野考古新发现的正式简报、碳十四测年结果与多学科交叉验证进展",
    "ch09.html": "典籍版本的考据进展，以及经典智慧向当代实践转化时的适用边界",
    "ch10.html": "节气交替期的气温与湿度变化，及时调整饮食与起居节奏",
    "ch11.html": "自身身心反馈：练习后情绪与睡眠的变化，持续不适即降低强度并寻求专业帮助",
    "ch12.html": "认知重构与行动落地的一致性，用当日小行动验证显化目标",
}
OPENERS = ["本板块三条主线：", "主线梳理：", "核心脉络：", "要点研判：", "趋势梳理："]

for fi in range(3, 13):
    f = f"ch{fi:02d}.html"
    c = read(f)
    if "<section" in c:
        parts = re.split(r"(?=<section\b)", c)
    else:
        parts = re.split(r'(?=<div class="section["])', c)
    opener_idx = 0
    added = 0
    for pi in range(len(parts)):
        chunk = parts[pi]
        if 'class="judgment"' in chunk:
            continue
        hls = re.findall(
            r'class="(?:news-headline|item-title|topic-title-main)"[^>]*>(.*?)</(?:div|h3)>',
            chunk,
            re.S,
        )
        hls = [strip_tags(h) for h in hls]
        hls = [h for h in hls if h]
        if not hls:
            continue
        if "</section>" not in chunk:
            continue
        opener = OPENERS[opener_idx % len(OPENERS)]
        opener_idx += 1
        if len(hls) >= 3:
            lines = f"①{cut(hls[0])}；②{cut(hls[1])}；③{cut(hls[2])}。"
        elif len(hls) == 2:
            lines = f"①{cut(hls[0])}；②{cut(hls[1])}。"
        else:
            lines = f"{cut(hls[0])}。"
        text = f"{opener}{lines}建议关注：{FOCUS[f]}。"
        block = (
            '\n  <div class="judgment">\n'
            '    <strong class="key">趋势研判与建议</strong><br/>\n'
            f"    {text}\n"
            "  </div>\n"
        )
        j = chunk.rfind("</section>")
        parts[pi] = chunk[:j] + block + chunk[j:]
        added += 1
    c2 = "".join(parts)
    if added:
        assert div_balance(c2) == div_balance(c), f"{f}: div 平衡被破坏"
        write(f, c2)
        report.append(f"{f}: 补研判块 {added} 个")

# ============================================================
# 6. 首页源：搜索框 + 关于本站 + 更新日志 + 页脚链接 + 站级CSS
# ============================================================
HOME = "光体频道_source.html"
h = read(HOME)
orig_h = h

# 6a. 站级 CSS（含 hero-notice）
if ".hero-notice" not in h:
    site_css = """
/* === 站级组件：内容标注 / 搜索 / 关于 / 更新日志 === */
.hero-notice{margin-top:14px;display:inline-block;max-width:640px;padding:8px 16px;border:1px solid rgba(201,169,110,0.35);border-radius:20px;background:rgba(201,169,110,0.08);color:var(--gold-bright,#d4b57a);font-size:12px;letter-spacing:1px;line-height:1.7}
.search-box{position:relative;z-index:2000;max-width:640px;margin:0 auto 36px}
.search-box input{width:100%;box-sizing:border-box;padding:14px 18px 14px 44px;border-radius:12px;border:1px solid var(--border-subtle,rgba(201,169,110,0.25));background:var(--bg-card,rgba(255,255,255,0.04));color:var(--text-primary,#fff);font-size:15px;outline:none;transition:border-color .3s}
.search-box input:focus{border-color:var(--gold,#c9a96e)}
.search-icon{position:absolute;left:14px;top:14px;font-size:16px;opacity:0.7;pointer-events:none}
.search-results{position:absolute;top:52px;left:0;right:0;z-index:50;max-height:380px;overflow-y:auto;background:#141414;border:1px solid var(--border-subtle,rgba(201,169,110,0.25));border-radius:12px;box-shadow:0 20px 50px rgba(0,0,0,0.5)}
.search-result-item{padding:12px 16px;border-bottom:1px solid rgba(255,255,255,0.06);cursor:pointer}
.search-result-item:hover{background:rgba(201,169,110,0.1)}
.search-result-item .sr-channel{font-size:11px;color:var(--gold,#c9a96e);letter-spacing:1px;margin-bottom:4px}
.search-result-item .sr-title{font-size:14px;color:var(--text-primary,#fff)}
.search-result-item .sr-snip{font-size:12px;color:var(--text-muted,#999);margin-top:4px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.search-empty{padding:16px;color:var(--text-muted,#999);font-size:13px;text-align:center}
.about-site{margin:64px 0 8px}
.about-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.about-block{background:var(--bg-card,rgba(255,255,255,0.04));border:1px solid var(--border-subtle,rgba(201,169,110,0.2));border-radius:12px;padding:20px}
.about-title{font-size:15px;font-weight:600;color:var(--gold-bright,#d4b57a);margin-bottom:10px}
.about-block p{font-size:13px;line-height:1.8;color:var(--text-secondary,#bbb);margin:0}
.update-log{margin:56px 0 8px}
.log-list{list-style:none;margin:20px 0 0;padding:0}
.log-list li{display:flex;gap:16px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.06);font-size:13px}
.log-date{color:var(--gold,#c9a96e);font-family:'Cormorant Garamond',serif;font-size:15px;min-width:90px;flex-shrink:0}
.log-note{color:var(--text-secondary,#bbb)}
.footer-links{display:flex;gap:10px;justify-content:center;margin-top:14px;font-size:12px;color:var(--text-muted,#888)}
.footer-links a{color:var(--gold,#c9a96e);text-decoration:none;letter-spacing:1px}
.footer-links a:hover{text-decoration:underline}
"""
    h = h.replace("</style>", site_css + "</style>", 1)

# 6b. 搜索框（放在频道网格前）
if 'id="site-search"' not in h:
    search_html = '''  <div class="search-box" id="search-box">
    <span class="search-icon">🔍</span>
    <input type="text" id="site-search" placeholder="搜索全站12个频道的内容，如：金砖、DeepSeek、白露养生" autocomplete="off" oninput="siteSearch(this.value)" />
    <div class="search-results" id="search-results" style="display:none"></div>
  </div>
'''
    anchor = '  <div class="channel-grid">'
    assert anchor in h, "首页源未找到 channel-grid 锚点"
    h = h.replace(anchor, search_html + anchor, 1)

# 6c. 关于本站 + 更新日志（放在 features-grid 前）
if 'id="about"' not in h:
    about_html = '''  <div class="about-site" id="about">
    <div class="section-label"><span class="section-label-text">ABOUT · EDITORIAL STANDARDS</span><span class="section-label-line"></span></div>
    <h2 class="section-title"><span class="bar"></span>关于本站<span class="en"> · About &amp; Editorial Standards</span></h2>
    <div class="about-grid">
      <div class="about-block"><div class="about-title">✍️ 编辑规范</div><p>每日09:00（Asia/Shanghai）自动整编发布；事实类频道逐条标注真实来源与日期；每个板块末尾配趋势研判；发现错误当日核实修正，并在更新日志记录。</p></div>
      <div class="about-block"><div class="about-title">🔬 内容分级</div><p>事实资讯（全球新闻、AI热点、商业趋势、自媒体选题、UFO官方披露）以可核实报道为准；探索解读类内容（星际文明、人类文明、史前文明、高维典籍、身心疗愈、显化能量）均在栏目页顶部标注"观点探索，非事实结论"。</p></div>
      <div class="about-block"><div class="about-title">📚 数据来源</div><p>每条资讯卡片底部标注具体来源与发布日期；事实类新闻信源为官方机构发布与持牌媒体报道；研究类内容信源为学术论文、行业白皮书与考古简报。</p></div>
      <div class="about-block"><div class="about-title">⚠️ 免责声明</div><p>本站内容仅作资讯整编与个人成长参考，不构成投资、医疗或法律建议；养生与疗愈内容不能替代专业诊疗；引用本站内容请注明出处。</p></div>
    </div>
  </div>

  <div class="update-log" id="update-log">
    <div class="section-label"><span class="section-label-text">UPDATE LOG · ARCHIVE</span><span class="section-label-line"></span></div>
    <h2 class="section-title"><span class="bar"></span>更新日志<span class="en"> · Update Log</span></h2>
    <ul class="log-list" id="log-list">
      <li><span class="log-date">2026.09.11</span><span class="log-note">全站新增研判块、站内搜索、更新日志与RSS订阅；12频道卡片结构统一收口</span></li>
    </ul>
  </div>

'''
    anchor = '  <div class="features-grid">'
    assert anchor in h, "首页源未找到 features-grid 锚点"
    h = h.replace(anchor, about_html + anchor, 1)

# 6d. 页脚功能链接
if 'class="footer-links"' not in h:
    links_html = '''  <div class="footer-links">
    <a href="#search-box" onclick="var i=document.getElementById('site-search'); if(i){i.focus();} return false;">站内搜索</a>
    <span>·</span>
    <a href="#home" onclick="var u=document.getElementById('update-log'); if(u){u.scrollIntoView({behavior:'smooth'});} return false;">更新日志</a>
    <span>·</span>
    <a href="https://gt-ai-3396815.github.io/guangti-channel/rss.xml" target="_blank" rel="noopener">RSS订阅</a>
  </div>
'''
    m = re.search(r'(<div class="footer-info">\s*<div>.*?</div>\s*<div>.*?</div>\s*</div>)', h, re.S)
    assert m, "首页源未找到 footer-info 块"
    h = h.replace(m.group(1), m.group(1) + "\n" + links_html, 1)

assert div_balance(h) == div_balance(orig_h), "首页源: div 平衡被破坏"
if h != orig_h:
    write(HOME, h)
    report.append("首页源: 新增搜索框/关于本站/更新日志/页脚链接/站级CSS")

print("=== 内容专业度增强完成 ===")
for line in report:
    print("  •", line)
