# Wispr Flow teardown (design + product), for FeatherLM

Date: 2026-11-01. Purpose: borrow the feel, never the assets. Colour and font values below were read from Wispr's live Webflow stylesheet (cdn.prod.website-files.com ... flowsite-dev.webflow.shared.11de844c4.min.css). Everything else is from the pages and press linked inline. Not logged in anywhere. Motion was inferred from CSS and page structure (8 Lottie references, ScrollTrigger-style `data-w-id` hooks, short transitions), not watched frame by frame, so treat motion notes as medium confidence.

---

## 1. Visual system

Source: [wisprflow.ai](https://wisprflow.ai), [pricing](https://wisprflow.ai/pricing), site CSS.

### Colour (named tokens in their CSS, hex read directly)

| Token | Hex | Role |
|---|---|---|
| lumen | `#ffffeb` | Page background. Warm butter cream, not white. Also text on dark. |
| lumen-dark | `#e4e4d0` | Secondary surfaces, fades, search fields |
| vast | `#1a1a1a` | Text, 2px borders, dark sections (never pure black) |
| dawn | `#f0d7ff` | Lavender. Emphasis words on dark, secondary background |
| fathom | `#034f46` | Deep green. Pricing block, dark cards (4px cream border, 40px radius) |
| (deep green 2) | `#07352f` | Dark chat bubbles, panels (12/12/12/4 radius = message bubble) |
| signal | `#ffbcf2` | Pink accent card backgrounds |
| flare | `#ff6c4c` | Coral. Errors, hot accent |
| glow | `#ffa946` | Orange accent |
| pulse | `#7f1c34` | Burgundy (error dark) |
| success green | `#34d399` | "Meeting / live" waveform |
| focus | `#2d62ff` | Focus ring only |
| border | `#1a1a1a4d` / vast | 2px solid borders, hard not soft |

Read: cream + ink + one deep green + two pastel pops (lavender, pink). Not a tech blue. Not a gradient site. Colour is used in flat blocks, one per card.

### Typography
- Headlines: **EB Garamond**, weight 400, `letter-spacing: -0.05em`, `line-height: .85`, up to 7.5rem (H1 clamps 3.5 -> 6 -> 7.5rem). Big, tight, regular-weight serif.
- Emphasis inside headlines: the `<em>` word is switched to lavender (`#f0d7ff`) on dark sections and kept upright (font-style normal). Example copy pattern: "4x faster _than typing_", "Your voice _stays yours._", "Good _questions._" The italic-ish word is the human beat.
- Body / UI: **Figtree** (friendly geometric sans), 1rem to 1.5rem scale.
- Also loaded: Inter, **IBM Plex Mono**, JetBrains Mono, Monaspace Neon (used in the technical/use-case blocks and status labels).
- Pairing logic: literary serif says "writing", clean sans says "tool". This is the single biggest reason it feels designed.

### Shape, spacing, motion
- Radii are generous and consistent: 0.5rem / 1rem (most used) / 1.5-2.5rem cards / up to 5rem section corners. Section blocks look like rounded paper sheets stacked on cream.
- Hard 2px ink borders on cream (sticker / paper-cut feel) instead of drop shadows.
- Huge vertical padding (6-10rem sections).
- Motion: transitions are short (0.2s colour, 0.2-0.3s transform/opacity), no spring theatrics in CSS. The showpiece motion lives in Lottie/demo animations, not in the chrome.

### Illustration / imagery style
- Mostly product-in-context: live UI mockups of the Flow bar, chat bubbles, "Add to vocabulary" dialog with names (Sarah, Aditya, Dillon), status chips ("Filler identified", "Correction identified", "Repetition identified", "Cleaning up..."). The product demonstrating the product.
- Real headshots + company logos for proof. Pastel flat colour blocks behind. No stock photos of laptops, no 3D blobs.

### Copy tone
- Short, confident, a bit playful. "Don't type, just speak." "You have a way with words. Now, two." "Good questions." About page: "make interacting with your devices as effortless as talking to a close friend." Benefit first, numbers second (4x, 45 vs 220 wpm).

### Landing page, section by section (as fetched 2026-11-01)
1. Top banner: Notetaker launch + "raised $81M to build the Voice OS" rotating line (stale vs the $280M raise, a reminder that banners rot). Button: Try for free.
2. Hero: "Don't type, just speak." Subhead: turns speech into clear, polished writing in every app. CTA Download for free. Four platform icons (Mac, Windows, iPhone, Android). Animated dictation demo: rambling in, clean message out. Logo strip: Microsoft, Amazon, Notion, Klarna, Groupon, Vercel, Mercury.
3. Speed proof: "4x faster than typing." Keyboard 45 wpm vs Flow 220 wpm, side-by-side demo.
4. How it works: "Speak at the speed you think, in every app, on every device." Three cards: Speak naturally / Edits as you speak / Use it anywhere (no plugins). Animated step demo with the status chips.
5. Tone: "Built around how you work, not how we think you should." One lunch-invite sentence rendered Formal, Casual, Very casual (capitalisation and punctuation relax).
6. Vocabulary + language: Add-to-vocabulary dialog, mixed-language demo.
7. Four-card grid: 100+ languages, learns your vocabulary, snippets with spoken shortcut, "make Flow sound like you" with per-app styles.
8. Privacy: "Your voice stays yours." SOC 2 Type II, HIPAA, ISO 27001 badges.
9. Social proof: "From the first people to use it." Quotes (Steven Bartlett, Alex Lieberman, Elena Verna, Dave Gilboa, Fast Company, SlashGear) + two case-study cards (Bartlett: 90% faster message output, 2 extra productive hours/day; Clay: 20% more customer calls/day, ~$3.08M est. annual savings).
10. FAQ: "Good questions." (compat, accents, noise, pricing, free tier 2,000 words/week).
11. Close: "You have a way with words. Now, two." Dictation + Notetaker in one free app. CTA again.
12. Footer + "Talk 4x faster" app card.

Rhythm: claim -> demo -> proof, repeated. Every section has one moving demo and one number or name.

---

## 2. Product mechanics

Sources: [docs: navigating the app](https://docs.wisprflow.ai/articles/5096240724-navigating-the-wispr-flow-app-desktop-ios-and-android), [Command Mode doc](https://docs.wisprflow.ai/articles/4816967992-how-to-use-command-mode), [pricing](https://wisprflow.ai/pricing), [search summary of reviews](https://letterly.app/blog/wispr-flow-review/).

- **Works everywhere:** system-wide, any text field, "no plugins." Desktop = hold/tap a hotkey (reviews say Fn on Mac; remappable in Settings > General). Dictation appears in the focused app via the **Flow Bar** (small floating pill; hidden by default on new desktop installs, toggle in Settings > System). Mobile: iPhone **Flow Keyboard**, Android **Flow Bubble**.
- **Hub** (Mac/Windows main window): Home (searchable transcript history by date, word count, shortcut, stats), Meetings, Dictionary, Snippets, Settings.
- **Cleanup as you speak:** removes filler, handles mid-sentence corrections and repetition, punctuates, formats. The landing page literally shows these as status chips.
- **Personal dictionary:** names, jargon, acronyms; auto-add option; shared dictionary on team plans.
- **Snippets:** spoken shortcut expands to saved text.
- **Styles / "sounds like you":** tone per app category (personal messages, work messages, email, other), levels Formal / Casual / Very casual. Mostly punctuation and casing control, not true voice cloning. Reviews say desktop English first, now a Style tab on iPhone.
- **Context awareness:** reads surrounding app content to spell names and format correctly. This is the privacy flashpoint (below).
- **Command Mode (important for FeatherLM):** [highlight text, hold shortcut, speak a command, release; Flow replaces the selection](https://docs.wisprflow.ai/articles/4816967992-how-to-use-command-mode). Without a selection it generates inline. Paid plan/trial, Settings > Experimental. In apps without write-back (e.g. Google Docs) it shows a popup to copy. This is exactly the "rewrite selected text" primitive, but driven by voice and generic instructions, not by a model of your style.
- **Notetaker:** meeting notes, summaries, action items (Mac/Windows).
- **Onboarding:** sources disagree. One says it asks your use case then demos in that context; one 2026 test calls it long with a broken final mic test. Not verified first-hand (I did not install or log in).
- **Languages:** 100+, auto-detect. **Platforms:** Mac, Windows, iOS, Android (Android launched Feb 2026).
- **Privacy:** SOC 2 Type II, HIPAA, ISO 27001 claimed. Privacy Mode / zero retention enforced on enterprise. A viral Feb 2026 Reddit thread alleged screenshots and keystroke logging for context awareness; sources conflict and the company response is unclear ([summary](https://www.doolpa.com/article/wispr-flow), [dictaflow take](https://dictaflow.io/blog/wispr-flow-trust-gap-viral-reddit-psa-2026.html)). Lesson: context-hungry features need loud, specific consent.

### Pricing (from [pricing page](https://wisprflow.ai/pricing))
| Tier | Price | Notes |
|---|---|---|
| Free | $0 | Limited words/week (FAQ says 2,000), dictionary + snippets, limited Notetaker |
| Pro | $15/user/mo, $12 annual | Unlimited dictation, shared dictionary, team workspace; 50% off for students/educators |
| Growth | ~$23-33 monthly view, ~$18-26 annual (page ambiguous) | SSO/SAML, HIPAA BAA, admin controls |
| Enterprise | Custom, annual | SCIM, audit logs, MDM, SLAs |
No free trial advertised on the page; free tier needs no card.

---

## 3. Growth

Sources: [TechCrunch, Aug 2026](https://techcrunch.com/2026/08/17/wispr-raises-280m-at-2b-valuation-as-it-looks-beyond-dictation/), [Reworked](https://www.reworked.co/ai-platforms/wispr-hits-2b-valuation-launches-canto-voice-model/), [AI Weekly](https://aiweekly.co/node/10188), [Bloomberg May 2026](https://www.bloomberg.com/news/articles/2026-05-12/ai-dictation-startup-wispr-in-funding-talks-at-2-billion-value), [Ground News on Series A](https://ground.news/article/wispr-flow-raises-30m-from-menlo-ventures-for-its-ai-powered-dictation-app), [Business Today on founder](https://www.businesstoday.in/technology/story/who-is-tanay-kothari-the-indian-origin-founder-betting-on-a-voice-first-future-with-wispr-flow-517860-2026-02-25).

- **Funding:** Series A $30M (June 2025, led by Menlo, with NEA, 8VC). $25M (Nov 2025, led by Notable Capital; $81M total then). **Series B $280M at $2B valuation, led by Menlo (Aug 2026), $361M total.** New investors: Acrew, Forerunner, Goodwater, Peak XV, Together Fund, PLUS Capital. Returning: Notable, NEA, Neo, 8VC, MVP.
- **Founders:** Tanay Kothari (CEO) and Sahaj Garg, Stanford; began as a neurotech/brain-interface hardware startup, pivoted to Flow in 2024. Jarvis / Iron Man origin story used in brand.
- **Numbers (company claims, not audited):** in 270 Fortune 500 companies as of Jan 2026, ~125 new enterprise customers/week; 40% MoM user and ARR growth (Reworked); Android waitlist 375,000 verified signups in under a week; founders claim millions of consumers and 100,000 businesses. ARR is not officially stated; third-party estimate ~$10M Oct 2025 (Latka, weak source). No absolute revenue in TechCrunch.
- **How they market:** founder-led and hands-on early (reported 500+ early users onboarded personally over calls), word of mouth and "viral moments," heavy creator/operator endorsement on the site (Steven Bartlett, Alex Lieberman, Elena Verna), enterprise logo strip, case studies with hard numbers, a "4x faster" single claim repeated everywhere. I found no verified public referral-program details. Expanding GTM in India and UK.
- **Product bets:** Canto, a 2B-parameter proprietary speech model (claims error rate from >30% to ~5-10% in hard audio); key internal metric "zero edit rate" (share of output accepted untouched); Notetaker; hardware (Oasis ring); Wispr Interface Labs.
- **Competitors named by TechCrunch:** Willow, Monologue, Aqua, Superwhisper; Granola, Fireflies, Read AI for notes.

**Takeaway worth stealing:** "zero edit rate" as the north-star metric. For FeatherLM the equivalent is "sent without edits" and "did people notice it was AI".

---

## 4. A "Wispr Flow for human writing"

Core inversion: Wispr makes *input* faster. FeatherLM makes *output* sound like a specific person. Their "Styles" are three tone presets; yours is a learned voice model with evidence. That gap is the product.

### Concept A: "Your voice, anywhere" system-wide rewrite (closest analogue, recommended first)
- Desktop + iOS/Android keyboard. Select text (or an AI draft pasted in), hit a hotkey, a small pill appears near the cursor, shows 2-3 rewrites in YOUR voice, Tab to accept. Works in Gmail, Slack, Docs, X, LinkedIn, IDE comments.
- Voice built from your own sent writing (emails, posts, DMs, exports), per-context (LinkedIn vs DMs vs cold email) like Wispr's per-app styles, but learned not preset.
- Hero metric surfaced in-product: "AI-ness" meter and "sounds like you" score; weekly "zero edit rate".
- Why first: smallest install, daily frequency, instantly demoable, direct analogue to proven Command Mode.

### Concept B: The writing surface ("a page that refuses slop")
- A calm single-column editor (cream paper, serif) where you paste or dictate a messy draft and it comes out as you. Side margin shows *why* each change: "removed 'delve'", "restored your short sentences", "your usual opener". Slop tells highlighted like spellcheck.
- Voice-in is a feature: reuse Wispr-style dictation-to-clean as input, but anchored to your voice profile. Export to email, X, LinkedIn.
- Why: the place to show taste, trust and explainability; best for content/marketing and the demo video.

### Concept C: Browser extension + API
- Extension: inline "make it sound like me" chip in Gmail, LinkedIn, X, Substack, Notion on web; also detects AI-sounding text in drafts and warns before send.
- API / SDK: `POST /rewrite {text, voice_id}` and "voice as a prompt" for agent builders so their agents' emails and posts don't read as AI. B2B revenue: sales teams, ghostwriters, agencies with many voices.
- Why: distribution and revenue (teams), and a moat of per-voice models.

Suggested order: A (wedge) -> C extension (distribution) -> B (brand showcase) -> API (B2B).

### Design moves to BORROW
1. Warm paper background instead of white (cream family, pick your own hue). It signals "writing", not "software".
2. Serif display + clean sans body, big, tight tracking, regular weight. Your product is about prose, so a serif headline is on-brand.
3. One highlighted word per headline in an accent colour (their lavender italic-feel). Gives a human beat.
4. Hard 1-2px ink borders and flat colour cards, no shadows or glass.
5. The product demonstrates itself: before/after in the hero, status chips that narrate what changed. Yours: "removed 3 AI tells", "matched your rhythm".
6. Claim -> demo -> proof rhythm with a single repeated number. Yours should be measurable (e.g. "reads as human to X% of readers" once you have a real eval, never invent it).
7. Plain, short, slightly playful copy. FAQ titled with a human line.
8. Per-surface styles (their per-app tone) -> your per-channel voice.
9. Logo strip + named-person quotes + 2 case studies with hard numbers.
10. Zero-edit-rate style north-star metric, shown to the user.

### Design moves to AVOID
1. Same palette combo (cream + lavender + deep green + pink) and the same EB Garamond + Figtree pair. Pick a distinct pair and hue so it never reads as a clone. Do not reuse their logos, wave mark, Lottie demos, copy lines ("Don't type, just speak", "way with words").
2. Voice-first positioning. Their moat is audio; yours is style fidelity. Do not call it dictation.
3. Hiding privacy behind a toggle. Their screenshot/keystroke backlash shows that anything that reads your writing needs plain-language, up-front consent and local-first or zero-retention by default. Your product ingests a person's private writing, so this is existential.
4. Preset tone sliders as the whole story (Formal/Casual). That is the "AI style" you are fighting. Use evidence from the user's own text.
5. Banner rot (their top bar still says $81M). Keep marketing claims in one source of truth.
6. Overpromising accuracy numbers; their Canto error-rate claims are self-reported. Publish a method.
7. Long onboarding with a late failing step. Make first win under 60 seconds: paste one AI paragraph, see it rewritten in a sample voice, then ask for the user's writing.

### Open items for the user to decide
- Voice source for v1: paste samples vs connect Gmail/X export.
- Name/brand hue and type pair (needs the lookbook step per your preference: show 3+ options before building).
- Confirm local-first vs cloud inference, since it drives the privacy copy.

### Confidence notes
- High: colours, fonts, section structure, pricing, funding amounts (multiple outlets agree).
- Medium: motion (inferred from CSS and Lottie count), onboarding, Style behaviour (third-party reviews).
- Low / unverified: ARR, user counts (company claims or estimates), referral program, keystroke/screenshot allegations.
