// softtarget front end. Lab 3 inserts model output with innerHTML ON PURPOSE.
const $ = (id) => document.getElementById(id);
const S = { labs: [], levels: [], lab: null, level: "low", session: null, solved: new Set(), busy: false };

function store(k, v) { try { v === undefined ? null : localStorage.setItem(k, v); return localStorage.getItem(k); } catch { return null; } }

async function api(path, body) {
  const r = await fetch(path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {});
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || `HTTP ${r.status}`);
  return data;
}

function toast(text) {
  const t = $("toast"); t.textContent = text; t.hidden = false;
  clearTimeout(toast.t); toast.t = setTimeout(() => (t.hidden = true), 3500);
}

function markSolved(list) {
  S.solved = new Set(list);
  renderLabs(); renderBrief();
}

// Lab 3 win detection: if injected JavaScript calls alert/confirm/prompt, report it.
for (const fn of ["alert", "confirm", "prompt"]) {
  window[fn] = async () => {
    if (S.lab?.id !== "output-html") return;
    toast(`JavaScript ran (${fn}). Solved at ${S.level}.`);
    const d = await api("/api/solved", { session: S.session, lab: "output-html", level: S.level });
    markSolved(d.solved_all);
  };
}

function renderLabs() {
  const nav = $("labs"); nav.innerHTML = "";
  S.labs.forEach((lab, i) => {
    const b = document.createElement("button");
    b.className = "lab"; b.setAttribute("aria-current", lab.id === S.lab.id);
    b.innerHTML = `<span class="n">${i + 1}</span><span class="t"></span><div class="dots"></div>`;
    b.querySelector(".t").textContent = lab.title;
    const dots = b.querySelector(".dots");
    S.levels.forEach((lv) => {
      const d = document.createElement("span");
      d.className = "dot" + (S.solved.has(`${lab.id}:${lv}`) ? " on" : "");
      d.title = `${lv}${S.solved.has(`${lab.id}:${lv}`) ? ": solved" : ""}`;
      dots.appendChild(d);
    });
    b.onclick = () => { S.lab = lab; store("st.lab", lab.id); renderAll(); };
    nav.appendChild(b);
  });
}

function renderBrief() {
  const lab = S.lab, lv = lab.levels[S.level];
  $("owasp").textContent = lab.owasp; $("title").textContent = lab.title;
  $("story").textContent = lab.story; $("goal").textContent = lab.goal;
  $("defence").textContent = lv.defence; $("hint").textContent = lv.hint;
  $("solvedBanner").hidden = !S.solved.has(`${lab.id}:${S.level}`);
  const box = $("levels"); box.innerHTML = "";
  S.levels.forEach((l) => {
    const b = document.createElement("button");
    b.type = "button"; b.role = "radio"; b.setAttribute("aria-checked", l === S.level);
    b.textContent = l; if (S.solved.has(`${lab.id}:${l}`)) b.insertAdjacentHTML("beforeend", '<span class="tick">✓</span>');
    b.onclick = () => { S.level = l; store("st.level", l); renderAll(); };
    box.appendChild(b);
  });
  const doc = lab.input === "document";
  $("composerLabel").textContent = doc ? "Your support ticket (Dana's assistant will summarize it)" : "Message Pip";
  $("input").rows = doc ? 4 : 2;
  $("send").textContent = doc ? "Submit ticket" : "Send";
}

function renderAll() {
  renderLabs(); renderBrief();
  $("chat").innerHTML = `<p class="empty">Level: <b>${S.level}</b>. Start attacking. Your chat, the model's secrets and the database are private to this browser session.</p>`; $("events").innerHTML = '<p class="muted">Tool calls, filters and leaks show up here.</p>';
}

