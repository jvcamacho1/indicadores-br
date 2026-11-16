/*
 * Painel: lê data.json (gerado pelo pipeline) e desenha blocos, gráficos e tabela.
 * O português está no HTML; o inglês fica em EN. Gráficos com Chart.js.
 */
const EN = {
  marca: "BR Indicators",
  titulo: "Brazil economic indicators",
  lead: "Interest rates, inflation, FX, activity, and unemployment in one place, from the public APIs of Brazil's Central Bank and IBGE. The data goes through a data engineering pipeline with Airflow and dbt, described at the end of the page.",
  sintetico: "Warning: this version was built with synthetic test data, not the real data.",
  ultimos: "Latest value of each indicator",
  periodo: "Period",
  p5: "5 years", p10: "10 years", ptudo: "All",
  "g.juros": "Interest and inflation",
  "g.juros.sub": "Selic target, 12-month IPCA inflation, and the resulting real interest rate (% per year).",
  "g.dolar": "US dollar", "g.dolar.sub": "Monthly average, BRL per USD",
  "g.ibc": "Economic activity", "g.ibc.sub": "IBC-Br, 12-month change (%)",
  "g.deso": "Unemployment", "g.deso.sub": "Unemployment rate, rolling quarter (%)",
  tabela: "See the data as a table",
  como: "How it works",
  "como.lead": "An ELT pipeline that runs locally with Docker and publishes only this static site. The code is open source.",
  "arq.bcb": "5 series", "arq.af": "monthly · retries · backfill", "arq.raw": "idempotent upsert",
  "arq.dbt1": "incremental fact · dimensions", "arq.dbt2": "tests · unit tests · freshness",
  "arq.dbt3": "docs with lineage", "arq.site": "This site",
  "c1.t": "Orchestration",
  c1: "Monthly DAG with <code>catchup</code>: backfilling since 2015 is one command. One task per indicator (dynamic task mapping), retries with exponential backoff, and a 3-month lookback window on every run, because IPCA is released the following month and series get revised.",
  "c2.t": "Idempotent loading",
  c2: "Upsert by (indicator, date) into the <code>raw</code> schema. Re-running never duplicates, and a source revision only changes what changed. Every run is logged in <code>raw.cargas</code>, which feeds <code>source freshness</code>.",
  "c3.t": "Modeling",
  c3: "Staging per source, an intermediate layer that brings everything to monthly grain using the catalog's aggregation rule, and marts with an incremental <code>fct_indicador_mensal</code>, <code>dim_indicador</code>, <code>dim_calendario</code>, and the dashboard mart.",
  "c4.t": "Quality",
  c4: "Key, relationship, and plausible-range tests; a test that reconciles the published 12-month IPCA with the compounded monthly changes; and dbt unit tests for the real interest rate (Fisher equation).",
  "l.docs": "Documentation and lineage (dbt docs)", "l.repo": "Code on GitHub", "l.port": "Portfolio",
  rodape: "Sources: Central Bank of Brazil (SGS) and IBGE (SIDRA). The data is public; this site is not affiliated with those institutions. Built by José Camacho.",
};

const TXT = {
  pt: {
    dadosAte: (m) => `Dados até ${m}`, geradoEm: (d) => `Gerado em ${d}`,
    em12: "em 12 meses", pp: "p.p.", mes: "Mês",
    tiles: { selic_meta: "Selic (meta)", ipca_12m: "IPCA 12 meses", juros_real: "Juros real", dolar_venda: "Dólar (média)", ibc_br_var_12m: "IBC-Br, 12 meses", desocupacao: "Desemprego" },
    series: { selic_meta: "Selic", ipca_12m: "IPCA 12m", juros_real: "Juros real", dolar_venda: "Dólar", ibc_br_var_12m: "IBC-Br 12m", desocupacao: "Desocupação" },
  },
  en: {
    dadosAte: (m) => `Data through ${m}`, geradoEm: (d) => `Built on ${d}`,
    em12: "over 12 months", pp: "p.p.", mes: "Month",
    tiles: { selic_meta: "Selic (target)", ipca_12m: "IPCA 12 months", juros_real: "Real interest", dolar_venda: "USD/BRL (avg)", ibc_br_var_12m: "IBC-Br, 12 months", desocupacao: "Unemployment" },
    series: { selic_meta: "Selic", ipca_12m: "IPCA 12m", juros_real: "Real rate", dolar_venda: "USD/BRL", ibc_br_var_12m: "IBC-Br 12m", desocupacao: "Unemployment" },
  },
};

