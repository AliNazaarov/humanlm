"""Public build of the blind A/B page for static hosting (Vercel).
Usage: build_public.py OUT_DIR [--src DIR] [--direct SUPABASE_URL PUBLISHABLE_KEY] [--table NAME]
Writes OUT_DIR/index.html (the Artifact page from DIR, default this folder, with a full document head and
window.FLM_REMOTE set) and OUT_DIR/pairs.json. Default is proxy mode: the page posts to /rest/v1/<table> on its own
site, where vercel/api/vote.js validates the rows and inserts them with a key kept in the Vercel environment, so no
key ships to readers. --direct writes a Supabase publishable key into the page instead (only for a project whose other
tables are all protected by row-level security).
Deploy: build into hackathon/demo/ab_page/vercel (set 1) and vercel/round2 (set 2, --src set2), then deploy that folder.
"""
import json, os, sys

here = os.path.dirname(os.path.abspath(__file__))
HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="robots" content="noindex">'
        '<style>:root{padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}'
        'body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>')


def build(out: str, src: str = here, url: str = "/", key: str = "proxy", table: str = "featherlm_ab_votes") -> str:
    page = open(os.path.join(src, "index.html"), encoding="utf-8").read()
    # the Artifact source opens with its own charset/viewport tags; the public head already has them
    page = "\n".join(l for l in page.splitlines() if not l.startswith(('<meta charset', '<meta name="viewport"')))
    cfg = f"<script>window.FLM_REMOTE = {json.dumps({'url': url, 'key': key, 'table': table})};</script>"
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(HEAD + cfg + "</head><body>" + page + "</body></html>")
    with open(os.path.join(out, "pairs.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(open(os.path.join(src, "pairs.json"), encoding="utf-8").read())
    return out


def main(argv: list[str]) -> int:
    a = list(argv)
    src = here
    if "--src" in a:
        i = a.index("--src"); src = os.path.abspath(a[i + 1]); del a[i:i + 2]
    table = "featherlm_ab_votes"
    if "--table" in a:
        i = a.index("--table"); table = a[i + 1]; del a[i:i + 2]
    url, key = "/", "proxy"
    if "--direct" in a:
        i = a.index("--direct"); url, key = a[i + 1], a[i + 2]; del a[i:i + 3]
    if len(a) != 1:
        print(__doc__); return 1
    print("->", build(a[0], src, url, key, table))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
