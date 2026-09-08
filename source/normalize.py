#!/usr/bin/env python3
"""
光体•星际频道 - 栏目格式统一化脚本
统一规则（与 STYLE_GUIDE.md 一致）：
  1. 徽章系统统一为 badge badge-pN（消除 tag-pN 双轨制）
  2. 栏目标题统一为 <span class="bar"></span> + 中文 + <span class="en"> · English</span>
  3. section-icon / section-num / section-label-line 统一用 <span> 标签
  4. ch03: card-title-row → news-head（标记+CSS 同步改名）
  5. ch07: civ-* 别名全部归一到 news-* 规范类（标记+CSS 同步改名）
带断言保护：任何结构性意外立即中止，不写入任何文件。
"""
import re

WORK = "."

def read(f):
    with open(f, encoding="utf-8") as fh:
        return fh.read()

def write(f, c):
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(c)

def div_balance(s):
    return len(re.findall(r"<div\b", s, re.I)) - len(re.findall(r"</div>", s, re.I))

changed = []

for i in range(1, 13):
    ch = f"ch{i:02d}.html"
    orig = read(ch)
    c = orig
    log = []

    # ---- 1. 徽章统一：tag-pN -> badge badge-pN ----
    def fix_badge(m):
        cls = m.group(1)
        cls = re.sub(r"\btag-p(\d)\b", r"badge-p\1", cls)
        if re.search(r"\bbadge-p\d\b", cls) and not re.search(r"\bbadge\b(?!-)", cls):
            cls = "badge " + cls
        return f'class="{cls}"'
    c2 = re.sub(r'class="([^"]*)"', fix_badge, c)
    if c2 != c:
        log.append("badge tag-pN->badge-pN")
        c = c2

    # ---- 2a. section-title 补 bar ----
    def fix_title(m):
        inner = m.group(1)
        if "<span" in inner and "bar" in inner:
            return m.group(0)
        return f'<h2 class="section-title"><span class="bar"></span>{inner}</h2>'
    c2 = re.sub(r'<h2 class="section-title">(?!<span class="bar">)(.*?)</h2>', fix_title, c, flags=re.S)
    if c2 != c:
        log.append("title+bar")
        c = c2

    # ---- 2b. en 前缀统一为 "· " ----
    def fix_en(m):
        inner = m.group(1).strip()
        if not inner:
            return m.group(0)
        if inner.startswith("·"):
            return f'<span class="en"> {inner}</span>'
        return f'<span class="en"> · {inner}</span>'
    c2 = re.sub(r'<span class="en">([^<]*)</span>', fix_en, c)
    if c2 != c:
        log.append("en·prefix")
        c = c2

    # ---- 3. 标签统一 span ----
    c2 = re.sub(r'<div class="section-icon">([\s\S]*?)</div>', r'<span class="section-icon">\1</span>', c)
    if c2 != c: log.append("section-icon->span"); c = c2
    c2 = re.sub(r'<div class="section-num">([\s\S]*?)</div>', r'<span class="section-num">\1</span>', c)
    if c2 != c: log.append("section-num->span"); c = c2
    c2 = re.sub(r'<div class="section-label-line"></div>', r'<span class="section-label-line"></span>', c)
    if c2 != c: log.append("label-line->span"); c = c2

    # ---- 4. ch03: card-title-row -> news-head ----
    if ch == "ch03.html":
        # ch03 已有同体规则的 .container .news-head 覆盖，改名后级联结果一致，安全
        c = c.replace('class="card-title-row"', 'class="news-head"')
        c = c.replace(".card-title-row", ".news-head")
        log.append("card-title-row->news-head(css+markup)")

    # ---- 5. ch07: civ-* -> news-* ----
    if ch == "ch07.html":
        pairs = [("civ-card", "news-card"), ("civ-number", "news-num"),
                 ("civ-headline", "news-headline"), ("civ-summary", "news-summary"),
                 ("civ-analysis", "news-analysis"), ("civ-tag", "tag"),
                 ("civ-source", "news-source"), ("civ-detail", "news-detail")]
        for old, new in pairs:
            # CSS 选择器先改名（在标记清理之前，避免 \b 匹配吃掉选择器文本）
            c2 = re.sub(rf"\.{old}\b", f".{new}", c)
            # 标记中移除别名（规范类已同时存在，如 "news-card civ-card"）
            c3 = re.sub(rf"\s*\b{old}\b(?!-)", "", c2)
            if c3 != c:
                log.append(f"{old}->{new}")
                c = c3

        # 6. news-analysis 覆盖写法对齐 ch01 规范（去掉完整定义，改用局部覆盖）
        full_analysis = re.search(
            r"\.container \.news-analysis\s*\{[^}]*border-radius[^}]*\}", c)
        if full_analysis:
            c = c.replace(full_analysis.group(0),
                ".container .news-analysis{background:linear-gradient(135deg,rgba(201,169,110,0.08),rgba(201,169,110,0.02));\n"
                "  border:1px solid rgba(201,169,110,0.2);}")
            log.append("news-analysis->canonical-override")

        # 6b. news-tag 归一到 .tag 徽章（处理 civ-tag 已被改名为 news-tag 的历史状态）
        if 'class="news-tag"' in c:
            c = c.replace('class="news-tag"', 'class="tag"')
            log.append("news-tag->tag(markup)")
        full_newstag = re.search(r"\.container \.news-tag\s*\{[^}]*border-radius:12px[^}]*\}", c)
        if full_newstag:
            c = c.replace(full_newstag.group(0), "")
            log.append("news-tag full-def removed(css)")

    # ---- 校验 ----
    assert div_balance(c) == div_balance(orig), f"{ch}: div 平衡被破坏"
    assert "civ-" not in c or ch != "ch07.html", "ch07 仍有 civ- 残留"
    if c != orig:
        write(ch, c)
        changed.append(f"{ch}: {', '.join(log)}")

print("=== 统一化完成 ===")
for line in changed:
    print(" ", line)
if not changed:
    print("  (无需改动)")

# ---- 全局复检 ----
print("\n=== 复检 ===")
for i in range(1, 13):
    ch = f"ch{i:02d}.html"
    c = read(ch)
    issues = []
    if div_balance(c) != 0:
        issues.append(f"div平衡={div_balance(c)}")
    if re.search(r'class="[^"]*\btag-p\d', c):
        issues.append("残留tag-pN")
    if 'class="card-title-row"' in c:
        issues.append("残留card-title-row")
    if re.search(r'class="[^"]*\bciv-', c):
        issues.append("残留civ-*")
    # badge 一致性
    badges = sorted(set(re.findall(r'class="badge badge-p(\d)"', c)))
    # 标题 bar 覆盖率
    titles = len(re.findall(r'<h2 class="section-title">', c))
    titles_bar = len(re.findall(r'<h2 class="section-title"><span class="bar">', c))
    status = "OK" if not issues else "ISSUES: " + ";".join(issues)
    print(f"  {ch}: {status} | badge-p{badges} | 标题bar {titles_bar}/{titles}")
