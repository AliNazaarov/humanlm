# Held-out set provenance audit

Audited 2026-11-02. File: `evals/heldout_pairs.jsonl` (120 rows). Read-only audit; nothing in the data was changed.

## 1. Sources and licences

No row has an empty `licence` or `url`. Dates come from joining each row's `pid` back to `data/pairs/*.jsonl` (`created` field; all 120 matched).

| Source | Rows | `licence` value in the file | Dates (`created`) | What the Common Pile card says | Card URL |
|---|---|---|---|---|---|
| cccc_filtered | 73 | `see source` (all 73) | 2013-05-18 to 2013-05-22 | "Per-document license information is available in the `license` entry of the `metadata` field"; only 537 manually verified CC domains kept | https://huggingface.co/datasets/common-pile/cccc_filtered |
| news_filtered | 21 | CC BY 4.0 (13), CC BY-SA 4.0 (8) | 2014-07-04 to 2021-06-23 | "We scrape the news sites that publish content under CC BY or CC BY-SA according to opennewswire" | https://huggingface.co/datasets/common-pile/news_filtered |
| project_gutenberg_filtered | 11 | `Public Domain` (all 11) | none recorded | Uses "all books that are 1) English and 2) marked as in the Public Domain according to the provided metadata" | https://huggingface.co/datasets/common-pile/project_gutenberg_filtered |
| public_domain_review_filtered | 11 | CC BY-SA 4.0 (all 11) | 2011 to 2019-09-17 | "We collect all articles published in the Public Domain Review under a CC BY-SA license" | https://huggingface.co/datasets/common-pile/public_domain_review_filtered |
| foodista_filtered | 4 | CC BY 3.0 (all 4) | 2011-03-23 to 2014-02-09 | "All content is licensed under CC BY" | https://huggingface.co/datasets/common-pile/foodista_filtered |

Every card also carries the same warning: licence laundering and bad metadata can give some documents the wrong licence.

Licence findings:
- **cccc (73 rows, 61%) has no concrete licence.** The card says each document carries its own licence in `metadata.license`, but `pipeline/passages.py` falls back to the string `see source` when that key is missing, and every cccc row ended up with it. So the specific CC variant (BY, BY-SA, BY-NC?) of these 73 rows is unknown from our files. The card only promises "Creative Commons" at the domain level, so BY-NC or ND domains are not ruled out by anything we hold.
- news, PDR and Foodista values agree with their cards. Gutenberg `Public Domain` is hard-coded by `passages.py` for `kind == "old"` (it was not read from metadata), but it matches the card's inclusion rule.
- 8 of the 21 news rows come from domains the card does not name: educeleb.com (6) and libertytvradio.com (2). The other 13 come from altnews.in, factly.in and freedom.press, which it does name. The card says the outlets "include" its list, so the list may simply be incomplete. Still, those two domains are unverified.
- Domains worth a second look inside cccc: pressreleasepoint.com (4 rows, company press releases), quotationsbook.com (1 row, a quotation from another author), ohloh.net (1 row, auto-filled site template text, see section 3).
- BY and BY-SA rows (36 outside cccc) carry attribution, and the BY-SA ones share-alike, obligations if the text is redistributed (for example in the report or demo).

## 2. Spot-check (12 rows, `random.Random(0).sample(rows, 12)`)

One GET per URL, 15 s timeout, 1 s between requests, a browser-like User-Agent. cccc URLs have no scheme, so `http://` was added. "Windows found" = how many of the row's 8-word windows of `human` (lowercased, punctuation stripped) appear in the page's text with tags removed. The cited span is the middle window of the text, or the first window that matched when the middle one did not.

| id | source | HTTP | Windows found | 8-word span from `human` | On page? |
|---|---|---|---|---|---|
| ho-109 | news (freedom.press, redirected) | 200 | 83/83 | "can be served by a constructive approach to" | yes |
| ho-050 | cccc (arthritis-research.com) | 404 | 0/110 | "a new investigator funded by the canadian institutes" | page gone |
| ho-098 | news (altnews.in, redirected off /englishclone/) | 200 | 80/87 | "in the view of the protest against the" | yes (middle span did not match; page has small edits) |
| ho-114 | public_domain_review | 200 | 121/121 | "the bright tailed and modern science gives it" | yes |
| ho-054 | cccc (wikidoc.org) | 200 | 105/105 | "by paracetamol and gastrointestinal irritation caused by aspirin" | yes |
| ho-006 | cccc (appropedia.org) | 200 | 65/129 | "can absorb and convert a much higher fraction" | yes, about half the passage (page has changed) |
| ho-034 | cccc (strategywiki.org) | 403 | 0/196 | "you before falling to the ground dance idiotically" | blocked |
| ho-066 | news (freedom.press, redirected) | 200 | 136/143 | "are still facing long term legal struggles they" | yes |
| ho-063 | cccc (quotationsbook.com) | 404 | 0/76 | "as bad as having only one jacket and" | page gone |
| ho-052 | cccc (werelate.org) | 403 | 0/95 | "between the nanay river and the left bank" | blocked |
| ho-118 | cccc (ccforum.com) | 404 | 0/128 | "and nonaerated lung regions between peep and zeep" | page gone |
| ho-101 | cccc (pressreleasepoint.com) | SSL error (connection closed) | 0/84 | "credit and a 4 million term loan for" | no response |

