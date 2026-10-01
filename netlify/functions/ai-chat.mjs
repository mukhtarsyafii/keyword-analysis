// Netlify Function: proxy chat ke provider OpenAI-compatible yang Hermes pakai.
// Kenapa proxy? Browser memblokir halaman publik -> http://127.0.0.1 (Private Network
// Access), jadi dashboard di GitHub Pages tidak bisa memanggil Hermes lokal.
// Key provider hidup di env Netlify, tidak pernah masuk repo public.
//
// ponytail: satu token bersama untuk semua pengguna widget. Cukup untuk situs kecil
// yang datanya sudah public. Upgrade path: ganti dengan verifikasi identitas per
// pengguna kalau mulai disalahgunakan.

const PROVIDER_URL = process.env.AI_PROVIDER_URL || "https://9router.difa00.digitalfinger.id/v1";
const PROVIDER_KEY = process.env.AI_PROVIDER_KEY || "";
const MODEL = process.env.AI_MODEL || "Code";
const WIDGET_TOKEN = process.env.AI_WIDGET_TOKEN || "";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, X-Widget-Token",
  "Content-Type": "application/json",
};

const json = (code, obj) => ({ statusCode: code, headers: CORS, body: JSON.stringify(obj) });

// Sistem prompt + snapshot data dikirim klien (sudah dibangun dari JSON dashboard),
// jadi fungsi ini tetap tipis dan datanya tidak perlu di-parse ulang di server.
export const handler = async (event) => {
  if (event.httpMethod === "OPTIONS") return { statusCode: 204, headers: CORS, body: "" };
  if (event.httpMethod !== "POST") return json(405, { error: "method_not_allowed" });

  if (!PROVIDER_KEY) return json(500, { error: "AI_PROVIDER_KEY belum diset di Netlify env" });

  // Gerbang: situs ini public, tanpa cek siapa pun bisa membakar kuota LLM pemiliknya.
  if (WIDGET_TOKEN && event.headers["x-widget-token"] !== WIDGET_TOKEN) {
    return json(401, { error: "token_widget_tidak_sesuai" });
  }

  let body;
  try {
    body = JSON.parse(event.body || "{}");
  } catch {
    return json(400, { error: "body_bukan_json" });
  }

  const messages = Array.isArray(body.messages) ? body.messages : [];
  if (!messages.length) return json(400, { error: "messages_kosong" });

  // Batas keras: payload & jumlah pesan, supaya satu request tidak jadi biaya besar.
  const chars = messages.reduce((a, m) => a + String(m.content || "").length, 0);
  if (messages.length > 30 || chars > 120000) return json(413, { error: "terlalu_besar" });

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 24000); // di bawah timeout function 26s
  try {
    const r = await fetch(`${PROVIDER_URL}/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${PROVIDER_KEY}` },
      body: JSON.stringify({ model: MODEL, messages, stream: false }),
      signal: ctrl.signal,
    });
    if (!r.ok) return json(502, { error: `provider_${r.status}`, detail: (await r.text()).slice(0, 300) });
    const j = await r.json();
    // Balas bentuk OpenAI supaya kode widget tidak berubah.
    return json(200, { choices: j.choices, usage: j.usage, model: j.model });
  } catch (e) {
    return json(504, { error: e.name === "AbortError" ? "provider_timeout" : String(e.message).slice(0, 200) });
  } finally {
    clearTimeout(timer);
  }
};
