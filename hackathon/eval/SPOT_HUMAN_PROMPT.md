# Spot-the-human prompt (hackathon/eval/spot_human.py)

Held-out ground-truth test. Per id the judge sees the real human original and one system's rewrite as
"Text 1" / "Text 2", in both orders, with no system message. Temperature 0, max_tokens 4096,
reasoning_effort none. Only the text between the markers is sent; `{{TEXT_1}}` and `{{TEXT_2}}` are
filled in a single pass. Changing anything between the markers changes the config hash, and old rows
are then refused (`--fresh` to start over).

<!-- begin:user -->
One of these two texts was written by a person; the other was rewritten by an AI. Which was written by a person? Answer on the last line: HUMAN: 1 or HUMAN: 2

Text 1:
{{TEXT_1}}

Text 2:
{{TEXT_2}}
<!-- end:user -->