// Safe Markdown-ish rendering for lab 2: images are shown as the request a browser would make, not loaded.
function renderMarkdownSafely(el, text) {
  const rx = /(!?)\[([^\]]*)\]\(((?:[^()\s]|\([^()\s]*\))+)\)/g; let last = 0, m;
  while ((m = rx.exec(text))) {
    el.append(text.slice(last, m.index));
    if (m[1]) { const s = document.createElement("span"); s.className = "imgleak"; s.textContent = `image request → ${m[3]}`; el.append(s); }
    else el.append(`${m[2]} (${m[3]})`);
    last = rx.lastIndex;
  }
  el.append(text.slice(last));
}

function addMsg(kind, text, render) {
  const div = document.createElement("div");
  $("chat").querySelector(".empty")?.remove();
  div.className = `msg ${kind}` + (render === "html" ? " html" : "");
  const who = document.createElement("span"); who.className = "who";
  who.textContent = kind === "you" ? (S.lab.input === "document" ? "Your ticket" : "You") : kind === "err" ? "Error" : S.lab.input === "document" ? "Dana's assistant" : "Pip";
  div.appendChild(who);
  const body = document.createElement("div");
  if (render === "html") body.innerHTML = text;          // deliberately vulnerable (lab 3)
  else if (render === "markdown") renderMarkdownSafely(body, text);
  else body.textContent = text;
  div.appendChild(body);
  $("chat").appendChild(div); div.scrollIntoView({ block: "end" });
  return div;
}

function addEvents(events) {
  const box = $("events"); if (events.length) box.querySelector(".muted")?.remove();
  for (const e of events) {
    const d = document.createElement("div"); d.className = `ev ${e.type}`;
    const h = document.createElement("b");
    const c = document.createElement("code");
    if (e.type === "tool") { h.textContent = `tool: ${e.tool}`; c.textContent = `${JSON.stringify(e.args)}\n→ ${e.result}`; }
    else if (e.type === "email") { h.textContent = "email sent"; c.textContent = `to: ${e.to}\nsubject: ${e.subject}\n\n${e.body}`; }
    else { h.textContent = e.type; c.textContent = e.text; }
    d.append(h, c); box.prepend(d);
  }
}

async function send(ev) {
  ev?.preventDefault();
  const text = $("input").value.trim(); if (!text || S.busy) return;
  S.busy = true; $("send").disabled = true; $("input").value = "";
  addMsg("you", text);
  const wait = addMsg("bot", "thinking…"); wait.classList.add("thinking");
  try {
    const d = await api("/api/chat", { session: S.session, lab: S.lab.id, level: S.level, text });
    wait.remove();
    addMsg("bot", d.reply || "(empty reply)", d.render);
    addEvents(d.events || []);
    const before = S.solved.has(`${S.lab.id}:${S.level}`);
    markSolved(d.solved_all || []);
    if (d.solved && !before) toast(`Solved: ${S.lab.title} at ${S.level}.`);
  } catch (e) { wait.remove(); addMsg("err", e.message); }
  S.busy = false; $("send").disabled = false; $("input").focus();
}

async function init() {
  const d = await api("/api/labs");
  S.labs = d.labs; S.levels = d.levels;
  S.session = store("st.session") || store("st.session", d.session) || d.session;
  S.lab = S.labs.find((l) => l.id === store("st.lab")) || S.labs[0];
  S.level = S.levels.includes(store("st.level")) ? store("st.level") : "low";
  renderAll();
  $("composer").onsubmit = send;
  $("input").addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) send(e); });
  $("reset").onclick = async () => { await api("/api/reset", { session: S.session, lab: S.lab.id, level: S.level }); renderAll(); };
  api("/api/health").then((h) => {
    const s = $("status"); s.className = "status " + (h.ok ? "ok" : "bad");
    s.textContent = h.ok ? `${h.model} · local` : h.error;
  }).catch(() => { $("status").textContent = "model status unknown"; });
}
init().catch((e) => { document.body.insertAdjacentHTML("afterbegin", `<p style="color:red;padding:16px">Failed to load: ${e.message}</p>`); });