Result: 6 of 12 pages loaded and all 6 contain the human text (4 near-verbatim, 2 partly). 3 returned 404 (two old BioMed Central journal URLs and quotationsbook), 2 returned 403 (bot blocking), 1 failed at TLS. All six that could not be checked are cccc rows from a 2013 crawl, so link rot is expected. No page contradicted the data.

## 3. Leakage check against `hackathon/data/train.jsonl`

Method: lowercase, split on `\w+`, build every 8-word window of every train message (user = AI draft, assistant = human; 5,000 rows, 1,083,354 distinct 8-grams), then intersect with each held-out `human` and `ai_draft`. Also repeated against `valid.jsonl` (200 rows).

**The guarantee does not hold.** `make_split.py` keeps held-out and train apart only by `pid` and by an exact md5 of `human`. It runs its 8-gram filter against the dev/trick/frontier eval files, never between held-out and train. Measured:

- 22 of 120 held-out rows share at least one 8-gram with train (`human` or `ai_draft`); 10 of them on the `human` side.
- Material overlaps on the `human` side (share of the row's own 8-grams also found in train):
  - ho-037 (cccc, ohloh.net): 84/96. Ohloh "factoids" template text with the project name changed; it appears in several train rows (204, 1814, 1933, 2293, 2323...).
  - ho-088 (cccc, uofmhealth.org): 47/97. About half the passage is the site's CC-licence footer, which also appears in train row 810.
  - ho-093 (cccc, perseus.tufts.edu): 44/97. The Perseus CC-licence footer is in the passage and in about 5 train rows.
  - ho-098 (news, altnews.in): 27/87. Train row 4701 is another Alt News article that reuses the same "old clip of a mock drill conducted by Khunti, Jharkhand police... reverse-search of one of its keyframes" sentences.
- Minor `human` overlaps (1 to 6 8-grams): ho-042, ho-044, ho-045, ho-069, ho-073, ho-081. These are fact-check stock phrases ("hence the claim made in the post is"), a book title, an organisation name.
- `ai_draft` overlaps (16 rows, mostly 1 to 13 8-grams) are the generator's letter wrappers: "dear customer i hope this message finds you well", "please do not hesitate to reach out". 22 of 120 held-out drafts open or close like a letter.
- Against valid: 6 rows overlap (ho-012, 016, 037, 069, 077, 118), the same patterns.

Practical effect: about 4 held-out references (ho-037, 088, 093, 098) contain long spans the tuned model saw as targets in training, and those spans are templates or boilerplate rather than prose. Scores on those rows can be inflated. Consider dropping them or reporting results with and without them.

## 4. Is the `human` text pre-AI human writing?

Dates (from `created` in the pair files):
- cccc: all 73 between 2013-05-18 and 2013-05-22. That five-day window looks like the Common Crawl snapshot date, not the authoring date. Either way the pages existed by May 2013, before GPT-2 (2019).
- news: 2014-07-04 to 2021-06-23, all before the pipeline's 2021-07-01 cutoff. 18 of 21 are from 2019 to 2021, when GPT-3 was available through an API, but they are bylined fact-checks and local news, low risk.
- public_domain_review: 2011 to 2019-09-17. foodista: 2011 to 2014.
- gutenberg: no date field; the texts are 19th and early 20th century public-domain books (ebook ids 1159 to 18967).

I read the opening of all 120 `human` texts. None reads as machine-generated. A scan for common LLM phrases found only "in conclusion" (ho-030, a 2013 Armenian speech) and "moreover" (ho-035, an Alt News piece), both normal in context. Some rows are not good examples of skilled prose, though:
- Template or boilerplate text: ho-037 (ohloh auto-text), ho-088 and ho-093 (licence footers make up half the passage), ho-101 (press release).
- Not prose, or not English: ho-048 (Spanish), ho-013 and ho-117 (gene or package catalogue entries), ho-118 (formula with voxel maths), ho-007 (ant taxonomy key).
- Scraping artefacts: ho-021 has missing spaces ("TheUnited Nations", "commemorationof").

## Caveats

- The licence column only records what the pipeline kept. For cccc it kept nothing specific, so confirming those 73 rows needs the original `metadata.license` from the raw Common Pile files.
- The spot-check is 12 rows. 6 could not be verified (404/403/TLS), so it confirms 6 of 120 rows directly.
- "Created" is whatever the Common Pile metadata carried. For cccc it is almost certainly crawl time. A crawl date sets a latest possible writing date, not a writing date.
- The 8-gram check uses `\w+` tokens, the same tokeniser as `make_split.py`. Overlap through paraphrase is not measured.
- Not legal advice. The licence lines are quoted from the dataset cards as fetched on 2026-11-02.
