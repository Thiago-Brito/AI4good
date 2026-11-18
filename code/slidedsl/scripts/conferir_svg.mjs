// Confere diagramas SVG contra um gabarito, renderizando no Chrome (Playwright).
// Uso: node scripts/conferir_svg.mjs <pasta_com_svgs> <gabarito.json> <saida.json>
// gabarito.json: { "<arquivo.svg>": { "elementos": ["Luz", ...], "ordem": "x" | null,
//                                     "barras": [{"rotulo": "A", "valor": 10}, ...] } }
// Vale para SVG de qualquer origem (compilador ou IA): mede geometria renderizada,
// sem depender dos atributos data-* do compilador. Também salva <arquivo>.png ao lado.
import { chromium } from "../editor/node_modules/playwright/index.mjs";
import fs from "node:fs/promises";
import path from "node:path";

const [folder, answersPath, output] = process.argv.slice(2);
if (!folder || !answersPath || !output) throw new Error("Informe pasta, gabarito e saída.");
const answers = JSON.parse(await fs.readFile(answersPath, "utf8"));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.SLIDEDSL_BROWSER ?? "C:/Program Files/Google/Chrome/Application/chrome.exe",
});
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
const norm = (s) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
const results = {};
try {
  for (const name of (await fs.readdir(folder)).filter((f) => f.endsWith(".svg")).sort()) {
    const svg = await fs.readFile(path.join(folder, name), "utf8");
    await page.setContent(`<html><body style="margin:0;background:#fff">${svg}</body></html>`);
    const geo = await page.evaluate(() => {
      const root = document.querySelector("svg");
      if (!root) return null;
      const r0 = root.getBoundingClientRect();
      const box = (el) => { const r = el.getBoundingClientRect(); return { x: r.x - r0.x, y: r.y - r0.y, w: r.width, h: r.height }; };
      const texts = [...root.querySelectorAll("text")].filter((t) => t.textContent.trim())
        .map((t) => { const spans = [...t.querySelectorAll("tspan")]; const raw = spans.length ? spans.map((x) => x.textContent).join(" ") : t.textContent; return { text: raw.replace(/\s+/g, " ").trim(), ...box(t) }; });
      const shapes = [...root.querySelectorAll("rect,circle,ellipse,polygon,path")]
        .filter((s) => !s.closest("defs,marker"))
        .map((s) => ({ tag: s.tagName, fill: getComputedStyle(s).fill, ...box(s) }))
        .filter((s) => s.w > 0 && s.h > 0 && !(s.w >= r0.width - 1 && s.h >= r0.height - 1));
      // Pontos amostrados das linhas/caminhos (setas, contornos) em coordenadas da figura.
      const strokes = [...root.querySelectorAll("line,polyline,path")]
        .filter((s) => !s.closest("defs,marker") && typeof s.getTotalLength === "function")
        .filter((s) => { const st = getComputedStyle(s); return st.stroke !== "none" && (st.fill === "none" || s.tagName === "line"); })
        .map((s) => {
          const len = s.getTotalLength(), m = s.getScreenCTM(), pts = [];
          for (let k = 0; k <= 40; k++) {
            const p = s.getPointAtLength((len * k) / 40);
            pts.push({ x: m.a * p.x + m.c * p.y + m.e - r0.x, y: m.b * p.x + m.d * p.y + m.f - r0.y });
          }
          return pts;
        });
      // Contraste: cor do texto contra o preenchimento da forma desenhada logo abaixo do centro.
      const rgb = (c) => (c.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
      const lum = ([r, g, b]) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
      const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
      const contrast = [...root.querySelectorAll("text")].filter((t) => t.textContent.trim()).map((t) => {
        const r = t.getBoundingClientRect();
        const under = document.elementsFromPoint(r.x + r.width / 2, r.y + r.height / 2)
          .find((el) => el !== t && !t.contains(el) && el.closest("svg") === root && /^(rect|circle|ellipse|polygon|path)$/.test(el.tagName));
        const bg = under ? getComputedStyle(under).fill : "rgb(255,255,255)";
        const fg = getComputedStyle(t).fill;
        return { text: t.textContent.trim(), ratio: bg.startsWith("rgb") && fg.startsWith("rgb") ? ratio(rgb(fg), rgb(bg)) : null };
      });
      return { width: r0.width, height: r0.height, texts, shapes, strokes, contrast };
    });
    await page.locator("svg").screenshot({ path: path.join(folder, name.replace(/\.svg$/, ".png")) });
    const problems = [];
    if (!geo) { results[name] = { correto: false, problemas: ["sem <svg>"] }; continue; }
    const tol = 1;
    for (const t of geo.texts) {
      if (t.x < -tol || t.y < -tol || t.x + t.w > geo.width + tol || t.y + t.h > geo.height + tol)
        problems.push(`texto fora da figura: "${t.text.slice(0, 40)}"`);
    }
    const inter = (a, b) => Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x)) *
      Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
    for (let i = 0; i < geo.texts.length; i++)
      for (let j = i + 1; j < geo.texts.length; j++)
        if (inter(geo.texts[i], geo.texts[j]) > 4)
          problems.push(`textos sobrepostos: "${geo.texts[i].text.slice(0, 25)}" × "${geo.texts[j].text.slice(0, 25)}"`);
    for (const t of geo.texts) for (const s of geo.shapes) {
      if (!["rect", "circle", "ellipse"].includes(s.tag) || s.w < 30 || s.h < 30) continue;
      const a = inter(t, s);
      const inside = t.x >= s.x - tol && t.y >= s.y - tol && t.x + t.w <= s.x + s.w + tol && t.y + t.h <= s.y + s.h + tol;
      if (a > 4 && !inside && a < t.w * t.h * 0.95) problems.push(`texto cruza a borda de uma caixa: "${t.text.slice(0, 30)}"`);
    }
    for (const t of geo.texts) {
      const inner = { x: t.x + 2, y: t.y + 2, w: t.w - 4, h: t.h - 4 };
      if (geo.strokes.some((pts) => pts.some((p) => p.x > inner.x && p.x < inner.x + inner.w && p.y > inner.y && p.y < inner.y + inner.h)))
        problems.push(`linha ou seta passa sobre o texto: "${t.text.slice(0, 30)}"`);
    }
    for (const c of geo.contrast) if (c.ratio !== null && c.ratio < 3)
      problems.push(`contraste baixo (${c.ratio.toFixed(1)}:1): "${c.text.slice(0, 30)}"`);
    const key = answers[name] ?? {};
    const all = norm(geo.texts.map((t) => t.text).join(" "));
    const missing = (key.elementos ?? []).filter((e) => !all.includes(norm(e)));
    for (const e of missing) problems.push(`falta elemento: "${e}"`);
    if (key.ordem === "x" && !missing.length) {
      const xs = key.elementos.map((e) => Math.min(...geo.texts.filter((t) => norm(t.text).includes(norm(e))).map((t) => t.x)));
      if (xs.some((x, k) => k && x <= xs[k - 1])) problems.push("ordem errada (esquerda → direita)");
    }
    let barErr = null;
    if (key.barras?.length) {
      const bars = geo.shapes.filter((s) => s.tag === "rect" && s.h > 0.5 && s.w < geo.width * 0.3 && s.h > s.w * 0.02)
        .sort((a, b) => a.x - b.x);
      const bottoms = bars.map((b) => b.y + b.h);
      const base = bottoms.length ? bottoms.sort((a, b) => b - a)[Math.floor(bottoms.length / 2)] : 0;
      const aligned = bars.filter((b) => Math.abs(b.y + b.h - base) < 3);
      if (aligned.length !== key.barras.length) {
        problems.push(`esperava ${key.barras.length} barras, achei ${aligned.length}`);
      } else {
        const peak = Math.max(...key.barras.map((b) => b.valor));
        const hPeak = Math.max(...aligned.map((b) => b.h));
        barErr = Math.max(...aligned.map((b, k) => Math.abs(b.h / hPeak - key.barras[k].valor / peak)));
        if (barErr > 0.02) problems.push(`barras fora de proporção (erro ${(barErr * 100).toFixed(1)}%)`);
      }
    }
    results[name] = { correto: problems.length === 0, problemas: [...new Set(problems)], erro_barras: barErr };
  }
} finally {
  await browser.close();
}
await fs.writeFile(output, JSON.stringify(results, null, 2), "utf8");
const ok = Object.values(results).filter((r) => r.correto).length;
console.log(`${ok}/${Object.keys(results).length} diagramas corretos → ${output}`);
