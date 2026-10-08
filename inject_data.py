# -*- coding: utf-8 -*-
"""用新解析的 JSON 替换 HTML 内嵌数据块（保留页面其余全部修改）"""
import re, os

_HERE = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(_HERE, "data", "xiangya-psychtree.json")
htmls = [os.path.join(_HERE, "index.html")]

new_json = open(json_path, encoding="utf-8").read().strip()
assert "</script>" not in new_json

pat = re.compile(r'(<script id="app-data" type="application/json">).*?(</script>)', re.S)

for hp in htmls:
    html = open(hp, encoding="utf-8").read()
    html, n = pat.subn(lambda m: m.group(1) + new_json + m.group(2), html, count=1)
    assert n == 1, "data block not found in " + hp
    open(hp, "w", encoding="utf-8").write(html)
    print("updated:", hp, len(html.encode("utf-8")), "bytes")
