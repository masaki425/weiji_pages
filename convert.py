#!/usr/bin/env python3
"""
md→HTML変換スクリプト
weiji_pages/ ディレクトリで実行：python3 convert.py
依存: pip install markdown
"""

import markdown
import os
import re

SIDEBAR = """  <nav class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <a href="../index.html" class="sidebar-title">W Eiji 論</a>
    </div>
    <div class="sidebar-body">
      <div class="nav-section">
        <h2 class="nav-heading">Ⅰ　二人のワタナベエイジ</h2>
        <ul class="nav-list">
          <li><a href="../weiji/weiji-scientist_analysis_report.html">渡辺英治（神経科学者）</a></li>
          <li><a href="../weiji/weiji-artist_analysis_report.html">渡辺英司（現代美術家）</a></li>
          <li><a href="../weiji/calculation_methods.html">計算手法の説明</a></li>
        </ul>
      </div>
      <div class="nav-section">
        <h2 class="nav-heading">Ⅱ　W Eiji 統合思考分析</h2>
        <ul class="nav-list">
          <li><a href="../network/network_00_introduction_chapter.html">序章　同姓同名の邂逅</a></li>
          <li><a href="../network/network_01_weiji-scientist_chapter.html">治の章　神経科学者の思考回路</a></li>
          <li><a href="../network/network_02_weiji-artist_chapter.html">司の章　現代美術家の思考回路</a></li>
          <li><a href="../network/network_03_epistemological_operations_chapter.html">認識論的操作の章　二つの否定</a></li>
          <li><a href="../network/network_04_encounter_chapter.html">邂逅の章　二人の出会い</a></li>
        </ul>
      </div>
      <div class="nav-section">
        <h2 class="nav-heading">Ⅲ　切り抜きの美学</h2>
        <ul class="nav-list">
          <li><a href="../kirinuki/kirinuki_00_introduction.html">序章　問いの設定</a></li>
          <li><a href="../kirinuki/kirinuki_01_chapter.html">第一章　「切り抜き」の操作</a></li>
          <li><a href="../kirinuki/kirinuki_02_chapter.html">第二章　操作の表現形式</a></li>
          <li><a href="../kirinuki/kirinuki_03_chapter.html">第三章　頻度と越境</a></li>
          <li><a href="../kirinuki/kirinuki_04_chapter.html">第四章　揺らぎの架け橋</a></li>
          <li><a href="../kirinuki/kirinuki_05_conclusion.html">結論</a></li>
        </ul>
      </div>
    </div>
  </nav>"""

KATEX_HEAD = """  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
  <script>
    document.addEventListener("DOMContentLoaded", function() {
      renderMathInElement(document.body, {
        delimiters: [
          {left: "$$", right: "$$", display: true},
          {left: "$", right: "$", display: false}
        ]
      });
    });
  </script>"""

TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — W Eiji 論</title>
  <link rel="stylesheet" href="../style.css">
{katex}
</head>
<body class="reader-page">

{sidebar}

  <main class="content">
    <article class="reader-content">
{body}
    </article>
    <footer class="content-footer">
      <p><a href="../index.html" style="color:inherit; text-decoration:none;">W Eiji 論</a></p>
    </footer>
  </main>

  <button class="sidebar-toggle" id="sidebar-toggle" aria-label="メニュー">☰</button>
  <script>
    document.getElementById('sidebar-toggle').addEventListener('click', () =>
      document.getElementById('sidebar').classList.toggle('open'));
    var here = location.pathname.split('/').pop();
    document.querySelectorAll('.nav-list a').forEach(function(a) {{
      if (a.getAttribute('href').endsWith(here)) a.classList.add('active');
    }});
  </script>

</body>
</html>"""

CONVERSIONS = {
    "weiji": [
        ("weiji-scientist_analysis_report.md", "weiji-scientist_analysis_report.html"),
        ("weiji-artist_analysis_report.md",    "weiji-artist_analysis_report.html"),
        ("weiji-artist_profile.md",            "weiji-artist_profile.html"),
        ("calculation_methods.md",             "calculation_methods.html"),
    ],
    "network": [
        ("network_00_introduction_chapter.md",                "network_00_introduction_chapter.html"),
        ("network_01_weiji-scientist_chapter.md",             "network_01_weiji-scientist_chapter.html"),
        ("network_02_weiji-artist_chapter.md",                "network_02_weiji-artist_chapter.html"),
        ("network_03_epistemological_operations_chapter.md",  "network_03_epistemological_operations_chapter.html"),
        ("network_04_encounter_chapter.md",                   "network_04_encounter_chapter.html"),
    ],
    "kirinuki": [
        ("kirinuki_00_introduction.md",  "kirinuki_00_introduction.html"),
        ("kirinuki_01_chapter.md",       "kirinuki_01_chapter.html"),
        ("kirinuki_02_chapter.md",       "kirinuki_02_chapter.html"),
        ("kirinuki_03_chapter.md",       "kirinuki_03_chapter.html"),
        ("kirinuki_04_chapter.md",       "kirinuki_04_chapter.html"),
        ("kirinuki_05_conclusion.md",    "kirinuki_05_conclusion.html"),
    ],
}

# 数式を含むファイル（KaTeXを読み込み、数式を保護する）
MATH_FILES = {"calculation_methods.md"}

def protect_math(text):
    """$$...$$ をプレースホルダーに置換してMarkdown変換から保護する"""
    store = []
    def replacer(m):
        store.append(m.group(0))
        return f"\x00MATH{len(store)-1}\x00"
    # $$...$$ (display) を先に処理
    text = re.sub(r'\$\$.+?\$\$', replacer, text, flags=re.DOTALL)
    return text, store

def restore_math(html, store):
    """プレースホルダーを元の数式に戻す"""
    for i, expr in enumerate(store):
        html = html.replace(f"\x00MATH{i}\x00", expr)
    return html

def extract_title(html):
    m = re.search(r'<h1>(.*?)</h1>', html)
    if m:
        return re.sub(r'<[^>]+>', '', m.group(1))
    return "W Eiji 論"

def main():
    md_converter = markdown.Markdown(extensions=['tables', 'fenced_code'])
    count = 0
    errors = 0

    for subdir, files in CONVERSIONS.items():
        for md_name, html_name in files:
            md_path = os.path.join(subdir, md_name)
            html_path = os.path.join(subdir, html_name)

            if not os.path.exists(md_path):
                print(f"  SKIP  {md_path} (not found)")
                errors += 1
                continue

            with open(md_path, "r", encoding="utf-8") as f:
                md_text = f.read()

            # 数式を含むファイルは数式を保護
            math_store = []
            if md_name in MATH_FILES:
                md_text, math_store = protect_math(md_text)

            md_converter.reset()
            body = md_converter.convert(md_text)

            # 数式を復元
            if math_store:
                body = restore_math(body, math_store)

            title = extract_title(body)
            katex = KATEX_HEAD if md_name in MATH_FILES else ""
            html = TEMPLATE.format(title=title, body=body, sidebar=SIDEBAR, katex=katex)

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)

            size = os.path.getsize(html_path)
            print(f"  OK    {html_path} ({size//1024}KB)")
            count += 1

    print(f"\n{count} files converted, {errors} skipped.")

if __name__ == "__main__":
    main()
