// Parcours navigateur : node source/tests/browser.test.js [dossier-captures]
"use strict";
const path = require("path");
let playwright;
try { playwright = require("playwright"); } catch (e) { playwright = require(require("child_process").execSync("npm root -g").toString().trim() + "/playwright"); }

const URL = "file://" + path.join(__dirname, "..", "..", "index.html");
const SHOTS = process.argv[2] || null;
const GOOD = {
  q1_1: "régulateur", q1_2: "batteries", q1_3: "onduleur", q1_4: "réguler", q1_5: "stocker", q1_6: "convertir",
  q1_7: "stocker", q1_8: "panneaux photovoltaïques", q1_9: "régulateur", q1_10: "batteries", q1_11: "onduleur",
  q1_12: "pompe", q1_13: "énergie solaire", q1_14: "électrique continue", q1_15: "électrique alternative",
  q1_16: "hydraulique", q2_1: "34", q2_2: "4,41 A", q2_3: "10", q2_4: "340", q2_5: "série", q2_6: "parallèle",
  q3_1: "1406,25 W", q3_2: "1406,25 Wh", q3_3: "10044,64 Wh", q3_4: "2", q3_5: "24 V", q3_6: "5160 Wh",
  q3_7: "1,95", q3_8: "2", q3_9: "parallèle", q3_10: "4", q3_11: "24 V", q3_12: "430 Ah", q3_13: "7,84 A",
  q3_14: "1434,95 W", q3_15: "59,79 A", q3_16: "7,19 h",
};

let fail = 0;
function check(cond, msg) { console.log((cond ? "ok   " : "ÉCHEC") + " " + msg); if (!cond) fail++; }

async function open(browser, w) {
  const page = await browser.newPage({ viewport: { width: w || 1400, height: 900 } });
  page.errors = [];
  page.on("pageerror", e => page.errors.push(String(e)));
  page.on("console", m => { if (m.type() === "error") page.errors.push(m.text()); });
  await page.goto(URL);
  return page;
}
const visible = (page, sel) => page.locator(sel).first().isVisible();

