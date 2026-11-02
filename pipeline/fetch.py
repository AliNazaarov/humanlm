"""Download licence-clean Common Pile subsets (openly licensed / public domain) to /data/raw."""
import sys
from huggingface_hub import snapshot_download

SETS = sys.argv[1:] or [
    "news_filtered", "foodista_filtered", "public_domain_review_filtered",
    "cccc_filtered", "project_gutenberg_filtered",
]
for s in SETS:
    p = snapshot_download(repo_id=f"common-pile/{s}", repo_type="dataset",
                          local_dir=f"/data/raw/{s}", max_workers=4)
    print("done", s, p, flush=True)
