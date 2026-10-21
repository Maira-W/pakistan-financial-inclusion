"use strict";
(function () {
  if (typeof Plotly === "undefined") {
    document.body.insertAdjacentHTML("afterbegin",
      '<p style="padding:14px 16px;margin:0;background:#fde8e1;color:#a5391f">The charts need an internet connection to load Plotly. Reload when you are online.</p>');
    return;
  }

  // ---------------------------------------------------------------- constants and helpers
  const C = { navy: "#1F3B57", teal: "#2A9D8F", orange: "#E76F51", amber: "#E9C46A", grey: "#8D99AE", purple: "#7B2CBF",
              ink: "#1d2733", muted: "#5b6777", grid: "#eceff4", pale: "#B8C2CE" };
  const PROV = { "Punjab": C.navy, "Sindh": C.teal, "Khyber Pakhtunkhwa": C.orange, "Balochistan": C.amber, "Islamabad": C.purple };
  const CLUSTERS = ["Frontier and remote", "Developing rural", "Established districts", "Metropolitan hubs"];
  const CLUSTER_COL = { "Frontier and remote": C.orange, "Developing rural": C.amber, "Established districts": C.teal, "Metropolitan hubs": C.navy };
  const SOUTH_ASIA = ["AFG", "BGD", "BTN", "IND", "LKA", "MDV", "NPL", "PAK"];
  const REPO = "https://github.com/Maira-W/pakistan-financial-inclusion";

  const U = DATA.units, H = DATA.headline, byId = {};
  U.forEach(u => { byId[u.id] = u; });

  const $ = id => document.getElementById(id);
  const nf0 = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
  const f0 = v => (v == null || isNaN(v)) ? "n/a" : nf0.format(Math.round(v));
  const f1 = v => (v == null || isNaN(v)) ? "n/a" : Number(v).toFixed(1);
  const f2 = v => (v == null || isNaN(v)) ? "n/a" : Number(v).toFixed(2);
  const f3 = v => (v == null || isNaN(v)) ? "n/a" : Number(v).toFixed(3);
  const pct = (v, d = 0) => (v == null || isNaN(v)) ? "n/a" : Number(v).toFixed(d) + "%";
  const ord = n => n + (["th", "st", "nd", "rd"][(n % 100 > 10 && n % 100 < 14) ? 0 : (n % 10 < 4 ? n % 10 : 0)]);
  const sum = (a, f) => a.reduce((s, x) => s + (f ? f(x) : x), 0);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  const CFG = { responsive: true, displaylogo: false, modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines"] };
  function layout(extra) {
    return Object.assign({
      font: { family: "system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif", size: 12, color: C.ink },
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", margin: { t: 10, r: 16, b: 48, l: 56 },
      hoverlabel: { font: { size: 12 } }, legend: { orientation: "h", y: -0.18 }
    }, extra);
  }
  function draw(id, traces, extra) { return Plotly.react(id, traces, layout(extra), CFG); }
  const axis = (extra) => Object.assign({ gridcolor: C.grid, zeroline: false, linecolor: "#c9d1dc" }, extra);

  // ---------------------------------------------------------------- tabs
  const rendered = {};
  const renderers = {};
  function show(name, scroll) {
    if (!renderers[name]) name = "overview";
    document.querySelectorAll("section.tab").forEach(s => { s.hidden = s.id !== "tab-" + name; });
    document.querySelectorAll("#tablist button").forEach(b => b.setAttribute("aria-selected", String(b.dataset.tab === name)));
    if (!rendered[name]) { renderers[name](); rendered[name] = true; }
    else document.querySelectorAll("#tab-" + name + " .js-plotly-plot").forEach(el => Plotly.Plots.resize(el));
    try { history.replaceState(null, "", "#" + name); } catch (e) { /* file:// pages may refuse */ }
    if (scroll) window.scrollTo({ top: 0, behavior: "smooth" });
  }
  document.querySelectorAll("#tablist button").forEach(b => b.addEventListener("click", () => show(b.dataset.tab, true)));
  document.querySelector("#tablist").addEventListener("keydown", e => {
    const tabs = [...document.querySelectorAll("#tablist button")];
    const i = tabs.findIndex(b => b.getAttribute("aria-selected") === "true");
    if (e.key === "ArrowRight") { tabs[(i + 1) % tabs.length].click(); tabs[(i + 1) % tabs.length].focus(); }
    if (e.key === "ArrowLeft") { tabs[(i + tabs.length - 1) % tabs.length].click(); tabs[(i + tabs.length - 1) % tabs.length].focus(); }
  });

  // ---------------------------------------------------------------- OVERVIEW
  renderers.overview = function () {
    const cc = DATA.crossSummary, p = cc.pakistan, ineq = DATA.inequality;
    const tiles = [
      { label: "Adults with an account, " + DATA.meta.vintages.findex, value: pct(p.account), alert: true,
        note: ord(cc.rank_lowest_account[0]) + " lowest of " + cc.rank_lowest_account[1] + " economies" },
      { label: "Below what income predicts", value: f0(p.shortfall_pts) + " pts",
        note: "Expected " + pct(p.expected) + " at $" + f0(p.gdp_pc_ppp) + " GDP per person (PPP)" },
      { label: "Phone gap, men vs women", value: f0(p.phone_gap) + " pts", alert: true,
        note: "Largest of " + cc.rank_largest_phone_gap[1] + " economies" },
      { label: "Branches per 100,000 people", value: f1(H.branches_per_100k),
        note: H.units_below_half_average + " of " + H.units + " districts are below half of that" },
      { label: "Share of branches in rural areas", value: pct(H.rural_branch_share),
        note: "Rural areas hold " + pct(H.rural_pop_share) + " of people" },
      { label: "Gini of bank branches", value: f3(ineq.banks_2024.gini), note: "No change since 2020 (" + f3(ineq.banks_2020.gini) + ")" }
    ];
    $("kpis").innerHTML = tiles.map(t => '<div class="kpi' + (t.alert ? " alert" : "") + '"><div class="label">' + esc(t.label) +
      '</div><div class="value">' + esc(t.value) + '</div><div class="note">' + esc(t.note) + "</div></div>").join("");
    $("findings").innerHTML = DATA.findings.map(f => "<li><h4>" + esc(f.title) + "</h4><p>" + esc(f.text) +
      '</p><button type="button" data-go="' + f.tab + '">See the evidence</button></li>').join("");
    document.querySelectorAll("#findings button").forEach(b => b.addEventListener("click", () => show(b.dataset.go, true)));
    $("ccView").addEventListener("change", drawCross);
    drawCross();
  };

  function drawCross() {
    const view = $("ccView").value, rows = DATA.cross;
    const key = { account: "account", accountGap: "account_gap", phoneGap: "phone_gap" }[view];
    const sa = r => SOUTH_ASIA.includes(r.country);
    const valid = rows.filter(r => r[key] != null && r.gdp_pc_ppp != null);
    const mk = (subset, color, size, extra) => Object.assign({
      type: "scatter", mode: "markers", x: subset.map(r => r.gdp_pc_ppp), y: subset.map(r => r[key]),
      text: subset.map(r => r.name), marker: { color: color, size: size, line: { color: "white", width: 0.8 } },
      hovertemplate: "<b>%{text}</b><br>GDP per person $%{x:,.0f}<br>%{y:.1f}" + (view === "account" ? "%" : " points") + "<extra></extra>"
    }, extra);
    const traces = [];
    if (view === "account") {
      const s = valid.slice().sort((a, b) => a.gdp_pc_ppp - b.gdp_pc_ppp);
      traces.push({ type: "scatter", mode: "lines", x: s.map(r => r.gdp_pc_ppp), y: s.map(r => r.pred_high), line: { width: 0 }, hoverinfo: "skip", showlegend: false });
      traces.push({ type: "scatter", mode: "lines", x: s.map(r => r.gdp_pc_ppp), y: s.map(r => r.pred_low), line: { width: 0 }, fill: "tonexty",
        fillcolor: "rgba(31,59,87,0.09)", hoverinfo: "skip", name: "90% range for a typical economy" });
      traces.push({ type: "scatter", mode: "lines", x: s.map(r => r.gdp_pc_ppp), y: s.map(r => r.expected_account), line: { color: "#5C6B7C", width: 2 },
        hoverinfo: "skip", name: "Expected at this income" });
    }
    traces.push(mk(valid.filter(r => !sa(r)), C.pale, 8, { name: "Other economies" }));
    traces.push(mk(valid.filter(r => sa(r) && r.country !== "PAK"), C.navy, 11, { name: "South Asia", mode: "markers+text",
      textposition: "top center", textfont: { size: 11, color: C.navy } }));
    traces.push(mk(valid.filter(r => r.country === "PAK"), C.orange, 17, { name: "Pakistan", mode: "markers+text", textposition: "bottom center",
      textfont: { size: 13, color: C.orange } }));
    const ylab = { account: "Adults with an account (%)", accountGap: "Men minus women, account ownership (points)", phoneGap: "Men minus women, phone ownership (points)" }[view];
    draw("ccChart", traces, {
      xaxis: axis({ type: "log", title: "GDP per person, PPP (constant 2021 international $, log scale)", tickvals: [1000, 2000, 5000, 10000, 20000, 50000, 100000], ticktext: ["1k", "2k", "5k", "10k", "20k", "50k", "100k"] }),
      yaxis: axis({ title: ylab, range: view === "account" ? [0, 105] : [-12, view === "phoneGap" ? 72 : 40] }),
      margin: { t: 10, r: 16, b: 72, l: 64 }, legend: { orientation: "h", y: -0.22 }
    });
    const cc = DATA.crossSummary, p = cc.pakistan;
    const rankL = r => (r === 1 ? "largest" : ord(r) + " largest");
    $("ccNote").textContent = {
      account: "Pakistan: " + pct(p.account) + " have an account against " + pct(p.expected) + " expected at its income, " + f0(p.shortfall_pts) + " points short. Line: OLS fit on log income across " + cc.n_economies + " economies.",
      accountGap: "Pakistan's account gap between men and women is " + f0(p.account_gap) + " points, the " + rankL(cc.rank_largest_account_gap[0]) + " of " + cc.rank_largest_account_gap[1] + " economies. Largest: " + cc.largest_account_gaps.map(g => g.name + " " + f0(g.account_gap)).join(", ") + ".",
      phoneGap: "Pakistan's phone ownership gap is " + f0(p.phone_gap) + " points, the " + rankL(cc.rank_largest_phone_gap[0]) + " of " + cc.rank_largest_phone_gap[1] + " economies. Others: " + cc.largest_phone_gaps.filter(g => g.name !== "Pakistan").map(g => g.name + " " + f0(g.phone_gap)).join(", ") + "."
    }[view];
  }

  // ---------------------------------------------------------------- WHO AND WHY
  renderers.who = function () {
    // Segments: hollow 2021, filled 2024
    const seg = {};
    DATA.findex.segments.forEach(s => { (seg[s.segment] = seg[s.segment] || {})[s.year] = s.value; });
    const order = ["Women", "Men", "Poorest 40%", "Richest 60%", "Primary education or less", "Secondary education or more",
      "Out of the labour force", "In the labour force", "Rural", "Urban", "Young adults (15-24)", "Older adults (25+)"].reverse();
    const lost = new Set(["Women", "Poorest 40%", "Out of the labour force"]);
    const lx = [], ly = [];
    order.forEach(n => { const a = seg[n][2021], b = seg[n][2024]; if (a != null && b != null) { lx.push(a, b, null); ly.push(n, n, null); } });
    const color = n => lost.has(n) ? C.orange : C.navy;
    const has21 = order.filter(n => seg[n][2021] != null);
    draw("segChart", [
      { type: "scatter", mode: "lines", x: lx, y: ly, line: { color: "#C5CDD8", width: 5 }, hoverinfo: "skip", showlegend: false },
      { type: "scatter", mode: "markers", name: "2021", x: has21.map(n => seg[n][2021]), y: has21,
        marker: { symbol: "circle-open", size: 12, color: has21.map(color), line: { width: 2.4, color: has21.map(color) } },
        hovertemplate: "%{y}, 2021: %{x:.1f}%<extra></extra>" },
      { type: "scatter", mode: "markers", name: "2024", x: order.map(n => seg[n][2024]), y: order,
        marker: { size: 12, color: order.map(color) }, hovertemplate: "%{y}, 2024: %{x:.1f}%<extra></extra>" },
      { type: "scatter", mode: "text", x: order.map(n => (seg[n][2021] != null ? Math.max(seg[n][2021], seg[n][2024]) : seg[n][2024]) + 1.4), y: order,
        text: order.map(n => f0(seg[n][2024]) + "%"), textposition: "middle right", textfont: { size: 11, color: order.map(color) }, hoverinfo: "skip", showlegend: false }
    ], { xaxis: axis({ title: "Adults with an account (%)", range: [0, 56] }), yaxis: axis({ automargin: true, categoryorder: "array", categoryarray: order }), margin: { l: 150, r: 24, t: 6, b: 58 },
         legend: { orientation: "h", y: -0.16 } });

    // Gender gaps, accounts and phones, Pakistan and neighbours
    const codes = ["PAK", "IND", "BGD", "LKA"], names = { PAK: "Pakistan", IND: "India", BGD: "Bangladesh", LKA: "Sri Lanka" };
    const cs = {}; DATA.cross.forEach(r => { cs[r.country] = r; });
    const xs = [[], []]; const women = [], men = [];
    const who = [];
    [["Accounts", "account_women", "account_men"], ["Phones", "phone_women", "phone_men"]].forEach(([grp, w, m]) => codes.forEach(c => {
      xs[0].push(grp); xs[1].push(c); who.push(names[c]); women.push(cs[c][w]); men.push(cs[c][m]); }));
    const lab = v => f0(v);
    draw("genderChart", [
      { type: "bar", name: "Women", x: xs, y: women, customdata: who, marker: { color: C.orange }, text: women.map(lab), textposition: "outside", cliponaxis: false,
        hovertemplate: "%{customdata}, %{x[0]}: %{y:.1f}%<extra>Women</extra>" },
      { type: "bar", name: "Men", x: xs, y: men, customdata: who, marker: { color: C.navy }, text: men.map(lab), textposition: "outside", cliponaxis: false,
        hovertemplate: "%{customdata}, %{x[0]}: %{y:.1f}%<extra>Men</extra>" }
    ], { barmode: "group", yaxis: axis({ title: "Adults (%)", range: [0, 112] }), xaxis: axis({ tickangle: 0 }), margin: { t: 8, r: 10, b: 70, l: 52 }, legend: { orientation: "h", y: -0.2 } });

    $("barrierView").addEventListener("change", drawBarriers);
    drawBarriers();

    const sers = { "account.t.d": ["Any account", C.navy], "fiaccount.t.d": ["Bank or similar institution", C.grey],
      "mobileaccount.t.d": ["Mobile money", C.teal], "g20.any": ["Made or received a digital payment", C.orange] };
    draw("typesChart", Object.keys(sers).map(k => {
      const v = DATA.findex.series[k].values.PAK;
      return { type: "scatter", mode: "lines+markers", name: sers[k][0], x: v.map(a => a[0]), y: v.map(a => a[1]),
        line: { color: sers[k][1], width: k === "account.t.d" ? 3.2 : 2.2 }, marker: { size: 8 }, hovertemplate: sers[k][0] + ", %{x}: %{y:.1f}%<extra></extra>" };
    }), { xaxis: axis({ tickvals: [2011, 2014, 2017, 2021, 2024] }), yaxis: axis({ title: "Adults (%)", rangemode: "tozero" }), margin: { t: 8, r: 12, b: 80, l: 52 }, legend: { orientation: "h", y: -0.26 } });
  };

  function drawBarriers() {
    const which = $("barrierView").value;
    let rows;
    if (which === "bank") {
      rows = DATA.findex.barriers.map(b => ({ label: b.reason, v: b.share_of_unbanked, derived: b.derived }));
      $("barrierNote").textContent = "Share of adults without a bank or similar account who give each reason. Several reasons can be given. Documentation is derived from the all-adults figure.";
    } else {
      rows = DATA.findex.mmBarriers.map(b => ({ label: b.reason, v: b.value, derived: false }));
      $("barrierNote").textContent = "Share of all adults aged 15 and over, as published by the World Bank for mobile money. This is not a share of adults without an account, so it cannot be compared with the bank view.";
    }
    rows.sort((a, b) => a.v - b.v);
    const top = Math.max(...rows.map(r => r.v));
    draw("barrierChart", [{
      type: "bar", orientation: "h", x: rows.map(r => r.v), y: rows.map(r => r.label),
      marker: { color: rows.map(r => r.v === top ? C.orange : C.navy), pattern: { shape: rows.map(r => r.derived ? "/" : "") } },
      text: rows.map(r => f0(r.v) + "%"), textposition: "outside", cliponaxis: false, hovertemplate: "%{y}: %{x:.1f}%<extra></extra>"
    }], { xaxis: axis({ range: [0, 82], title: "%" }), yaxis: axis({ automargin: true }), margin: { l: 250, r: 24, t: 6, b: 48 } });
  }

  // ---------------------------------------------------------------- WHERE
  const stepScale = (bins, colors) => {
    const top = bins[bins.length - 1], out = [];
    colors.forEach((c, i) => { out.push([bins[i] / top, c]); out.push([bins[i + 1] / top, c]); });
    return out;
  };
  const MAP_METRICS = [
    { key: "per100k", label: "Bank and microfinance branches per 100,000 people", fmt: f1, zmin: 0, zmax: 40,
      scale: stepScale([0, 2, 4, 6, 9, 14, 40], ["#7A1F0A", C.orange, "#F4A582", "#CFE3E0", C.teal, C.navy]),
      legend: [["#7A1F0A", "Under 2"], [C.orange, "2 to 4"], ["#F4A582", "4 to 6"], ["#CFE3E0", "6 to 9"], [C.teal, "9 to 14"], [C.navy, "14 or more"]],
      note: "National average " + f1(H.branches_per_100k) + " per 100,000. Half of that is " + f1(H.branches_per_100k / 2) + "." },
    { key: "ppb", label: "People per branch", fmt: v => f0(v), zmin: 0, zmax: 60000,
      scale: [[0, "#EAF4F3"], [0.15, "#CFE3E0"], [0.4, "#F4A582"], [1, "#7A1F0A"]], note: "Darker means more people share each branch (capped at 60,000)." },
    { key: "ratio", label: "Actual branches / expected branches (model)", fmt: f2, zmin: 0.4, zmax: 1.6, scale: "BrBG", zmid: 1,
      note: "Brown: fewer branches than similar districts. Expected values are leave-one-out predictions." },
    { key: "dChange", label: "Change in bank branches per 100,000, 2020 to 2024", fmt: f2, zmin: -3, zmax: 3,
      scale: [[0, C.orange], [0.5, "#F5F5F5"], [1, C.teal]], zmid: 0, note: "Banks only, so it matches the 2020 baseline. Capped at plus and minus 3." },
    { key: "ruralShare", label: "Rural share of branches (%)", fmt: v => pct(v), zmin: 0, zmax: 100, scale: [[0, "#EAF4F3"], [1, C.navy]],
      note: "Rural and urban tags are from the SBP register." },
    { key: "mfbShare", label: "Microfinance share of branches (%)", fmt: v => pct(v), zmin: 0, zmax: 25, scale: [[0, "#EAF4F3"], [1, C.teal]],
      note: "Microfinance banks and DFIs as a share of all branches (capped at 25%)." },
    { key: "litF", label: "Female literacy, age 10 and over (%)", fmt: v => pct(v), zmin: 10, zmax: 90, scale: [[0, "#fde8e1"], [1, C.navy]], note: "PBS Census 2023." },
    { key: "litGap", label: "Literacy gap, men minus women (points)", fmt: f1, zmin: 0, zmax: 40, scale: [[0, "#F5F5F5"], [1, C.orange]], note: "PBS Census 2023." },
    { key: "ses", label: "Development index (standard deviations)", fmt: f2, zmin: -2, zmax: 2, scale: [[0, C.orange], [0.5, "#F5F5F5"], [1, C.teal]], zmid: 0,
      note: "First principal component of literacy, housing, power, water, sanitation and cooking fuel." },
    { key: "cluster", label: "District type", categorical: true, note: "K-means on population, urban share, development and branch density." }
  ];
  let selectedUnit = null;

  function provinceOutline() {
    const lon = [], lat = [];
    DATA.provinceGeo.features.forEach(f => {
      const polys = f.geometry.type === "MultiPolygon" ? f.geometry.coordinates : [f.geometry.coordinates];
      polys.forEach(poly => { poly.forEach(ring => { ring.forEach(pt => { lon.push(pt[0]); lat.push(pt[1]); }); lon.push(null); lat.push(null); }); });
    });
    return { type: "scattergeo", mode: "lines", lon: lon, lat: lat, line: { color: "#2B2F36", width: 1 }, hoverinfo: "skip", showlegend: false };
  }

  function drawMap(div, valueOf, opts) {
    const ids = U.map(u => u.id);
    const trace = {
      type: "choropleth", geojson: DATA.geo, featureidkey: "properties.unit_id", locations: ids, z: U.map(valueOf),
      hovertext: U.map(opts.hover), hoverinfo: "text", marker: { line: { color: "white", width: 0.4 } },
      colorscale: opts.scale, zmin: opts.zmin, zmax: opts.zmax, showscale: !!opts.showscale
    };
    if (opts.zmid != null) trace.zmid = opts.zmid;
    if (opts.showscale) trace.colorbar = { thickness: 12, len: 0.6, title: { text: opts.colorbarTitle || "", font: { size: 11 } } };
    const fig = draw(div, [trace, provinceOutline()], {
      geo: { fitbounds: "locations", visible: false, projection: { type: "mercator" }, bgcolor: "rgba(0,0,0,0)" },
      margin: { t: 0, r: 0, b: 0, l: 0 }, showlegend: false
    });
    return fig;
  }

  function hoverFor(u, metric) {
    const val = metric.categorical ? u.cluster : metric.fmt(u[metric.key]);
    return "<b>" + esc(u.name) + "</b>, " + esc(u.province) + "<br>" + esc(metric.label) + ": " + esc(val) +
      "<br>Branches " + f0(u.branches) + " (" + f1(u.per100k) + " per 100,000)<br>Population " + f0(u.pop);
  }

  function drawWhereMap() {
    const metric = MAP_METRICS.find(m => m.key === $("mapMetric").value);
    let opts;
    if (metric.categorical) {
      const idx = {}; CLUSTERS.forEach((c, i) => { idx[c] = i; });
      const cols = CLUSTERS.map(c => CLUSTER_COL[c]);
      const scale = []; cols.forEach((c, i) => { scale.push([i / 4, c]); scale.push([(i + 1) / 4, c]); });
      opts = { scale: scale, zmin: 0, zmax: 4, hover: u => hoverFor(u, metric), showscale: false };
      drawMap("mapChart", u => idx[u.cluster] + 0.5, opts);
      $("mapLegend").innerHTML = CLUSTERS.map(c => '<span><i style="background:' + CLUSTER_COL[c] + '"></i>' + esc(c) + "</span>").join("");
    } else {
      opts = { scale: metric.scale, zmin: metric.zmin, zmax: metric.zmax, zmid: metric.zmid, hover: u => hoverFor(u, metric),
        showscale: !metric.legend, colorbarTitle: "" };
      drawMap("mapChart", u => { const v = u[metric.key]; return v == null ? null : Math.min(Math.max(v, metric.zmin), metric.zmax); }, opts);
      $("mapLegend").innerHTML = metric.legend ? '<span><b>' + esc(metric.label) + ":</b></span>" + metric.legend.map(l => '<span><i style="background:' + l[0] + '"></i>' + esc(l[1]) + "</span>").join("") : "<span><b>" + esc(metric.label) + "</b></span>";
    }
    $("mapNote").textContent = metric.note + " Azad Jammu & Kashmir and Gilgit-Baltistan are not covered by the census district tables.";
    const div = $("mapChart");
    if (!div.dataset.bound) {
      div.on("plotly_click", ev => { if (ev.points && ev.points[0] && ev.points[0].location) selectUnit(ev.points[0].location, false); });
      div.dataset.bound = "1";
    }
  }

  function selectUnit(id, scrollToMap) {
    selectedUnit = byId[id];
    renderProfile();
    if (scrollToMap) $("mapChart").scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function renderProfile() {
    const u = selectedUnit;
    const rank = U.filter(x => x.per100k < u.per100k).length + 1;
    const need = Math.max(0, Math.ceil(H.branches_per_100k * u.pop / 1e5 - u.branches));
    const below = u.per100k < DATA.meta.lowDensityShare * H.branches_per_100k;
    const status = u.robust ? '<span class="pill low">flagged: fewer than similar districts</span>' : (u.above ? '<span class="pill high">more than similar districts</span>' : "");
    $("profile").innerHTML =
      "<h3>" + esc(u.name) + "</h3>" +
      '<div><span class="tag" style="background:' + PROV[u.province] + '">' + esc(u.province) + '</span><span class="tag" style="background:' + CLUSTER_COL[u.cluster] + '">' + esc(u.cluster) + "</span></div>" +
      '<div class="metrics">' +
      "<div><span>Population (2023)</span><strong>" + f0(u.pop) + "</strong></div>" +
      "<div><span>Urban share</span><strong>" + pct(u.urban) + "</strong></div>" +
      "<div><span>Branches (banks + microfinance)</span><strong>" + f0(u.branches) + "</strong> <span>" + f0(u.banks) + " + " + f0(u.mfb) + "</span></div>" +
      "<div><span>Per 100,000 people</span><strong>" + f1(u.per100k) + "</strong> <span>" + (below ? "below half the national average" : "national " + f1(H.branches_per_100k)) + "</span></div>" +
      "<div><span>People per branch</span><strong>" + (u.ppb == null ? "no branch" : f0(u.ppb)) + "</strong></div>" +
      "<div><span>Rank, fewest per person</span><strong>" + rank + " of " + U.length + "</strong></div>" +
      "<div><span>Rural share of branches</span><strong>" + pct(u.ruralShare) + "</strong> <span>rural people " + pct(u.ruralPopShare) + "</span></div>" +
      "<div><span>Bank branches 2020 to 2024</span><strong>" + f0(u.banks2020) + " to " + f0(u.banks) + "</strong></div>" +
      "<div><span>Model: expected branches</span><strong>" + f0(u.expected) + "</strong> <span>range " + f0(u.expLo) + " to " + f0(u.expHi) + "</span></div>" +
      "<div><span>Actual / expected</span><strong>" + f2(u.ratio) + "</strong> <span>chance of this few or fewer: " + pct(u.pBelow * 100) + "</span></div>" +
      "<div><span>Female literacy</span><strong>" + pct(u.litF) + "</strong> <span>male " + pct(u.litM) + "</span></div>" +
      "<div><span>Banks serving the district</span><strong>" + f0(u.nBanks) + "</strong> <span>largest holds " + pct((u.topBank || 0) * 100) + "</span></div>" +
      "</div>" + status +
      '<p class="note">To reach the national average of ' + f1(H.branches_per_100k) + " per 100,000, this district would need " + f0(need) + " more branches or access points.</p>";
  }

  renderers.where = function () {
    const sel = $("mapMetric");
    sel.innerHTML = MAP_METRICS.map(m => '<option value="' + m.key + '">' + esc(m.label) + "</option>").join("");
    sel.addEventListener("change", drawWhereMap);
    selectedUnit = selectedUnit || byId["lahore"] || U[0];
    drawWhereMap();
    renderProfile();

    const provs = DATA.provinces.slice().sort((a, b) => a.branches_per_100k - b.branches_per_100k);
    draw("provChart", [
      { type: "bar", orientation: "h", name: "Banks", y: provs.map(p => p.province), x: provs.map(p => p.banks_per_100k), marker: { color: C.navy }, hovertemplate: "%{y}: %{x:.1f} banks<extra></extra>" },
      { type: "bar", orientation: "h", name: "Microfinance banks and DFIs", y: provs.map(p => p.province), x: provs.map(p => p.mfb_per_100k), marker: { color: C.teal },
        hovertemplate: "%{y}: %{x:.2f} microfinance<extra></extra>", text: provs.map(p => f1(p.branches_per_100k)), textposition: "outside", cliponaxis: false, textfont: { color: C.ink } }
    ], { barmode: "stack", xaxis: axis({ title: "Branches per 100,000 people", range: [0, 36] }), yaxis: axis({ automargin: true }), margin: { l: 130, r: 30, t: 6, b: 70 }, legend: { orientation: "h", y: -0.28 } });

    const rp = DATA.provinces.filter(p => p.province !== "Islamabad").sort((a, b) => a.rural_branches_per_100k_rural - b.rural_branches_per_100k_rural);
    const cats = rp.map(p => p.province).concat(["Pakistan"]);
    draw("ruralChart", [
      { type: "bar", name: "Per 100,000 rural residents", x: cats, y: rp.map(p => p.rural_branches_per_100k_rural).concat([H.rural_per_100k_rural]), marker: { color: C.orange },
        text: rp.map(p => f1(p.rural_branches_per_100k_rural)).concat([f1(H.rural_per_100k_rural)]), textposition: "outside", cliponaxis: false },
      { type: "bar", name: "Per 100,000 urban residents", x: cats, y: rp.map(p => p.urban_branches_per_100k_urban).concat([H.urban_per_100k_urban]), marker: { color: C.navy },
        text: rp.map(p => f1(p.urban_branches_per_100k_urban)).concat([f1(H.urban_per_100k_urban)]), textposition: "outside", cliponaxis: false }
    ], { barmode: "group", yaxis: axis({ title: "Branches", range: [0, 25] }), xaxis: axis({}), margin: { t: 6, r: 12, b: 80, l: 52 }, legend: { orientation: "h", y: -0.2 } });

    buildUnitTable();
  };

  // sortable, searchable district table
  const UCOLS = [
    { k: "name", t: "District" }, { k: "province", t: "Province" }, { k: "cluster", t: "Type" },
    { k: "pop", t: "Population", num: 1, f: f0 }, { k: "branches", t: "Branches", num: 1, f: f0 },
    { k: "per100k", t: "Per 100,000", num: 1, f: f1 }, { k: "expected", t: "Expected", num: 1, f: f0 },
    { k: "ratio", t: "Actual / expected", num: 1, f: f2 }, { k: "pBelow", t: "Chance of this few", num: 1, f: v => pct(v * 100) },
    { k: "bChange", t: "Banks, change since 2020", num: 1, f: v => (v > 0 ? "+" : "") + f0(v) }, { k: "litF", t: "Female literacy", num: 1, f: v => pct(v) }
  ];
  let sortKey = "per100k", sortDir = 1;
  function buildUnitTable() {
    $("unitTable").querySelector("thead").innerHTML = "<tr>" + UCOLS.map(c => '<th data-k="' + c.k + '"' + (c.num ? " data-num" : "") + ">" + esc(c.t) + "</th>").join("") + "</tr>";
    $("unitTable").querySelectorAll("th").forEach(th => th.addEventListener("click", () => {
      sortDir = sortKey === th.dataset.k ? -sortDir : 1; sortKey = th.dataset.k; fillUnitTable(); }));
    $("search").addEventListener("input", fillUnitTable);
    fillUnitTable();
  }
  function fillUnitTable() {
    const q = $("search").value.trim().toLowerCase();
    const rows = U.filter(u => !q || (u.name + " " + u.province + " " + u.cluster).toLowerCase().includes(q));
    rows.sort((a, b) => {
      const x = a[sortKey], y = b[sortKey];
      if (x == null && y == null) return 0; if (x == null) return 1; if (y == null) return -1;
      return (typeof x === "string" ? x.localeCompare(y) : x - y) * sortDir;
    });
    $("tCount").textContent = rows.length + " of " + U.length + " districts. Click a row to see it on the map.";
    $("unitTable").querySelector("tbody").innerHTML = rows.map(u => '<tr data-id="' + u.id + '" style="cursor:pointer">' +
      UCOLS.map(c => '<td class="' + (c.num ? "num" : "") + '">' + esc(c.f ? c.f(u[c.k]) : u[c.k]) + "</td>").join("") + "</tr>").join("");
    $("unitTable").querySelectorAll("tbody tr").forEach(tr => tr.addEventListener("click", () => selectUnit(tr.dataset.id, true)));
  }

  // ---------------------------------------------------------------- DIGITAL
  const WREG = ["Balochistan", "Khyber Pakhtunkhwa", "Sindh", "Punjab (incl. Islamabad)"];
  const WCOL = { "Balochistan": C.amber, "Khyber Pakhtunkhwa": C.orange, "Sindh": C.teal, "Punjab (incl. Islamabad)": C.navy };
  renderers.digital = function () {
    const W = DATA.wallet.regions, quarters = [...new Set(W.map(r => r.quarter))].sort();
    const last = quarters[quarters.length - 1], first = quarters[0];
    const labelOf = q => W.find(r => r.quarter === q).label;
    const at = (region, q) => W.find(r => r.region === region && r.quarter === q);
    $("walletSub").textContent = labelOf(last) + ". Punjab includes Islamabad because SBP reports them together.";
    const ag = WREG.map(r => at(r, last).agents_per_100k_adults), ac = WREG.map(r => at(r, last).accounts_per_100_adults);
    draw("walletBars", [
      { type: "bar", orientation: "h", name: "Agents per 100,000 adults", y: WREG, x: ag, marker: { color: C.orange }, text: ag.map(f0), textposition: "outside", cliponaxis: false, xaxis: "x", yaxis: "y" },
      { type: "bar", orientation: "h", name: "Accounts per 100 adults", y: WREG, x: ac, marker: { color: C.purple }, text: ac.map(f0), textposition: "outside", cliponaxis: false, xaxis: "x2", yaxis: "y2" }
    ], { grid: { rows: 1, columns: 2, pattern: "independent" }, xaxis: axis({ title: "Agents per 100,000 adults", range: [0, 800] }), xaxis2: axis({ title: "Accounts per 100 adults", range: [0, 150] }),
         yaxis: axis({ automargin: true }), yaxis2: axis({ showticklabels: false }), showlegend: false, margin: { l: 150, r: 20, t: 6, b: 56 } });

    const line = (metric, flagKeys, fmtf) => WREG.map(region => {
      const rows = quarters.map(q => at(region, q)).filter(r => !flagKeys.some(k => r[k]));
      return { type: "scatter", mode: "lines+markers", name: region, x: rows.map(r => r.label), y: rows.map(r => r[metric]),
        line: { color: WCOL[region], width: 2.6 }, marker: { size: 6 }, hovertemplate: region + ", %{x}: %{y:" + fmtf + "}<extra></extra>" };
    });
    const qAxis = axis({ type: "category", categoryorder: "array", categoryarray: quarters.map(labelOf), tickangle: -35, tickfont: { size: 10.5 } });
    draw("walletLines", line("accounts_per_100_adults", ["flag_accounts"], ".0f"), { xaxis: qAxis, yaxis: axis({ title: "Accounts per 100 adults" }), margin: { t: 8, r: 10, b: 96, l: 56 }, legend: { orientation: "h", y: -0.34 } });
    draw("walletWomen", line("female_share", ["flag_accounts", "flag_female"], ".1f"), { xaxis: qAxis, yaxis: axis({ title: "Women's share of accounts (%)", range: [18, 38] }), margin: { t: 8, r: 10, b: 96, l: 56 }, legend: { orientation: "h", y: -0.34 } });

    const N = DATA.wallet.national;
    draw("walletAgents", [
      { type: "bar", name: "All agents", x: N.map(n => n.label), y: N.map(n => n.agents / 1000), marker: { color: "#C8D1DC" }, hovertemplate: "%{x}: %{y:.0f}k agents<extra></extra>" },
      { type: "bar", name: "Active agents", x: N.map(n => n.label), y: N.map(n => n.active_agents / 1000), marker: { color: C.teal }, hovertemplate: "%{x}: %{y:.0f}k active<extra></extra>",
        text: N.map(n => f0(n.active_agent_share) + "%"), textposition: "outside", textfont: { size: 11 } }
    ], { barmode: "overlay", yaxis: axis({ title: "Agents (thousands)", range: [0, 1000] }), xaxis: axis({ type: "category" }), margin: { t: 8, r: 10, b: 80, l: 56 }, legend: { orientation: "h", y: -0.3 } });

    const prov = {};
    DATA.provinces.forEach(p => {
      const r = p.province === "Islamabad" ? "Punjab (incl. Islamabad)" : (p.province === "Punjab" ? "Punjab (incl. Islamabad)" : p.province);
      prov[r] = prov[r] || { branches: 0, pop: 0 }; prov[r].branches += p.branches_2024; prov[r].pop += p.pop;
    });
    const women = region => { const rows = quarters.slice(-4).map(q => at(region, q)).filter(r => !r.flag_accounts && !r.flag_female); return sum(rows, r => r.female_share) / rows.length; };
    const cols = ["Region", "Branches per 100,000 people", "Agents per 100,000 adults", "Wallet accounts per 100 adults", "Women's share of accounts", "Accounts per 100 adults, change since " + labelOf(first)];
    $("digitalTable").querySelector("thead").innerHTML = "<tr>" + cols.map((c, i) => "<th" + (i ? " data-num" : "") + ">" + esc(c) + "</th>").join("") + "</tr>";
    $("digitalTable").querySelector("tbody").innerHTML = WREG.slice().reverse().map(region => {
      const a = at(region, last), b = at(region, first);
      return "<tr><td>" + esc(region) + '</td><td class="num">' + f1(prov[region].branches / prov[region].pop * 1e5) + '</td><td class="num">' + f0(a.agents_per_100k_adults) +
        '</td><td class="num">' + f0(a.accounts_per_100_adults) + '</td><td class="num">' + pct(women(region)) + '</td><td class="num">+' + f0(a.accounts_per_100_adults - b.accounts_per_100_adults) + "</td></tr>";
    }).join("");
  };

  // ---------------------------------------------------------------- MODEL AND CHANGE
  renderers.model = function () {
    const m = DATA.model;
    $("modelSub").textContent = "Error " + f0(m.mae_reduction_vs_baseline * 100) + "% lower than a rule of branches proportional to population. Orange: flagged as fewer than expected, a list to review (chance alone would flag about one district in ten).";
    const mk = (subset, color, size, name) => ({ type: "scatter", mode: "markers", name: name, x: subset.map(u => u.expected), y: subset.map(u => u.branches),
      text: subset.map(u => u.name), marker: { color: color, size: size, line: { color: "white", width: 0.6 } },
      hovertemplate: "<b>%{text}</b><br>Expected %{x:.0f}, actual %{y:.0f}<extra></extra>" });
    const rest = U.filter(u => !u.robust && !u.above), robust = U.filter(u => u.robust), above = U.filter(u => u.above);
    const label = ["Lahore", "Karachi", "Gujranwala", "Islamabad", "Hyderabad", "Sheikhupura"];
    const big = U.filter(u => label.includes(u.name));
    draw("modelScatter", [
      { type: "scatter", mode: "lines", x: [0.8, 4000], y: [0.8, 4000], line: { color: "#333", dash: "dot", width: 1 }, hoverinfo: "skip", showlegend: false },
      mk(rest, C.pale, 8, "Within the expected range"), mk(above, C.teal, 9, "Flagged: more than expected"), mk(robust, C.orange, 10, "Flagged: fewer than expected"),
      { type: "scatter", mode: "text", x: big.map(u => u.expected), y: big.map(u => u.branches), text: big.map(u => u.name), textposition: "top right", textfont: { size: 11 }, hoverinfo: "skip", showlegend: false }
    ], { xaxis: axis({ type: "log", title: "Expected branches (leave-one-out)", range: [Math.log10(0.8), Math.log10(4000)], tickvals: [1, 10, 100, 1000], ticktext: ["1", "10", "100", "1,000"] }),
         yaxis: axis({ type: "log", title: "Actual branches", range: [Math.log10(0.8), Math.log10(4000)], tickvals: [1, 10, 100, 1000], ticktext: ["1", "10", "100", "1,000"] }),
         legend: { orientation: "h", y: -0.2 }, margin: { t: 8, r: 14, b: 76, l: 62 } });

    const terms = { log_pop: "Population (+1 log point)", urban: "Urban share (0 to 100%)", ses_index: "Development index (+1 SD)" };
    const co = m.coefficients.filter(c => terms[c.term]).reverse();
    draw("modelCoef", [{
      type: "scatter", mode: "markers", x: co.map(c => Math.exp(c.coefficient)), y: co.map(c => terms[c.term]),
      error_x: { type: "data", symmetric: false, array: co.map(c => Math.exp(c.ci_high) - Math.exp(c.coefficient)), arrayminus: co.map(c => Math.exp(c.coefficient) - Math.exp(c.ci_low)), color: C.navy, thickness: 2.4, width: 6 },
      marker: { color: C.navy, size: 11 }, text: co.map(c => "x" + f2(Math.exp(c.coefficient))), textposition: "bottom center",
      hovertemplate: "%{y}<br>Rate ratio %{x:.2f}<extra></extra>", mode: "markers+text"
    }], { xaxis: axis({ title: "Change in expected branches (rate ratio, 95% interval)", range: [0.6, 4.4] }), yaxis: axis({ automargin: true }),
          shapes: [{ type: "line", x0: 1, x1: 1, y0: -0.5, y1: 2.5, line: { color: C.grey, width: 1 } }], margin: { l: 190, r: 20, t: 8, b: 56 }, showlegend: false });
    $("modelNote").textContent = "A district twice the size is expected to have " + f2(Math.pow(2, m.coefficients.find(c => c.term === "log_pop").coefficient)) + " times the branches, not twice. " +
      "Total shortfall against the model: about " + f0(m.shortfall_total) + " branches (90% range " + f0(m.shortfall_p05) + " to " + f0(m.shortfall_p95) + "). This is an association among similar districts, not a causal estimate.";

    const L = DATA.lorenz, I = DATA.inequality;
    const lz = (key, name, color, dash, width) => ({ type: "scatter", mode: "lines", name: name + " (Gini " + f3(I[key].gini) + ")", x: L[key].population_share, y: L[key].branch_share,
      line: { color: color, width: width, dash: dash }, hovertemplate: "%{x:.0%} of people have %{y:.0%} of branches<extra></extra>" });
    draw("lorenzChart", [
      { type: "scatter", mode: "lines", x: [0, 1], y: [0, 1], line: { color: C.grey, dash: "dot", width: 1.4 }, name: "Perfect equality", hoverinfo: "skip" },
      lz("banks_2020", "Banks, 2020", C.orange, "solid", 3), lz("banks_2024", "Banks, 2024", C.navy, "dash", 2), lz("branches_2024", "Banks and microfinance, 2024", C.teal, "solid", 2.4)
    ], { xaxis: axis({ title: "Cumulative share of people (fewest branches per person first)", tickformat: ".0%", range: [0, 1] }), yaxis: axis({ title: "Cumulative share of branches", tickformat: ".0%", range: [0, 1] }), legend: { orientation: "h", y: -0.32 }, margin: { t: 8, r: 10, b: 100, l: 60 } });
    $("lorenzNote").textContent = "The least-served 20% of people have " + pct(I.bottom_20pct_population.branch_share * 100) + " of branches. The ten districts with most branches hold " + pct(I.top10_by_branches.branch_share * 100) + " of them for " + pct(I.top10_by_branches.population_share * 100) + " of people. " +
      "About " + pct(I.branches_2024.between_share * 100) + " of the inequality is between provinces; the rest is within them.";

    const cv = DATA.convergence;
    const provList = Object.keys(PROV);
    const traces = provList.map(pn => {
      const s = U.filter(u => u.province === pn);
      return { type: "scatter", mode: "markers", name: pn, x: s.map(u => u.d2020), y: s.map(u => u.dChange), text: s.map(u => u.name),
        marker: { color: PROV[pn], size: 9, line: { color: "white", width: 0.6 } }, hovertemplate: "<b>%{text}</b><br>2020: %{x:.1f} per 100,000<br>Change: %{y:+.2f}<extra></extra>" };
    });
    const mx = sum(U, u => u.d2020) / U.length, my = sum(U, u => u.dChange) / U.length, xmax = Math.max(...U.map(u => u.d2020));
    traces.push({ type: "scatter", mode: "lines", x: [0, xmax], y: [my - cv.slope_initial_density * mx, my + cv.slope_initial_density * (xmax - mx)], line: { color: "#333", dash: "dash", width: 1.4 }, hoverinfo: "skip", showlegend: false });
    draw("catchChart", traces, { xaxis: axis({ title: "Bank branches per 100,000 people in 2020" }), yaxis: axis({ title: "Change by 2024 (per 100,000)", zeroline: true, zerolinecolor: C.grey }), legend: { orientation: "h", y: -0.28 }, margin: { t: 8, r: 10, b: 90, l: 60 } });
    $("catchNote").textContent = "Fitted slope " + (cv.slope_initial_density >= 0 ? "+" : "") + f2(cv.slope_initial_density) + " (p = " + f2(cv.p_value) + "): no sign that districts with few branches caught up. The " + cv.low_density_units + " districts below the 2020 median hold " + pct(cv.low_density_share_of_population * 100) + " of people and received " + pct(cv.low_density_share_of_new * 100) + " of the " + f0(cv.net_new_banks) + " net new bank branches. " + cv.units_losing_branches + " districts lost bank branches.";

    // cluster table
    const cp = DATA.clusters.profile;
    $("clusterTable").querySelector("thead").innerHTML = "<tr><th>Type</th><th data-num>Districts</th><th data-num>Population</th><th data-num>Urban share</th><th data-num>Development index</th><th data-num>Female literacy</th><th data-num>Branches per 100,000 (median)</th><th data-num>Microfinance share</th><th data-num>Rural share of branches</th><th>Largest districts</th></tr>";
    $("clusterTable").querySelector("tbody").innerHTML = cp.map(c => '<tr><td><i style="display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;background:' + CLUSTER_COL[c.cluster] + '"></i>' + esc(c.cluster) +
      '</td><td class="num">' + c.units + '</td><td class="num">' + f1(c.population / 1e6) + 'M</td><td class="num">' + pct(c.urban_share) + '</td><td class="num">' + f2(c.ses_index) + '</td><td class="num">' + pct(c.literacy_female) +
      '</td><td class="num">' + f1(c.branches_per_100k) + '</td><td class="num">' + pct(c.mfb_share) + '</td><td class="num">' + pct(c.rural_branch_share) + "</td><td>" + esc(c.largest_units) + "</td></tr>").join("");
    $("clusterNote").textContent = DATA.clusters.selection_note + " Silhouette " + f2(DATA.clusters.silhouette_selected) + ".";

    const gaps = U.filter(u => u.gap > 0).sort((a, b) => b.gap - a.gap).slice(0, 25);
    $("gapTable").querySelector("thead").innerHTML = "<tr><th>District</th><th>Province</th><th data-num>Branches</th><th data-num>Expected</th><th data-num>Missing against model</th><th data-num>Chance of this few</th><th>Status</th></tr>";
    $("gapTable").querySelector("tbody").innerHTML = gaps.map(u => "<tr data-id=\"" + u.id + "\" style=\"cursor:pointer\"><td>" + esc(u.name) + "</td><td>" + esc(u.province) + '</td><td class="num">' + f0(u.branches) + '</td><td class="num">' + f0(u.expected) +
      '</td><td class="num">' + f0(u.gap) + '</td><td class="num">' + pct(u.pBelow * 100) + "</td><td>" + (u.robust ? '<span class="pill low">flagged</span>' : (u.below ? '<span class="pill low">fewer</span>' : "within range")) + "</td></tr>").join("");
    $("gapTable").querySelectorAll("tbody tr").forEach(tr => tr.addEventListener("click", () => { selectedUnit = byId[tr.dataset.id]; show("where", true); renderProfile(); }));
  };

  // ---------------------------------------------------------------- PLANNER
  const STRATS = [
    { id: "equity", title: "Even out people per branch", rule: "Each new point goes to the district where the most people would share one branch, until the load is level." },
    { id: "gap", title: "Close the model gap", rule: "Each new point goes to the district with the largest remaining shortfall against the model, so points go where networks lag similar districts." },
    { id: "women", title: "Women-first equity", rule: "As the first rule, but each district's need is weighted by how much more literate men are than women there, so places where women are furthest behind come first." }
  ];
  let planStrategy = "equity";

  function allocate(strategy, k) {
    const n = U.length, added = new Array(n).fill(0);
    const gaps = U.map(u => Math.max(u.litGap || 0, 0)), meanGap = sum(gaps) / n;
    const weight = gaps.map(g => meanGap > 0 ? g / meanGap : 1);
    const prio = i => {
      const u = U[i];
      if (strategy === "gap") { const rem = u.expected - (u.branches + added[i]); return rem > 0 ? rem : -Infinity; }
      const need = u.pop / (u.branches + added[i] + 1);
      return strategy === "women" ? need * weight[i] : need;
    };
    const p = U.map((_, i) => prio(i));
    let placed = 0;
    while (placed < k) {
      let best = -1, bv = -Infinity;
      for (let i = 0; i < n; i++) if (p[i] > bv) { bv = p[i]; best = i; }
      if (best < 0) break;
      added[best] += 1; placed += 1; p[best] = prio(best);
    }
    return added;
  }

  function lorenzGini(pop, counts) {
    const idx = pop.map((_, i) => i).sort((a, b) => counts[a] / pop[a] - counts[b] / pop[b]);
    const tp = sum(pop), tc = sum(counts);
    let cx = 0, cy = 0, area = 0;
    idx.forEach(i => { const nx = cx + pop[i] / tp, ny = cy + counts[i] / tc; area += (nx - cx) * (cy + ny) / 2; cx = nx; cy = ny; });
    return 1 - 2 * area;
  }

  function outcomes(added) {
    const total = U.map((u, i) => u.branches + (added ? added[i] : 0));
    const popSum = sum(U, u => u.pop), national = sum(total) / popSum * 1e5;
    const below = U.map((u, i) => total[i] / u.pop * 1e5 < DATA.meta.lowDensityShare * national);
    const placed = added ? sum(added) : 0;
    const lowF = added ? sum(U.map((u, i) => u.litF < DATA.meta.lowFemaleLiteracy ? added[i] : 0)) : 0;
    return {
      national: national, below: below.filter(Boolean).length, belowPop: sum(U.map((u, i) => below[i] ? u.pop : 0)) / popSum,
      gini: lorenzGini(U.map(u => u.pop), total), worst: Math.max(...U.map((u, i) => u.pop / Math.max(total[i], 1))),
      placed: placed, lowFemale: placed ? lowF / placed : null
    };
  }

  let planAdded = {};
  renderers.planner = function () {
    $("planK").addEventListener("input", updatePlanner);
    $("planDownload").addEventListener("click", downloadPlan);
    updatePlanner();
  };

  function updatePlanner() {
    const k = +$("planK").value;
    $("planKValue").textContent = f0(k);
    $("planKShare").textContent = "= " + (k / DATA.scenario.network_size * 100).toFixed(1) + "% of today's " + f0(DATA.scenario.network_size) + " branches";
    const res = { before: outcomes(null) };
    STRATS.forEach(s => { planAdded[s.id] = allocate(s.id, k); res[s.id] = outcomes(planAdded[s.id]); });
    const card = (id, title, o, selectable) =>
      '<' + (selectable ? 'button type="button" class="opt" data-s="' + id + '" aria-pressed="' + (planStrategy === id) + '"' : 'div class="opt" style="cursor:default"') + ">" +
      "<h4>" + esc(title) + '</h4><div class="big">' + o.below + '</div><div class="row"><span>districts below half the average</span></div>' +
      '<div class="row"><span>Gini</span><b>' + f2(o.gini) + '</b></div><div class="row"><span>Most people per branch</span><b>' + f0(o.worst / 1000) + 'k</b></div>' +
      '<div class="row"><span>In low female-literacy districts</span><b>' + (o.lowFemale == null ? "n/a" : pct(o.lowFemale * 100)) + "</b></div>" +
      (o.placed < k && selectable ? '<div class="row"><span>Placed</span><b>' + f0(o.placed) + " of " + f0(k) + "</b></div>" : "") +
      "</" + (selectable ? "button" : "div") + ">";
    $("planCompare").innerHTML = card("before", "Today", res.before, false) + STRATS.map(s => card(s.id, s.title, res[s.id], true)).join("");
    $("planCompare").querySelectorAll("button.opt").forEach(b => b.addEventListener("click", () => { planStrategy = b.dataset.s; updatePlanner(); }));
    $("planRule").textContent = STRATS.find(s => s.id === planStrategy).rule +
      (planStrategy === "gap" && res.gap.placed < k ? " Fewer than " + f0(k) + " points were placed because every district's model shortfall is already filled." : "");

    const added = planAdded[planStrategy];
    const rows = U.map((u, i) => ({ u: u, add: added[i] })).filter(r => r.add > 0).sort((a, b) => b.add - a.add);
    draw("planBars", [{ type: "bar", orientation: "h", y: rows.slice(0, 20).map(r => r.u.name).reverse(), x: rows.slice(0, 20).map(r => r.add).reverse(),
      marker: { color: C.orange }, hovertemplate: "%{y}: %{x} points<extra></extra>", text: rows.slice(0, 20).map(r => r.add).reverse(), textposition: "outside", cliponaxis: false }],
      { xaxis: axis({ title: "New points" }), yaxis: axis({ automargin: true }), margin: { l: 120, r: 24, t: 6, b: 48 } });
    const maxAdd = Math.max(1, ...added);
    drawMap("planMap", u => added[U.indexOf(u)], { scale: [[0, "#F3F5F8"], [0.001, "#FCE3DA"], [1, C.orange]], zmin: 0, zmax: maxAdd, showscale: true, colorbarTitle: "New points",
      hover: u => "<b>" + esc(u.name) + "</b>, " + esc(u.province) + "<br>New points: " + f0(added[U.indexOf(u)]) + "<br>Branches today: " + f0(u.branches) });

    $("planTable").querySelector("thead").innerHTML = "<tr><th>District</th><th>Province</th><th>Type</th><th data-num>Branches today</th><th data-num>New points</th><th data-num>Per 100,000 today</th><th data-num>Per 100,000 after</th><th data-num>Female literacy</th></tr>";
    $("planTable").querySelector("tbody").innerHTML = rows.map(r => "<tr><td>" + esc(r.u.name) + "</td><td>" + esc(r.u.province) + "</td><td>" + esc(r.u.cluster) + '</td><td class="num">' + f0(r.u.branches) +
      '</td><td class="num"><b>' + f0(r.add) + '</b></td><td class="num">' + f1(r.u.per100k) + '</td><td class="num">' + f1((r.u.branches + r.add) / r.u.pop * 1e5) + '</td><td class="num">' + pct(r.u.litF) + "</td></tr>").join("");
    $("planCount").textContent = rows.length + " districts receive points.";
  }

  function downloadPlan() {
    const added = planAdded[planStrategy], k = $("planK").value;
    const lines = ["district,province,type,branches_today,new_points,per_100k_today,per_100k_after"];
    U.forEach((u, i) => { if (added[i] > 0) lines.push([u.name, u.province, u.cluster, u.branches, added[i], u.per100k.toFixed(2), ((u.branches + added[i]) / u.pop * 1e5).toFixed(2)].map(v => '"' + String(v).replace(/"/g, '""') + '"').join(",")); });
    const blob = new Blob([lines.join("\n") + "\n"], { type: "text/csv" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "allocation_" + planStrategy + "_" + k + ".csv"; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  // ---------------------------------------------------------------- METHOD AND DATA
  renderers.method = function () {
    const v = DATA.meta.vintages, q = DATA.quality;
    const src = [
      ["World Bank Global Findex 2025 (survey year " + v.findex + ")", "https://www.worldbank.org/en/publication/globalfindex", "Account ownership, groups, barriers, phones, digital payments. 138 economies for the benchmark."],
      ["World Bank World Development Indicators", "https://data.worldbank.org", "GDP per person (PPP) and commercial bank branches per 100,000 adults (IMF Financial Access Survey)."],
      ["State Bank of Pakistan: branch register of banks and microfinance banks, " + v.branches, "https://www.sbp.org.pk/our-operations/publications/statistics-on-scheduled-banks-microfinance-banks-and-development-finance-institutions-in-pakistan/382/statistics-on-scheduled-banks-microfinance-banks-and-development-finance-institutions-in-pakistan-dec-2024", "Every branch with district, rural or urban, and Islamic or conventional."],
      ["State Bank of Pakistan: Statistics on Scheduled Banks, district appendix, " + v.baseline, "https://www.sbp.org.pk/assets/document/IV__Appendices11_statistics_december_2020.pdf", "The 2020 baseline for bank branches by district."],
      ["State Bank of Pakistan: branchless banking statistics, " + v.wallet_first + " to " + v.wallet_last, "https://www.sbp.org.pk/acd/branchless/", "Wallet accounts and agents by province, quarterly."],
      ["Pakistan Bureau of Statistics: Population and Housing Census " + v.census, "https://census23.pbos.gov.pk/Analysis/DistrictWise", "District population, literacy, housing and services. Tables used as CSV conversions, reconciled to the official totals."],
      ["geoBoundaries (World Food Programme via HDX), 2022", "https://www.geoboundaries.org/", "District outlines for the maps, merged to the analysis units. CC BY 3.0 IGO."]
    ];
    $("sourceList").innerHTML = src.map(s => '<li><a href="' + s[1] + '" target="_blank" rel="noopener">' + esc(s[0]) + "</a><br><span class=\"note\">" + esc(s[2]) + "</span></li>").join("");

    const ok = (t) => '<p><span class="pass">Pass</span> ' + t + "</p>";
    const allZero = q.census.every(r => r.diff_2023 === 0 && r.diff_2017 === 0);
    const ex = q.external, e24 = ex.banks_per_100k_adults_2024, e20 = ex.banks_per_100k_adults_2020;
    $("checks").innerHTML =
      ok("District populations add up to the official provincial totals in the PBS National Census Report for 2023 and 2017" + (allZero ? " (difference 0 in all five provinces)" : "") + ". A duplicated block in the third-party table (Tando Muhammad Khan, 272,427 people) was removed to get there.") +
      ok("The 2020 district rows add up to the SBP table total of " + f0(q.sbp2020.grand_total) + " branches; " + f0(q.sbp2020.outside_coverage) + " are in Azad Jammu & Kashmir and Gilgit-Baltistan and are excluded.") +
      ok("The 2024 register lists " + f0(q.register.rows) + " branches: " + f0(q.register.banks) + " banks and " + f0(q.register.mfb_dfi) + " microfinance banks and DFIs. " + f0(q.register.in_scope) + " fall inside the census coverage; " + q.register.province_mismatches.length + " have a province that disagrees with their district, resolved by district.") +
      ok("Bank branches per 100,000 adults: " + f1(e24.this_project) + " here against " + f1(e24.world_bank_wdi) + " in the World Bank series for 2024, and " + f1(e20.this_project) + " against " + f1(e20.world_bank_wdi) + " for 2020.") +
      ok("In every wallet quarter the provinces add up to the national total of accounts and agents.") +
      '<p><span class="warn">Note</span> ' + q.wallet.length + " provincial wallet points are out of line with the quarters either side (" + q.wallet.map(w => w.region + " " + w.quarter + (w.what === "accounts" ? " accounts" : " women's share")).join("; ") + "). They are left out of the charts.</p>";

    $("limits").innerHTML = [
      "Branches show where formal providers are, not who uses them. Agents, ATMs and wallets are covered only at province level.",
      "The 2020 to 2024 comparison uses banks only because the 2020 appendix has no microfinance branches. Districts are on 2020 boundaries.",
      "Rural and urban tags in the branch register and the census are defined differently, so rural against urban ratios are indicative.",
      "Wallet accounts are accounts, not people; many are dormant or duplicated across providers.",
      "Findex figures are survey estimates with sampling error. Barrier shares are for a bank or similar account, not for mobile money.",
      "The model describes patterns among similar districts. It does not say why a district has few branches, and it excludes demand, cost and security.",
      "The planner places points by simple rules. It ignores cost, the difference between a branch and an agent, and what each point can do."
    ].map(t => "<li>" + esc(t) + "</li>").join("");

    $("links").innerHTML = [
      [REPO, "Project repository"], [REPO + "/blob/main/docs/methodology.md", "Methodology"], [REPO + "/blob/main/docs/data_dictionary.md", "Data dictionary"],
      [REPO + "/blob/main/docs/data_sources.md", "Data sources and data issues"], [REPO + "/blob/main/docs/recommendation_memo.md", "Recommendation memo"],
      [REPO + "/blob/main/notebooks/analysis.ipynb", "Analysis notebook"], [REPO + "/tree/main/powerbi", "Power BI project"],
      ["../data/processed/units.csv", "District table (CSV)"], ["../data/processed/summary.json", "All model results (JSON)"]
    ].map(l => '<li><a href="' + l[0] + '">' + esc(l[1]) + "</a></li>").join("");
  };

  // ---------------------------------------------------------------- boot
  $("vintage").textContent = "Branches at " + DATA.meta.vintages.branches + " (2020 baseline " + DATA.meta.vintages.baseline + "). Census " + DATA.meta.vintages.census +
    ". Global Findex " + DATA.meta.vintages.findex + ". Wallet statistics " + DATA.meta.vintages.wallet_first + " to " + DATA.meta.vintages.wallet_last + ".";
  const start = (location.hash || "").replace("#", "");
  show(renderers[start] ? start : "overview", false);
  window.addEventListener("resize", () => document.querySelectorAll("section.tab:not([hidden]) .js-plotly-plot").forEach(el => Plotly.Plots.resize(el)));
  window.fininc = { allocate: allocate, outcomes: outcomes, units: U };   // handy for checks in the console
})();
