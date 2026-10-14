#!/usr/bin/env python3
"""
make_manuscript.py -- extract the prose of index.html into an Org manuscript.

WHY.  index.html is the artifact; hand-editing HTML is not how BL wants to write.
This produces memento-manuscript.org: every section, paragraph, list and table of
the page as editable Org text.  Edit there, then have the edits applied back to
index.html (by hand or by an agent) -- deliberately a LOOSE coupling, not a build
pipeline.  The page keeps its own design; the manuscript keeps the words.

DRIFT.  Re-running this after the page changes regenerates the manuscript from
the artifact, so `diff` (or git) shows exactly where words have moved apart.
Regenerate into a scratch copy if you have unapplied edits -- this OVERWRITES.

Verbatim blocks (quoted tool output) are marked and must not be edited: they are
transcripts of actual runs, and editing them would make the page dishonest.

Run:  python3 make_manuscript.py            (writes memento-manuscript.org)
"""
import html as _html
import os
import re
import textwrap
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "index.html")
OUT = os.path.join(HERE, "memento-manuscript.org")

VOID = {"br", "img", "meta", "link", "hr", "input"}
INLINE = {"em", "strong", "code", "a", "s", "sup", "sub", "span", "br", "abbr"}


class Node:
    def __init__(self, tag, attrs=None):
        self.tag, self.attrs, self.kids = tag, dict(attrs or []), []


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs)
        self.stack[-1].kids.append(n)
        if tag not in VOID:
            self.stack.append(n)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].kids.append(data)


# ---------------------------------------------------------------- inline text
def inline(node):
    if isinstance(node, str):
        return node
    inner = "".join(inline(k) for k in node.kids)
    t, a = node.tag, node.attrs
    if t == "em":
        return f"/{inner.strip()}/" if inner.strip() else ""
    if t == "strong":
        return f"*{inner.strip()}*" if inner.strip() else ""
    if t == "code":
        return f"={inner.strip()}=" if inner.strip() else ""
    if t == "s":
        return f"+{inner.strip()}+" if inner.strip() else ""
    if t == "sup":
        return f"^{{{inner.strip()}}}"
    if t == "sub":
        return f"_{{{inner.strip()}}}"
    if t == "br":
        return "\u2028"
    if t == "a":
        href = a.get("href", "")
        # relative hrefs must become file: links -- a bare path is a FUZZY link in
        # Org and aborts the HTML export ("Unable to resolve link")
        if not re.match(r"^(https?:|mailto:|#)", href):
            href = "file:" + href
        return f"[[{href}][{inner.strip()}]]"
    if t == "span" and "badge" in a.get("class", ""):
        return f" [badge:{inner.strip()}]"
    return inner


def flow(node):
    """inline text of a block, whitespace-normalised, non-breaking spaces flattened"""
    s = inline(node).replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s)              # source line breaks are not content
    s = s.replace("\u2028", "\n")           # only <br> survives as a line break
    return s.strip()


def wrap(s, indent=""):
    out = []
    for para in s.split("\n"):
        if not para.strip():
            continue
        out.append(textwrap.fill(para.strip(), 88, initial_indent=indent,
                                 subsequent_indent=indent,
                                 break_long_words=False, break_on_hyphens=False))
    return "\n".join(out)


def raw_text(node):
    if isinstance(node, str):
        return node
    return "".join(raw_text(k) for k in node.kids)


# ---------------------------------------------------------------- block emit
def emit(node, w):
    for k in node.kids:
        if isinstance(k, str):
            continue
        t, a = k.tag, k.attrs
        if t == "h2":
            anchor = a.get("id")
            w(f"\n* {flow(k)}\n")
            if anchor:
                w(":PROPERTIES:\n:CUSTOM_ID: %s\n:END:\n" % anchor)
        elif t in ("h1", "h3"):
            w(f"\n** {flow(k)}\n")
        elif t == "p":
            s = flow(k)
            if s:
                w(wrap(s) + "\n\n")
        elif t == "ul":
            for li in k.kids:
                if not isinstance(li, str) and li.tag == "li":
                    w(wrap(flow(li), "").replace("\n", "\n  ").join(["- ", "\n"]))
            w("\n")
        elif t == "pre":
            w("# VERBATIM -- transcript of an actual run; do not edit the block below.\n")
            w("#+begin_example\n" + raw_text(k).strip("\n") + "\n#+end_example\n\n")
        elif t == "table":
            emit_table(k, w)
        elif t == "figure":
            cap = [x for x in k.kids if not isinstance(x, str) and x.tag == "figcaption"]
            w("# FIGURE (kept in index.html; caption is editable)\n")
            if cap:
                w(wrap("*Caption:* " + flow(cap[0])) + "\n\n")
        elif t == "div":
            cls = a.get("class", "")
            if cls:
                w(f"# --- div.{cls} ---\n")
            emit(k, w)
        elif t in ("main", "header", "section", "blockquote"):
            emit(k, w)


def emit_table(tbl, w):
    rows = [r for r in tbl.kids if not isinstance(r, str) and r.tag == "tr"]
    if not rows:
        return
    head = [flow(c) for c in rows[0].kids
            if not isinstance(c, str) and c.tag in ("th", "td")]
    is_head = any(not isinstance(c, str) and c.tag == "th" for c in rows[0].kids)
    body = rows[1:] if is_head else rows
    w("# TABLE -- one bullet per row; the sub-bullets are the columns.\n")
    for r in body:
        cells = [flow(c) for c in r.kids if not isinstance(c, str) and c.tag in ("th", "td")]
        if not cells:
            continue
        w(wrap("- " + cells[0]).replace("\n", "\n  ") + "\n")
        for i, c in enumerate(cells[1:], start=1):
            label = head[i] if is_head and i < len(head) else f"col {i + 1}"
            w(wrap(f"- /{label}:/ {c}", "  ").replace("\n" + " " * 2, "\n" + " " * 4) + "\n")
    w("\n")


# ---------------------------------------------------------------- go
src = open(SRC, encoding="utf-8").read()
body = re.search(r"<main>(.*)</main>", src, re.S).group(1)
tree = Tree()
tree.feed(body)

chunks = []
emit(tree.root, chunks.append)
text = "".join(chunks)
text = re.sub(r"\n{3,}", "\n\n", text)

title = re.search(r"<title>(.*?)</title>", src, re.S)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(f"""#+TITLE: {_html.unescape(title.group(1)).strip() if title else 'Memento for Mimo'} — manuscript
#+SUBTITLE: Editing surface for index.html — edit here, then apply back
#+OPTIONS: toc:2 num:nil
#+STARTUP: content

# Generated from index.html by make_manuscript.py.  This file is the place to
# EDIT the words; index.html is the artifact that gets deployed.  The coupling is
# loose and manual on purpose: no build step, no templating, the page keeps its
# own design.  After editing here, ask Claude Code to apply the edits to
# index.html (or do it by hand), then review the page in a browser.
#
# Regenerating OVERWRITES this file.  Re-run make_manuscript.py after the page
# changes to see, via git diff, where page and manuscript have drifted apart.
#
# Markers used below:
#   [badge:...]   an epistemic badge on the page
#   # VERBATIM    quoted tool output -- do NOT edit; it is a transcript
#   # TABLE       a page table, flattened to bullets (row, then columns)
#   # FIGURE      an image kept in index.html; only the caption is editable
{text}""")
print(f"wrote {OUT} ({os.path.getsize(OUT)} bytes)")
