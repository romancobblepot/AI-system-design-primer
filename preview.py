#!/usr/bin/env python3
"""Local preview server for this repo: browse folders, render .md files, serve the rest."""
import html
import mimetypes
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))

PAGE = """<!doctype html>
<html><head><meta charset="utf-8">
<title>{title}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/github-markdown-css@5.5.1/github-markdown.min.css">
<style>
  body {{ margin:0; font-family: -apple-system, system-ui, sans-serif; background:#0d1117; color:#c9d1d9; }}
  header {{ padding: 14px 24px; border-bottom: 1px solid #30363d; }}
  header a {{ color:#58a6ff; text-decoration:none; }}
  header a:hover {{ text-decoration:underline; }}
  main {{ max-width: 900px; margin: 0 auto; padding: 24px; }}
  .markdown-body {{ background:#0d1117; color:#c9d1d9; }}
  ul.filelist {{ list-style:none; padding:0; }}
  ul.filelist li {{ padding:6px 0; border-bottom:1px solid #21262d; }}
  ul.filelist a {{ color:#c9d1d9; text-decoration:none; }}
  ul.filelist a:hover {{ color:#58a6ff; }}
  .meta {{ color:#8b949e; font-size:12px; float:right; }}
</style>
</head>
<body>
<header>{breadcrumb}</header>
<main>{body}</main>
</body></html>
"""


def breadcrumb_html(rel_path):
    parts = [p for p in rel_path.split("/") if p]
    crumbs = ['<a href="/">repo root</a>']
    acc = ""
    for p in parts:
        acc += "/" + p
        crumbs.append(f'<a href="{acc}">{html.escape(p)}</a>')
    return " / ".join(crumbs)


def render_dir(fs_path, rel_path):
    names = [n for n in os.listdir(fs_path) if not n.startswith(".")]
    names.sort(key=lambda n: (not os.path.isdir(os.path.join(fs_path, n)), n.lower()))
    items = []
    for name in names:
        full = os.path.join(fs_path, name)
        href = (rel_path.rstrip("/") + "/" + name) if rel_path else name
        if os.path.isdir(full):
            items.append(
                f'<li>\U0001F4C1 <a href="/{html.escape(href)}/"><b>{html.escape(name)}/</b></a></li>'
            )
        else:
            size = os.path.getsize(full)
            icon = "\U0001F4C4" if name.lower().endswith(".md") else "\U0001F4C3"
            items.append(
                f'<li>{icon} <a href="/{html.escape(href)}">{html.escape(name)}</a>'
                f'<span class="meta">{size:,} bytes</span></li>'
            )
    body = f"<h2>{html.escape('/' + rel_path if rel_path else 'repo root')}</h2><ul class='filelist'>{''.join(items)}</ul>"
    return PAGE.format(title=rel_path or "repo root", breadcrumb=breadcrumb_html(rel_path), body=body)


def render_md(rel_path):
    body = (
        '<div id="content" class="markdown-body">Loading…</div>'
        '<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>'
        "<script>"
        f"fetch('/__raw/{urllib.parse.quote(rel_path)}')"
        ".then(r => r.text())"
        ".then(md => document.getElementById('content').innerHTML = marked.parse(md));"
        "</script>"
    )
    return PAGE.format(title=rel_path, breadcrumb=breadcrumb_html(rel_path), body=body)


class Handler(BaseHTTPRequestHandler):
    def _safe_path(self, rel):
        full = os.path.realpath(os.path.join(ROOT, rel))
        if not (full == ROOT or full.startswith(ROOT + os.sep)):
            return None
        return full

    def do_GET(self):
        path = urllib.parse.unquote(urllib.parse.urlparse(self.path).path)

        if path.startswith("/__raw/"):
            rel = path[len("/__raw/"):]
            full = self._safe_path(rel)
            if not full or not os.path.isfile(full):
                self.send_error(404)
                return
            with open(full, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        rel = path.lstrip("/")
        full = self._safe_path(rel) if rel else ROOT
        if full is None or not os.path.exists(full):
            self.send_error(404)
            return

        if os.path.isdir(full):
            self._send_html(render_dir(full, rel.rstrip("/")))
        elif rel.lower().endswith(".md"):
            self._send_html(render_md(rel))
        else:
            self._send_file(full)

    def _send_html(self, content):
        data = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, full):
        with open(full, "rb") as f:
            data = f.read()
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Serving {ROOT} at http://127.0.0.1:{port}")
    server.serve_forever()
