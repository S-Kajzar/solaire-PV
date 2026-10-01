// Tests du moteur de correction sur la configuration du sujet : node source/tests/grading.test.js
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const page = fs.readFileSync(path.join(__dirname, "..", "..", "index.html"), "utf8");
const ctx = { window: {}, module: undefined };
vm.createContext(ctx);
vm.runInContext(page.match(/<script>(window\.__PARTS__[\s\S]*?)<\/script>/)[1], ctx);
vm.runInContext(page.match(/\/\*GRADING-START\*\/([\s\S]*?)\/\*GRADING-END\*\//)[1] + ";this.Grading=Grading;", ctx);
const G = ctx.Grading, Q = ctx.window.__QCFG__;

// [id, saisie, score attendu]
const CASES = [
  ["q1_1", "Régulateur", 1], ["q1_1", "regulateur de charge", 1], ["q1_1", "Régulatuer", 1], ["q1_1", "onduleur", 0],
  ["q1_2", "les batteries", 1], ["q1_2", "Accumulateurs", 1], ["q1_2", "baterie", 1], ["q1_2", "régulateur", 0],
  ["q1_3", "Onduleur", 1], ["q1_3", "convertisseur continu/alternatif", 1], ["q1_3", "convertisseur DC AC", 1], ["q1_3", "batterie", 0],
  ["q1_4", "réguler", 1], ["q1_4", "Contrôler la charge", 1], ["q1_4", "protéger les batteries", 1], ["q1_4", "régulateur", 0], ["q1_4", "stocker", 0],
  ["q1_5", "stocker", 1], ["q1_5", "Stockage de l'énergie", 1], ["q1_5", "emmagasiner", 1], ["q1_5", "convertir", 0],
  ["q1_6", "convertir", 1], ["q1_6", "Conversion continu alternatif", 1], ["q1_6", "stocker", 0],
  ["q1_7", "STOCKER", 1], ["q1_7", "distribuer", 0],
  ["q1_8", "panneaux photovoltaïques", 1], ["q1_8", "Panneau solaire", 1], ["q1_8", "regulateur", 0],
  ["q1_9", "régulateur", 1], ["q1_9", "onduleur", 0],
  ["q1_10", "batteries", 1], ["q1_10", "onduleur", 0],
  ["q1_11", "onduleur", 1], ["q1_11", "inverseur de source", 0],
  ["q1_12", "pompe", 1], ["q1_12", "moteur de la pompe", 1], ["q1_12", "Motopompe", 1], ["q1_12", "onduleur", 0],
  ["q1_13", "énergie solaire", 1], ["q1_13", "Lumineuse", 1], ["q1_13", "rayonnement", 1], ["q1_13", "électrique", 0],
  ["q1_14", "énergie électrique continue", 1], ["q1_14", "electrique continu", 1], ["q1_14", "électrique", 0], ["q1_14", "électrique alternative", 0],
  ["q1_15", "électrique alternative", 1], ["q1_15", "Energie electrique alternatif", 1], ["q1_15", "électrique continue", 0], ["q1_15", "électrique", 0],
  ["q1_16", "énergie hydraulique", 1], ["q1_16", "eau sous pression", 1], ["q1_16", "mécanique", 0], ["q1_16", "électrique", 0],
  ["q2_1", "34", 1], ["q2_1", "34 cellules", 1], ["q2_1", "n = 34", 1], ["q2_1", "35", 0], ["q2_1", "8,5", 0],
  ["q2_2", "4,41 A", 1], ["q2_2", "I = 4.41 A", 1], ["q2_2", "4,41 ampères", 1], ["q2_2", "4,41", 0.5], ["q2_2", "4,41 V", 0.5], ["q2_2", "4,4 A", 0], ["q2_2", "4,42 A", 0],
  ["q2_3", "10", 1], ["q2_3", "10 branches", 1], ["q2_3", "9,8", 0], ["q2_3", "9", 0],
  ["q2_4", "340", 1], ["q2_4", "340 cellules", 1], ["q2_4", "306", 0],
  ["q2_5", "série", 1], ["q2_5", "En serie", 1], ["q2_5", "parallèle", 0], ["q2_5", "dérivation", 0],
  ["q2_6", "parallèle", 1], ["q2_6", "en dérivation", 1], ["q2_6", "Parralèle", 1], ["q2_6", "série", 0],
  ["q3_1", "1406,25 W", 1], ["q3_1", "1 406,25 W", 1], ["q3_1", "Pa = 1406.25 watts", 1], ["q3_1", "1,41 kW", 1], ["q3_1", "1406,25", 0.5],
  ["q3_1", "1406,25 Wh", 0.5], ["q3_1", "1,41", 0], ["q3_1", "576 W", 0], ["q3_1", "1406 W", 0],
  ["q3_2", "1406,25 Wh", 1], ["q3_2", "1406,25 W.h", 1], ["q3_2", "1406,25 W·h", 1], ["q3_2", "1406,25 Wh/j", 1], ["q3_2", "1406,25 Wh par jour", 1],
  ["q3_2", "1,41 kWh", 1], ["q3_2", "1406,25 W", 0.5], ["q3_2", "1406,25", 0.5], ["q3_2", "900 Wh", 0],
  ["q3_3", "10044,64 Wh", 1], ["q3_3", "10 044,64 W.h", 1], ["q3_3", "10044,65 Wh", 1], ["q3_3", "10,04 kWh", 1], ["q3_3", "10044,64", 0.5],
  ["q3_3", "10044,64 W", 0.5], ["q3_3", "9843,75 Wh", 0], ["q3_3", "9646,88 Wh", 0], ["q3_3", "10,04", 0],
  ["q3_4", "2", 1], ["q3_4", "2 batteries", 1], ["q3_4", "4", 0],
  ["q3_5", "24 V", 1], ["q3_5", "24 volts", 1], ["q3_5", "24", 0.5], ["q3_5", "24 A", 0.5], ["q3_5", "12 V", 0],
  ["q3_6", "5160 Wh", 1], ["q3_6", "5 160 W.h", 1], ["q3_6", "5,16 kWh", 1], ["q3_6", "5160", 0.5], ["q3_6", "10320 Wh", 0], ["q3_6", "2580 Wh", 0],
  ["q3_7", "1,95", 1], ["q3_7", "1.95", 1], ["q3_7", "1,9", 0], ["q3_7", "2", 0],
  ["q3_8", "2", 1], ["q3_8", "2 ensembles", 1], ["q3_8", "1", 0],
  ["q3_9", "parallèle", 1], ["q3_9", "en dérivation", 1], ["q3_9", "série", 0],
  ["q3_10", "4", 1], ["q3_10", "4 batteries", 1], ["q3_10", "2", 0],
  ["q3_11", "24 V", 1], ["q3_11", "24", 0.5], ["q3_11", "48 V", 0],
  ["q3_12", "430 Ah", 1], ["q3_12", "430 A.h", 1], ["q3_12", "430 A·h", 1], ["q3_12", "430", 0.5], ["q3_12", "430 Wh", 0.5], ["q3_12", "215 Ah", 0],
  ["q3_13", "7,84 A", 1], ["q3_13", "7,83 A", 1], ["q3_13", "I = 7,84 ampères", 1], ["q3_13", "7,84", 0.5], ["q3_13", "5,02 A", 0], ["q3_13", "7,85 A", 0],
  ["q3_14", "1434,95 W", 1], ["q3_14", "1,43 kW", 1], ["q3_14", "1434,95", 0.5], ["q3_14", "1378,13 W", 0],
  ["q3_15", "59,79 A", 1], ["q3_15", "59.79 A", 1], ["q3_15", "59,79", 0.5], ["q3_15", "6,24 A", 0], ["q3_15", "58,59 A", 0],
  ["q3_16", "7,19 h", 1], ["q3_16", "7,19 heures", 1], ["q3_16", "t = 7.19 h", 1], ["q3_16", "7,19", 0.5], ["q3_16", "7,19 min", 0.5], ["q3_16", "7,2 h", 0], ["q3_16", "7 h 11 min", 0],
];

let fail = 0;
const seen = new Set();
for (const [id, ans, want] of CASES) {
  if (!Q[id]) { console.log("question inconnue", id); fail++; continue; }
  seen.add(id);
  const r = G.grade(ans, Q[id].grader);
  const got = r.invalid ? 0 : r.score;
  if (got !== want) { fail++; console.log("ÉCHEC", id, JSON.stringify(ans), "attendu", want, "obtenu", got, JSON.stringify(r)); }
}
for (const id of Object.keys(Q)) {
  const scores = CASES.filter(c => c[0] === id).map(c => c[2]);
  if (!scores.includes(1) || !scores.includes(0)) { fail++; console.log("Cas juste ET faux manquants pour", id); }
}
console.log(CASES.length + " cas, " + Object.keys(Q).length + " questions, " + fail + " échec(s)");
process.exit(fail ? 1 : 0);
