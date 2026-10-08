# -*- coding: utf-8 -*-
"""替换标题 logo 与 favicon 为湘雅精神卫生研究所徽章（base64 内嵌，保持自包含）"""
import re

html_path = r"C:\Users\wenji\Doubao\chats\2026-10-02\new-chat\xiangya-psychtree\work\index.html"
b64 = open(r"C:\Users\wenji\Doubao\chats\2026-10-02\new-chat\xiangya-psychtree\_b64.txt", encoding="utf-8").read().strip()
data_uri = "data:image/png;base64," + b64

html = open(html_path, encoding="utf-8").read()

# 1) favicon：整行 <link rel="icon" href="data:image/svg+xml,...">
pat_fav = re.compile(r'<link rel="icon" href="[^"]+">')
html, n1 = pat_fav.subn(
    '<link rel="icon" href="' + data_uri + '">', html, count=1)
assert n1 == 1, "favicon link not found"

# 2) 标题左侧 logo：替换 <a class="logo"> 内的 svg 元素（唯一 width="24" 的 svg）
pat_logo = re.compile(r'<svg width="24" height="24"[^>]*>.*?</svg>', re.S)
new_logo_inner = ('<img src="' + data_uri + '" width="24" height="24" '
                  'alt="湘雅精神卫生研究所徽章" style="border-radius:5px;object-fit:cover">')
html, n2 = pat_logo.subn(new_logo_inner, html, count=1)
assert n2 == 1, "logo svg not found"

open(html_path, "w", encoding="utf-8").write(html)
print("favicon replaced:", n1, "| logo replaced:", n2, "| size:", len(html.encode("utf-8")))
