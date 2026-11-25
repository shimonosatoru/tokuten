"""特典ページを作る：src/<名前>.md → docs/<名前>/index.html（GitHub Pages は docs/ を公開）

使い方: python3 build_site.py
- 検索に出ないように noindex を入れ、robots.txt でもクロールを断る
- トップ（docs/index.html）は一覧を出さない。URL を知っている人だけが開ける
- コードブロックにはコピーボタンを付ける
"""
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
OUT = os.path.join(HERE, "docs")


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def md_to_html(md):
    lines = md.split("\n")
    out, i, n_code = [], 0, 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            body = []
            i += 1
            while not lines[i].startswith("```"):
                body.append(lines[i])
                i += 1
            n_code += 1
            cid = f"code{n_code}"
            out.append(
                f'<div class="copyable"><span class="copy">'
                f'<button type="button" class="copy-button" command="--copy" commandfor="{cid}" '
                f'aria-label="プロンプト{n_code}をコピー">コピー</button>'
                f'<span class="tip" role="status"></span></span>'
                f'<pre tabindex="0"><code id="{cid}">{html.escape(chr(10).join(body))}</code></pre></div>')
        elif line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            out.append(f"<h{level}>{inline(line[level:].strip())}</h{level}>")
        elif line.strip() == "---":
            out.append("<hr>")
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[\s\-|:]+\|$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            i -= 1
            head = "".join(f"<th>{inline(c)}</th>" for c in rows[0])
            body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
            out.append(f'<div class="table"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
        elif line.startswith(">"):
            out.append(f"<blockquote>{inline(line.lstrip('> '))}</blockquote>")
        elif re.match(r"^(\d+\.|-) ", line):
            ordered = line[0].isdigit()
            items = []
            while i < len(lines) and re.match(r"^(\d+\.|-) ", lines[i]):
                items.append(f"<li>{inline(re.sub(r'^(\d+\.|-) ', '', lines[i]))}</li>")
                i += 1
            i -= 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>{''.join(items)}</{tag}>")
        elif line.strip():
            para = [line]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(#|```|\||>|---|\d+\. |- )", lines[i + 1]):
                i += 1
                para.append(lines[i])
            out.append("<p>" + "<br>".join(inline(p) for p in para) + "</p>")
        i += 1
    return "\n".join(out)


PAGE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{title}</title>
<style>
:root {{ color-scheme: light; --accent: #6d4bd6; --line: #e6e3ef; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: "Hiragino Sans", "Noto Sans JP", system-ui, sans-serif; line-height: 1.8;
  color: #1f1d2b; background: #faf9fd; }}
main {{ max-inline-size: 760px; margin-inline: auto; padding: 32px 20px 80px; }}
h1 {{ font-size: 1.6rem; line-height: 1.4; margin-block: 0 .5em; }}
h2 {{ font-size: 1.25rem; margin-block: 2em .6em; padding-inline-start: .6em; border-inline-start: 5px solid var(--accent); }}
h3 {{ font-size: 1.05rem; margin-block: 1.6em .4em; }}
hr {{ border: 0; border-block-start: 1px solid var(--line); margin-block: 2em; }}
code {{ font-family: ui-monospace, Menlo, monospace; font-size: .9em; background: #efecf7; padding: .1em .35em; border-radius: 4px; }}
pre {{ margin: 0; padding: 16px; overflow-x: auto; background: #1f1d2b; color: #f3f1fa; border-radius: 10px;
  white-space: pre-wrap; word-break: break-word; }}
pre code {{ background: none; padding: 0; color: inherit; font-size: .88rem; line-height: 1.7; }}
.copyable {{ display: flex; flex-direction: column; gap: 8px; margin-block: 1em 1.5em; }}
.copy {{ position: relative; align-self: flex-end; }}
.copy-button {{ min-inline-size: 24px; min-block-size: 24px; padding: 6px 16px; font: inherit; font-size: .9rem; font-weight: 700;
  color: #fff; background: var(--accent); border: 0; border-radius: 999px; cursor: pointer; }}
.copy-button[data-copied] {{ background: #1f9d55; }}
.copy-button[data-failed] {{ background: #c0392b; }}
.tip {{ position: absolute; inset-inline-end: 0; inset-block-end: calc(100% + 6px); white-space: nowrap; font-size: .8rem;
  background: #1f1d2b; color: #fff; padding: 2px 8px; border-radius: 6px; opacity: 0; transition: opacity .15s; }}
.tip:not(:empty) {{ opacity: 1; }}
.table {{ overflow-x: auto; }}
table {{ border-collapse: collapse; inline-size: 100%; font-size: .92rem; background: #fff; }}
th, td {{ border: 1px solid var(--line); padding: 8px 10px; text-align: start; vertical-align: top; }}
th {{ background: #f1eef9; }}
blockquote {{ margin: 1em 0; padding: 12px 16px; background: #fff7e6; border-radius: 8px; border-inline-start: 4px solid #f0a500; }}
@media (prefers-reduced-motion: reduce) {{ .tip {{ transition: none; }} }}
</style>
</head>
<body>
<main>
{body}
</main>
<script>
const timers = new WeakMap();
function report(button, ok) {{
  const tip = button.nextElementSibling;
  clearTimeout(timers.get(button));
  button.removeAttribute('data-copied');
  button.removeAttribute('data-failed');
  tip.textContent = '';
  button.setAttribute(ok ? 'data-copied' : 'data-failed', '');
  button.textContent = ok ? 'コピーしました' : 'コピー失敗';
  requestAnimationFrame(() => (tip.textContent = ok ? 'コピーしました' : 'コピーできませんでした'));
  timers.set(button, setTimeout(() => {{
    button.removeAttribute('data-copied');
    button.removeAttribute('data-failed');
    button.textContent = 'コピー';
    tip.textContent = '';
  }}, 2000));
}}
async function copy(button, target) {{
  const text = target.innerText.trim();
  if (!text) return;
  try {{ await navigator.clipboard.writeText(text); report(button, true); }}
  catch {{ report(button, false); }}
}}
if ('CommandEvent' in window) {{
  document.addEventListener('command', (e) => {{ if (e.command === '--copy') copy(e.source, e.target); }}, true);
}} else {{
  document.addEventListener('click', (e) => {{
    if (e.defaultPrevented) return;
    const b = e.target.closest('button[command="--copy"]');
    const t = b && document.getElementById(b.getAttribute('commandfor'));
    if (t) copy(b, t);
  }});
}}
</script>
</body>
</html>
"""


def main():
    os.makedirs(OUT, exist_ok=True)
    for name in sorted(os.listdir(SRC)):
        if not name.endswith(".md"):
            continue
        slug = name[:-3]
        md = open(os.path.join(SRC, name), encoding="utf-8").read()
        title = re.search(r"^# (.+)$", md, re.M).group(1)
        os.makedirs(os.path.join(OUT, slug), exist_ok=True)
        with open(os.path.join(OUT, slug, "index.html"), "w", encoding="utf-8") as f:
            f.write(PAGE.format(title=html.escape(title), body=md_to_html(md)))
        print(f"docs/{slug}/index.html")
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write('<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8">'
                '<meta name="robots" content="noindex, nofollow"><title>特典</title></head>'
                '<body><p>このページには何もありません。</p></body></html>\n')
    with open(os.path.join(OUT, "robots.txt"), "w") as f:
        f.write("User-agent: *\nDisallow: /\n")
    open(os.path.join(OUT, ".nojekyll"), "w").close()


if __name__ == "__main__":
    main()
