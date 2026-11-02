// Public vote endpoint for the blind A/B pages (rewritten from /rest/v1/featherlm_ab_votes, see vercel.json).
// Validates the page's rows and inserts them into the Supabase table with a key held only in the Vercel environment
// (SUPABASE_URL, SUPABASE_KEY), so no key ships to readers. It can only insert; it never reads or returns votes.
const MAX_ROWS = 20;
const str = (v, lo, hi) => typeof v === "string" && v.length >= lo && v.length <= hi;
const valid = (r) => r && typeof r === "object" && str(r.version, 8, 32) && str(r.ballot, 4, 40)
  && Number.isInteger(r.pid) && r.pid >= 1 && r.pid <= 100 && ["a", "b", "tie"].includes(r.pick);
const clean = (r) => ({
  version: r.version, ballot: r.ballot, pid: r.pid, pick: r.pick,
  first: ["a", "b"].includes(r.first) ? r.first : null,
  reason: typeof r.reason === "string" ? r.reason.slice(0, 300) : null,
  ui: Number.isInteger(r.ui) && r.ui >= 0 && r.ui <= 100 ? r.ui : null,
  vw: Number.isInteger(r.vw) && r.vw >= 0 && r.vw <= 10000 ? r.vw : null,
  at: typeof r.at === "string" && !Number.isNaN(Date.parse(r.at)) ? r.at : null,
});

module.exports = async (req, res) => {
  if (req.method !== "POST") { res.status(405).end(); return; }
  let rows = req.body;
  if (typeof rows === "string") { try { rows = JSON.parse(rows); } catch { rows = null; } }
  if (!Array.isArray(rows) || !rows.length || rows.length > MAX_ROWS || !rows.every(valid)) {
    res.status(400).json({ error: "expected 1-20 vote rows" }); return;
  }
  const { SUPABASE_URL, SUPABASE_KEY } = process.env;
  try {
    const up = await fetch(`${SUPABASE_URL}/rest/v1/featherlm_ab_votes`, {
      method: "POST", body: JSON.stringify(rows.map(clean)),
      headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}`, "Content-Type": "application/json", Prefer: "return=minimal" },
    });
    res.status(up.ok ? 201 : 502).end();  // 502 makes the page keep the rows and retry
  } catch {
    res.status(502).end();
  }
};