const UNIDADE = { selic_meta: "%", ipca_12m: "%", juros_real: "%", dolar_venda: "R$", ibc_br_var_12m: "%", desocupacao: "%" };

const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* sem storage */ } },
};

const estado = { lang: "pt", anos: 10, dados: null, graficos: [] };
const root = document.documentElement;

/* ---------- idioma ---------- */
const nodes = document.querySelectorAll("[data-i18n]");
const PT = {};
nodes.forEach((el) => { PT[el.dataset.i18n] = el.innerHTML; });

function aplicarIdioma(lang) {
  estado.lang = lang;
  const dict = lang === "en" ? EN : PT;
  nodes.forEach((el) => { if (dict[el.dataset.i18n] !== undefined) el.innerHTML = dict[el.dataset.i18n]; });
  root.lang = lang === "en" ? "en" : "pt-BR";
  const t = document.querySelector("title");
  t.dataset.titlePt = t.dataset.titlePt || t.textContent;
  t.textContent = lang === "en" ? t.dataset.titleEn : t.dataset.titlePt;
  document.querySelectorAll("#idioma button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === lang)));
  store.set("lang", lang);
  if (estado.dados) desenhar();
}

/* ---------- formatação ---------- */
const fmt = (v, casas = 2) => v == null ? "–" : new Intl.NumberFormat(estado.lang === "en" ? "en-US" : "pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas }).format(v);
const fmtMes = (iso) => {
  const [a, m] = iso.split("-").map(Number);
  return new Intl.DateTimeFormat(estado.lang === "en" ? "en-US" : "pt-BR", { month: "short", year: "numeric", timeZone: "UTC" }).format(new Date(Date.UTC(a, m - 1, 1)));
};
const cor = (nome) => getComputedStyle(root).getPropertyValue(nome).trim();

/* ---------- blocos ---------- */
function ultimo(meses, campo) {
  for (let i = meses.length - 1; i >= 0; i--) if (meses[i][campo] != null) return i;
  return -1;
}

function desenharTiles() {
  const { meses } = estado.dados;
  const t = TXT[estado.lang];
  const html = Object.keys(UNIDADE).map((campo) => {
    const i = ultimo(meses, campo);
    if (i < 0) return "";
    const v = meses[i][campo];
    const antes = i >= 12 ? meses[i - 12][campo] : null;
    let delta = "";
    if (antes != null) {
      if (campo === "dolar_venda") {
        const d = (v / antes - 1) * 100;
        delta = `${d >= 0 ? "+" : ""}${fmt(d, 1)}% ${t.em12}`;
      } else {
        const d = v - antes;
        delta = `${d >= 0 ? "+" : ""}${fmt(d, 2)} ${t.pp} ${t.em12}`;
      }
    }
    const valor = campo === "dolar_venda" ? `R$ ${fmt(v, 2)}` : `${fmt(v, 2)}%`;
    return `<div class="tile"><div class="rotulo">${t.tiles[campo]} · ${fmtMes(meses[i].mes)}</div><div class="valor">${valor}</div><div class="delta">${delta}</div></div>`;
  }).join("");
  document.getElementById("tiles").innerHTML = html;
}

/* ---------- gráficos ---------- */
const rotulosDiretos = {
  id: "rotulosDiretos",
  afterDatasetsDraw(chart, _a, opts) {
    if (!opts || !opts.ativo) return;
    const { ctx, chartArea } = chart;
    const itens = chart.data.datasets.map((ds, i) => {
      const meta = chart.getDatasetMeta(i);
      let j = ds.data.length - 1;
      while (j >= 0 && ds.data[j] == null) j--;
      if (j < 0 || meta.hidden) return null;
      return { y: meta.data[j].y, x: meta.data[j].x, texto: ds.label, corSerie: ds.borderColor };
    }).filter(Boolean).sort((a, b) => a.y - b.y);
    for (let k = 1; k < itens.length; k++) itens[k].y = Math.max(itens[k].y, itens[k - 1].y + 15);
    ctx.save();
    ctx.font = "600 12px system-ui, sans-serif";
    ctx.textBaseline = "middle";
    itens.forEach((it) => {
      const x = Math.min(it.x, chartArea.right) + 8;
      ctx.fillStyle = it.corSerie;
      ctx.beginPath(); ctx.arc(x + 3, it.y, 3, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = cor("--text");
      ctx.fillText(it.texto, x + 10, it.y);
    });
    ctx.restore();
  },
};

const cruz = {
  id: "cruz",
  afterDatasetsDraw(chart) {
    const ativo = chart.tooltip && chart.tooltip.getActiveElements();
    if (!ativo || !ativo.length) return;
    const x = ativo[0].element.x;
    const { ctx, chartArea } = chart;
    ctx.save();
    ctx.strokeStyle = cor("--muted");
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.beginPath(); ctx.moveTo(x, chartArea.top); ctx.lineTo(x, chartArea.bottom); ctx.stroke();
    ctx.restore();
  },
};

function grafico(id, meses, series, { legenda = false, diretos = false, sufixo = "%", casas = 2, zero = false, marcasX = 6 } = {}) {
  const t = TXT[estado.lang];
  const texto = cor("--muted");
  const grade = cor("--grid");
  const c = new Chart(document.getElementById(id), {
    type: "line",
    data: {
      labels: meses.map((m) => m.mes),
      datasets: series.map(([campo, corVar]) => ({
        label: t.series[campo],
        data: meses.map((m) => m[campo]),
        borderColor: cor(corVar),
        backgroundColor: cor(corVar),
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHoverBorderWidth: 2,
        pointHoverBorderColor: cor("--surface"),
        spanGaps: false,
        tension: 0,
      })),
    },
    options: {
      maintainAspectRatio: false,
      animation: false,
      interaction: { mode: "index", intersect: false },
      layout: { padding: { right: diretos ? 84 : 4 } },
      scales: {
        x: {
          ticks: { color: texto, maxRotation: 0, autoSkip: true, maxTicksLimit: marcasX, callback(v) { return fmtMes(this.getLabelForValue(v)); } },
          grid: { display: false },
          border: { color: grade },
        },
        y: {
          ticks: { color: texto, maxTicksLimit: 6, callback: (v) => `${fmt(v, sufixo === "%" ? 0 : 1)}${sufixo === "%" ? "%" : ""}` },
          grid: { color: (ctx) => (zero && ctx.tick.value === 0 ? texto : grade) },
          border: { display: false },
        },
      },
      plugins: {
        legend: { display: legenda, position: "top", align: "start", labels: { color: cor("--text"), usePointStyle: true, pointStyle: "line", boxWidth: 24 } },
        tooltip: {
          backgroundColor: cor("--surface"), titleColor: cor("--text"), bodyColor: cor("--text"),
          borderColor: cor("--border"), borderWidth: 1, padding: 10, usePointStyle: true,
          callbacks: {
            title: (itens) => fmtMes(itens[0].label),
            label: (item) => ` ${item.dataset.label}: ${item.raw == null ? "–" : (sufixo === "R$" ? "R$ " + fmt(item.raw, casas) : fmt(item.raw, casas) + "%")}`,
          },
        },
        rotulosDiretos: { ativo: diretos },
      },
    },
    plugins: [rotulosDiretos, cruz],
  });
  estado.graficos.push(c);
}

function recorte() {
  const { meses } = estado.dados;
  if (!estado.anos) return meses;
  return meses.slice(-estado.anos * 12);
}

function desenharGraficos() {
  estado.graficos.forEach((g) => g.destroy());
  estado.graficos = [];
  const meses = recorte();
  grafico("c-juros", meses, [["selic_meta", "--series-1"], ["ipca_12m", "--series-2"], ["juros_real", "--series-3"]], { legenda: true, diretos: true, zero: true });
  grafico("c-dolar", meses, [["dolar_venda", "--series-1"]], { sufixo: "R$", casas: 2, marcasX: 3 });
  grafico("c-ibc", meses, [["ibc_br_var_12m", "--series-1"]], { zero: true, marcasX: 3 });
  grafico("c-deso", meses, [["desocupacao", "--series-1"]], { casas: 1, marcasX: 3 });
}

function desenharTabela() {
  const t = TXT[estado.lang];
  const campos = Object.keys(UNIDADE);
  const linhas = [...recorte()].reverse();
  const cab = `<thead><tr><th>${t.mes}</th>${campos.map((c) => `<th>${t.tiles[c]}</th>`).join("")}</tr></thead>`;
  const corpo = linhas.map((m) => `<tr><td>${fmtMes(m.mes)}</td>${campos.map((c) => `<td>${fmt(m[c], c === "desocupacao" ? 1 : 2)}</td>`).join("")}</tr>`).join("");
  document.getElementById("tabela").innerHTML = cab + `<tbody>${corpo}</tbody>`;
}

function desenharMeta() {
  const d = estado.dados;
  const t = TXT[estado.lang];
  const ultimoMes = d.meses.length ? d.meses[ultimo(d.meses, "selic_meta")].mes : null;
  document.getElementById("meta-dados").textContent = ultimoMes ? t.dadosAte(fmtMes(ultimoMes)) : "";
  const gerado = new Intl.DateTimeFormat(estado.lang === "en" ? "en-US" : "pt-BR", { dateStyle: "medium" }).format(new Date(d.gerado_em));
  document.getElementById("meta-gerado").textContent = t.geradoEm(gerado);
  document.getElementById("aviso-sintetico").hidden = !d.sintetico;
}

function desenhar() {
  desenharMeta();
  desenharTiles();
  desenharGraficos();
  desenharTabela();
}

/* ---------- controles ---------- */
document.querySelectorAll("#idioma button").forEach((b) => b.addEventListener("click", () => aplicarIdioma(b.dataset.lang)));
document.querySelectorAll("#periodo button").forEach((b) => b.addEventListener("click", () => {
  estado.anos = Number(b.dataset.anos);
  document.querySelectorAll("#periodo button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
  desenharGraficos();
  desenharTabela();
}));
const temaSalvo = store.get("tema");
if (temaSalvo) root.dataset.theme = temaSalvo;
document.getElementById("tema").addEventListener("click", () => {
  const escuro = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = escuro ? "light" : "dark";
  store.set("tema", root.dataset.theme);
  if (estado.dados) desenharGraficos();
});
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { if (estado.dados && !root.dataset.theme) desenharGraficos(); });

const langInicial = store.get("lang") || ((navigator.language || "pt").toLowerCase().startsWith("pt") ? "pt" : "en");
aplicarIdioma(langInicial);

fetch("data.json")
  .then((r) => r.json())
  .then((d) => { estado.dados = d; desenhar(); })
  .catch((e) => {
    document.getElementById("tiles").textContent = "Não foi possível carregar data.json / Could not load data.json";
    console.error(e);
  });
