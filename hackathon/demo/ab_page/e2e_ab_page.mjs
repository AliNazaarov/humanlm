// End-to-end test of the blind A/B page (Playwright, Node). Serves index.html + pairs.json wrapped in the same
// head the Artifact publish adds, then walks the reader journey at phone and desktop size, light and dark.
// Usage: node hackathon/demo/ab_page/e2e_ab_page.mjs [--shots DIR]
//   Needs the `playwright` package: PLAYWRIGHT_MODULE=<path to node_modules/playwright/index.js> if not resolvable.
// Checks: no sideways scroll; vote buttons >= 44 px; the stored pick is the side the reader saw; Enter on a focused
// vote button records nothing extra; reload resumes the ballot; an old-version ballot is never resumed; each reader
// gets PER_READER (5) of the 20 pairs; the tally sums to 5; the vote code has 20 letters, the 5 stored picks and "-"
// elsewhere; text contrast >= 4.5:1 (3:1 for large text).
// Public mode (window.FLM_REMOTE, as build_public.py injects): every pick and reason change is POSTed as one row to a
// local stand-in for the Supabase REST insert; rows survive failed inserts (queued in localStorage, retried) and are
// neither lost nor duplicated; with the server down the done screen falls back to the vote code.
import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const shots = args.includes("--shots") ? args[args.indexOf("--shots") + 1] : fs.mkdtempSync(path.join(os.tmpdir(), "ab-e2e-"));
fs.mkdirSync(shots, { recursive: true });
const mod = process.env.PLAYWRIGHT_MODULE ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : "playwright";
const pw = await import(mod);
const chromium = pw.chromium || pw.default.chromium;  // CommonJS package: named export may sit on default

const PER_READER = 5, ALL_PAIRS = 20, KEY = "test-key";
const SKELETON = '<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light;padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style></head><body>';
const source = fs.readFileSync(path.join(here, "index.html"), "utf8");
const page_html = SKELETON + source + "</body></html>";
const pairs = fs.readFileSync(path.join(here, "pairs.json"), "utf8");
const PAIRS = JSON.parse(pairs).pairs;
const VERSION = JSON.parse(pairs).meta.version;

