# XiangyaPsychTree

中南大学湘雅精神医学专业历届 **本科 / 硕士 / 博士** 学生名录的可视化展示
https://wenjiantan.github.io/XiangyaPsychTree/

## 数据来源
https://ncrcmdxy.xyeyy.com/education/graduate-remember
中南大学历年硕士博士拟录取名单、知网

## 使用

- 直接用浏览器打开 `XiangyaPsychTree.html` 即可（数据与头图均已内嵌，完全自包含、可离线使用）
- 部署到 GitHub Pages：将本站文件以 `index.html` 命名推送到仓库根目录（连同 `data/` 一并推送），在 Settings → Pages → 构建来源选择「从分支部署」→ `main` / 根目录 → 保存，即可访问 `https://<用户名>.github.io/<仓库名>/`

## 目录

```
XiangyaPsychTree.html   站点（单文件，数据与头图已内嵌；部署时命名为 index.html）
assets/hero-banner.png  机构标识源文件（已内嵌进页面，仅作素材保留）
data/                   解析产物（source 为名单快照，xiangya-psychtree.json 为结构化数据）
parse.py / build.py     数据解析与构建脚本
```
