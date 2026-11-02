// End-to-end test of the blind A/B page (Playwright, Node). Serves index.html + pairs.json wrapped in the same
// head the Artifact publish adds, then walks the reader journey at phone and desktop size, light and dark.
// Usage: node hackathon/demo/ab_page/e2e_ab_page.mjs [--shots DIR]
//   Needs the `playwright` package: PLAYWRIGHT_MODULE=<path to node_modules/playwright/index.js> if not resolvable.
// Checks: no sideways scroll; vote buttons >= 44 px; the stored pick is the side the reader saw; Enter on a focused
// vote button records nothing extra; reload resumes the ballot; an old-version ballot is never resumed; the tally
// sums to 20; the vote code holds exactly the stored picks; text contrast >= 4.5:1 (3:1 for large text).
import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const shots = args.includes("--shots") ? args[args.indexOf("--shots") + 1] : fs.mkdtempSync(path.join(os.tmpdir(), "ab-e2e-"));
const mod = process.env.PLAYWRIGHT_MODULE ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : "playwright";
const pw = await import(mod);
const chromium = pw.chromium || pw.default.chromium;  // CommonJS package: named export may sit on default

const SKELETON = '<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light;padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style></head><body>';
const page_html = SKELETON + fs.readFileSync(path.join(here, "index.html"), "utf8") + "</body></html>";
const pairs = fs.readFileSync(path.join(here, "pairs.json"), "utf8");
const VERSION = JSON.parse(pairs).meta.version;

const server = http.createServer((req, res) => {
  if (req.url.startsWith("/pairs.json")) { res.writeHead(200, { "content-type": "application/json" }); return res.end(pairs); }
  res.writeHead(200, { "content-type": "text/html; charset=utf-8" }); res.end(page_html);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const URL_ = `http://127.0.0.1:${server.address().port}/`;

const failures = [];
const check = (ok, what) => { if (!ok) failures.push(what); console.log(`${ok ? "ok  " : "FAIL"} ${what}`); };

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
  const W = () => page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]);
  let [sw, cw] = await W(); check(sw <= cw, `${name}: intro has no sideways scroll (${sw} <= ${cw})`);
  check((await page.textContent("#start")).trim() === "Start reading", `${name}: old-version ballot is not offered for resume`);
  await page.screenshot({ path: path.join(shots, `${name}-1-intro.png`), fullPage: true });
  let bad = await page.evaluate(CONTRAST); check(!bad.length, `${name}: intro text contrast ${bad.length ? bad.join(" | ") : "AA"}`);

  await page.click("#start");
  await page.waitForSelector("#pairView:not([hidden])");
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
  check(st1.b.ui === 2 && st1.b.vw > 0, `${name}: ballot records page version and viewport width (ui ${st1.b.ui}, vw ${st1.b.vw})`);
  check(!!st1.s.local.ballots.bOLD, `${name}: old-version ballot kept in storage`);
  const pk = st1.b.picks[pidsPicked[0]];
  const pair = JSON.parse(pairs).pairs.find((p) => String(p.pid) === pidsPicked[0]);
  check(pair[pk.pick] === shownB, `${name}: stored pick is the text the reader saw as B`);
  check(/Pair 2 of 20/.test(await page.textContent("#pairNo")), `${name}: Enter advanced to pair 2`);

  // Moving to a new pair never animates the previous pick's highlight onto it.
  await page.keyboard.press("2");
  const dur = await page.evaluate(() => { document.getElementById("next").click(); return getComputedStyle(document.getElementById("sideB")).transitionDuration; });
  check(/^0s(, 0s)?$/.test(dur), `${name}: no highlight transition on a new pair (${dur})`);
  await page.keyboard.press("ArrowLeft"); await page.keyboard.press("Enter");  // back to pair 3, unchanged

  // Eight more by keyboard (pairs 3-10), then reload: the page offers to continue at pair 11.
  for (let i = 0; i < 8; i++) { await page.keyboard.press(["1", "2", "0"][i % 3]); await page.keyboard.press("Enter"); }
  await page.reload();
  await page.waitForFunction(() => document.getElementById("count").textContent.includes("picked"));
  check((await page.textContent("#start")).includes("Continue"), `${name}: reload offers to continue`);
  await page.click("#start");
  check(/Pair 11 of 20/.test(await page.textContent("#pairNo")), `${name}: resumes at the first unanswered pair`);
  for (let i = 0; i < 10; i++) { await page.keyboard.press(["2", "1", "0", "2"][i % 4]); await page.keyboard.press("Enter"); }
  await page.waitForSelector("#done:not([hidden])");

  const done = await page.evaluate(() => {
    const s = JSON.parse(localStorage.getItem("ab-read-v1")); const b = s.local.ballots[s.ballot];
    const nums = [...document.querySelectorAll("#legend span")].map((e) => +(e.textContent.match(/ (\d+) \(/) || [0, 0])[1]);
    return { picks: b.picks, finished: !!b.finished, tally: nums.reduce((x, y) => x + y, 0), code: document.getElementById("voteCode").textContent,
             codeShown: !document.getElementById("codeBox").hidden };
  });
  check(done.finished && Object.keys(done.picks).length === 20, `${name}: ballot finished with 20 picks`);
  check(done.tally === 20, `${name}: tally sums to 20 (${done.tally})`);
  check(done.codeShown, `${name}: vote code shown when the shared store is out of reach`);
  const m = done.code.match(/^FLM1:([0-9a-f]{8}):([0-9a-z]{6}):([abt-]{20})$/);
  check(!!m && m[1] === VERSION.slice(0, 8), `${name}: vote code format ${done.code}`);
  if (m) {
    const want = Object.keys(done.picks).map(Number).sort((x, y) => x - y).map((p) => ({ a: "a", b: "b", tie: "t" })[done.picks[p].pick]).join("");
    check(m[3] === want, `${name}: vote code letters equal the stored picks`);
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
await browser.close();
server.close();
console.log(`\nscreenshots: ${shots}`);
console.log(failures.length ? `\n${failures.length} FAILED` : "\nALL PASSED");
process.exit(failures.length ? 1 : 0);