(async () => {
  const browser = await playwright.chromium.launch();

  // ---------- accueil ----------
  let page = await open(browser);
  check(await visible(page, "#home"), "accueil affiché");
  check(!(await visible(page, "main.page")) && !(await visible(page, ".banner")), "sujet et bandeau masqués avant choix du mode");
  const facts = await page.locator(".home-facts b").allTextContents();
  check(facts.length === 4, "quatre chiffres clés : " + facts.join(" | "));
  if (SHOTS) await page.screenshot({ path: SHOTS + "/accueil.png", fullPage: true });

  // ---------- entraînement : tout juste ----------
  await page.click(".btn-mode[data-mode=training]");
  check(await visible(page, "main.page"), "entraînement : sujet affiché");
  await page.click(".qbar .doc-chip[data-doc=DP2]");
  check(await page.evaluate(() => document.body.classList.contains("panel-open")), "un repère de document ouvre le panneau");
  check(await visible(page, "#doc-DP2 .doc-img"), "le panneau affiche DP2");
  if (SHOTS) await page.screenshot({ path: SHOTS + "/panneau-documents.png" });
  await page.click("#dp-close");
  for (const [id, v] of Object.entries(GOOD)) {
    await page.fill("#in-" + id, v);
    await page.click("#" + id + " .btn-validate");
  }
  const ko = await page.locator(".q.is-ko, .q.is-half").count();
  check(ko === 0, "toutes les bonnes réponses sont jugées justes (" + ko + " écart)");
  check(await page.locator(".q-input:not([disabled])").count() === 0, "réponses verrouillées après validation");
  check(await page.locator(".q .q-expl:not([hidden])").count() === 38, "38 démarches affichées");
  const fin = (await page.locator(".recap .final-note").textContent()).trim();
  check(fin === "20,0/20", "sujet parfait = 20/20 (" + fin + ")");
  check((await page.locator("#score-val").textContent()).startsWith("20,0"), "bandeau à 20/20");
  check(await page.locator(".btn-print").count() === 1, "un seul bouton « Imprimer ma copie »");
  check(/^\d:\d\d:\d\d$/.test(await page.locator("#timer-val").textContent()), "chronomètre au format h:mm:ss");
  await page.fill("#nom-eleve", "Élève Test");
  await page.evaluate(() => window.dispatchEvent(new Event("beforeprint")));
  await page.emulateMedia({ media: "print" });
  check(await visible(page, ".print-summary") && !(await visible(page, ".banner")), "impression : en-tête de copie, bandeau masqué");
  check((await page.locator(".print-mode").first().textContent()) === "entraînement", "impression : mode indiqué");
  check((await page.locator(".print-time").first().textContent()).length > 0, "impression : temps de rédaction indiqué");
  if (SHOTS) await page.pdf({ path: SHOTS + "/copie-entrainement.pdf" });
  check(page.errors.length === 0, "aucune erreur JavaScript (entraînement) " + page.errors.join(" / "));
  await page.close();

  // ---------- entraînement : notation partielle et demi-point ----------
  page = await open(browser);
  await page.click(".btn-mode[data-mode=training]");
  await page.fill("#in-q2_2", "4,41"); await page.click("#q2_2 .btn-validate");
  check(await page.locator("#q2_2.is-half").count() === 1, "valeur juste sans unité : demi-point");
  check(!(await page.locator("#q2_2 .q-unit-msg").isHidden()), "message « Unité manquante » affiché");
  await page.fill("#in-q2_1", "35"); await page.click("#q2_1 .btn-validate");
  check(await page.locator("#q2_1.is-ko").count() === 1, "valeur fausse : 0");
  await page.click("#q2_3 .btn-validate");
  check((await page.locator("#q2_3 .q-msg").textContent()).length > 0 && !(await page.locator("#in-q2_3").isDisabled()),
    "validation d'un champ vide refusée");
  const prov = await page.locator("#score-val").textContent();
  check(prov.startsWith("5,0"), "note provisoire renormalisée sur la partie entamée (" + prov + ")");
  if (SHOTS) { await page.locator("#q2_2").scrollIntoViewIfNeeded(); await page.screenshot({ path: SHOTS + "/demi-point.png" }); }
  check(page.errors.length === 0, "aucune erreur JavaScript (partiel)");
  await page.close();

  // ---------- examen ----------
  page = await open(browser);
  await page.click(".btn-mode[data-mode=exam]");
  check(await visible(page, ".exam-state"), "examen : « Note masquée » dans le bandeau");
  check(!(await visible(page, ".btn-validate")), "examen : pas de bouton Valider");
  const entries = Object.entries(GOOD);
  for (const [id, v] of entries.slice(0, 30)) await page.fill("#in-" + id, v);
  await page.fill("#in-q1_1", "onduleur");
  await page.fill("#in-q1_1", "régulateur"); // modifiable avant la remise
  check(await page.locator(".q .q-expl:not([hidden])").count() === 0, "examen : aucune correction avant la remise");
  check(!(await visible(page, "#recap-graded")), "examen : récapitulatif masqué avant la remise");
  await page.evaluate(() => window.dispatchEvent(new Event("beforeprint")));
  await page.emulateMedia({ media: "print" });
  check(await visible(page, ".print-nograde"), "impression avant remise : « Copie non corrigée »");
  check(!(await visible(page, ".print-note-line")) && !(await page.locator(".q-expl").first().isVisible()),
    "impression avant remise : ni note ni corrigé");
  if (SHOTS) await page.pdf({ path: SHOTS + "/copie-examen-non-corrigee.pdf" });
  await page.emulateMedia({ media: "screen" });
  await page.click("#exam-submit");
  const warn = await page.locator("#exam-warn").textContent();
  check(/8 réponse\(s\) encore vide/.test(warn), "confirmation en deux temps avec nombre de vides (" + warn + ")");
  const t1 = await page.locator("#timer-val").textContent();
  await page.click("#exam-submit");
  check(await page.evaluate(() => document.body.classList.contains("graded")), "copie corrigée après confirmation");
  check(await page.locator(".q-input:not([disabled])").count() === 0, "examen : tout est verrouillé");
  check(await page.locator(".q .q-expl:not([hidden])").count() === 38, "examen : corrections dévoilées");
  const exFin = (await page.locator(".recap .final-note").textContent()).trim();
  // 8 questions vides de la partie 3 : 8/16 → 10/20 sur la partie 3 (poids 45/80) ; parties 1 et 2 à 20/20
  const expected = (20 * 35 / 80 + 10 * 45 / 80).toFixed(1).replace(".", ",") + "/20";
  check(exFin === expected, "note examen pondérée " + exFin + " (attendu " + expected + ")");
  await page.waitForTimeout(1300);
  check((await page.locator("#timer-val").textContent()) === (await page.locator("#timer-val").textContent()) &&
    (await page.evaluate(() => { const a = window.__app__.elapsedMs(); return new Promise(r => setTimeout(() => r(window.__app__.elapsedMs() === a), 1100)); })),
    "chronomètre arrêté à la remise (" + t1 + ")");
  if (SHOTS) { await page.locator("#recap").scrollIntoViewIfNeeded(); await page.screenshot({ path: SHOTS + "/recap-examen.png" }); }
  check(page.errors.length === 0, "aucune erreur JavaScript (examen) " + page.errors.join(" / "));
  await page.close();

  // ---------- mobile ----------
  page = await open(browser, 390);
  await page.click(".btn-mode[data-mode=training]");
  check(await visible(page, "#btn-docs") && !(await visible(page, ".rail")), "mobile : bouton « Documents » à la place du rail");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check(overflow <= 0, "mobile : pas de défilement horizontal (" + overflow + " px)");
  if (SHOTS) await page.screenshot({ path: SHOTS + "/mobile.png" });
  await page.close();

  await browser.close();
  console.log(fail ? fail + " échec(s)" : "Tous les tests navigateur passent");
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