// Stand-in for Supabase's REST insert. failLeft: answer 500 to that many requests; failAll: answer 500 to all.
// A 500 stores nothing, so every accepted row should appear exactly once.
const remote = { reqs: [], rows: [], failLeft: 0, failAll: false, delay: 150 };
const server = http.createServer((req, res) => {
  if (req.method === "POST" && req.url.startsWith("/rest/v1/ab_votes")) {
    let body = "";
    req.on("data", (c) => (body += c));
    req.on("end", () => {
      const fail = remote.failAll || remote.failLeft > 0;
      if (remote.failLeft > 0) remote.failLeft--;
      let rows = null; try { rows = JSON.parse(body); } catch {}
      remote.reqs.push({ headers: req.headers, rows, status: fail ? 500 : 201 });
      if (!fail && Array.isArray(rows)) remote.rows.push(...rows);
      // A little latency, so picks made while an insert is in flight are exercised.
      setTimeout(() => { res.writeHead(fail ? 500 : 201, { "content-type": "application/json" }); res.end(fail ? '{"message":"test failure"}' : ""); }, remote.delay);
    });
    return;
  }
  if (req.url.split("?")[0].endsWith("/pairs.json")) { res.writeHead(200, { "content-type": "application/json" }); return res.end(pairs); }
  // /public/: the page with window.FLM_REMOTE set before its content, as build_public.py does.
  const html = req.url.startsWith("/public/")
    ? SKELETON + `<script>window.FLM_REMOTE = ${JSON.stringify({ url: ORIGIN, key: KEY })};</script>` + source + "</body></html>"
    : page_html;
  res.writeHead(200, { "content-type": "text/html; charset=utf-8" }); res.end(html);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;
const URL_ = ORIGIN + "/";

const failures = [];
const check = (ok, what) => { if (!ok) failures.push(what); console.log(`${ok ? "ok  " : "FAIL"} ${what}`); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const LETTER = { a: "a", b: "b", tie: "t" };
// The vote code letters the page should write: one per pid over all 20 pairs, "-" where this reader has no pick.
const codeFor = (picks) => PAIRS.map((p) => p.pid).sort((x, y) => x - y).map((pid) => LETTER[picks[pid]?.pick] || "-").join("");

// WCAG contrast of every visible text node against its first opaque ancestor background.
const CONTRAST = () => {
  const lum = (c) => { const [r, g, b] = c.map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const rgb = (s) => (s.match(/[\d.]+/g) || []).map(Number);
  const bgOf = (el) => { for (let e = el; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor); if (c.length >= 3 && (c[3] === undefined || c[3] > 0.9)) return c.slice(0, 3); } return [255, 255, 255]; };
  const bad = [];
  for (const el of document.querySelectorAll("body *")) {
    if (!el.offsetParent && getComputedStyle(el).position !== "fixed") continue;
    const own = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    if (!own) continue;
    const st = getComputedStyle(el);
    const fg = rgb(st.color).slice(0, 3), bg = bgOf(el);
    const [a, b] = [lum(fg), lum(bg)].sort((x, y) => y - x);
    const ratio = (a + 0.05) / (b + 0.05);
    const large = parseFloat(st.fontSize) >= 24 || (parseFloat(st.fontSize) >= 18.66 && +st.fontWeight >= 700);
    if (ratio < (large ? 3 : 4.5)) bad.push(`${el.tagName.toLowerCase()}#${el.id}.${el.className} "${el.textContent.trim().slice(0, 30)}" ${ratio.toFixed(2)}`);
  }
  return bad;
};
// The stored state: current ballot id, its record, and the remote queue.
const STATE = () => { const s = JSON.parse(localStorage.getItem("ab-read-v1") || "{}"); return { s, ballot: s.ballot, b: s.local?.ballots?.[s.ballot], queue: s.queue }; };
const BOOTED = () => !/^(Loading|Connecting)/.test(document.getElementById("status").textContent);

const browser = await chromium.launch();
for (const [name, opts] of [
  ["phone-light", { viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true, colorScheme: "light" }],
  ["phone-dark", { viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true, colorScheme: "dark" }],
  ["desktop-light", { viewport: { width: 1280, height: 860 }, colorScheme: "light" }],
  ["desktop-dark", { viewport: { width: 1280, height: 860 }, colorScheme: "dark" }],
]) {
  console.log(`\n== ${name}`);
  const ctx = await browser.newContext(opts);
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  // An unfinished ballot from an older pairs version must be kept but never resumed.
  await page.addInitScript(() => {
    if (!sessionStorage.getItem("seeded")) {
      sessionStorage.setItem("seeded", "1");
      localStorage.setItem("ab-read-v1", JSON.stringify({ ballot: "bOLD", local: { ballots: { bOLD: { version: "0000000000000000", picks: { "1": { pick: "a", first: "a" } } } } } }));
    }
  });
  await page.goto(URL_);
  await page.waitForFunction(() => document.getElementById("count").textContent.includes("pairs"));
  await page.waitForFunction(BOOTED);
  const W = () => page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]);
  let [sw, cw] = await W(); check(sw <= cw, `${name}: intro has no sideways scroll (${sw} <= ${cw})`);
  check((await page.textContent("#start")).trim() === "Start reading", `${name}: old-version ballot is not offered for resume`);
  const introLabel = (await page.textContent("#intro .label")).trim();
  check(/\b5 pairs\b/.test(introLabel), `${name}: intro label says 5 pairs ("${introLabel}")`);
  await page.screenshot({ path: path.join(shots, `${name}-1-intro.png`), fullPage: true });
  let bad = await page.evaluate(CONTRAST); check(!bad.length, `${name}: intro text contrast ${bad.length ? bad.join(" | ") : "AA"}`);

  await page.click("#start");
  await page.waitForSelector("#pairView:not([hidden])");
  check(/Pair 1 of 5\b/.test(await page.textContent("#pairNo")), `${name}: pair counter reads "Pair 1 of 5"`);
  check((await page.locator("#ticks i").count()) === PER_READER, `${name}: progress shows ${PER_READER} ticks`);
  for (const id of ["vA", "vT", "vB"]) {
    const bb = await page.locator(`#${id}`).boundingBox();
    check(bb && bb.height >= 44 && bb.width >= 44, `${name}: #${id} tap target ${bb && Math.round(bb.width)}x${bb && Math.round(bb.height)} >= 44`);
  }
  // The first rewrite starts above the fixed vote bar.
  const [sideTop, barTop] = await page.evaluate(() => [document.getElementById("sideA").getBoundingClientRect().top, document.getElementById("bar").getBoundingClientRect().top]);
  check(sideTop < barTop - 60, `${name}: rewrite A visible above the vote bar (${Math.round(sideTop)} < ${Math.round(barTop)})`);
  [sw, cw] = await W(); check(sw <= cw, `${name}: pair view has no sideways scroll`);
  await page.screenshot({ path: path.join(shots, `${name}-2-pair.png`) });

  // Bias guards: no side letter in the placeholder, the draft starts folded on every device.
  const ph = await page.getAttribute("#why", "placeholder");
  check(!/\b[AB]\b/.test(ph), `${name}: reason placeholder names no side ("${ph}")`);
  check(!(await page.evaluate(() => document.getElementById("draftBox").open)), `${name}: draft folded by default`);
  // The reason field stays clear of the fixed vote bar at full scroll.
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(150);
  const [whyBottom, barTop2] = await page.evaluate(() => [document.getElementById("why").getBoundingClientRect().bottom, document.getElementById("bar").getBoundingClientRect().top]);
  check(whyBottom <= barTop2, `${name}: reason field not covered by the vote bar (${Math.round(whyBottom)} <= ${Math.round(barTop2)})`);
  await page.evaluate(() => window.scrollTo(0, 0));

  // Click B, then press Enter while the B button keeps focus: one pick only, on pair 1.
  const shownB = await page.textContent("#textB");
  await page.click("#vB");
  await page.keyboard.press("Enter");
  const st1 = await page.evaluate(() => { const s = JSON.parse(localStorage.getItem("ab-read-v1")); return { s, b: s.local.ballots[s.ballot] }; });
  const pidsPicked = Object.keys(st1.b.picks);
  check(pidsPicked.length === 1, `${name}: one click + Enter records exactly one pick (${pidsPicked.length})`);
  check(st1.b.version === VERSION, `${name}: new ballot carries pairs version ${VERSION}`);
  check(st1.b.ui === 3 && st1.b.vw > 0, `${name}: ballot records page version and viewport width (ui ${st1.b.ui}, vw ${st1.b.vw})`);
  check(!!st1.s.local.ballots.bOLD, `${name}: old-version ballot kept in storage`);
  const pk = st1.b.picks[pidsPicked[0]];
  const pair = PAIRS.find((p) => String(p.pid) === pidsPicked[0]);
  check(pair[pk.pick] === shownB, `${name}: stored pick is the text the reader saw as B`);
  check(/Pair 2 of 5\b/.test(await page.textContent("#pairNo")), `${name}: Enter advanced to pair 2`);

  // Moving to a new pair never animates the previous pick's highlight onto it.
  await page.keyboard.press("2");
  const dur = await page.evaluate(() => { document.getElementById("next").click(); return getComputedStyle(document.getElementById("sideB")).transitionDuration; });
  check(/^0s(, 0s)?$/.test(dur), `${name}: no highlight transition on a new pair (${dur})`);
  await page.keyboard.press("ArrowLeft"); await page.keyboard.press("Enter");  // back to pair 2, unchanged, then on to pair 3
  const st2 = await page.evaluate(STATE);
  check(Object.keys(st2.b.picks).length === 2, `${name}: 2 picks after pairs 1-2 (${Object.keys(st2.b.picks).length})`);
  check(/Pair 3 of 5\b/.test(await page.textContent("#pairNo")), `${name}: back + Enter lands on pair 3`);

  // One more by keyboard (pair 3), then reload: the page offers to continue at pair 4.
  await page.keyboard.press("0"); await page.keyboard.press("Enter");
  await page.reload();
  await page.waitForFunction(() => document.getElementById("count").textContent.includes("picked"));
  check(/^3 \/ 5 picked$/.test((await page.textContent("#count")).trim()), `${name}: reload shows 3 / 5 picked ("${(await page.textContent("#count")).trim()}")`);
  check((await page.textContent("#start")).includes("Continue"), `${name}: reload offers to continue`);
  await page.click("#start");
  check(/Pair 4 of 5\b/.test(await page.textContent("#pairNo")), `${name}: resumes at the first unanswered pair (pair 4)`);
  check((await page.textContent("#next")).trim() === "Next pair", `${name}: pair 4 button reads "Next pair"`);
  await page.keyboard.press("1"); await page.keyboard.press("Enter");
  check((await page.textContent("#next")).trim() === "Finish", `${name}: the last pair's button reads "Finish"`);
  await page.keyboard.press("2"); await page.keyboard.press("Enter");
  await page.waitForSelector("#done:not([hidden])");

  const done = await page.evaluate(() => {
    const s = JSON.parse(localStorage.getItem("ab-read-v1")); const b = s.local.ballots[s.ballot];
    const nums = [...document.querySelectorAll("#legend span")].map((e) => +(e.textContent.match(/ (\d+) \(/) || [0, 0])[1]);
    return { ballot: s.ballot, picks: b.picks, finished: !!b.finished, tally: nums.reduce((x, y) => x + y, 0), code: document.getElementById("voteCode").textContent,
             codeShown: !document.getElementById("codeBox").hidden, title: document.getElementById("doneTitle").textContent,
             tallyLabel: document.getElementById("tallyLabel").textContent };
  });
  check(done.finished && Object.keys(done.picks).length === PER_READER, `${name}: ballot finished with ${PER_READER} picks (${Object.keys(done.picks).length})`);
  check(/That's all 5\./.test(done.title), `${name}: done title "${done.title}"`);
  check(done.tally === PER_READER, `${name}: tally sums to ${PER_READER} (${done.tally})`);
  check(done.tallyLabel === "Picks on this device", `${name}: tally labelled "${done.tallyLabel}"`);
  check(done.codeShown, `${name}: vote code shown when the shared store is out of reach`);
  const m = done.code.match(/^FLM1:([0-9a-f]{8}):([0-9a-z]{6}):([abt-]{20})$/);
  check(!!m && m[1] === VERSION.slice(0, 8) && m[2] === done.ballot.slice(-6), `${name}: vote code format ${done.code}`);
  if (m) {
    check(m[3].replace(/-/g, "").length === PER_READER, `${name}: vote code has exactly ${PER_READER} picked letters`);
    check(m[3] === codeFor(done.picks), `${name}: vote code letters equal the stored picks, "-" elsewhere (${m[3]} vs ${codeFor(done.picks)})`);
  }
  const order = await page.evaluate(() => [!document.getElementById("review"), document.getElementById("codeBox").compareDocumentPosition(document.getElementById("tally")) & Node.DOCUMENT_POSITION_FOLLOWING]);
  check(order[0], `${name}: no "Change my picks" after the tally is shown`);
  check(!!order[1], `${name}: vote code comes before the tally`);
  await page.click("#nextPerson");
  check(!(await page.isHidden("#done")) && /Tap again/.test(await page.textContent("#nextPerson")), `${name}: Next reader asks once more when the code wasn't copied`);
  [sw, cw] = await W(); check(sw <= cw, `${name}: done screen has no sideways scroll`);
  bad = await page.evaluate(CONTRAST); check(!bad.length, `${name}: done text contrast ${bad.length ? bad.join(" | ") : "AA"}`);
  await page.screenshot({ path: path.join(shots, `${name}-3-done.png`), fullPage: true });
  check(!errors.length, `${name}: no page errors ${errors.join(" | ")}`);
  await ctx.close();
}

// ---- Public mode: picks POSTed to the (stand-in) Supabase table.
{
  const name = "phone-public";
  console.log(`\n== ${name}`);
  const ctx = await browser.newContext({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true, colorScheme: "light" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto(URL_ + "public/");
  await page.waitForFunction(BOOTED);
  const statusText = (await page.textContent("#status")).trim();
  check(/saved as you go/.test(statusText), `${name}: status says picks are saved as you go ("${statusText}")`);
  check(/\b5 pairs\b/.test(await page.textContent("#intro .label")), `${name}: intro label says 5 pairs`);
  check(remote.reqs.length === 0, `${name}: nothing sent before the first pick (${remote.reqs.length})`);

  const key = (r) => [r.ballot, r.pid, r.at, r.pick, r.reason || ""].join("|");
  // Run one action and record the row it should produce: exactly one stored pick changes per pick or reason edit.
  async function act(exp, label, fn) {
    const before = (await page.evaluate(STATE)).b?.picks || {};
    await fn();
    const { ballot, b } = await page.evaluate(STATE);
    const changed = Object.keys(b.picks).filter((p) => JSON.stringify(b.picks[p]) !== JSON.stringify(before[p]));
    check(changed.length === 1, `${name}: ${label} changes exactly one stored pick (${changed.length})`);
    for (const p of changed) exp.push({ ballot, pid: Number(p), ...b.picks[p], ui: b.ui, vw: b.vw });
  }
  // One reader's 5 pairs: picks by tap and keyboard, a changed pick, and two reasons (one committed by Tab).
  async function readFive(tag) {
    const exp = [];
    await page.click("#start");
    await page.waitForSelector("#pairView:not([hidden])");
    check(/Pair 1 of 5\b/.test(await page.textContent("#pairNo")), `${name}/${tag}: starts at "Pair 1 of 5"`);
    await act(exp, `${tag} tap A on pair 1`, () => page.click("#vA"));
    await page.fill("#why", "sounds like a real person");
    await act(exp, `${tag} reason on pair 1`, () => page.press("#why", "Tab"));
    await page.click("#next");
    await act(exp, `${tag} key 2 on pair 2`, () => page.keyboard.press("2"));
    await act(exp, `${tag} change to key 1 on pair 2`, () => page.keyboard.press("1"));
    await page.keyboard.press("Enter");
    await act(exp, `${tag} key 0 on pair 3`, () => page.keyboard.press("0"));
    await page.keyboard.press("Enter");
    await act(exp, `${tag} key 2 on pair 4`, () => page.keyboard.press("2"));
    await page.keyboard.press("Enter");
    check(/Pair 5 of 5\b/.test(await page.textContent("#pairNo")), `${name}/${tag}: reached "Pair 5 of 5"`);
    await act(exp, `${tag} key 1 on pair 5`, () => page.keyboard.press("1"));
    await page.fill("#why", "plainer");
    await act(exp, `${tag} reason on pair 5`, () => page.press("#why", "Tab"));
    await page.click("#next");
    await page.waitForSelector("#done:not([hidden])");
    return exp;
  }
  // Wait until every expected row was accepted, then check rows and headers.
  async function checkArrived(tag, exp, ms) {
    const want = new Set(exp.map(key));
    const t0 = Date.now();
    while (Date.now() - t0 < ms && ![...want].every((k) => remote.rows.some((r) => key(r) === k))) await sleep(100);
    const mine = remote.rows.filter((r) => r.ballot === exp[0].ballot);
    const got = new Set(mine.map(key));
    const missing = [...want].filter((k) => !got.has(k));
    check(!missing.length, `${name}/${tag}: all ${exp.length} pick/reason rows arrived within ${ms / 1000}s (${missing.length} missing, ${((Date.now() - t0) / 1000).toFixed(1)}s)`);
    check(mine.length === got.size, `${name}/${tag}: no row accepted twice (${mine.length} rows, ${got.size} distinct)`);
    check(mine.every((r) => want.has(key(r))), `${name}/${tag}: no row the reader didn't make`);
    const byKey = Object.fromEntries(exp.map((e) => [key(e), e]));
    const badRows = mine.filter((r) => { const e = byKey[key(r)];
      return !e || r.version !== VERSION || r.ui !== 3 || typeof r.pid !== "number" || r.first !== e.first || r.vw !== e.vw || !(r.vw > 0); });
    check(!badRows.length, `${name}/${tag}: every row has version ${VERSION.slice(0, 8)}…, ballot, numeric pid, pick, first, ui 3, vw (${badRows.length} bad)`);
  }
  const headersOk = (reqs) => reqs.every((q) => q.headers.apikey === KEY && q.headers.authorization === "Bearer " + KEY
    && /^application\/json/.test(q.headers["content-type"] || "") && q.headers.prefer === "return=minimal" && Array.isArray(q.rows) && q.rows.length > 0);
  const doneState = () => page.evaluate(() => {
    const s = JSON.parse(localStorage.getItem("ab-read-v1") || "{}");
    const nums = [...document.querySelectorAll("#legend span")].map((e) => +(e.textContent.match(/ (\d+) \(/) || [0, 0])[1]);
    return { queue: s.queue, codeShown: !document.getElementById("codeBox").hidden, msg: document.getElementById("doneMsg").textContent,
             title: document.getElementById("doneTitle").textContent, tally: nums.reduce((x, y) => x + y, 0),
             tallyLabel: document.getElementById("tallyLabel").textContent, code: document.getElementById("voteCode").textContent,
             picks: s.local.ballots[s.ballot].picks };
  });
  const settled = (ms) => page.waitForFunction(() => {
    const s = JSON.parse(localStorage.getItem("ab-read-v1") || "{}");
    return Array.isArray(s.queue) && s.queue.length === 0 && document.getElementById("codeBox").hidden;
  }, null, { timeout: ms }).then(() => true, () => false);

  // 1. Server up: every row arrives, the queue empties, the code box hides.
  let r0 = remote.reqs.length;
  const exp1 = await readFive("ok");
  await checkArrived("ok", exp1, 5000);
  check(headersOk(remote.reqs.slice(r0)), `${name}/ok: every POST carries apikey + Bearer ${KEY}, JSON body array, Prefer return=minimal`);
  check(remote.reqs.slice(r0).every((q) => q.status === 201), `${name}/ok: every POST answered 201`);
  check(await settled(5000), `${name}/ok: queue in localStorage empty and code box hidden after finishing`);
  let d = await doneState();
  check(d.msg === "Your picks are saved.", `${name}/ok: done message "${d.msg}"`);
  check(/That's all 5\./.test(d.title), `${name}/ok: done title "${d.title}"`);
  check(d.tallyLabel === "Picks on this device" && d.tally === PER_READER, `${name}/ok: tally shows this device's ${PER_READER} picks ("${d.tallyLabel}", ${d.tally})`);
  check((await page.textContent("#status")).includes("saved as you go"), `${name}/ok: status line still says picks are saved as you go`);
  let [sw, cw] = await page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]);
  check(sw <= cw, `${name}/ok: done screen has no sideways scroll`);
  let bad = await page.evaluate(CONTRAST); check(!bad.length, `${name}/ok: done text contrast ${bad.length ? bad.join(" | ") : "AA"}`);
  await page.screenshot({ path: path.join(shots, `${name}-1-done-saved.png`), fullPage: true });

  // 2. First 2 inserts fail: rows still arrive after retries, nothing lost or duplicated.
  await page.click("#nextPerson");
  check(!(await page.isHidden("#intro")) && (await page.textContent("#start")).trim() === "Start reading", `${name}: Next reader goes straight to a fresh intro once picks are saved`);
  r0 = remote.reqs.length; remote.failLeft = 2;
  const exp2 = await readFive("retry");
  check(exp2[0].ballot !== exp1[0].ballot, `${name}/retry: a new ballot id for the next reader`);
  await checkArrived("retry", exp2, 15000);
  const reqs2 = remote.reqs.slice(r0);
  check(reqs2.filter((q) => q.status === 500).length === 2 && reqs2.at(-1).status === 201, `${name}/retry: 2 failed inserts, then accepted (${reqs2.map((q) => q.status).join(",")})`);
  check(headersOk(reqs2), `${name}/retry: every POST carries the key headers and a row array`);
  check(await settled(5000), `${name}/retry: queue empty and code box hidden after the retries`);

  // 3. Server down for good: the done screen falls back to the vote code and the queue stays in localStorage.
  await page.click("#nextPerson");
  r0 = remote.reqs.length; const rows0 = remote.rows.length; remote.failAll = true;
  const exp3 = await readFive("down");
  await sleep(2500);
  d = await doneState();
  check(remote.reqs.length > r0 && remote.rows.length === rows0, `${name}/down: inserts were tried (${remote.reqs.length - r0}) and none accepted`);
  check(d.codeShown, `${name}/down: vote code shown as the fallback`);
  check(/haven't reached/.test(d.msg), `${name}/down: done message says picks haven't reached the tally ("${d.msg}")`);
  const queued = new Set((d.queue || []).map(key));
  check((d.queue || []).length === exp3.length && exp3.every((e) => queued.has(key(e))), `${name}/down: all ${exp3.length} rows kept in the localStorage queue (${(d.queue || []).length})`);
  const m3 = d.code.match(/^FLM1:([0-9a-f]{8}):([0-9a-z]{6}):([abt-]{20})$/);
  check(!!m3 && m3[3] === codeFor(d.picks) && m3[3].replace(/-/g, "").length === PER_READER, `${name}/down: fallback code holds the ${PER_READER} picks (${d.code})`);
  await page.screenshot({ path: path.join(shots, `${name}-2-done-fallback.png`), fullPage: true });
  bad = await page.evaluate(CONTRAST); check(!bad.length, `${name}/down: done text contrast ${bad.length ? bad.join(" | ") : "AA"}`);

  // 4. The server comes back: a reload sends the kept queue, once.
  remote.failAll = false;
  await page.reload();
  await page.waitForFunction(BOOTED);
  await checkArrived("down→reload", exp3, 10000);
  const emptied = await page.waitForFunction(() => (JSON.parse(localStorage.getItem("ab-read-v1") || "{}").queue || [1]).length === 0, null, { timeout: 5000 }).then(() => true, () => false);
  check(emptied, `${name}/down→reload: queue empty once the kept rows are accepted`);
  check(!errors.length, `${name}: no page errors ${errors.join(" | ")}`);
  await ctx.close();
}

await browser.close();
server.close();
console.log(`\nscreenshots: ${shots}`);
console.log(failures.length ? `\n${failures.length} FAILED` : "\nALL PASSED");
process.exit(failures.length ? 1 : 0);
