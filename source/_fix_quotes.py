# -*- coding: utf-8 -*-
"""修复 _daily_*.py 中被工具转成直引号的中文引号：CJK 邻接判定，逐行开闭交替"""
import io, os, sys

SRC = os.path.dirname(os.path.abspath(__file__))
FILES = ['_daily_ch01.py', '_daily_ch02.py', '_daily_ch03.py',
         '_daily_ch04.py', '_daily_ch05.py', '_daily_ch1012.py']

def cjkish(ch):
    if not ch:
        return False
    o = ord(ch)
    return (0x3000 <= o <= 0x303F or 0x3400 <= o <= 0x4DBF or
            0x4E00 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or
            0xFF00 <= o <= 0xFFEF or o in (0x2014, 0x2026, 0x00B7, 0x2018, 0x2019))

for fn in FILES:
    p = os.path.join(SRC, fn)
    lines = io.open(p, encoding='utf-8').read().split('\n')
    out = []
    fixed = 0
    for line in lines:
        chars = list(line)
        open_next = True
        for i, ch in enumerate(chars):
            if ch != '"':
                continue
            prev = chars[i-1] if i > 0 else ''
            nxt = chars[i+1] if i+1 < len(chars) else ''
            if cjkish(prev) or cjkish(nxt):
                chars[i] = '\u201c' if open_next else '\u201d'
                open_next = not open_next
                fixed += 1
        out.append(''.join(chars))
    io.open(p, 'w', encoding='utf-8', newline='').write('\n'.join(out))
    print('[OK] %s fixed=%d' % (fn, fixed))

# ch04 hook 内层单引号改为弯单引号
p = os.path.join(SRC, '_daily_ch04.py')
t = io.open(p, encoding='utf-8').read()
old = "：'基于尊重、公平、对等的建设性战略稳定关系'。这期"
new = "：\u2018基于尊重、公平、对等的建设性战略稳定关系\u2019。这期"
n = t.count(old)
if n == 1:
    t = t.replace(old, new)
    io.open(p, 'w', encoding='utf-8', newline='').write(t)
    print('[OK] ch04 inner quotes fixed')
else:
    print('[WARN] ch04 inner-quote anchor count=%d (skip)' % n)

# 语法校验
import py_compile
for fn in FILES + ['_daily_dates.py']:
    py_compile.compile(os.path.join(SRC, fn), doraise=True)
print('[OK] all scripts compile')
