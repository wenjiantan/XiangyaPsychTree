# -*- coding: utf-8 -*-
"""将 data/xiangya-psychtree.json 注入 XiangyaPsychTree.html 模板，生成最终单文件页面"""
import os

BASE = r"C:\Users\mechrevo\Doubao\chats\2026-10-02\new-chat\xiangya-psychtree"
html_path = os.path.join(BASE, "XiangyaPsychTree.html")
data_path = os.path.join(BASE, "data", "xiangya-psychtree.json")

html = open(html_path, encoding="utf-8").read()
data = open(data_path, encoding="utf-8").read()

assert "__DATA_JSON__" in html, "模板中缺少数据占位符"
assert "</script>" not in data, "数据中含 </script>，会导致页面截断"
assert "<!--" not in data, "数据中含注释标记"

html = html.replace("__DATA_JSON__", data)
open(html_path, "w", encoding="utf-8").write(html)
print("构建完成:", os.path.getsize(html_path), "bytes")
