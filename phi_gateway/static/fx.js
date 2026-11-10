/* Motion layer: GSAP + ScrollTrigger, vanilla ports of React Bits effects
   (Aurora, BlurText/SplitText, CountUp, ShinyText, SpotlightCard, Magnet, scroll reveal). */
(function () {
  if (!window.gsap) return;
  gsap.registerPlugin(ScrollTrigger);
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  /* ---- scroll progress bar ---- */
  const bar = document.createElement("div");
  bar.className = "fx-progress";
  document.body.appendChild(bar);
  gsap.to(bar, { scaleX: 1, ease: "none",
    scrollTrigger: { trigger: document.body, start: "top top", end: "bottom bottom", scrub: 0.3 } });

  /* ---- Aurora background in the hero ---- */
  const hero = document.querySelector(".hero");
  if (hero) {
    const wrap = document.createElement("div");
    wrap.className = "fx-aurora";
    ["#2563eb", "#7c3aed", "#f59e0b"].forEach((c, i) => {
      const b = document.createElement("i");
      b.style.background = c;
      b.style.left = [8, 45, 70][i] + "%";
      b.style.top = [10, 30, 0][i] + "%";
      wrap.appendChild(b);
      gsap.to(b, { x: "random(-120,120)", y: "random(-60,60)", scale: "random(.8,1.3)",
        duration: "random(5,9)", repeat: -1, yoyo: true, ease: "sine.inOut" });
    });
    hero.prepend(wrap);
  }

  /* ---- BlurText / SplitText: word-by-word headline reveal ---- */
  const h1 = document.querySelector(".hero h1");
  if (h1) {
    const words = [];
    (function walk(node) {
      [...node.childNodes].forEach((n) => {
        if (n.nodeType === 3) {
          const frag = document.createDocumentFragment();
          n.textContent.split(/(\s+)/).forEach((t) => {
            if (!t.trim()) { frag.appendChild(document.createTextNode(t)); return; }
            const s = document.createElement("span");
            s.className = "fx-word"; s.textContent = t; words.push(s); frag.appendChild(s);
          });
          n.replaceWith(frag);
        } else if (n.nodeType === 1) walk(n);
      });
    })(h1);
    gsap.from(words, { y: 46, opacity: 0, filter: "blur(10px)", duration: 0.9,
      stagger: 0.07, ease: "power3.out", delay: 0.15 });
  }
  gsap.from(".hero .eyebrow, .hero p", { y: 18, opacity: 0, duration: 0.8, stagger: 0.15, delay: 0.6, ease: "power2.out" });
  gsap.from(".hero-stats > div", { y: 30, opacity: 0, duration: 0.8, stagger: 0.12, delay: 0.9, ease: "power3.out" });
  gsap.from(".hero-stats", { clipPath: "inset(0 100% 0 0)", duration: 1.1, delay: 0.8, ease: "power3.inOut" });
  gsap.from("header.topbar .wrap > *", { y: -20, opacity: 0, duration: 0.6, stagger: 0.08, ease: "power2.out" });

  /* ---- CountUp: animate any number rendered into stat/KPI slots ---- */
  let busy = 0;
  function countUp(el) {
    const txt = el.textContent.trim();
    const m = txt.match(/^([^\d-]*)(-?\d[\d,]*\.?\d*)(.*)$/);
    if (!m || el.dataset.cu === txt) return;
    const pre = m[1], num = m[2], post = m[3];
    const target = parseFloat(num.replace(/,/g, ""));
    if (!isFinite(target)) return;
    const dec = (num.split(".")[1] || "").length;
    el.dataset.cu = txt;
    const o = { v: 0 };
    busy++;
    gsap.to(o, { v: target, duration: 1.6, ease: "power2.out",
      onUpdate: function () { el.textContent = pre + o.v.toFixed(dec) + post; },
      onComplete: function () { el.textContent = txt; busy--; } });
  }
  const mo = new MutationObserver(function () {
    if (busy) return;
    document.querySelectorAll(".hero-stats b, .kpi .val").forEach(function (el) {
      const t = el.textContent.trim();
      if (t !== "–" && t !== "") countUp(el);
    });
  });
  [".hero-stats", "#kpis", "#ev-kpis", "#ut-kpis"].forEach(function (sel) {
    const el = document.querySelector(sel);
    if (el) mo.observe(el, { childList: true, subtree: true, characterData: true });
  });

  /* ---- chips / rows pop in with a stagger after masking or an answer ---- */
  ["masked-out", "ans-raw", "ans-rehyd", "ut-m", "ut-r", "map-body", "type-dist"].forEach(function (id) {
    const el = document.getElementById(id); if (!el) return;
    new MutationObserver(function () {
      const t = el.querySelectorAll(".chip, .badge, tr");
      if (t.length) gsap.fromTo(t, { opacity: 0, scale: 0.6, y: 6 },
        { opacity: 1, scale: 1, y: 0, duration: 0.45, stagger: 0.03, ease: "back.out(2)", clearProps: "transform" });
    }).observe(el, { childList: true });
  });

  /* ---- scroll reveals ---- */
  const revealSel = ".sec-h, .sec-sub, .card, .panel, .steps, h3.sub-h, .tabs, .lbl2, textarea, .out, .ledgend";
  gsap.set(revealSel, { opacity: 0, y: 40 });
  ScrollTrigger.batch(revealSel, {
    start: "top 92%", once: true,
    onEnter: function (els) {
      gsap.to(els, { y: 0, opacity: 1, duration: 0.8, stagger: 0.09, ease: "power3.out", overwrite: true });
    },
  });
  gsap.utils.toArray(".sec-h .no").forEach(function (n) {
    gsap.from(n, { x: -24, opacity: 0, duration: 0.7, scrollTrigger: { trigger: n, start: "top 92%", once: true } });
  });

  /* ---- SpotlightCard: cursor-following glow ---- */
  document.addEventListener("pointermove", function (e) {
    const c = e.target.closest && e.target.closest(".card");
    if (!c) return;
    const r = c.getBoundingClientRect();
    c.style.setProperty("--mx", e.clientX - r.left + "px");
    c.style.setProperty("--my", e.clientY - r.top + "px");
  });

  /* ---- Magnet buttons ---- */
  document.querySelectorAll("button.btn").forEach(function (b) {
    const xTo = gsap.quickTo(b, "x", { duration: 0.5, ease: "power3.out" });
    const yTo = gsap.quickTo(b, "y", { duration: 0.5, ease: "power3.out" });
    b.addEventListener("pointermove", function (e) {
      const r = b.getBoundingClientRect();
      xTo((e.clientX - (r.left + r.width / 2)) * 0.25);
      yTo((e.clientY - (r.top + r.height / 2)) * 0.35);
    });
    b.addEventListener("pointerleave", function () { xTo(0); yTo(0); });
    b.addEventListener("pointerdown", function () {
      gsap.fromTo(b, { scale: 0.94 }, { scale: 1, duration: 0.5, ease: "elastic.out(1,.4)" });
    });
  });

  /* ---- ripple pulse on the masked panel ---- */
  const mb = document.getElementById("btn-mask");
  if (mb) mb.addEventListener("click", function () {
    gsap.fromTo("#masked-out", { boxShadow: "0 0 0 0 rgba(29,78,216,.5)" },
      { boxShadow: "0 0 0 14px rgba(29,78,216,0)", duration: 1, ease: "power2.out" });
  });
})();
