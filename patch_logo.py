# -*- coding: utf-8 -*-
"""用机构标识替换站点头图：更新内嵌 data URI、alt 文案与 .banner 样式"""
import base64, re

BASE = r"C:\Users\mechrevo\Doubao\chats\2026-10-02\new-chat\xiangya-psychtree"
html_path = BASE + r"\XiangyaPsychTree.html"
png_path = BASE + r"\assets\hero-banner.png"

png = open(png_path, "rb").read()
print("png bytes:", len(png))
assert png[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"

b64 = base64.b64encode(png).decode("ascii")
html = open(html_path, encoding="utf-8").read()

# 1) 替换 <img> 标签（data URI + alt）
pat = re.compile(r'<img src="data:image/png;base64,[^"]+" alt="[^"]*">')
new_img = '<img src="data:image/png;base64,' + b64 + '" alt="国家精神疾病医学中心 · 精神心理疾病国家临床医学研究中心标识">'
html, n1 = pat.subn(new_img, html, count=1)
assert n1 == 1, "img tag not replaced"

# 2) 更新 .banner 样式：logo 为宽扁形，完整显示不裁切，宽屏居中
old_css_banner = """.banner{
  margin-top:16px; border:1px solid var(--border); border-radius:var(--radius); overflow:hidden;
  background:var(--surface); position:relative;
}
.banner img{display:block; width:100%; height:auto; aspect-ratio:21/9; object-fit:cover}"""
new_css_banner = """.banner{
  margin-top:16px; border:1px solid var(--border); border-radius:var(--radius); overflow:hidden;
  background:var(--surface); position:relative; padding:14px 18px;
}
.banner img{display:block; width:100%; max-width:1100px; height:auto; margin:0 auto; object-fit:contain}"""
assert old_css_banner in html, "banner css block not found"
html = html.replace(old_css_banner, new_css_banner, 1)

open(html_path, "w", encoding="utf-8").write(html)
print("patched ok, size:", len(html.encode("utf-8")))
