# -*- coding: utf-8 -*-
"""将 hero-banner.png 以 base64 data URI 内嵌进 XiangyaPsychTree.html，生成完全自包含单文件"""
import base64

BASE = r"C:\Users\mechrevo\Doubao\chats\2026-10-02\new-chat\xiangya-psychtree"
png_path = BASE + r"\assets\hero-banner.png"
html_path = BASE + r"\XiangyaPsychTree.html"

png = open(png_path, "rb").read()
b64 = base64.b64encode(png).decode("ascii")

html = open(html_path, encoding="utf-8").read()
old = '<img src="assets/hero-banner.png"'
new = '<img src="data:image/png;base64,' + b64 + '"'
assert old in html, "img tag not found"
html = html.replace(old, new, 1)

open(html_path, "w", encoding="utf-8").write(html)
print("inlined ok, new size:", len(html.encode("utf-8")), "bytes")
