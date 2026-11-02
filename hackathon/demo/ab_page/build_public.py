"""Public build of the blind A/B page for static hosting (Vercel).
Usage: build_public.py SUPABASE_URL PUBLISHABLE_KEY [OUT_DIR] [--table NAME]   (table default featherlm_ab_votes)
Writes OUT_DIR/index.html (the Artifact page with a full document head and window.FLM_REMOTE set, so picks go to the
insert-only Supabase table `ab_votes`) and OUT_DIR/pairs.json. The key must be the project's publishable/anon key:
row-level security lets it insert votes and nothing else.
"""
import json, os, sys

here = os.path.dirname(os.path.abspath(__file__))
HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="robots" content="noindex">'
        '<style>:root{padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}'
        'body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>')


def build(url: str, key: str, out: str, table: str = "featherlm_ab_votes") -> str:
    page = open(os.path.join(here, "index.html"), encoding="utf-8").read()
    # the Artifact source opens with its own charset/viewport tags; the public head already has them
    page = "\n".join(l for l in page.splitlines() if not l.startswith(('<meta charset', '<meta name="viewport"')))
    cfg = f"<script>window.FLM_REMOTE = {json.dumps({'url': url.rstrip('/'), 'key': key, 'table': table})};</script>"
    html = HEAD + cfg + "</head><body>" + page + "</body></html>"
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    with open(os.path.join(out, "pairs.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(open(os.path.join(here, "pairs.json"), encoding="utf-8").read())
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    table = "featherlm_ab_votes"
    if "--table" in a:
        i = a.index("--table"); table = a[i + 1]; del a[i:i + 2]
    if len(a) < 2:
        print(__doc__); sys.exit(1)
    print("->", build(a[0], a[1], a[2] if len(a) > 2 else os.path.join(here, "public"), table))
