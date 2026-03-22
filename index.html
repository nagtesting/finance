
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<meta name="theme-color" content="#0A0A0F">
<title>MoneyVeda — SIP, EMI, FIRE, PPF, NPS & Tax Calculator India</title>
<meta name="description" content="Free financial calculators for India — SIP, EMI, FIRE, PPF, EPF, NPS, Step-Up SIP, Sukanya Samriddhi, Tax optimizer. No signup required.">
<link rel="canonical" href="https://moneyveda.org/">
<meta property="og:title" content="MoneyVeda — India's Free Financial Calculator Suite">
<meta property="og:description" content="SIP, EMI, FIRE, PPF, NPS, Tax & Insurance calculators. Free. Real-time market data.">
<meta property="og:url" content="https://moneyveda.org/">
<meta name="robots" content="index, follow">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{
  --gold:#C9A84C;--gold-light:#E8C97A;--cream:#F5F0E8;
  --dark:#0A0A0F;--dark2:#111118;--dark3:#18181F;--dark4:#22222C;
  --muted:#9090A8;--green:#22C55E;--red:#EF4444;--blue:#6366F1;
  --sidebar-w:264px;--topbar-h:56px;--bottomnav-h:62px;
}
*{box-sizing:border-box;margin:0;padding:0;}
html{height:100%;}
body{height:100%;background:var(--dark);color:var(--cream);font-family:'DM Sans',sans-serif;}
::-webkit-scrollbar{width:6px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:rgba(201,168,76,.4);border-radius:10px;}
::-webkit-scrollbar-thumb:hover{background:var(--gold);}
#sidebar::-webkit-scrollbar{width:9px;}
#sidebar::-webkit-scrollbar-track{background:var(--dark3);}
#sidebar::-webkit-scrollbar-thumb{background:rgba(201,168,76,.5);border-radius:10px;border:2px solid var(--dark2);}
#sidebar::-webkit-scrollbar-thumb:hover{background:var(--gold-light);}
#sidebar{scrollbar-width:thin;scrollbar-color:rgba(201,168,76,.5) var(--dark3);}

/* ---- DESKTOP LAYOUT ---- */
.app{display:flex;height:100vh;height:100dvh;}

#sidebar{
  width:var(--sidebar-w);min-width:var(--sidebar-w);flex-shrink:0;
  background:var(--dark2);border-right:1px solid rgba(201,168,76,.15);
  display:flex;flex-direction:column;
  height:100vh;height:100dvh;
  overflow-y:auto;
  position:relative;z-index:10;
}
#main{
  flex:1;min-width:0;
  display:flex;flex-direction:column;
  height:100vh;height:100dvh;
  overflow:hidden;
}
#main-scroll{
  flex:1;
  overflow-y:auto;overflow-x:hidden;
}

/* ---- TOPBAR (mobile only, hidden on desktop) ---- */
#topbar{
  display:none;
}

/* ---- DRAWER OVERLAY ---- */
#drawer-overlay{
  display:none;position:fixed;inset:0;
  background:rgba(0,0,0,.6);z-index:998;
  opacity:0;transition:opacity .3s;
  backdrop-filter:blur(4px);
  pointer-events:none;
}
#drawer-overlay.open{opacity:1;pointer-events:auto;}

/* ---- BOTTOM NAV (mobile only, hidden on desktop) ---- */
#bottom-nav{display:none;}

/* ---- BOTTOM NAV ITEMS ---- */
.bnav-item{
  flex:1;min-width:48px;min-height:44px;
  display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:2px;padding:8px 2px 4px;
  border-radius:10px;cursor:pointer;border:none;
  background:transparent;color:var(--muted);
  font-family:'DM Sans',sans-serif;
  -webkit-tap-highlight-color:transparent;
  touch-action:manipulation;
  user-select:none;-webkit-user-select:none;
  transition:color .2s;
}
.bnav-item.active{color:var(--gold-light);}
.bnav-item .bnav-icon{font-size:17px;line-height:1;display:block;}
.bnav-item .bnav-label{font-size:8px;font-weight:600;letter-spacing:.3px;white-space:nowrap;display:block;}
.bnav-indicator{position:absolute;bottom:0;left:50%;transform:translateX(-50%);width:4px;height:4px;border-radius:50%;background:var(--gold);opacity:0;transition:opacity .2s;}
.bnav-item.active .bnav-indicator{opacity:1;}

#menu-btn{width:40px;height:40px;background:transparent;border:none;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px;cursor:pointer;flex-shrink:0;touch-action:manipulation;-webkit-tap-highlight-color:transparent;}
#menu-btn span{display:block;width:22px;height:2px;background:var(--cream);border-radius:2px;transition:all .3s;}

/* ===== MODE SELECTOR — 4 options ===== */
.mode-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-top:12px;}
.mode-btn{
  padding:6px 8px;border-radius:8px;font-size:10px;font-weight:700;
  cursor:pointer;border:1px solid rgba(255,255,255,.08);background:transparent;
  transition:all .25s;color:var(--muted);font-family:'DM Sans',sans-serif;
  text-align:center;line-height:1.3;
}
.mode-btn:hover{border-color:rgba(255,255,255,.15);color:var(--cream);}
.mode-btn.active-india{background:rgba(255,107,53,.15);border-color:rgba(255,107,53,.4);color:#FF8C5A;}
.mode-btn.active-usa{background:rgba(59,130,246,.15);border-color:rgba(59,130,246,.4);color:#60a5fa;}
.mode-btn.active-europe{background:rgba(99,102,241,.15);border-color:rgba(99,102,241,.4);color:#a5b4fc;}
.mode-btn.active-world{background:rgba(34,197,94,.12);border-color:rgba(34,197,94,.3);color:#4ade80;}

/* Mobile top-bar mode — compact row */
.mob-mode-row{display:flex;gap:3px;}
.mob-mode-btn{
  padding:4px 7px;border-radius:6px;font-size:9px;font-weight:700;
  cursor:pointer;border:1px solid rgba(255,255,255,.1);background:transparent;
  color:var(--muted);font-family:'DM Sans',sans-serif;
  -webkit-tap-highlight-color:transparent;touch-action:manipulation;
  user-select:none;-webkit-user-select:none;
}
.mob-mode-btn.active-india{background:rgba(255,107,53,.2);border-color:rgba(255,107,53,.5);color:#FF8C5A;}
.mob-mode-btn.active-usa{background:rgba(59,130,246,.2);border-color:rgba(59,130,246,.5);color:#60a5fa;}
.mob-mode-btn.active-europe{background:rgba(99,102,241,.2);border-color:rgba(99,102,241,.5);color:#a5b4fc;}
.mob-mode-btn.active-world{background:rgba(34,197,94,.15);border-color:rgba(34,197,94,.4);color:#4ade80;}

.mode-banner{padding:6px 20px;font-size:10px;font-weight:600;letter-spacing:2px;text-transform:uppercase;transition:all .4s;flex-shrink:0;}
.mode-banner.india{background:rgba(255,107,53,.08);border-bottom:1px solid rgba(255,107,53,.15);color:#FF8C5A;}
.mode-banner.usa{background:rgba(59,130,246,.08);border-bottom:1px solid rgba(59,130,246,.15);color:#60a5fa;}
.mode-banner.europe{background:rgba(99,102,241,.08);border-bottom:1px solid rgba(99,102,241,.15);color:#a5b4fc;}
.mode-banner.world{background:rgba(34,197,94,.07);border-bottom:1px solid rgba(34,197,94,.15);color:#4ade80;}

.nav-item{display:flex;align-items:center;gap:10px;padding:10px 18px;border-radius:8px;cursor:pointer;transition:all .2s;font-size:13px;font-weight:500;color:var(--muted);border-left:3px solid transparent;margin:1px 10px;}
.nav-item:hover{background:rgba(201,168,76,.07);color:var(--cream);}
.nav-item.active{background:rgba(201,168,76,.12);color:var(--gold-light);border-left:3px solid var(--gold);}

.display{font-family:'Playfair Display',serif;}
.mono{font-family:'DM Mono',monospace;}
.section-eyebrow{font-size:10px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--gold);margin-bottom:6px;}
.gold-line{height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent);}

.card{background:var(--dark3);border:1px solid rgba(201,168,76,.12);border-radius:14px;padding:20px;transition:border-color .3s;}
.card:hover{border-color:rgba(201,168,76,.26);}
.result-box{background:linear-gradient(135deg,rgba(201,168,76,.1),rgba(201,168,76,.03));border:1px solid rgba(201,168,76,.25);border-radius:10px;padding:16px;text-align:center;}

.big-number{font-family:'Playfair Display',serif;font-size:2.6rem;font-weight:900;color:var(--gold-light);line-height:1;letter-spacing:-1px;}

.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}
.grid-2-1{display:grid;grid-template-columns:1.2fr 0.8fr;gap:18px;}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px;}

input[type=range]{-webkit-appearance:none;appearance:none;width:100%;height:4px;background:var(--dark4);border-radius:2px;outline:none;margin-top:10px;}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:20px;height:20px;border-radius:50%;background:var(--gold);cursor:pointer;box-shadow:0 0 0 3px rgba(201,168,76,.2);}

.badge-green{background:rgba(34,197,94,.12);color:#4ade80;border:1px solid rgba(34,197,94,.2);border-radius:100px;padding:2px 9px;font-size:10px;font-weight:600;}
.badge-red{background:rgba(239,68,68,.12);color:#f87171;border:1px solid rgba(239,68,68,.2);border-radius:100px;padding:2px 9px;font-size:10px;font-weight:600;}
.badge-gold{background:rgba(201,168,76,.12);color:var(--gold-light);border:1px solid rgba(201,168,76,.2);border-radius:100px;padding:2px 9px;font-size:10px;font-weight:600;}
.stat-pill{background:rgba(201,168,76,.1);border:1px solid rgba(201,168,76,.25);border-radius:100px;padding:3px 12px;font-size:11px;color:var(--gold-light);font-weight:600;}

.progress-bar{height:5px;background:var(--dark4);border-radius:3px;overflow:hidden;}
.progress-fill{height:100%;border-radius:3px;background:linear-gradient(90deg,var(--gold),var(--gold-light));transition:width .6s ease;}

table{width:100%;border-collapse:collapse;}
th{font-size:10px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);padding:8px 12px;text-align:left;border-bottom:1px solid rgba(255,255,255,.06);}
td{padding:10px 12px;font-size:12px;border-bottom:1px solid rgba(255,255,255,.04);}
tr:hover td{background:rgba(255,255,255,.02);}

.btn-outline{background:transparent;color:var(--gold-light);font-weight:600;padding:8px 18px;border-radius:8px;border:1px solid rgba(201,168,76,.35);cursor:pointer;font-family:'DM Sans',sans-serif;font-size:12px;transition:all .2s;}
.btn-outline:hover,.btn-outline:active{background:rgba(201,168,76,.1);}

.edu-card{background:var(--dark3);border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:18px;transition:all .3s;cursor:pointer;}
.edu-card:hover{border-color:var(--gold);transform:translateY(-2px);}

.chart-wrap{position:relative;max-width:190px;margin:0 auto;}
.chart-center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;}

.compare-row{display:flex;align-items:center;gap:10px;margin-bottom:12px;}
.compare-label{width:130px;font-size:11px;color:var(--muted);flex-shrink:0;}
.compare-bar{flex:1;height:7px;background:var(--dark4);border-radius:4px;overflow:hidden;}
.compare-fill{height:100%;border-radius:4px;transition:width .8s ease;}
.compare-val{width:70px;text-align:right;font-size:11px;font-family:'DM Mono',monospace;color:var(--gold-light);}

.milestone{display:flex;align-items:flex-start;gap:14px;padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05);}
.milestone:last-child{border-bottom:none;}
.milestone-dot{width:9px;height:9px;border-radius:50%;background:var(--gold);margin-top:4px;flex-shrink:0;box-shadow:0 0 7px rgba(201,168,76,.5);}

.tab{display:none;padding:24px 20px;max-width:1100px;}.tab.active{display:block;}

.accordion-content{max-height:0;overflow:hidden;transition:max-height .4s ease;}
.accordion-content.open{max-height:500px;}

@keyframes pulse{0%,100%{opacity:1;}50%{opacity:.4;}}
.live-dot{width:6px;height:6px;border-radius:50%;background:#4ade80;display:inline-block;animation:pulse 2s infinite;}

@keyframes shimmer{0%{background-position:-200% 0}100%{background-position:200% 0}}
.sb-skeleton{height:16px;border-radius:4px;margin-bottom:8px;background:linear-gradient(90deg,var(--dark4) 25%,var(--dark3) 50%,var(--dark4) 75%);background-size:200% 100%;animation:shimmer 1.4s infinite;}

.num-input{background:var(--dark4);border:1px solid rgba(201,168,76,.2);border-radius:8px;color:var(--cream);padding:10px 14px;font-family:'DM Mono',monospace;font-size:14px;width:100%;outline:none;}
.num-input:focus{border-color:var(--gold);}

@keyframes fadeUp{from{opacity:0;transform:translateY(16px);}to{opacity:1;transform:translateY(0);}}
.fade-in{animation:fadeUp .4s ease forwards;}
.d1{animation-delay:.1s;opacity:0;}.d2{animation-delay:.2s;opacity:0;}

/* ===== MOBILE ===== */
@media(max-width:768px){
  /* Topbar: fixed at top */
  #topbar{
    display:flex;
    position:fixed;top:0;left:0;right:0;
    height:var(--topbar-h);
    background:var(--dark2);
    border-bottom:1px solid rgba(201,168,76,.15);
    padding:0 14px;
    align-items:center;justify-content:space-between;gap:10px;
    z-index:999;
  }

  /* Bottom nav: fixed at bottom */
  #bottom-nav{
    display:flex;
    position:fixed;bottom:0;left:0;right:0;
    height:var(--bottomnav-h);
    background:var(--dark2);
    border-top:1px solid rgba(201,168,76,.15);
    padding:0 2px 8px;
    align-items:flex-end;
    z-index:999;
    overflow-x:auto;
    -webkit-overflow-scrolling:touch;
    scrollbar-width:none;
  }
  #bottom-nav::-webkit-scrollbar{display:none;}

  /* Sidebar: fixed drawer */
  #sidebar{
    position:fixed;left:0;top:0;
    height:100%;width:var(--sidebar-w);
    transform:translateX(-100%);
    transition:transform .3s ease;
    z-index:1000;
    box-shadow:4px 0 40px rgba(0,0,0,.5);
  }
  #sidebar.open{transform:translateX(0);}

  /* App: just a wrapper, no overflow tricks */
  .app{display:block;}

  /* Main: full viewport, flex column like desktop */
  #main{
    display:flex;
    flex-direction:column;
    height:100vh;height:100dvh;
    overflow:hidden;
    padding-top:var(--topbar-h);
  }

  /* Scroll area fills remaining space */
  #main-scroll{
    flex:1;
    overflow-y:scroll;
    overflow-x:hidden;
    -webkit-overflow-scrolling:touch;
    padding-bottom:var(--bottomnav-h);
    box-sizing:border-box;
    min-height:0;
  }

  /* Layout */
  .big-number{font-size:2rem;}
  .tab{padding:16px 14px;}
  h1.display{font-size:1.8rem !important;}
  .grid-3{grid-template-columns:1fr;}
  .grid-2-1{grid-template-columns:1fr;}
  .grid-2{grid-template-columns:1fr;}
  .card{padding:16px;}
  .result-box{padding:14px;}
  .mode-banner{padding:5px 14px;font-size:8px;}
  .table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;}
  .compare-label{width:90px;}
  .compare-val{width:58px;}
  .chart-wrap{max-width:150px;}
  .edu-3{grid-template-columns:1fr !important;}
}
@media(min-width:769px) and (max-width:1024px){
  :root{--sidebar-w:230px;}
  .grid-3{grid-template-columns:repeat(2,1fr);}
  .tab{padding:28px 24px;}
  .big-number{font-size:2.3rem;}
}

/* ===== MARKET PULSE NEWS ===== */
#news-strip{padding:16px 20px;border-bottom:1px solid rgba(255,255,255,.06);background:var(--dark2);}
.news-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;}
.news-header-label{font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted);display:flex;align-items:center;gap:6px;}
.news-refresh{font-size:9px;color:var(--muted);cursor:pointer;padding:3px 8px;border-radius:100px;border:1px solid rgba(255,255,255,.08);background:transparent;font-family:'DM Sans',sans-serif;transition:all .2s;}
.news-refresh:hover{border-color:rgba(201,168,76,.3);color:var(--gold-light);}
.news-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;}
@media(max-width:1024px){.news-grid{grid-template-columns:repeat(2,1fr);}}
@media(max-width:768px){.news-grid{grid-template-columns:1fr 1fr;gap:8px;}#news-strip{padding:12px 14px;}}
.news-card{background:var(--dark3);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:12px;cursor:pointer;transition:all .25s;text-decoration:none;display:block;}
.news-card:hover{border-color:rgba(201,168,76,.25);transform:translateY(-1px);}
.news-card-top{display:flex;align-items:center;gap:6px;margin-bottom:8px;}
.news-badge{font-size:8px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:2px 7px;border-radius:100px;}
.news-time{font-size:9px;color:var(--muted);margin-left:auto;font-family:'DM Mono',monospace;white-space:nowrap;}
.news-title{font-size:11px;font-weight:600;color:var(--cream);line-height:1.5;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
.news-skeleton{background:linear-gradient(90deg,var(--dark4) 25%,var(--dark3) 50%,var(--dark4) 75%);background-size:200% 100%;animation:shimmer 1.4s infinite;border-radius:6px;}
</style>
</head>
<body>
<div class="app">

<!-- MOBILE TOP BAR -->
<div id="topbar">
  <button id="menu-btn" onclick="toggleDrawer()" aria-label="Menu">
    <span></span><span></span><span></span>
  </button>
  <div class="display" style="font-size:16px;font-weight:900;letter-spacing:-.3px;flex-shrink:0;">
    MONEY<span style="color:var(--gold);">VEDA</span>
  </div>
  <div class="mob-mode-row">
    <button class="mob-mode-btn active-india" id="mob-btn-india" onclick="setMode('india')">🇮🇳</button>
    <button class="mob-mode-btn" id="mob-btn-usa" onclick="setMode('usa')">🇺🇸</button>
    <button class="mob-mode-btn" id="mob-btn-europe" onclick="setMode('europe')">🇪🇺</button>
    <button class="mob-mode-btn" id="mob-btn-world" onclick="setMode('world')">🌍</button>
  </div>
</div>

<div id="drawer-overlay" onclick="closeDrawer()"></div>

<!-- SIDEBAR -->
<nav id="sidebar">
  <div style="padding:20px 18px 14px;">
    <div class="display" style="font-size:18px;font-weight:900;letter-spacing:-.5px;">
      MONEY<span style="color:var(--gold);">VEDA</span>
    </div>
    <div style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin-top:2px;">India's Finance Suite</div>
    <div style="margin-top:14px;">
      <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:7px;">Market Region</div>
      <div class="mode-grid">
        <button class="mode-btn active-india" id="desk-btn-india" onclick="setMode('india')">🇮🇳 India</button>
        <button class="mode-btn" id="desk-btn-usa" onclick="setMode('usa')">🇺🇸 USA</button>
        <button class="mode-btn" id="desk-btn-europe" onclick="setMode('europe')">🇪🇺 Europe</button>
        <button class="mode-btn" id="desk-btn-world" onclick="setMode('world')">🌍 World</button>
      </div>
    </div>
  </div>

  <div class="gold-line" style="margin:0 18px;"></div>

  <div style="padding:12px 0;flex:1;overflow-y:auto;">
    <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);padding:8px 20px 5px;">Calculators</div>
    <div class="nav-item active" id="btn-sip"       onclick="navTo('sip')">📈 Investment Planner</div>
    <div class="nav-item"       id="btn-emi"        onclick="navTo('emi')">🏠 Loan & Mortgage</div>
    <div class="nav-item"       id="btn-fire"       onclick="navTo('fire')">🔥 FIRE Retirement</div>
    <div class="nav-item"       id="btn-roi"        onclick="navTo('roi')">💹 ROI & Compound</div>
    <div class="nav-item"       id="btn-insurance"  onclick="navTo('insurance')">🛡️ Insurance Planner</div>
    <div class="nav-item"       id="btn-tax"        onclick="navTo('tax')">📋 Tax Optimizer</div>
    <div id="india-only-nav">
    <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);padding:16px 20px 5px;">🇮🇳 India Schemes</div>
    <div class="nav-item" id="btn-ppf"     onclick="navTo('ppf')">🏦 PPF Calculator</div>
    <div class="nav-item" id="btn-epf"     onclick="navTo('epf')">👷 EPF Calculator</div>
    <div class="nav-item" id="btn-nps"     onclick="navTo('nps')">🎯 NPS Calculator</div>
    <div class="nav-item" id="btn-stepsip" onclick="navTo('stepsip')">📊 Step-Up SIP</div>
    <div class="nav-item" id="btn-ssa"     onclick="navTo('ssa')">👧 Sukanya Samriddhi</div>
    </div>
    <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);padding:16px 20px 5px;">🔥 Viral Tools</div>
    <div class="nav-item" id="btn-crorepati" onclick="navTo('crorepati')" style="color:var(--gold-light);"><span id="nav-crorepati-label">🏆 Crorepati Calc</span></div>
    <div class="nav-item" id="btn-habit"     onclick="navTo('habit')"     style="color:var(--gold-light);">☕ Habit vs Invest</div>
    <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);padding:16px 20px 5px;">Learn</div>
    <div class="nav-item" id="btn-edu"      onclick="navTo('edu')">🎓 Financial Academy</div>
    <div class="nav-item" id="btn-glossary" onclick="navTo('glossary')">📖 Glossary</div>
    <div class="nav-item" id="btn-compare" onclick="navTo('compare')">⚖️ SIP vs Lump Sum</div>
    <div class="nav-item" id="btn-contact"  onclick="navTo('contact')">✉️ Write to Us</div>
  </div>

  <div style="padding:14px 18px;border-top:1px solid rgba(201,168,76,.1);">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
      <div style="display:flex;align-items:center;gap:5px;">
        <span class="live-dot" id="sidebar-live-dot"></span>
        <span style="font-size:10px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;">Live</span>
      </div>
      <span style="font-size:9px;color:var(--muted);" id="sidebar-updated">—</span>
    </div>
    <div id="sidebar-market">
      <div class="sb-skeleton"></div><div class="sb-skeleton"></div>
      <div class="sb-skeleton"></div><div class="sb-skeleton"></div>
      <div class="sb-skeleton"></div>
    </div>
    <div style="font-size:8px;color:var(--muted);margin-top:8px;line-height:1.5;">Live via /api/market · 30s refresh<br>Not for trading.</div>
  </div>
</nav>

<!-- MAIN -->
<div id="main">
  <div class="mode-banner india" id="mode-banner">🇮🇳 &nbsp;India — INR · NSE/BSE · Indian Tax Laws</div>

  <div id="live-ticker" style="background:var(--dark2);border-bottom:1px solid rgba(201,168,76,.1);overflow:hidden;height:44px;position:relative;flex-shrink:0;">
    <div id="ticker-track" style="display:flex;align-items:center;height:100%;position:absolute;white-space:nowrap;will-change:transform;"></div>
  </div>


  <!-- ====== MARKET PULSE — India RSS News ====== -->
  <div id="news-strip" style="display:none;">
    <div class="news-header">
      <div class="news-header-label">
        <span class="live-dot" id="news-live-dot"></span>
        📰 Market Pulse — Official Sources
      </div>
      <button class="news-refresh" onclick="fetchNews(true)">↻ Refresh</button>
    </div>
    <div class="news-grid" id="news-grid">
      <!-- Skeletons shown on load -->
      <div style="background:var(--dark3);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:12px;">
        <div class="news-skeleton" style="height:12px;width:60%;margin-bottom:10px;"></div>
        <div class="news-skeleton" style="height:10px;width:100%;margin-bottom:6px;"></div>
        <div class="news-skeleton" style="height:10px;width:80%;"></div>
      </div>
      <div style="background:var(--dark3);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:12px;">
        <div class="news-skeleton" style="height:12px;width:50%;margin-bottom:10px;"></div>
        <div class="news-skeleton" style="height:10px;width:100%;margin-bottom:6px;"></div>
        <div class="news-skeleton" style="height:10px;width:90%;"></div>
      </div>
      <div style="background:var(--dark3);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:12px;">
        <div class="news-skeleton" style="height:12px;width:55%;margin-bottom:10px;"></div>
        <div class="news-skeleton" style="height:10px;width:100%;margin-bottom:6px;"></div>
        <div class="news-skeleton" style="height:10px;width:75%;"></div>
      </div>
      <div style="background:var(--dark3);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:12px;">
        <div class="news-skeleton" style="height:12px;width:65%;margin-bottom:10px;"></div>
        <div class="news-skeleton" style="height:10px;width:100%;margin-bottom:6px;"></div>
        <div class="news-skeleton" style="height:10px;width:85%;"></div>
      </div>
    </div>
    <div style="font-size:8px;color:rgba(144,144,168,.5);margin-top:8px;text-align:right;">
      Sources: RBI · AMFI · Official feeds only · <span id="news-updated">Updating…</span>
    </div>
  </div>

  <div id="main-scroll">

  <!-- ====== SIP TAB ====== -->
  <div id="sip" class="tab active">
    <div class="fade-in">
      <div class="section-eyebrow" id="sip-eyebrow">SIP · India</div>
      <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;" id="sip-title">Investment Planner</h1>
      <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;max-width:500px;" id="sip-desc">Harness compounding through disciplined monthly SIPs — India's most powerful wealth-creation tool.</p>
    </div>

    <div class="grid-3 fade-in d1" style="margin-bottom:20px;">
      <div class="result-box" style="box-shadow:0 0 24px rgba(201,168,76,.1);">
        <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Total Corpus</div>
        <div class="big-number" id="sip_total">—</div>
        <div class="stat-pill" style="margin-top:8px;display:inline-block;" id="sip_xbadge">0x</div>
      </div>
      <div class="result-box">
        <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Amount Invested</div>
        <div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;" id="sip_invested">—</div>
        <div style="font-size:11px;color:var(--muted);margin-top:6px;" id="sip_inv_note">—</div>
      </div>
      <div class="result-box">
        <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Wealth Gained</div>
        <div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;color:#4ade80;" id="sip_gains">—</div>
        <div style="font-size:11px;color:var(--muted);margin-top:6px;" id="sip_gain_pct">0% gains</div>
      </div>
    </div>

    <div class="grid-2-1 fade-in d2" style="margin-bottom:20px;">
      <div class="card">
        <div style="font-size:11px;font-weight:600;color:var(--muted);letter-spacing:.5px;margin-bottom:18px;">PARAMETERS</div>
        <div style="margin-bottom:20px;">
          <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
            <label style="font-size:12px;color:var(--muted);" id="sip-p-label">Monthly Investment</label>
            <span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_sip_p">—</span>
          </div>
          <input type="range" id="sip_p" min="500" max="200000" step="500" value="25000">
        </div>
        <div style="margin-bottom:20px;">
          <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
            <label style="font-size:12px;color:var(--muted);">Expected Return</label>
            <span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_sip_r">12.0</span><span style="font-size:10px;color:var(--muted);">%</span></span>
          </div>
          <input type="range" id="sip_r" min="1" max="30" step="0.5" value="12">
          <div style="font-size:9px;color:var(--muted);margin-top:3px;text-align:center;" id="sip-rate-hint">Nifty 50 hist. avg ~13%</div>
        </div>
        <div style="margin-bottom:20px;">
          <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
            <label style="font-size:12px;color:var(--muted);">Tenure</label>
            <span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_sip_t">15</span><span style="font-size:10px;color:var(--muted);">yrs</span></span>
          </div>
          <input type="range" id="sip_t" min="1" max="40" step="1" value="15">
        </div>
        <div style="background:rgba(201,168,76,.07);border:1px solid rgba(201,168,76,.2);border-radius:10px;padding:12px;">
          <div style="font-size:9px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:3px;" id="sip-tax-label">Tax Benefit</div>
          <div style="font-size:1.3rem;font-weight:700;font-family:'DM Mono',monospace;color:var(--gold-light);" id="sip_tax">—</div>
          <div style="font-size:10px;color:var(--muted);margin-top:3px;" id="sip-tax-note">—</div>
        </div>
      </div>
      <div class="card" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;">
        <div class="section-eyebrow" style="text-align:center;">Corpus Breakdown</div>
        <div class="chart-wrap">
          <canvas id="sipChart" width="160" height="160"></canvas>
          <div class="chart-center">
            <div style="font-size:8px;color:var(--muted);">Returns</div>
            <div style="font-size:1.1rem;font-weight:700;font-family:'Playfair Display',serif;color:var(--gold-light);" id="sip_return_pct_center">0%</div>
          </div>
        </div>
        <div style="display:flex;gap:12px;">
          <div style="display:flex;align-items:center;gap:5px;"><div style="width:8px;height:8px;border-radius:2px;background:#334155;"></div><span style="font-size:10px;color:var(--muted);">Invested</span></div>
          <div style="display:flex;align-items:center;gap:5px;"><div style="width:8px;height:8px;border-radius:2px;background:var(--gold);"></div><span style="font-size:10px;color:var(--muted);">Earnings</span></div>
        </div>
        <div style="width:100%;">
          <div style="font-size:10px;color:var(--muted);margin-bottom:6px;text-align:center;">Milestones</div>
          <div id="sip_milestones" style="font-size:11px;"></div>
        </div>
      </div>
    </div>

    <div style="display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;">
      <button class="btn-outline" onclick="shareResult('sip')" style="display:flex;align-items:center;gap:6px;flex:1;justify-content:center;"><span>📤</span> Share Result</button>
      <button class="btn-outline" onclick="navTo('compare')" style="display:flex;align-items:center;gap:6px;flex:1;justify-content:center;background:rgba(201,168,76,.08);"><span>⚖️</span> SIP vs Lump Sum</button>
    </div>

    <div class="card" style="margin-bottom:20px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:8px;">
        <h3 style="font-size:14px;font-weight:700;">Year-by-Year Projection</h3>
        <button class="btn-outline" onclick="downloadSIPCSV()">⬇ Export CSV</button>
      </div>
      <div class="table-wrap" style="max-height:280px;overflow-y:auto;">
        <table><thead><tr><th>Yr</th><th>Invested</th><th>Value</th><th>Gains</th><th>%</th><th>Progress</th></tr></thead>
        <tbody id="sip_tbody"></tbody></table>
      </div>
    </div>

    <div class="edu-3" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
      <div class="edu-card" onclick="showLesson('start-early')"><div style="font-size:20px;margin-bottom:8px;">⚡</div><h4 style="font-size:12px;font-weight:700;margin-bottom:6px;">Start Early</h4><p style="font-size:11px;color:var(--muted);line-height:1.6;" id="edu-sip-1">Time in market beats timing the market. Every decade of delay roughly halves your final corpus.</p><div style="margin-top:10px;font-size:10px;color:var(--gold);font-weight:700;letter-spacing:1px;">READ MORE →</div></div>
      <div class="edu-card" onclick="showLesson('rule-72')"><div style="font-size:20px;margin-bottom:8px;">📐</div><h4 style="font-size:12px;font-weight:700;margin-bottom:6px;">Rule of 72</h4><p style="font-size:11px;color:var(--muted);line-height:1.6;">Divide 72 by return rate = doubling time. At 12%, money doubles every 6 years.</p><div style="margin-top:10px;font-size:10px;color:var(--gold);font-weight:700;letter-spacing:1px;">READ MORE →</div></div>
      <div class="edu-card" onclick="showLesson('cost-averaging')"><div style="font-size:20px;margin-bottom:8px;">📊</div><h4 style="font-size:12px;font-weight:700;margin-bottom:6px;" id="edu-sip-3-title">Cost Averaging</h4><p style="font-size:11px;color:var(--muted);line-height:1.6;" id="edu-sip-3">Regular investing buys more units when prices fall and fewer when high — automatically lowering average cost.</p><div style="margin-top:10px;font-size:10px;color:var(--gold);font-weight:700;letter-spacing:1px;">READ MORE →</div></div>
    </div>
  </div>

  <!-- ====== EMI TAB ====== -->
  <div id="emi" class="tab">
    <div class="section-eyebrow" id="emi-eyebrow">Loan Planning</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;" id="emi-title">Loan & Mortgage Planner</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;" id="emi-desc">Calculate monthly repayments, total interest burden and tax benefits on your home loan.</p>

    <div class="grid-3" style="margin-bottom:20px;">
      <div class="result-box" style="box-shadow:0 0 24px rgba(201,168,76,.1);"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;" id="emi-monthly-label">Monthly EMI</div><div class="big-number" id="emi_monthly">—</div></div>
      <div class="result-box"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Total Interest</div><div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;color:#f87171;" id="emi_interest">—</div></div>
      <div class="result-box"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Total Payment</div><div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;" id="emi_total">—</div></div>
    </div>

    <div class="grid-2-1" style="margin-bottom:20px;">
      <div class="card">
        <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:18px;">LOAN PARAMETERS</div>
        <div style="margin-bottom:18px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);" id="emi-p-label">Loan Amount</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_emi_p">—</span></div><input type="range" id="emi_p" min="10000" max="20000000" step="10000" value="5000000"></div>
        <div style="margin-bottom:18px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Interest Rate</label><span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_emi_r">8.5</span><span style="font-size:10px;color:var(--muted);">%</span></span></div><input type="range" id="emi_r" min="1" max="20" step="0.25" value="8.5"><div style="font-size:9px;color:var(--muted);margin-top:3px;text-align:center;" id="emi-rate-hint">SBI Home Loan ~8.25% (2026)</div></div>
        <div style="margin-bottom:18px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Tenure</label><span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_emi_t">20</span><span style="font-size:10px;color:var(--muted);">yrs</span></span></div><input type="range" id="emi_t" min="1" max="30" step="1" value="20"></div>
        <div style="background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.15);border-radius:10px;padding:12px;">
          <div style="font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:3px;" id="emi-tax-label">Tax Benefit</div>
          <div style="font-size:1.2rem;font-weight:700;font-family:'DM Mono',monospace;color:#4ade80;" id="emi_tax_saved">—</div>
          <div style="font-size:10px;color:var(--muted);margin-top:2px;" id="emi-tax-note">Loading…</div>
        </div>
      </div>
      <div class="card" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;">
        <div class="section-eyebrow" style="text-align:center;">Payment Breakdown</div>
        <div class="chart-wrap"><canvas id="emiChart" width="160" height="160"></canvas><div class="chart-center"><div style="font-size:8px;color:var(--muted);">Interest</div><div style="font-size:1.1rem;font-weight:700;font-family:'Playfair Display',serif;color:#f87171;" id="emi_interest_pct_center">0%</div></div></div>
        <div style="width:100%;">
          <div class="compare-row"><span class="compare-label">Principal</span><div class="compare-bar"><div class="compare-fill" id="emi_bar_p" style="width:50%;background:#4f46e5;"></div></div><span class="compare-val" id="emi_pct_p">50%</span></div>
          <div class="compare-row"><span class="compare-label">Interest</span><div class="compare-bar"><div class="compare-fill" id="emi_bar_i" style="width:50%;background:#ef4444;"></div></div><span class="compare-val" id="emi_pct_i">50%</span></div>
        </div>
        <div style="background:rgba(201,168,76,.07);border:1px solid rgba(201,168,76,.15);border-radius:8px;padding:10px;width:100%;text-align:center;">
          <div style="font-size:10px;color:var(--muted);margin-bottom:3px;">Min income recommended</div>
          <div style="font-size:12px;color:var(--cream);" id="emi-dti-label">EMI &lt;40% of gross</div>
          <div style="font-size:11px;color:var(--gold-light);margin-top:2px;" id="emi_income_req">—</div>
        </div>
      </div>
    </div>

    <div class="card">
      <h3 style="font-size:14px;font-weight:700;margin-bottom:14px;">Amortization Schedule</h3>
      <div class="table-wrap" style="max-height:280px;overflow-y:auto;">
        <table><thead><tr><th>Yr</th><th>Opening</th><th>Principal</th><th>Interest</th><th>Closing</th></tr></thead>
        <tbody id="emi_tbody"></tbody></table>
      </div>
    </div>

    <div class="edu-3" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:20px;">
      <div class="edu-card" onclick="showLesson('emi-prepay')"><div style="font-size:20px;margin-bottom:8px;">💰</div><h4 style="font-size:12px;font-weight:700;margin-bottom:6px;">Prepay Your Loan</h4><p style="font-size:11px;color:var(--muted);line-height:1.6;">Even one extra EMI/year can slash years off your loan and save lakhs in interest.</p><div style="margin-top:10px;font-size:10px;color:var(--gold);font-weight:700;letter-spacing:1px;">READ MORE →</div></div>
      <div class="edu-card" onclick="showLesson('emi-tax')"><div style="font-size:20px;margin-bottom:8px;">📋</div><h4 style="font-size:12px;font-weight:700;margin-bottom:6px;">Tax Benefits</h4><p style="font-size:11px;color:var(--muted);line-height:1.6;">A home loan gives you dual tax deductions — principal under 80C and interest under 24(b).</p><div style="margin-top:10px;font-size:10px;color:var(--gold);font-weight:700;letter-spacing:1px;">READ MORE →</div></div>
      <div class="edu-card" onclick="showLesson('emi-vs-rent')"><div style="font-size:20px;margin-bottom:8px;">🏠</div><h4 style="font-size:12px;font-weight:700;margin-bottom:6px;">Buy vs Rent</h4><p style="font-size:11px;color:var(--muted);line-height:1.6;">Buying isn't always better than renting. The real calculation is more nuanced than most think.</p><div style="margin-top:10px;font-size:10px;color:var(--gold);font-weight:700;letter-spacing:1px;">READ MORE →</div></div>
    </div>
  </div>

  <!-- ====== FIRE TAB ====== -->
  <div id="fire" class="tab">
    <div class="section-eyebrow" id="fire-eyebrow">Financial Independence</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;">🔥 FIRE Calculator</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;" id="fire-desc">Find your <strong style="color:var(--cream);">FIRE Number</strong> — the corpus that funds your lifestyle forever.</p>

    <div class="grid-3" style="margin-bottom:20px;">
      <div class="result-box" style="box-shadow:0 0 24px rgba(201,168,76,.1);"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">🎯 FIRE Corpus</div><div class="big-number" id="fire_corpus">—</div></div>
      <div class="result-box"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Years to FIRE</div><div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;" id="fire_years">0 yrs</div><div style="font-size:11px;margin-top:5px;color:var(--muted);" id="fire_year_label">—</div></div>
      <div class="result-box"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Safe Withdrawal/mo</div><div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;color:#4ade80;" id="fire_swr">—</div></div>
    </div>

    <div class="grid-2-1" style="margin-bottom:20px;">
      <div class="card">
        <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:18px;">FIRE INPUTS</div>
        <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Current Age</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_fire_age">30</span></div><input type="range" id="fire_age" min="20" max="55" value="30"></div>
        <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);" id="fire-exp-label">Monthly Expenses</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_fire_exp">—</span></div><input type="range" id="fire_exp" min="500" max="30000" step="100" value="5000"></div>
        <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Current Savings</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_fire_saved">—</span></div><input type="range" id="fire_saved" min="0" max="2000000" step="5000" value="100000"></div>
        <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Monthly Investment</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_fire_inv">—</span></div><input type="range" id="fire_inv" min="100" max="20000" step="100" value="2000"></div>
        <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Portfolio Return</label><span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_fire_ret">10</span><span style="font-size:10px;color:var(--muted);">%</span></span></div><input type="range" id="fire_ret" min="4" max="20" step="0.5" value="10"></div>
        <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Inflation</label><span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_fire_inf">6</span><span style="font-size:10px;color:var(--muted);">%</span></span></div><input type="range" id="fire_inf" min="1" max="12" step="0.5" value="6"></div>
      </div>
      <div class="card">
        <div class="section-eyebrow" style="margin-bottom:12px;">FIRE Journey</div>
        <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><span style="font-size:11px;color:var(--muted);">Progress to FIRE</span><span style="font-size:11px;color:var(--gold-light);font-weight:600;" id="fire_progress_pct">0%</span></div><div class="progress-bar"><div class="progress-fill" id="fire_progress_bar" style="width:0%;"></div></div></div>
        <div id="fire_milestones" style="font-size:11px;"></div>
        <div style="margin-top:14px;background:rgba(201,168,76,.07);border:1px solid rgba(201,168,76,.15);border-radius:10px;padding:12px;">
          <div style="font-size:9px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);margin-bottom:5px;">Your FIRE Type</div>
          <div id="fire_type" style="font-size:12px;font-weight:700;color:var(--gold-light);margin-bottom:4px;">—</div>
          <div id="fire_type_desc" style="font-size:10px;color:var(--muted);line-height:1.6;"></div>
        </div>
      </div>
    </div>

    <div class="edu-3" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:20px;">
      <div class="edu-card" onclick="showLesson('fire-4pct')"><div style="font-size:20px;margin-bottom:8px;">🔥</div><h4 style="font-size:12px;font-weight:700;margin-bottom:6px;">The 4% Rule</h4><p style="font-size:11px;color:var(--muted);line-height:1.6;">The safest withdrawal rate that lets your corpus last 30+ years without running out.</p><div style="margin-top:10px;font-size:10px;color:var(--gold);font-weight:700;letter-spacing:1px;">READ MORE →</div></div>
      <div class="edu-card" onclick="showLesson('fire-types')"><div style="font-size:20px;margin-bottom:8px;">🎯</div><h4 style="font-size:12px;font-weight:700;margin-bottom:6px;">Types of FIRE</h4><p style="font-size:11px;color:var(--muted);line-height:1.6;">Lean FIRE, Fat FIRE, Barista FIRE — find the retirement style that fits your lifestyle.</p><div style="margin-top:10px;font-size:10px;color:var(--gold);font-weight:700;letter-spacing:1px;">READ MORE →</div></div>
      <div class="edu-card" onclick="showLesson('fire-inflation')"><div style="font-size:20px;margin-bottom:8px;">📉</div><h4 style="font-size:12px;font-weight:700;margin-bottom:6px;">Inflation Risk</h4><p style="font-size:11px;color:var(--muted);line-height:1.6;">The silent destroyer of retirement plans — how to inflation-proof your FIRE corpus.</p><div style="margin-top:10px;font-size:10px;color:var(--gold);font-weight:700;letter-spacing:1px;">READ MORE →</div></div>
    </div>
  </div>

  <!-- ====== ROI TAB ====== -->
  <div id="roi" class="tab">
    <div class="section-eyebrow" id="roi-eyebrow">Returns Analysis</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;">ROI & Compound Growth</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;">Compare investment vehicles and understand compound growth.</p>

    <div class="grid-2-1" style="margin-bottom:20px;">
      <div class="card">
        <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:18px;">LUMP SUM CALCULATOR</div>
        <div style="margin-bottom:18px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);" id="roi-p-label">Initial Investment</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_roi_p">—</span></div><input type="range" id="roi_p" min="1000" max="1000000" step="1000" value="100000"></div>
        <div style="margin-bottom:18px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Annual Return</label><span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_roi_r">12</span><span style="font-size:10px;color:var(--muted);">%</span></span></div><input type="range" id="roi_r" min="1" max="30" step="0.5" value="12"></div>
        <div style="margin-bottom:18px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Period</label><span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_roi_t">20</span><span style="font-size:10px;color:var(--muted);">yrs</span></span></div><input type="range" id="roi_t" min="1" max="50" step="1" value="20"></div>
        <div class="grid-3" style="margin-top:20px;gap:8px;">
          <div class="result-box" style="padding:12px;"><div style="font-size:9px;text-transform:uppercase;color:var(--muted);margin-bottom:4px;">Final</div><div style="font-size:1.1rem;font-weight:800;color:var(--gold-light);font-family:'Playfair Display',serif;" id="roi_final">—</div></div>
          <div class="result-box" style="padding:12px;"><div style="font-size:9px;text-transform:uppercase;color:var(--muted);margin-bottom:4px;">Returns</div><div style="font-size:1.1rem;font-weight:800;color:#4ade80;font-family:'Playfair Display',serif;" id="roi_returns">—</div></div>
          <div class="result-box" style="padding:12px;"><div style="font-size:9px;text-transform:uppercase;color:var(--muted);margin-bottom:4px;">Multiplier</div><div style="font-size:1.1rem;font-weight:800;font-family:'Playfair Display',serif;" id="roi_mult">0x</div></div>
        </div>
      </div>
      <div class="card"><div class="section-eyebrow" style="text-align:center;margin-bottom:12px;">Growth Curve</div><canvas id="roiChart" height="200"></canvas></div>
    </div>

    <div class="card">
      <h3 style="font-size:14px;font-weight:700;margin-bottom:5px;" id="roi-compare-title">Asset Class Comparison — 20 Years</h3>
      <p style="font-size:11px;color:var(--muted);margin-bottom:16px;" id="roi-compare-sub">Historical averages</p>
      <div id="asset_compare"></div>
    </div>

    <div class="edu-3" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:20px;">
      <div class="edu-card" onclick="showLesson('roi-cagr')"><div style="font-size:20px;margin-bottom:8px;">📈</div><h4 style="font-size:12px;font-weight:700;margin-bottom:6px;">What is CAGR?</h4><p style="font-size:11px;color:var(--muted);line-height:1.6;">Compound Annual Growth Rate — the one number that tells you how an investment truly performed.</p><div style="margin-top:10px;font-size:10px;color:var(--gold);font-weight:700;letter-spacing:1px;">READ MORE →</div></div>
      <div class="edu-card" onclick="showLesson('roi-xirr')"><div style="font-size:20px;margin-bottom:8px;">🧮</div><h4 style="font-size:12px;font-weight:700;margin-bottom:6px;">CAGR vs XIRR</h4><p style="font-size:11px;color:var(--muted);line-height:1.6;">Why XIRR is the correct metric for SIPs — and why CAGR alone can mislead you.</p><div style="margin-top:10px;font-size:10px;color:var(--gold);font-weight:700;letter-spacing:1px;">READ MORE →</div></div>
      <div class="edu-card" onclick="showLesson('roi-rebalance')"><div style="font-size:20px;margin-bottom:8px;">⚖️</div><h4 style="font-size:12px;font-weight:700;margin-bottom:6px;">Rebalancing</h4><p style="font-size:11px;color:var(--muted);line-height:1.6;">Why rebalancing your portfolio annually beats buy-and-hold in risk-adjusted returns.</p><div style="margin-top:10px;font-size:10px;color:var(--gold);font-weight:700;letter-spacing:1px;">READ MORE →</div></div>
    </div>
  </div>

  <!-- ====== INSURANCE TAB ====== -->
  <div id="insurance" class="tab">
    <div class="section-eyebrow" id="ins-eyebrow">Protection Planning</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;" id="ins-title">Life Insurance Planner</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;" id="ins-desc">Calculate recommended cover and explore local insurance products.</p>

    <div class="grid-2-1" style="margin-bottom:20px;">
      <div class="card">
        <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:18px;">YOUR PROFILE</div>
        <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);" id="ins-inc-label">Annual Income</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_ins_inc">—</span></div><input type="range" id="ins_inc" min="10000" max="500000" step="5000" value="60000"></div>
        <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Current Age</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_ins_age">32</span></div><input type="range" id="ins_age" min="18" max="55" value="32"></div>
        <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Retirement Age</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_ins_ret">65</span></div><input type="range" id="ins_ret" min="55" max="70" value="65"></div>
        <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);" id="ins-liab-label">Liabilities</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_ins_liab">—</span></div><input type="range" id="ins_liab" min="0" max="500000" step="5000" value="100000"></div>
        <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Existing Cover</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_ins_exist">—</span></div><input type="range" id="ins_exist" min="0" max="500000" step="5000" value="0"></div>
      </div>
      <div class="card" style="display:flex;flex-direction:column;gap:12px;">
        <div class="result-box" style="box-shadow:0 0 24px rgba(201,168,76,.1);"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Recommended Cover</div><div class="big-number" id="ins_cover">—</div></div>
        <div class="result-box"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Coverage Gap</div><div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;color:#f87171;" id="ins_gap">—</div></div>
        <div style="background:rgba(201,168,76,.07);border:1px solid rgba(201,168,76,.15);border-radius:10px;padding:12px;">
          <div style="font-size:9px;color:var(--muted);margin-bottom:3px;text-transform:uppercase;letter-spacing:1px;" id="ins-premium-label">Est. Premium/yr</div>
          <div style="font-size:1.2rem;font-weight:700;font-family:'DM Mono',monospace;color:var(--gold-light);" id="ins_premium">—</div>
          <div style="font-size:9px;color:var(--muted);margin-top:2px;" id="ins-premium-note">Term plan estimate</div>
        </div>
      </div>
    </div>

    <!-- Local products panel — populated by JS -->
    <div class="card" id="ins-local-panel">
      <h3 style="font-size:14px;font-weight:700;margin-bottom:14px;" id="ins-local-title">Popular Products</h3>
      <div id="ins-local-content"></div>
    </div>
  </div>

  <!-- ====== TAX TAB ====== -->
  <div id="tax" class="tab">
    <div class="section-eyebrow" id="tax-eyebrow">Tax Optimization</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;" id="tax-title">Tax Optimizer</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;" id="tax-desc">Maximize deductions and compare tax regimes.</p>
    <!-- Dynamically rendered by JS per region -->
    <div id="tax-content"></div>
  </div>

  <!-- ====== EDU TAB ====== -->
  <div id="edu" class="tab">
    <div class="section-eyebrow">Financial Academy</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;">Master Your Money</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;">Structured learning for every stage of your wealth journey.</p>
    <div class="grid-3" style="margin-bottom:28px;">
      <div style="background:linear-gradient(135deg,rgba(201,168,76,.15),rgba(201,168,76,.03));border:1px solid rgba(201,168,76,.3);border-radius:14px;padding:20px;"><span class="badge-gold" style="margin-bottom:12px;display:inline-block;">Beginner</span><h3 style="font-size:15px;font-weight:800;margin-bottom:6px;">Financial Foundation</h3><p style="font-size:11px;color:var(--muted);line-height:1.6;margin-bottom:12px;">Emergency fund, insurance, first investment — the non-negotiables.</p><div style="font-size:10px;color:var(--muted);">6 modules · 45 min</div></div>
      <div style="background:linear-gradient(135deg,rgba(99,102,241,.12),rgba(99,102,241,.03));border:1px solid rgba(99,102,241,.25);border-radius:14px;padding:20px;"><span class="badge-gold" style="background:rgba(99,102,241,.12);color:#818cf8;border-color:rgba(99,102,241,.25);margin-bottom:12px;display:inline-block;">Intermediate</span><h3 style="font-size:15px;font-weight:800;margin-bottom:6px;">Wealth Architect</h3><p style="font-size:11px;color:var(--muted);line-height:1.6;margin-bottom:12px;">Asset allocation, equity vs debt, tax-efficient investing.</p><div style="font-size:10px;color:var(--muted);">8 modules · 75 min</div></div>
      <div style="background:linear-gradient(135deg,rgba(34,197,94,.1),rgba(34,197,94,.02));border:1px solid rgba(34,197,94,.2);border-radius:14px;padding:20px;"><span class="badge-green" style="margin-bottom:12px;display:inline-block;">Advanced</span><h3 style="font-size:15px;font-weight:800;margin-bottom:6px;">FIRE Mastermind</h3><p style="font-size:11px;color:var(--muted);line-height:1.6;margin-bottom:12px;">Retirement, withdrawal strategy, estate planning.</p><div style="font-size:10px;color:var(--muted);">10 modules · 90 min</div></div>
    </div>
    <h3 style="font-size:15px;font-weight:700;margin-bottom:14px;">Key Financial Concepts</h3>
    <div id="accordion_container" style="display:flex;flex-direction:column;gap:6px;"></div>
    <div class="card" style="margin-top:24px;"><h3 style="font-size:14px;font-weight:700;margin-bottom:16px;">Ideal Milestone Timeline</h3><div id="timeline_content"></div></div>
  </div>

  <!-- ====== GLOSSARY TAB ====== -->
  <div id="glossary" class="tab">
    <div class="section-eyebrow">Reference</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;">Finance Glossary</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;">Every financial term in plain language.</p>
    <div style="position:relative;margin-bottom:20px;">
      <input id="gloss_search" type="text" placeholder="Search any term…" class="num-input" style="padding-left:40px;">
      <span style="position:absolute;left:13px;top:50%;transform:translateY(-50%);color:var(--muted);">🔍</span>
    </div>
    <div id="glossary_list"></div>
  </div>

  <!-- ====== COMPARE TAB ====== -->
  <div id="compare" class="tab">
    <div class="section-eyebrow">Side-by-Side Analysis</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;">SIP vs Lump Sum</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;">Same money, same return, same duration — which strategy wins?</p>

    <div class="card" style="margin-bottom:20px;">
      <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:18px;">COMPARISON INPUTS</div>
      <div class="grid-3" style="gap:18px;">
        <div>
          <div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Monthly Amount</label><span class="mono" style="font-size:13px;font-weight:600;color:var(--gold-light);" id="cmp_p_val">—</span></div>
          <input type="range" id="cmp_p" min="500" max="200000" step="500" value="25000" oninput="buildCompare()">
        </div>
        <div>
          <div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Annual Return</label><span class="mono" style="font-size:13px;font-weight:600;color:var(--gold-light);" id="cmp_r_val">12%</span></div>
          <input type="range" id="cmp_r" min="1" max="30" step="0.5" value="12" oninput="buildCompare()">
        </div>
        <div>
          <div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Years</label><span class="mono" style="font-size:13px;font-weight:600;color:var(--gold-light);" id="cmp_t_val">15 yrs</span></div>
          <input type="range" id="cmp_t" min="1" max="40" step="1" value="15" oninput="buildCompare()">
        </div>
      </div>
    </div>

    <div class="grid-2" style="margin-bottom:20px;">
      <div class="result-box" id="cmp_sip_box" style="padding:20px;">
        <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">📈 SIP (Monthly)</div>
        <div style="font-family:Playfair Display,serif;font-size:1.9rem;font-weight:900;color:var(--gold-light);" id="cmp_sip_corpus">—</div>
        <div style="font-size:11px;color:var(--muted);margin-top:6px;" id="cmp_sip_detail">—</div>
        <div style="margin-top:12px;font-size:10px;font-weight:700;color:#4ade80;" id="cmp_sip_winner"></div>
      </div>
      <div class="result-box" id="cmp_ls_box" style="padding:20px;">
        <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">💰 Lump Sum (Upfront)</div>
        <div style="font-family:Playfair Display,serif;font-size:1.9rem;font-weight:900;color:var(--gold-light);" id="cmp_ls_corpus">—</div>
        <div style="font-size:11px;color:var(--muted);margin-top:6px;" id="cmp_ls_detail">—</div>
        <div style="margin-top:12px;font-size:10px;font-weight:700;color:#4ade80;" id="cmp_ls_winner"></div>
      </div>
    </div>

    <div class="card" style="margin-bottom:20px;">
      <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:14px;">YEAR-BY-YEAR GROWTH</div>
      <canvas id="cmpChart" height="180"></canvas>
    </div>

    <div class="card" style="margin-bottom:20px;">
      <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:16px;">THE VERDICT</div>
      <div id="cmp_verdict" style="font-size:13px;color:var(--cream);line-height:1.8;"></div>
    </div>

    <div class="edu-3" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
      <div class="edu-card" onclick="showLesson('cmp-when-sip')"><div style="font-size:20px;margin-bottom:8px;">📅</div><h4 style="font-size:12px;font-weight:700;margin-bottom:6px;">When to Choose SIP</h4><p style="font-size:11px;color:var(--muted);line-height:1.6;">SIPs shine in volatile markets and for salaried investors who earn monthly.</p><div style="margin-top:10px;font-size:10px;color:var(--gold);font-weight:700;letter-spacing:1px;">READ MORE →</div></div>
      <div class="edu-card" onclick="showLesson('cmp-when-ls')"><div style="font-size:20px;margin-bottom:8px;">💸</div><h4 style="font-size:12px;font-weight:700;margin-bottom:6px;">When Lump Sum Wins</h4><p style="font-size:11px;color:var(--muted);line-height:1.6;">After a market crash or when you have a windfall, lump sum can dramatically outperform.</p><div style="margin-top:10px;font-size:10px;color:var(--gold);font-weight:700;letter-spacing:1px;">READ MORE →</div></div>
      <div class="edu-card" onclick="showLesson('cmp-hybrid')"><div style="font-size:20px;margin-bottom:8px;">🔀</div><h4 style="font-size:12px;font-weight:700;margin-bottom:6px;">Hybrid Strategy</h4><p style="font-size:11px;color:var(--muted);line-height:1.6;">Lump sum into debt + STP to equity — how the pros deploy large amounts safely.</p><div style="margin-top:10px;font-size:10px;color:var(--gold);font-weight:700;letter-spacing:1px;">READ MORE →</div></div>
    </div>
  </div>


  <!-- ====== PPF TAB ====== -->
  <div id="ppf" class="tab">
    <div class="section-eyebrow">Government Scheme · India</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;">🏦 PPF Calculator</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;">Public Provident Fund — sovereign-backed, EEE tax status at 7.1% p.a. Best guaranteed tax-free investment in India.</p>
    <div class="grid-3" style="margin-bottom:20px;">
      <div class="result-box" style="box-shadow:0 0 24px rgba(201,168,76,.1);"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Maturity Value</div><div class="big-number" id="ppf_maturity">—</div></div>
      <div class="result-box"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Total Invested</div><div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;" id="ppf_invested">—</div></div>
      <div class="result-box"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Interest Earned</div><div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;color:#4ade80;" id="ppf_interest">—</div></div>
    </div>
    <div class="grid-2-1" style="margin-bottom:20px;">
      <div class="card">
        <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:18px;">PPF INPUTS</div>
        <div style="margin-bottom:20px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Yearly Investment</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_ppf_y">—</span></div><input type="range" id="ppf_y" min="500" max="150000" step="500" value="150000" oninput="calcPPF()"></div>
        <div style="margin-bottom:20px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Tenure (15 yr min)</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_ppf_t">15</span></div><input type="range" id="ppf_t" min="15" max="50" step="5" value="15" oninput="calcPPF()"></div>
        <div style="background:rgba(201,168,76,.07);border:1px solid rgba(201,168,76,.2);border-radius:10px;padding:12px;margin-bottom:10px;"><div style="font-size:9px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Current PPF Rate</div><div style="font-size:1.4rem;font-weight:700;font-family:'DM Mono',monospace;color:var(--gold-light);">7.1% p.a.</div><div style="font-size:10px;color:var(--muted);margin-top:3px;">Compounded annually · Govt-set quarterly</div></div>
        <div style="background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.15);border-radius:10px;padding:12px;"><div style="font-size:9px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Tax Saved (80C/yr)</div><div style="font-size:1.2rem;font-weight:700;font-family:'DM Mono',monospace;color:#4ade80;" id="ppf_tax">—</div><div style="font-size:10px;color:var(--muted);margin-top:3px;">EEE — Exempt on invest, growth &amp; withdrawal</div></div>
      </div>
      <div class="card"><div class="section-eyebrow" style="margin-bottom:12px;">Year-by-Year</div><div class="table-wrap" style="max-height:320px;overflow-y:auto;"><table><thead><tr><th>Yr</th><th>Invested</th><th>Interest</th><th>Balance</th></tr></thead><tbody id="ppf_tbody"></tbody></table></div></div>
    </div>
  </div>

  <!-- ====== EPF TAB ====== -->
  <div id="epf" class="tab">
    <div class="section-eyebrow">Employee Benefit · India</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;">👷 EPF Calculator</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;">Employee Provident Fund — 8.25% guaranteed with employer matching. Your most underappreciated wealth builder.</p>
    <div class="grid-3" style="margin-bottom:20px;">
      <div class="result-box" style="box-shadow:0 0 24px rgba(201,168,76,.1);"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">EPF Corpus at Retirement</div><div class="big-number" id="epf_corpus">—</div></div>
      <div class="result-box"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Your Total Contribution</div><div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;" id="epf_employee">—</div></div>
      <div class="result-box"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Employer Contribution</div><div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;color:#4ade80;" id="epf_employer">—</div></div>
    </div>
    <div class="card" style="margin-bottom:20px;">
      <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:18px;">YOUR EMPLOYMENT DETAILS</div>
      <div class="grid-3" style="gap:20px;">
        <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Basic Salary/month</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_epf_sal">—</span></div><input type="range" id="epf_sal" min="10000" max="300000" step="1000" value="50000" oninput="calcEPF()"></div>
        <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Current Age</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_epf_age">28</span></div><input type="range" id="epf_age" min="18" max="55" step="1" value="28" oninput="calcEPF()"></div>
        <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Salary Growth %/yr</label><span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_epf_grow">8</span><span style="font-size:10px;color:var(--muted);">%</span></span></div><input type="range" id="epf_grow" min="0" max="20" step="1" value="8" oninput="calcEPF()"></div>
      </div>
      <div style="margin-top:16px;padding:12px;background:rgba(201,168,76,.07);border:1px solid rgba(201,168,76,.15);border-radius:10px;display:flex;gap:24px;flex-wrap:wrap;">
        <div><div style="font-size:9px;color:var(--muted);text-transform:uppercase;">EPF Rate</div><div style="font-size:1.1rem;font-weight:700;color:var(--gold-light);font-family:'DM Mono',monospace;">8.25% p.a.</div></div>
        <div><div style="font-size:9px;color:var(--muted);text-transform:uppercase;">Employee</div><div style="font-size:1.1rem;font-weight:700;color:var(--gold-light);font-family:'DM Mono',monospace;">12% of basic</div></div>
        <div><div style="font-size:9px;color:var(--muted);text-transform:uppercase;">Employer EPF</div><div style="font-size:1.1rem;font-weight:700;color:var(--gold-light);font-family:'DM Mono',monospace;">3.67%</div></div>
        <div><div style="font-size:9px;color:var(--muted);text-transform:uppercase;">Retirement</div><div style="font-size:1.1rem;font-weight:700;color:var(--gold-light);font-family:'DM Mono',monospace;">Age 58</div></div>
      </div>
    </div>
    <div id="epf_result_card" class="card"></div>
  </div>

  <!-- ====== NPS TAB ====== -->
  <div id="nps" class="tab">
    <div class="section-eyebrow">Pension Scheme · India</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;">🎯 NPS Calculator</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;">National Pension System — market-linked growth with an extra ₹50,000 tax deduction under 80CCD(1B), over and above 80C.</p>
    <div class="grid-3" style="margin-bottom:20px;">
      <div class="result-box" style="box-shadow:0 0 24px rgba(201,168,76,.1);"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">NPS Corpus</div><div class="big-number" id="nps_corpus">—</div></div>
      <div class="result-box"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Lump Sum (60%)</div><div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;color:#4ade80;" id="nps_lumpsum">—</div></div>
      <div class="result-box"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Monthly Pension</div><div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;color:var(--gold-light);" id="nps_pension">—</div></div>
    </div>
    <div class="grid-2-1" style="margin-bottom:20px;">
      <div class="card">
        <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:18px;">NPS INPUTS</div>
        <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Monthly Contribution</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_nps_p">—</span></div><input type="range" id="nps_p" min="500" max="100000" step="500" value="5000" oninput="calcNPS()"></div>
        <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Current Age</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_nps_age">30</span></div><input type="range" id="nps_age" min="18" max="55" step="1" value="30" oninput="calcNPS()"></div>
        <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Equity % (max 75%)</label><span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_nps_eq">75</span><span style="font-size:10px;color:var(--muted);">%</span></span></div><input type="range" id="nps_eq" min="0" max="75" step="5" value="75" oninput="calcNPS()"></div>
        <div style="background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.15);border-radius:10px;padding:12px;"><div style="font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">Extra Tax Saving</div><div style="font-size:1.2rem;font-weight:700;font-family:'DM Mono',monospace;color:#4ade80;" id="nps_tax">—</div><div style="font-size:10px;color:var(--muted);margin-top:3px;">80CCD(1B) — ₹50K extra over 80C</div></div>
      </div>
      <div class="card"><div class="section-eyebrow" style="margin-bottom:12px;">Fund Allocation</div><div id="nps_alloc"></div><div style="margin-top:14px;padding:10px;background:rgba(201,168,76,.06);border:1px solid rgba(201,168,76,.12);border-radius:8px;font-size:11px;color:var(--cream);line-height:1.7;">60% withdrawn tax-free at 60. 40% buys annuity (pension at 6% p.a.).</div></div>
    </div>
  </div>

  <!-- ====== STEP-UP SIP TAB ====== -->
  <div id="stepsip" class="tab">
    <div class="section-eyebrow">Advanced SIP · India</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;">📊 Step-Up SIP Calculator</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;">Increase your SIP by a fixed % every year as your income grows. A 10% step-up can <strong style="color:var(--cream);">nearly double</strong> your final corpus vs a flat SIP.</p>
    <div class="grid-3" style="margin-bottom:20px;">
      <div class="result-box" style="box-shadow:0 0 24px rgba(201,168,76,.1);"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Step-Up Corpus</div><div class="big-number" id="ss_corpus">—</div></div>
      <div class="result-box"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">vs Flat SIP</div><div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;color:#4ade80;" id="ss_flat">—</div></div>
      <div class="result-box"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Extra Wealth</div><div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;color:var(--gold-light);" id="ss_extra">—</div></div>
    </div>
    <div class="card" style="margin-bottom:20px;">
      <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:18px;">STEP-UP INPUTS</div>
      <div class="grid-3" style="gap:20px;">
        <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Starting Monthly SIP</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_ss_p">—</span></div><input type="range" id="ss_p" min="500" max="100000" step="500" value="10000" oninput="calcStepSIP()"></div>
        <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Annual Step-Up %</label><span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_ss_step">10</span><span style="font-size:10px;color:var(--muted);">%</span></span></div><input type="range" id="ss_step" min="0" max="30" step="1" value="10" oninput="calcStepSIP()"></div>
        <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Expected Return</label><span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_ss_r">12</span><span style="font-size:10px;color:var(--muted);">%</span></span></div><input type="range" id="ss_r" min="4" max="25" step="0.5" value="12" oninput="calcStepSIP()"></div>
        <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Tenure</label><span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_ss_t">20</span><span style="font-size:10px;color:var(--muted);">yrs</span></span></div><input type="range" id="ss_t" min="1" max="40" step="1" value="20" oninput="calcStepSIP()"></div>
      </div>
    </div>
    <div class="card"><div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:14px;">YEAR-BY-YEAR</div><div class="table-wrap" style="max-height:300px;overflow-y:auto;"><table><thead><tr><th>Yr</th><th>Monthly SIP</th><th>Step-Up Value</th><th>Flat SIP Value</th><th>Advantage</th></tr></thead><tbody id="ss_tbody"></tbody></table></div></div>
  </div>

  <!-- ====== SSA TAB ====== -->
  <div id="ssa" class="tab">
    <div class="section-eyebrow">Girl Child Scheme · India</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;">👧 Sukanya Samriddhi Calculator</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;">Best government scheme for daughters — 8.2% p.a., EEE tax. Invest 15 years, mature when she turns 21.</p>
    <div class="grid-3" style="margin-bottom:20px;">
      <div class="result-box" style="box-shadow:0 0 24px rgba(201,168,76,.1);"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Maturity Amount</div><div class="big-number" id="ssa_maturity">—</div></div>
      <div class="result-box"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Total Invested</div><div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;" id="ssa_invested">—</div></div>
      <div class="result-box"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Interest Earned</div><div style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;color:#4ade80;" id="ssa_interest">—</div></div>
    </div>
    <div class="grid-2-1">
      <div class="card">
        <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:18px;">ACCOUNT DETAILS</div>
        <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Daughter's Age</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_ssa_age">3</span></div><input type="range" id="ssa_age" min="0" max="10" step="1" value="3" oninput="calcSSA()"></div>
        <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Yearly Deposit</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_ssa_dep">—</span></div><input type="range" id="ssa_dep" min="250" max="150000" step="250" value="150000" oninput="calcSSA()"></div>
        <div style="background:rgba(236,72,153,.08);border:1px solid rgba(236,72,153,.2);border-radius:10px;padding:12px;"><div style="font-size:9px;color:var(--muted);margin-bottom:3px;text-transform:uppercase;letter-spacing:1px;">SSA Rate</div><div style="font-size:1.4rem;font-weight:700;font-family:'DM Mono',monospace;color:#f472b6;">8.2% p.a.</div></div>
      </div>
      <div class="card"><div class="section-eyebrow" style="margin-bottom:12px;">Year-by-Year</div><div class="table-wrap" style="max-height:320px;overflow-y:auto;"><table><thead><tr><th>Yr</th><th>Deposit</th><th>Interest</th><th>Balance</th></tr></thead><tbody id="ssa_tbody"></tbody></table></div></div>
    </div>
  </div>

  <!-- ====== CROREPATI / MILLIONAIRE TAB ====== -->
  <div id="crorepati" class="tab">
    <div class="section-eyebrow" style="color:var(--gold);">Viral Calculator</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;" id="cr_title">🏆 Crorepati Calculator</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;" id="cr_desc">How much do you need to invest every month to become a Crorepati?</p>
    <div class="card" style="margin-bottom:20px;background:linear-gradient(135deg,rgba(201,168,76,.1),rgba(201,168,76,.02));border-color:rgba(201,168,76,.3);">
      <div class="grid-3" style="gap:20px;margin-bottom:20px;">
        <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Target Corpus</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_cr_target">—</span></div><input type="range" id="cr_target" min="1000000" max="500000000" step="1000000" value="10000000" oninput="calcCrorepati()"></div>
        <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Time Frame</label><span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_cr_t">15</span><span style="font-size:10px;color:var(--muted);">yrs</span></span></div><input type="range" id="cr_t" min="1" max="40" step="1" value="15" oninput="calcCrorepati()"></div>
        <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Expected Return</label><span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_cr_r">12</span><span style="font-size:10px;color:var(--muted);">%</span></span></div><input type="range" id="cr_r" min="4" max="20" step="0.5" value="12" oninput="calcCrorepati()"></div>
      </div>
      <div style="text-align:center;padding:28px;background:rgba(201,168,76,.08);border:1px solid rgba(201,168,76,.25);border-radius:14px;">
        <div style="font-size:11px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin-bottom:8px;">YOU NEED TO INVEST</div>
        <div class="big-number" style="font-size:3.5rem;" id="cr_monthly">—</div>
        <div style="font-size:14px;color:var(--muted);margin-top:8px;">per month to reach <span id="cr_target_label" style="color:var(--gold-light);font-weight:700;">—</span> in <span id="cr_t_label" style="color:var(--cream);">15 years</span></div>
        <button class="btn-outline" onclick="shareResult('crorepati')" style="margin-top:16px;padding:10px 24px;font-size:13px;">📤 Share on WhatsApp</button>
      </div>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px;align-items:center;">
      <span style="font-size:11px;color:var(--muted);">Quick targets:</span>
      <div id="cr_quick_targets" style="display:flex;gap:8px;flex-wrap:wrap;"></div>
    </div>
    <div class="card" style="background:rgba(34,197,94,.06);border-color:rgba(34,197,94,.2);"><div id="cr_verdict" style="font-size:13px;line-height:1.8;color:var(--cream);"></div></div>
  </div>

  <!-- ====== HABIT VS INVEST TAB ====== -->
  <div id="habit" class="tab">
    <div class="section-eyebrow" style="color:var(--gold);">Viral Tool</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;">☕ Habit vs Investing</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:24px;">What if you invested the money you spend on daily habits? The numbers will shock you.</p>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px;" id="habit_pills">
      <button onclick="setHabit('coffee',4500)"    id="hp-coffee"    style="padding:7px 14px;border-radius:100px;font-size:11px;font-weight:700;cursor:pointer;background:rgba(201,168,76,.12);border:1px solid rgba(201,168,76,.4);color:var(--gold-light);font-family:'DM Sans',sans-serif;">☕ Coffee ₹150/day</button>
      <button onclick="setHabit('swiggy',12000)"   id="hp-swiggy"   style="padding:7px 14px;border-radius:100px;font-size:11px;font-weight:700;cursor:pointer;background:transparent;border:1px solid rgba(255,255,255,.1);color:var(--muted);font-family:'DM Sans',sans-serif;">🛵 Swiggy ₹400/day</button>
      <button onclick="setHabit('cigarette',6000)" id="hp-cigarette" style="padding:7px 14px;border-radius:100px;font-size:11px;font-weight:700;cursor:pointer;background:transparent;border:1px solid rgba(255,255,255,.1);color:var(--muted);font-family:'DM Sans',sans-serif;">🚬 Cigarette ₹200/day</button>
      <button onclick="setHabit('ott',2000)"       id="hp-ott"      style="padding:7px 14px;border-radius:100px;font-size:11px;font-weight:700;cursor:pointer;background:transparent;border:1px solid rgba(255,255,255,.1);color:var(--muted);font-family:'DM Sans',sans-serif;">📺 OTT ₹2,000/mo</button>
      <button onclick="setHabit('custom',0)"       id="hp-custom"   style="padding:7px 14px;border-radius:100px;font-size:11px;font-weight:700;cursor:pointer;background:transparent;border:1px solid rgba(255,255,255,.1);color:var(--muted);font-family:'DM Sans',sans-serif;">✏️ Custom</button>
    </div>
    <div class="card" style="margin-bottom:20px;">
      <div class="grid-3" style="gap:20px;">
        <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Monthly Habit Cost</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_hab_p">—</span></div><input type="range" id="hab_p" min="100" max="50000" step="100" value="4500" oninput="calcHabit()"></div>
        <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Years</label><span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_hab_t">20</span><span style="font-size:10px;color:var(--muted);">yrs</span></span></div><input type="range" id="hab_t" min="1" max="40" step="1" value="20" oninput="calcHabit()"></div>
        <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Return if Invested</label><span><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_hab_r">12</span><span style="font-size:10px;color:var(--muted);">%</span></span></div><input type="range" id="hab_r" min="4" max="20" step="0.5" value="12" oninput="calcHabit()"></div>
      </div>
    </div>
    <div class="grid-2" style="margin-bottom:20px;">
      <div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.25);border-radius:14px;padding:24px;text-align:center;"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#f87171;margin-bottom:8px;">💸 SPENT ON HABIT</div><div style="font-family:'Playfair Display',serif;font-size:2.4rem;font-weight:900;color:#f87171;" id="hab_spent">—</div><div style="font-size:11px;color:var(--muted);margin-top:6px;" id="hab_spent_sub">—</div></div>
      <div style="background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.25);border-radius:14px;padding:24px;text-align:center;"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#4ade80;margin-bottom:8px;">📈 IF INVESTED INSTEAD</div><div style="font-family:'Playfair Display',serif;font-size:2.4rem;font-weight:900;color:#4ade80;" id="hab_corpus">—</div><div style="font-size:11px;color:var(--muted);margin-top:6px;" id="hab_corpus_sub">—</div></div>
    </div>
    <div class="card" style="background:rgba(201,168,76,.06);border-color:rgba(201,168,76,.2);margin-bottom:20px;"><div id="hab_verdict" style="font-size:14px;line-height:1.9;color:var(--cream);"></div><button class="btn-outline" onclick="shareResult('habit')" style="margin-top:16px;">📤 Share on WhatsApp</button></div>
  </div>

  <!-- ====== CONTACT TAB ====== -->
  <div id="contact" class="tab">
    <div class="section-eyebrow">Get in Touch</div>
    <h1 class="display" style="font-size:2.2rem;font-weight:900;margin-bottom:6px;">✉️ Write to Us</h1>
    <p style="color:var(--muted);line-height:1.7;margin-bottom:28px;">Bug reports, feature requests, data corrections, press enquiries or partnership opportunities.</p>
    <div class="grid-2" style="gap:16px;margin-bottom:24px;">
      <div class="card">
        <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:18px;">SEND A MESSAGE</div>
        <div style="margin-bottom:14px;"><label style="font-size:11px;color:var(--muted);display:block;margin-bottom:5px;">Your Name</label><input type="text" id="ct_name" placeholder="Rahul Sharma" class="num-input" style="font-family:'DM Sans',sans-serif;font-size:13px;"></div>
        <div style="margin-bottom:14px;"><label style="font-size:11px;color:var(--muted);display:block;margin-bottom:5px;">Email Address</label><input type="email" id="ct_email" placeholder="you@email.com" class="num-input" style="font-family:'DM Sans',sans-serif;font-size:13px;"></div>
        <div style="margin-bottom:14px;"><label style="font-size:11px;color:var(--muted);display:block;margin-bottom:5px;">Topic</label>
          <select id="ct_topic" class="num-input" style="font-family:'DM Sans',sans-serif;font-size:13px;cursor:pointer;">
            <option value="">Select topic…</option>
            <option value="bug">🐛 Bug Report</option>
            <option value="feature">💡 Feature Request</option>
            <option value="data">📊 Data / Calculation Error</option>
            <option value="partnership">🤝 Partnership</option>
            <option value="press">📰 Press / Media</option>
            <option value="other">💬 Other</option>
          </select>
        </div>
        <div style="margin-bottom:18px;"><label style="font-size:11px;color:var(--muted);display:block;margin-bottom:5px;">Message</label><textarea id="ct_message" placeholder="Describe your query…" rows="5" class="num-input" style="font-family:'DM Sans',sans-serif;font-size:13px;resize:vertical;min-height:100px;"></textarea></div>
        <button onclick="submitContact()" style="width:100%;padding:13px;background:var(--gold);color:#0A0A0F;border:none;border-radius:10px;font-weight:700;font-size:14px;cursor:pointer;font-family:'DM Sans',sans-serif;">Send Message →</button>
        <div id="ct_success" style="display:none;margin-top:14px;padding:12px;background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.3);border-radius:10px;font-size:13px;color:#4ade80;text-align:center;"></div>
        <div id="ct_error"   style="display:none;margin-top:14px;padding:12px;background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);border-radius:10px;font-size:13px;color:#f87171;text-align:center;"></div>
      </div>
      <div style="display:flex;flex-direction:column;gap:14px;">
        <div class="card" style="background:rgba(201,168,76,.06);border-color:rgba(201,168,76,.2);"><div style="font-size:18px;margin-bottom:8px;">⏱️</div><div style="font-size:13px;font-weight:700;margin-bottom:4px;">Response Time</div><div style="font-size:12px;color:var(--muted);line-height:1.7;">We reply within <strong style="color:var(--cream);">24–48 hours</strong> on business days. Urgent data corrections prioritised same-day.</div></div>
        <div class="card"><div style="font-size:18px;margin-bottom:8px;">🐛</div><div style="font-size:13px;font-weight:700;margin-bottom:6px;">Found a Bug?</div><div style="font-size:12px;color:var(--muted);line-height:1.7;">Use the form to report calculation errors, UI issues or wrong data. We fix critical issues within <strong style="color:var(--cream);">24 hours</strong>.</div></div>
        <div class="card" style="background:rgba(239,68,68,.05);border-color:rgba(239,68,68,.15);"><div style="font-size:18px;margin-bottom:8px;">⚠️</div><div style="font-size:13px;font-weight:700;margin-bottom:6px;">Disclaimer</div><div id="contact_disclaimer" style="font-size:11px;color:var(--muted);line-height:1.7;">MoneyVeda is for educational purposes only. Not SEBI-registered. Consult a qualified adviser before investing.</div></div>
      </div>
    </div>
  </div>

  </div><!-- end main-scroll -->
</div><!-- end main -->

<!-- MOBILE BOTTOM NAV -->
<nav id="bottom-nav">
  <button class="bnav-item active" id="bnav-sip"      onclick="navTo('sip')"       style="position:relative;"><span class="bnav-icon">📈</span><span class="bnav-label">SIP</span><span class="bnav-indicator"></span></button>
  <button class="bnav-item" id="bnav-emi"              onclick="navTo('emi')"       style="position:relative;"><span class="bnav-icon">🏠</span><span class="bnav-label">EMI</span><span class="bnav-indicator"></span></button>
  <button class="bnav-item" id="bnav-fire"             onclick="navTo('fire')"      style="position:relative;"><span class="bnav-icon">🔥</span><span class="bnav-label">FIRE</span><span class="bnav-indicator"></span></button>
  <button class="bnav-item" id="bnav-ppf"              onclick="navTo('ppf')"       style="position:relative;"><span class="bnav-icon">🏦</span><span class="bnav-label">PPF</span><span class="bnav-indicator"></span></button>
  <button class="bnav-item" id="bnav-epf"              onclick="navTo('epf')"       style="position:relative;"><span class="bnav-icon">👷</span><span class="bnav-label">EPF</span><span class="bnav-indicator"></span></button>
  <button class="bnav-item" id="bnav-nps"              onclick="navTo('nps')"       style="position:relative;"><span class="bnav-icon">🎯</span><span class="bnav-label">NPS</span><span class="bnav-indicator"></span></button>
  <button class="bnav-item" id="bnav-stepsip"          onclick="navTo('stepsip')"   style="position:relative;"><span class="bnav-icon">📊</span><span class="bnav-label">Step SIP</span><span class="bnav-indicator"></span></button>
  <button class="bnav-item" id="bnav-ssa"              onclick="navTo('ssa')"       style="position:relative;"><span class="bnav-icon">👧</span><span class="bnav-label">SSA</span><span class="bnav-indicator"></span></button>
  <button class="bnav-item" id="bnav-crorepati"        onclick="navTo('crorepati')" style="position:relative;"><span class="bnav-icon">🏆</span><span class="bnav-label" id="bnav-cr-label">Crorepati</span><span class="bnav-indicator"></span></button>
  <button class="bnav-item" id="bnav-habit"            onclick="navTo('habit')"     style="position:relative;"><span class="bnav-icon">☕</span><span class="bnav-label">Habit$</span><span class="bnav-indicator"></span></button>
  <button class="bnav-item" id="bnav-roi"              onclick="navTo('roi')"       style="position:relative;"><span class="bnav-icon">💹</span><span class="bnav-label">ROI</span><span class="bnav-indicator"></span></button>
  <button class="bnav-item" id="bnav-insurance"        onclick="navTo('insurance')" style="position:relative;"><span class="bnav-icon">🛡️</span><span class="bnav-label">Insure</span><span class="bnav-indicator"></span></button>
  <button class="bnav-item" id="bnav-tax"              onclick="navTo('tax')"       style="position:relative;"><span class="bnav-icon">📋</span><span class="bnav-label">Tax</span><span class="bnav-indicator"></span></button>
  <button class="bnav-item" id="bnav-edu"              onclick="navTo('edu')"       style="position:relative;"><span class="bnav-icon">🎓</span><span class="bnav-label">Learn</span><span class="bnav-indicator"></span></button>
  <button class="bnav-item" id="bnav-compare"          onclick="navTo('compare')"   style="position:relative;"><span class="bnav-icon">⚖️</span><span class="bnav-label">Compare</span><span class="bnav-indicator"></span></button>
  <button class="bnav-item" id="bnav-contact"          onclick="navTo('contact')"   style="position:relative;"><span class="bnav-icon">✉️</span><span class="bnav-label">Contact</span><span class="bnav-indicator"></span></button>
</nav>

</div><!-- end app -->

<script>
// ================================================================
// REGION CONFIG — all locale data in one place
// ================================================================
const REGIONS = {
  india: {
    flag:'🇮🇳', name:'India',
    currency:'₹', code:'INR',
    bannerClass:'india',
    bannerText:'🇮🇳 &nbsp;India — INR · NSE/BSE · Indian Tax Laws',
    // SIP
    sipLabel:'Monthly SIP',
    sipDefault:25000, sipMin:500, sipMax:200000, sipStep:500,
    sipRateHint:'Nifty 50 hist. avg ~13%',
    sipTaxLabel:'Tax Saved (80C/ELSS)',
    sipTaxNote:'Up to ₹1.5L/yr deduction',
    sipTaxCalc:(p,r,t)=>Math.min(p*12,150000)*0.30,
    sipDesc:"Harness compounding through disciplined monthly SIPs — India's most powerful wealth-creation tool.",
    sipEdu1:'₹5,000/month at 25 = ₹3.5 Cr by 60. At 35, same SIP = only ₹1.2 Cr. Start early.',
    sipEdu3:'Rupee Cost Averaging',
    sipEdu3Desc:'SIPs buy more units when markets fall and fewer when high — automatically lowering average cost.',
    // EMI
    emiLabel:'Loan Amount',
    emiDefault:5000000, emiMin:100000, emiMax:20000000, emiStep:100000,
    emiRateDefault:8.5, emiRateHint:'SBI Home Loan ~8.25% (2026)',
    emiTaxLabel:'Tax Benefit Sec 24(b)',
    emiTaxNote:'Up to ₹2L deduction/yr',
    emiTaxCalc:(totalInt,t)=>Math.min(totalInt/t,200000)*0.30,
    emiDtiLabel:'EMI <40% of gross income',
    emiMonthlyLabel:'Monthly EMI',
    emiDesc:'Calculate EMI, total interest and Section 24(b) tax benefits on your home loan.',
    // FIRE
    fireExpDefault:75000, fireExpMin:10000, fireExpMax:500000, fireExpStep:5000,
    fireSavedDefault:2500000, fireSavedMin:0, fireSavedMax:50000000, fireSavedStep:100000,
    fireInvDefault:50000, fireInvMin:5000, fireInvMax:300000, fireInvStep:5000,
    fireLeanMax:40000, fireFatMin:150000,
    // ROI
    roiDefault:1000000, roiMin:10000, roiMax:10000000, roiStep:10000,
    roiAssets:[
      {name:'Savings A/C',rate:3.5,color:'#64748b'},{name:'FD (5yr)',rate:7.0,color:'#0ea5e9'},
      {name:'PPF (15yr)',rate:7.1,color:'#6366f1'},{name:'Gold (hist.)',rate:9.5,color:'#f59e0b'},
      {name:'Nifty 50',rate:13.0,color:'#C9A84C'},{name:'Equity MF',rate:14.0,color:'#4ade80'},
      {name:'Real Estate',rate:9.0,color:'#ec4899'},
    ],
    roiBase:100000,
    roiCompareSub:'Historical averages · Base: ₹1 Lakh',
    // Insurance
    insIncDefault:1800000, insIncMin:300000, insIncMax:10000000, insIncStep:100000,
    insRetDefault:60,
    insLiabDefault:3000000, insLiabMin:0, insLiabMax:20000000, insLiabStep:100000,
    insExistMin:0, insExistMax:20000000, insExistStep:100000,
    insPremiumRate:(age)=>age<35?0.0012:age<45?0.002:0.004,
    insDesc:'Calculate recommended cover using the Human Life Value (HLV) method.',
    insLocalTitle:'Popular Indian Insurance Products',
    insLocalItems:[
      {name:'LIC Tech Term Plan',detail:'Pure term cover up to ₹5 Cr. Online, no agent commission. Sec 80C deduction on premium.'},
      {name:'HDFC Click 2 Protect',detail:'Whole-life option available. Critical illness add-on. Premium waiver on disability.'},
      {name:'Max Life Smart Secure',detail:'Return of premium option. Increasing cover option to beat inflation.'},
      {name:'Star Health (Family Floater)',detail:'Cashless at 14,000+ hospitals. No co-pay. Includes AYUSH treatment.'},
      {name:'Niva Bupa Reassure 2.0',detail:'No room rent cap. Unlimited recharge. Mental health coverage included.'},
    ],
    // Tax
    taxDesc:'Compare Old vs New regime (FY2025-26) and maximize deductions.',
  },
  usa: {
    flag:'🇺🇸', name:'USA',
    currency:'$', code:'USD',
    bannerClass:'usa',
    bannerText:'🇺🇸 &nbsp;USA — USD · NYSE/NASDAQ · Federal Tax 2026',
    sipLabel:'Monthly Contribution',
    sipDefault:1500, sipMin:100, sipMax:10000, sipStep:100,
    sipRateHint:'S&P 500 hist. avg ~10.5%',
    sipTaxLabel:'401(k) Tax Saving (est.)',
    sipTaxNote:'22% bracket, $23,500 limit/yr',
    sipTaxCalc:(p,r,t)=>Math.min(p*12,23500)*0.22,
    sipDesc:'Build long-term wealth through consistent 401(k) and index fund investing — the American way.',
    sipEdu1:'$500/month at 25 in S&P 500 index = ~$1.9M by 65 at 10.5%. Start in your employer 401(k) first for the match.',
    sipEdu3:'Dollar-Cost Averaging',
    sipEdu3Desc:'Investing a fixed dollar amount regularly means buying more shares when prices drop — lowering your average cost per share.',
    emiLabel:'Loan Amount',
    emiDefault:400000, emiMin:50000, emiMax:2000000, emiStep:10000,
    emiRateDefault:6.75, emiRateHint:'30yr Fixed Mortgage ~6.75% (2026)',
    emiTaxLabel:'Mortgage Interest Deduction',
    emiTaxNote:'Up to $750K principal deductible',
    emiTaxCalc:(totalInt,t)=>Math.min(totalInt/t,25000)*0.22,
    emiDtiLabel:'DTI ratio should stay below 43%',
    emiMonthlyLabel:'Monthly Payment',
    emiDesc:'Calculate monthly payments, total interest and mortgage interest deduction on your home loan.',
    fireExpDefault:5000, fireExpMin:1000, fireExpMax:30000, fireExpStep:500,
    fireSavedDefault:100000, fireSavedMin:0, fireSavedMax:2000000, fireSavedStep:10000,
    fireInvDefault:2000, fireInvMin:200, fireInvMax:20000, fireInvStep:200,
    fireLeanMax:2500, fireFatMin:8000,
    roiDefault:100000, roiMin:5000, roiMax:1000000, roiStep:5000,
    roiAssets:[
      {name:'HYSA',rate:4.5,color:'#64748b'},{name:'US Treasury (10yr)',rate:4.3,color:'#0ea5e9'},
      {name:'S&P 500 Index',rate:10.5,color:'#6366f1'},{name:'Gold (hist.)',rate:8.5,color:'#f59e0b'},
      {name:'NASDAQ 100',rate:12.0,color:'#C9A84C'},{name:'Real Estate (REIT)',rate:8.0,color:'#4ade80'},
      {name:'Total Bond Market',rate:4.0,color:'#ec4899'},
    ],
    roiBase:10000,
    roiCompareSub:'Historical averages · Base: $10,000',
    insIncDefault:80000, insIncMin:30000, insIncMax:500000, insIncStep:5000,
    insRetDefault:65,
    insLiabDefault:200000, insLiabMin:0, insLiabMax:1000000, insLiabStep:10000,
    insExistMin:0, insExistMax:2000000, insExistStep:50000,
    insPremiumRate:(age)=>age<35?0.0012:age<45?0.002:0.004,
    insDesc:'Calculate recommended life cover using the DIME (Debt, Income, Mortgage, Education) method.',
    insLocalTitle:'Popular US Insurance Products',
    insLocalItems:[
      {name:'Term Life (20-30yr)',detail:'Pure death benefit. $500K policy for 30yr old ~$25/mo. Shop via Policygenius or Haven Life.'},
      {name:'Whole Life / IUL',detail:'Cash value builds tax-deferred. More complex — often better to buy term and invest the difference.'},
      {name:'Health Insurance (ACA)',detail:'Marketplace plans. Check for premium tax credits if income 100–400% of FPL. HSA eligible with HDHP.'},
      {name:'HSA — Health Savings Account',detail:'Triple tax advantage: pre-tax contributions, tax-free growth, tax-free medical withdrawals. 2026 limit: $4,300 single.'},
      {name:'Umbrella Insurance',detail:'Extra liability beyond home/auto policy. $1M coverage ~$200–300/yr. Essential for high net worth.'},
    ],
    taxDesc:'Calculate federal income tax, understand brackets and maximize deductions (FY2026).',
  },
  europe: {
    flag:'🇪🇺', name:'Europe',
    currency:'€', code:'EUR',
    bannerClass:'europe',
    bannerText:'🇪🇺 &nbsp;Europe — EUR · Euro Stoxx · EU Tax Overview',
    sipLabel:'Monthly Investment',
    sipDefault:500, sipMin:50, sipMax:10000, sipStep:50,
    sipRateHint:'Euro Stoxx 50 hist. avg ~8.5%',
    sipTaxLabel:'Tax-Advantaged Saving (est.)',
    sipTaxNote:'Varies by country',
    sipTaxCalc:(p,r,t)=>p*12*0.15*0.25,
    sipDesc:'Build wealth through diversified Euro-denominated ETFs and tax-advantaged European savings vehicles.',
    sipEdu1:'€300/month at 25 invested in a pan-European ETF = ~€830K at 60 at 8.5% avg. Use your country\'s ISA equivalent first.',
    sipEdu3:'Euro Cost Averaging',
    sipEdu3Desc:'Investing a fixed euro amount regularly means buying more units when markets fall — naturally lowering your average cost.',
    emiLabel:'Loan Amount',
    emiDefault:250000, emiMin:20000, emiMax:1500000, emiStep:10000,
    emiRateDefault:4.5, emiRateHint:'ECB rate ~3.65% · avg mortgage ~4.5% (2026)',
    emiTaxLabel:'Mortgage Interest Relief',
    emiTaxNote:'Varies by EU country',
    emiTaxCalc:(totalInt,t)=>(totalInt/t)*0.15,
    emiDtiLabel:'DTI ratio below 40% recommended',
    emiMonthlyLabel:'Monthly Payment',
    emiDesc:'Calculate monthly repayments and total interest on your European mortgage.',
    fireExpDefault:2500, fireExpMin:500, fireExpMax:15000, fireExpStep:250,
    fireSavedDefault:80000, fireSavedMin:0, fireSavedMax:1000000, fireSavedStep:5000,
    fireInvDefault:1000, fireInvMin:100, fireInvMax:10000, fireInvStep:100,
    fireLeanMax:1500, fireFatMin:5000,
    roiDefault:50000, roiMin:1000, roiMax:500000, roiStep:1000,
    roiAssets:[
      {name:'Savings Account',rate:3.0,color:'#64748b'},{name:'German Bunds (10yr)',rate:2.8,color:'#0ea5e9'},
      {name:'Euro Stoxx 50',rate:8.5,color:'#6366f1'},{name:'Gold (hist.)',rate:8.5,color:'#f59e0b'},
      {name:'MSCI World ETF',rate:9.5,color:'#C9A84C'},{name:'European REIT',rate:6.5,color:'#4ade80'},
      {name:'Pan-EU Bond Fund',rate:3.5,color:'#ec4899'},
    ],
    roiBase:10000,
    roiCompareSub:'Historical averages · Base: €10,000',
    insIncDefault:60000, insIncMin:15000, insIncMax:300000, insIncStep:5000,
    insRetDefault:67,
    insLiabDefault:150000, insLiabMin:0, insLiabMax:800000, insLiabStep:10000,
    insExistMin:0, insExistMax:1000000, insExistStep:25000,
    insPremiumRate:(age)=>age<35?0.0010:age<45?0.0018:0.0035,
    insDesc:'Calculate recommended life cover — supplementing European social security systems.',
    insLocalTitle:'European Insurance Overview',
    insLocalItems:[
      {name:'Germany — Risikolebensversicherung',detail:'Pure term life. Very competitive rates. Separate Berufsunfähigkeitsversicherung (BU) for disability — critical in Germany.'},
      {name:'France — Assurance Vie',detail:'Tax-advantaged investment wrapper after 8 years. €152,500 inheritance exemption per beneficiary. Very popular.'},
      {name:'UK — ISA + Term Life',detail:'Stocks & Shares ISA (£20K/yr tax-free). Separate term life outside your estate for clean IHT planning.'},
      {name:'Netherlands — Lijfrente',detail:'Annuity product with tax deductibility. Jaarruimte calculation determines max annual deduction.'},
      {name:'Spain — Plan de Pensiones',detail:'Pension plan with deductible contributions up to €1,500/yr (individual). Employer contributions up to €8,500.'},
    ],
    taxDesc:'Overview of major European tax systems — income tax, VAT, and investment taxation.',
  },
  world: {
    flag:'🌍', name:'Global',
    currency:'$', code:'USD',
    bannerClass:'world',
    bannerText:'🌍 &nbsp;Global — Multi-Currency · World Markets',
    sipLabel:'Monthly Investment',
    sipDefault:1000, sipMin:100, sipMax:10000, sipStep:100,
    sipRateHint:'MSCI World hist. avg ~10%',
    sipTaxLabel:'Tax-Deferred Estimate',
    sipTaxNote:'Varies by jurisdiction',
    sipTaxCalc:(p,r,t)=>p*12*0.20*0.15,
    sipDesc:'Build a globally diversified portfolio across world-class markets and asset classes.',
    sipEdu1:'Consistent global investing over 30+ years in low-cost MSCI World ETFs has historically outperformed most active strategies.',
    sipEdu3:'Global Diversification',
    sipEdu3Desc:'Spreading investments across geographies reduces single-country risk. Currency diversification adds another layer of protection.',
    emiLabel:'Loan Amount',
    emiDefault:300000, emiMin:10000, emiMax:2000000, emiStep:10000,
    emiRateDefault:6.0, emiRateHint:'Global avg mortgage ~5–7% (2026)',
    emiTaxLabel:'Interest Deduction (est.)',
    emiTaxNote:'Varies by jurisdiction',
    emiTaxCalc:(totalInt,t)=>(totalInt/t)*0.20,
    emiDtiLabel:'DTI ratio below 43% recommended',
    emiMonthlyLabel:'Monthly Payment',
    emiDesc:'Calculate loan repayments for any currency and region.',
    fireExpDefault:3000, fireExpMin:500, fireExpMax:20000, fireExpStep:250,
    fireSavedDefault:100000, fireSavedMin:0, fireSavedMax:2000000, fireSavedStep:10000,
    fireInvDefault:1500, fireInvMin:100, fireInvMax:15000, fireInvStep:100,
    fireLeanMax:2000, fireFatMin:7000,
    roiDefault:50000, roiMin:1000, roiMax:500000, roiStep:1000,
    roiAssets:[
      {name:'Cash/T-Bills',rate:4.0,color:'#64748b'},{name:'Global Bonds',rate:4.5,color:'#0ea5e9'},
      {name:'MSCI World',rate:10.0,color:'#6366f1'},{name:'Gold',rate:8.5,color:'#f59e0b'},
      {name:'MSCI EM',rate:9.0,color:'#C9A84C'},{name:'Global REITs',rate:7.5,color:'#4ade80'},
      {name:'Commodities',rate:5.5,color:'#ec4899'},
    ],
    roiBase:10000,
    roiCompareSub:'Historical averages · Base: $10,000',
    insIncDefault:70000, insIncMin:15000, insIncMax:500000, insIncStep:5000,
    insRetDefault:65,
    insLiabDefault:150000, insLiabMin:0, insLiabMax:1000000, insLiabStep:10000,
    insExistMin:0, insExistMax:2000000, insExistStep:25000,
    insPremiumRate:(age)=>age<35?0.0012:age<45?0.002:0.004,
    insDesc:'Calculate your recommended life insurance cover based on global best practices.',
    insLocalTitle:'Global Insurance Principles',
    insLocalItems:[
      {name:'Human Life Value (HLV)',detail:'Cover = Annual income × years to retirement + liabilities. Widely used in India, UK, and SE Asia.'},
      {name:'DIME Method',detail:'Debt + Income (10yr) + Mortgage + Education costs. Popular in USA and Canada for comprehensive coverage.'},
      {name:'10× Income Rule',detail:'Simple rule of thumb: cover = 10× annual gross income. Good starting point for most markets.'},
      {name:'Income Replacement Ratio',detail:'Most planners target 70–80% income replacement in retirement. Ensure your corpus supports this after inflation.'},
      {name:'Critical Illness + Disability',detail:'Often overlooked — disability is 3× more likely than death during working years. Add a rider or standalone policy.'},
    ],
    taxDesc:'Tax systems around the world — compare rates and structures across major economies.',
  }
};

// ================================================================
// STATE
// ================================================================
let currentMode = 'india';
const R = ()=>REGIONS[currentMode];
const sym = ()=>R().currency;
const fmtK = (n,s)=>{
  s = s||sym();
  const a=Math.abs(n);
  if(currentMode==='india'){
    if(a>=10000000) return s+(n/10000000).toFixed(2)+' Cr';
    if(a>=100000)   return s+(n/100000).toFixed(2)+' L';
    return s+Math.round(n).toLocaleString('en-IN');
  }
  if(a>=1000000) return s+(n/1000000).toFixed(2)+'M';
  if(a>=1000)    return s+(n/1000).toFixed(1)+'K';
  return s+Math.round(n).toLocaleString();
};
const fmtSym = n=>fmtK(n);

let sipChart,emiChart,roiChart;
function destroyChart(c){if(c){try{c.destroy();}catch(e){}}}

// ================================================================
// DRAWER
// ================================================================
function toggleDrawer(){
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('drawer-overlay').classList.toggle('open');
}
function closeDrawer(){
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('drawer-overlay').classList.remove('open');
}

// ================================================================
// NAVIGATION
// ================================================================
const ALL_TABS=['sip','emi','fire','roi','insurance','tax','ppf','epf','nps','stepsip','ssa','crorepati','habit','edu','glossary','compare','contact'];
function navTo(id){
  closeDrawer();
  ALL_TABS.forEach(t=>{
    document.getElementById(t).classList.toggle('active',t===id);
    const b=document.getElementById('btn-'+t);if(b)b.classList.toggle('active',t===id);
    const nb=document.getElementById('bnav-'+t);if(nb)nb.classList.toggle('active',t===id);
  });
  if(id==='sip') calcSIP();
  else if(id==='emi') calcEMI();
  else if(id==='fire') calcFIRE();
  else if(id==='roi') calcROI();
  else if(id==='insurance') calcInsurance();
  else if(id==='tax') renderTax();
  else if(id==='ppf') calcPPF();
  else if(id==='epf') calcEPF();
  else if(id==='nps') calcNPS();
  else if(id==='stepsip') calcStepSIP();
  else if(id==='ssa') calcSSA();
  else if(id==='crorepati') calcCrorepati();
  else if(id==='habit') calcHabit();
  else if(id==='contact') renderContact();
  else if(id==='edu') buildEdu();
  else if(id==='glossary') buildGlossary();
  else if(id==='compare') buildCompare();
  var s=document.getElementById('main-scroll');if(s)s.scrollTop=0;
}

// ================================================================
// SET MODE
// ================================================================
function setMode(mode){
  currentMode=mode;
  // Update all mode buttons
  ['india','usa','europe','world'].forEach(m=>{
    ['desk-btn-','mob-btn-'].forEach(pfx=>{
      const el=document.getElementById(pfx+m);
      if(!el)return;
      el.className=(pfx==='desk-btn-'?'mode-btn':'mob-mode-btn')+(m===mode?' active-'+m:'');
    });
  });
  const b=document.getElementById('mode-banner');
  b.className='mode-banner '+R().bannerClass;
  b.innerHTML=R().bannerText;
  loadTickerData(mode);
  startSidebarRefresh();
  updateSliderRanges();
  updateStaticLabels();

  // India-only: show/hide nav section and bottom nav buttons
  var indiaOnly=['ppf','epf','nps','stepsip','ssa'];
  var isIndia=(mode==='india');
  var indiaNav=document.getElementById('india-only-nav');
  if(indiaNav) indiaNav.style.display=isIndia?'':'none';
  indiaOnly.forEach(function(tab){
    var btn=document.getElementById('bnav-'+tab);
    if(btn) btn.style.display=isIndia?'':'none';
  });

  // Update Crorepati/Millionaire label
  var WEALTH_LABELS={india:'🏆 Crorepati',usa:'💰 Millionaire',europe:'🏰 Millionaire',world:'🌍 Millionaire'};
  var WEALTH_TARGETS={
    india:{targets:[10000000,50000000,100000000,250000000],labels:['₹1Cr','₹5Cr','₹10Cr','₹25Cr'],def:10000000,max:500000000,step:10000000},
    usa:  {targets:[1000000,5000000,10000000,25000000],  labels:['$1M','$5M','$10M','$25M'],    def:1000000, max:50000000, step:1000000},
    europe:{targets:[1000000,5000000,10000000,25000000], labels:['€1M','€5M','€10M','€25M'],    def:1000000, max:50000000, step:1000000},
    world:{targets:[1000000,5000000,10000000,25000000],  labels:['$1M','$5M','$10M','$25M'],    def:1000000, max:50000000, step:1000000}
  };
  var wl=WEALTH_LABELS[mode]||WEALTH_LABELS.india;
  var wt=WEALTH_TARGETS[mode]||WEALTH_TARGETS.india;
  var crNavEl=document.getElementById('nav-crorepati-label');
  if(crNavEl) crNavEl.textContent=wl+' Calc';
  var crBnavEl=document.getElementById('bnav-cr-label');
  if(crBnavEl) crBnavEl.textContent=wl.split(' ')[1]||wl;
  var crTitleEl=document.getElementById('cr_title');
  if(crTitleEl) crTitleEl.textContent=wl+' Calculator';
  var crDescEl=document.getElementById('cr_desc');
  if(crDescEl) crDescEl.textContent='How much to invest monthly to become a '+wl.replace(/[^a-zA-Z ]/g,'').trim()+'?';
  // Update slider range
  var crSlider=document.getElementById('cr_target');
  if(crSlider){crSlider.min=wt.def/10;crSlider.max=wt.max;crSlider.step=wt.step;crSlider.value=wt.def;}
  // Update quick-target buttons
  var qtWrap=document.getElementById('cr_quick_targets');
  if(qtWrap) qtWrap.innerHTML=wt.labels.map(function(lbl,i){
    return '<button class="btn-outline" onclick="setCrorepatiTarget('+wt.targets[i]+')" style="font-size:11px;padding:6px 14px;">'+lbl+'</button>';
  }).join('');

  // Update region-specific disclaimer
  var DISCLAIMERS={
    india:'⚠️ Educational only. Not SEBI-registered. Consult a SEBI-registered investment adviser.',
    usa:'⚠️ Educational only. Not SEC/FINRA registered. Consult a licensed CFP/RIA.',
    europe:'⚠️ Educational only. Not ESMA regulated. Consult a MiFID II-authorised adviser.',
    world:'⚠️ Educational only. Not regulated by any authority. Consult a licensed professional in your country.'
  };
  var disc=DISCLAIMERS[mode]||DISCLAIMERS.india;
  var discEl=document.getElementById('contact_disclaimer');
  if(discEl) discEl.textContent=disc;
  var sideDisc=document.getElementById('sidebar-disclaimer');
  if(sideDisc) sideDisc.textContent=disc;

  // Recalc active tab — redirect if on India-only tab and switching away
  // Show/hide news strip based on region
  fetchNews(false);

  var at=document.querySelector('.tab.active');
  if(at && !isIndia && indiaOnly.indexOf(at.id)>-1){
    navTo('sip');
  } else if(at){
    navTo(at.id);
  }
}

function updateSliderRanges(){
  const r=R();
  // SIP
  setSlider('sip_p',r.sipMin,r.sipMax,r.sipStep,r.sipDefault);
  // EMI
  setSlider('emi_p',r.emiMin,r.emiMax,r.emiStep,r.emiDefault);
  document.getElementById('emi_r').value=r.emiRateDefault;
  // FIRE
  setSlider('fire_exp',r.fireExpMin,r.fireExpMax,r.fireExpStep,r.fireExpDefault);
  setSlider('fire_saved',r.fireSavedMin,r.fireSavedMax,r.fireSavedStep,r.fireSavedDefault);
  setSlider('fire_inv',r.fireInvMin,r.fireInvMax,r.fireInvStep,r.fireInvDefault);
  // ROI
  setSlider('roi_p',r.roiMin,r.roiMax,r.roiStep,r.roiDefault);
  // Insurance
  setSlider('ins_inc',r.insIncMin,r.insIncMax,r.insIncStep,r.insIncDefault);
  document.getElementById('ins_ret').value=r.insRetDefault;
  setSlider('ins_liab',r.insLiabMin,r.insLiabMax,r.insLiabStep,r.insLiabDefault);
  setSlider('ins_exist',r.insExistMin,r.insExistMax,r.insExistStep,0);
}
function setSlider(id,min,max,step,val){
  const el=document.getElementById(id);
  el.min=min;el.max=max;el.step=step;el.value=Math.min(Math.max(val,min),max);
}

function updateStaticLabels(){
  const r=R();
  document.getElementById('sip-eyebrow').textContent='Investment · '+r.name;
  document.getElementById('sip-desc').textContent=r.sipDesc;
  document.getElementById('sip-p-label').textContent=r.sipLabel;
  document.getElementById('sip-rate-hint').textContent=r.sipRateHint;
  document.getElementById('sip-tax-label').textContent=r.sipTaxLabel;
  document.getElementById('sip-tax-note').textContent=r.sipTaxNote;
  document.getElementById('edu-sip-1').textContent=r.sipEdu1;
  document.getElementById('edu-sip-3-title').textContent=r.sipEdu3;
  document.getElementById('edu-sip-3').textContent=r.sipEdu3Desc;

  document.getElementById('emi-eyebrow').textContent='Loan · '+r.name;
  document.getElementById('emi-desc').textContent=r.emiDesc;
  document.getElementById('emi-p-label').textContent=r.emiLabel;
  document.getElementById('emi-rate-hint').textContent=r.emiRateHint;
  document.getElementById('emi-tax-label').textContent=r.emiTaxLabel;
  document.getElementById('emi-tax-note').textContent=r.emiTaxNote;
  document.getElementById('emi-dti-label').textContent=r.emiDtiLabel;
  document.getElementById('emi-monthly-label').textContent=r.emiMonthlyLabel;

  document.getElementById('fire-eyebrow').textContent='FIRE · '+r.name;
  document.getElementById('fire-exp-label').textContent='Monthly Expenses ('+r.currency+')';

  document.getElementById('roi-eyebrow').textContent='Returns · '+r.name;
  document.getElementById('roi-p-label').textContent='Initial Investment ('+r.currency+')';
  document.getElementById('roi-compare-title').textContent='Asset Class Comparison — 20 Years';
  document.getElementById('roi-compare-sub').textContent=r.roiCompareSub;

  document.getElementById('ins-eyebrow').textContent='Insurance · '+r.name;
  document.getElementById('ins-desc').textContent=r.insDesc;
  document.getElementById('ins-inc-label').textContent='Annual Income ('+r.currency+')';
  document.getElementById('ins-liab-label').textContent='Liabilities ('+r.currency+')';
  document.getElementById('ins-local-title').textContent=r.insLocalTitle;
  document.getElementById('ins-local-content').innerHTML=r.insLocalItems.map(item=>
    `<div style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05);">
      <div style="font-size:12px;font-weight:700;color:var(--cream);margin-bottom:4px;">${item.name}</div>
      <div style="font-size:11px;color:var(--muted);line-height:1.7;">${item.detail}</div>
    </div>`
  ).join('');

  document.getElementById('tax-eyebrow').textContent='Tax · '+r.name;
  document.getElementById('tax-desc').textContent=r.taxDesc;
}

// ================================================================
// SIP CALCULATOR
// ================================================================
function calcSIP(){
  const p=+document.getElementById('sip_p').value;
  const r=+document.getElementById('sip_r').value;
  const t=+document.getElementById('sip_t').value;
  document.getElementById('v_sip_p').textContent=fmtSym(p);
  document.getElementById('v_sip_r').textContent=r.toFixed(1);
  document.getElementById('v_sip_t').textContent=t;
  const months=t*12,mr=r/12/100;
  const invested=p*months;
  const total=p*(((Math.pow(1+mr,months)-1)/mr)*(1+mr));
  const earnings=total-invested,mult=total/invested,gainPct=(earnings/invested)*100;
  const tax=R().sipTaxCalc(p,r,t);
  document.getElementById('sip_total').textContent=fmtSym(total);
  document.getElementById('sip_invested').textContent=fmtSym(invested);
  document.getElementById('sip_gains').textContent=fmtSym(earnings);
  document.getElementById('sip_xbadge').textContent=mult.toFixed(1)+'x';
  document.getElementById('sip_gain_pct').textContent=gainPct.toFixed(0)+'% gains';
  document.getElementById('sip_inv_note').textContent=months+' months';
  document.getElementById('sip_tax').textContent=fmtSym(tax)+'/yr';
  document.getElementById('sip_return_pct_center').textContent=((earnings/total)*100).toFixed(0)+'%';
  destroyChart(sipChart);
  sipChart=new Chart(document.getElementById('sipChart').getContext('2d'),{
    type:'doughnut',data:{labels:['Invested','Earnings'],datasets:[{data:[Math.round(invested),Math.round(earnings)],backgroundColor:['#334155','#C9A84C'],borderWidth:0,hoverOffset:4}]},
    options:{cutout:'72%',plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>' '+fmtSym(c.raw)}}}}
  });
  const mr2=mr;
  let rows='';
  for(let y=1;y<=t;y++){
    const m=y*12,iy=p*m;
    const vy=p*(((Math.pow(1+mr2,m)-1)/mr2)*(1+mr2));
    const gy=vy-iy,gp=gy/iy*100,prog=(vy/total)*100;
    rows+=`<tr><td><span class="badge-gold">${y}</span></td><td class="mono">${fmtSym(iy)}</td><td class="mono" style="color:var(--gold-light);">${fmtSym(vy)}</td><td class="mono" style="color:#4ade80;">${fmtSym(gy)}</td><td><span class="badge-${gp>0?'green':'red'}">${gp.toFixed(1)}%</span></td><td style="min-width:80px;"><div class="progress-bar"><div class="progress-fill" style="width:${prog}%;"></div></div></td></tr>`;
  }
  document.getElementById('sip_tbody').innerHTML=rows;
  // Milestones — region-aware
  const targets=currentMode==='india'
    ?[200000,500000,1000000,5000000,10000000,50000000]
    :[5000,10000,50000,100000,500000,1000000];
  const lbls=currentMode==='india'
    ?['₹2L','₹5L','₹10L','₹50L','₹1Cr','₹5Cr']
    :['5K','10K','50K','100K','500K','1M'].map(l=>sym()+l);
  let mhtml='';
  targets.forEach((tgt,i)=>{
    if(tgt>total) return;
    let yr=0;
    for(let m=1;m<=t*12;m++){const v=p*(((Math.pow(1+mr2,m)-1)/mr2)*(1+mr2));if(v>=tgt){yr=Math.ceil(m/12);break;}}
    if(yr>0) mhtml+=`<div class="milestone"><div class="milestone-dot"></div><div><div style="font-weight:600;color:var(--cream);font-size:11px;">${lbls[i]}</div><div style="color:var(--muted);font-size:10px;">Year ${yr}</div></div></div>`;
  });
  document.getElementById('sip_milestones').innerHTML=mhtml||'<div style="color:var(--muted);font-size:10px;">Increase tenure to see milestones.</div>';
}

// ================================================================
// EMI CALCULATOR
// ================================================================
function calcEMI(){
  const p=+document.getElementById('emi_p').value;
  const r=+document.getElementById('emi_r').value;
  const t=+document.getElementById('emi_t').value;
  document.getElementById('v_emi_p').textContent=fmtSym(p);
  document.getElementById('v_emi_r').textContent=r.toFixed(2);
  document.getElementById('v_emi_t').textContent=t;
  const mr=r/12/100,months=t*12;
  const emi=(p*mr*Math.pow(1+mr,months))/(Math.pow(1+mr,months)-1);
  const totalPaid=emi*months,totalInt=totalPaid-p;
  const taxSaved=R().emiTaxCalc(totalInt,t);
  document.getElementById('emi_monthly').textContent=fmtSym(emi);
  document.getElementById('emi_interest').textContent=fmtSym(totalInt);
  document.getElementById('emi_total').textContent=fmtSym(totalPaid);
  document.getElementById('emi_tax_saved').textContent=fmtSym(taxSaved)+'/yr';
  document.getElementById('emi_income_req').textContent=fmtSym(emi/0.4)+'/mo';
  const pp=(p/totalPaid)*100,ip=(totalInt/totalPaid)*100;
  document.getElementById('emi_bar_p').style.width=pp+'%';
  document.getElementById('emi_bar_i').style.width=ip+'%';
  document.getElementById('emi_pct_p').textContent=pp.toFixed(1)+'%';
  document.getElementById('emi_pct_i').textContent=ip.toFixed(1)+'%';
  document.getElementById('emi_interest_pct_center').textContent=ip.toFixed(0)+'%';
  destroyChart(emiChart);
  emiChart=new Chart(document.getElementById('emiChart').getContext('2d'),{
    type:'doughnut',data:{labels:['Principal','Interest'],datasets:[{data:[Math.round(p),Math.round(totalInt)],backgroundColor:['#4f46e5','#ef4444'],borderWidth:0}]},
    options:{cutout:'72%',plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>' '+fmtSym(c.raw)}}}}
  });
  let rows='',balance=p;
  for(let y=1;y<=t;y++){
    const ob=balance;let yP=0,yI=0;
    for(let m=0;m<12&&balance>0;m++){const i=balance*mr,pr=Math.min(emi-i,balance);yP+=pr;yI+=i;balance-=pr;}
    const cb=Math.max(balance,0);
    rows+=`<tr><td><span class="badge-gold">${y}</span></td><td class="mono">${fmtSym(ob)}</td><td class="mono" style="color:#818cf8;">${fmtSym(yP)}</td><td class="mono" style="color:#f87171;">${fmtSym(yI)}</td><td class="mono" style="color:var(--muted);">${fmtSym(cb)}</td></tr>`;
  }
  document.getElementById('emi_tbody').innerHTML=rows;
}

// ================================================================
// FIRE CALCULATOR
// ================================================================
function calcFIRE(){
  const age=+document.getElementById('fire_age').value;
  const exp=+document.getElementById('fire_exp').value;
  const saved=+document.getElementById('fire_saved').value;
  const inv=+document.getElementById('fire_inv').value;
  const ret=+document.getElementById('fire_ret').value/100;
  const inf=+document.getElementById('fire_inf').value/100;
  document.getElementById('v_fire_age').textContent=age;
  document.getElementById('v_fire_exp').textContent=fmtSym(exp);
  document.getElementById('v_fire_saved').textContent=fmtSym(saved);
  document.getElementById('v_fire_inv').textContent=fmtSym(inv);
  document.getElementById('v_fire_ret').textContent=(ret*100).toFixed(1);
  document.getElementById('v_fire_inf').textContent=(inf*100).toFixed(1);
  const fireCorpus=exp*12*25,swr=fireCorpus*0.04/12;
  document.getElementById('fire_corpus').textContent=fmtSym(fireCorpus);
  document.getElementById('fire_swr').textContent=fmtSym(swr);
  const mr=ret/12;let corpus=saved,years=0;
  for(let m=0;m<600;m++){corpus=corpus*(1+mr)+inv;if(corpus>=fireCorpus){years=Math.ceil(m/12);break;}}
  document.getElementById('fire_years').textContent=years>0?years+' yrs':'Already FIRE! 🎉';
  document.getElementById('fire_year_label').textContent=years>0?'Retire at age '+(age+years):'Congrats!';
  const prog=Math.min((saved/fireCorpus)*100,100);
  document.getElementById('fire_progress_pct').textContent=prog.toFixed(1)+'%';
  document.getElementById('fire_progress_bar').style.width=prog+'%';
  const tL=R().fireLeanMax,tH=R().fireFatMin;
  const [ft,fd]=exp<tL?['🌿 Lean FIRE','Minimal lifestyle, maximum speed to independence.']:exp>tH?['🏆 Fat FIRE','Luxury retirement — needs a large corpus.']:['⚖️ Regular FIRE','Balanced approach — part-time optional.'];
  document.getElementById('fire_type').textContent=ft;
  document.getElementById('fire_type_desc').textContent=fd;
  let mhtml='';
  [25,50,75,100].forEach(pc=>{
    const tgt=fireCorpus*pc/100;
    let yr=0,c=saved;
    for(let m=0;m<600;m++){c=c*(1+mr)+inv;if(c>=tgt){yr=Math.ceil(m/12);break;}}
    const reached=saved>=tgt;
    mhtml+=`<div class="milestone"><div class="milestone-dot" style="background:${reached?'#4ade80':'var(--gold)'};box-shadow:0 0 7px ${reached?'rgba(34,197,94,.5)':'rgba(201,168,76,.4)'};"></div><div><div style="font-weight:600;color:var(--cream);font-size:11px;">${pc}% — ${fmtSym(tgt)}</div><div style="color:var(--muted);font-size:10px;">${yr>0?'Year '+yr+' (Age '+(age+yr)+')':(reached?'✅ Done':'—')}</div></div></div>`;
  });
  document.getElementById('fire_milestones').innerHTML=mhtml;
}

// ================================================================
// ROI CALCULATOR
// ================================================================
function calcROI(){
  const p=+document.getElementById('roi_p').value;
  const r=+document.getElementById('roi_r').value;
  const t=+document.getElementById('roi_t').value;
  document.getElementById('v_roi_p').textContent=fmtSym(p);
  document.getElementById('v_roi_r').textContent=r.toFixed(1);
  document.getElementById('v_roi_t').textContent=t;
  const final=p*Math.pow(1+r/100,t),returns=final-p;
  document.getElementById('roi_final').textContent=fmtSym(final);
  document.getElementById('roi_returns').textContent=fmtSym(returns);
  document.getElementById('roi_mult').textContent=(final/p).toFixed(1)+'x';
  destroyChart(roiChart);
  const labels=[],vals=[];
  for(let y=0;y<=t;y++){labels.push('Y'+y);vals.push(p*Math.pow(1+r/100,y));}
  roiChart=new Chart(document.getElementById('roiChart').getContext('2d'),{
    type:'line',data:{labels,datasets:[{data:vals,borderColor:'#C9A84C',backgroundColor:'rgba(201,168,76,.08)',fill:true,tension:.4,borderWidth:2,pointRadius:0,pointHoverRadius:4}]},
    options:{plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>' '+fmtSym(c.raw)}}},scales:{x:{grid:{color:'rgba(255,255,255,.05)'},ticks:{color:'#9090A8',font:{size:9}}},y:{grid:{color:'rgba(255,255,255,.05)'},ticks:{color:'#9090A8',font:{size:9},callback:v=>fmtSym(v)}}}}
  });
  const assets=R().roiAssets;
  const base=R().roiBase,yrs=20;
  const maxV=Math.max(...assets.map(a=>base*Math.pow(1+a.rate/100,yrs)));
  document.getElementById('asset_compare').innerHTML=assets.map(a=>{
    const v=base*Math.pow(1+a.rate/100,yrs),w=(v/maxV)*100;
    return`<div class="compare-row"><span class="compare-label">${a.name}</span><div class="compare-bar"><div class="compare-fill" style="width:${w}%;background:${a.color};"></div></div><span class="compare-val">${fmtSym(v)}</span><span style="width:36px;text-align:right;font-size:10px;color:${a.color};">${a.rate}%</span></div>`;
  }).join('');
}

// ================================================================
// INSURANCE CALCULATOR
// ================================================================
function calcInsurance(){
  const inc=+document.getElementById('ins_inc').value;
  const age=+document.getElementById('ins_age').value;
  const ret=+document.getElementById('ins_ret').value;
  const liab=+document.getElementById('ins_liab').value;
  const exist=+document.getElementById('ins_exist').value;
  document.getElementById('v_ins_inc').textContent=fmtSym(inc);
  document.getElementById('v_ins_age').textContent=age;
  document.getElementById('v_ins_ret').textContent=ret;
  document.getElementById('v_ins_liab').textContent=fmtSym(liab);
  document.getElementById('v_ins_exist').textContent=fmtSym(exist);
  const hlv=(inc*(ret-age))+liab,gap=Math.max(hlv-exist,0);
  const pr=R().insPremiumRate(age);
  document.getElementById('ins_cover').textContent=fmtSym(hlv);
  document.getElementById('ins_gap').textContent=fmtSym(gap);
  document.getElementById('ins_premium').textContent=fmtSym(gap*pr)+'/yr approx';
}

// ================================================================
// TAX — fully localized per region
// ================================================================
function renderTax(){
  const c=document.getElementById('tax-content');
  if(currentMode==='india') c.innerHTML=buildIndiaTax();
  else if(currentMode==='usa') c.innerHTML=buildUSATax();
  else if(currentMode==='europe') c.innerHTML=buildEuropeTax();
  else c.innerHTML=buildWorldTax();
  if(currentMode==='india') wireIndiaTax();
}

function buildIndiaTax(){
  return`
  <div class="grid-2-1" style="margin-bottom:20px;">
    <div class="card">
      <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:18px;">INCOME & DEDUCTIONS (FY2025-26)</div>
      <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">Gross Annual Income (CTC)</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_tax_inc">₹18L</span></div><input type="range" id="tax_inc" min="500000" max="10000000" step="50000" value="1800000"></div>
      <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">80C (ELSS, PPF, LIC…)</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_tax_80c">₹1.5L</span></div><input type="range" id="tax_80c" min="0" max="150000" step="5000" value="150000"></div>
      <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">80D Health Insurance</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_tax_80d">₹25K</span></div><input type="range" id="tax_80d" min="0" max="75000" step="5000" value="25000"></div>
      <div style="margin-bottom:16px;"><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">24(b) Home Loan Interest</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_tax_hl">₹0</span></div><input type="range" id="tax_hl" min="0" max="200000" step="5000" value="0"></div>
      <div><div style="display:flex;justify-content:space-between;margin-bottom:5px;"><label style="font-size:12px;color:var(--muted);">80CCD(1B) NPS Extra</label><span class="mono" style="font-size:14px;font-weight:600;color:var(--gold-light);" id="v_tax_nps">₹50K</span></div><input type="range" id="tax_nps" min="0" max="50000" step="5000" value="50000"></div>
    </div>
    <div class="card">
      <div class="section-eyebrow" style="margin-bottom:14px;">Regime Comparison</div>
      <div style="margin-bottom:16px;"><div style="font-size:11px;color:var(--muted);margin-bottom:5px;">Old Regime Tax</div><div style="font-size:1.8rem;font-weight:800;font-family:'Playfair Display',serif;color:var(--gold-light);" id="tax_old">₹0</div><div style="font-size:10px;color:var(--muted);margin-top:2px;" id="tax_old_eff">Eff: 0%</div></div>
      <div class="gold-line" style="margin:12px 0;"></div>
      <div style="margin-bottom:16px;"><div style="font-size:11px;color:var(--muted);margin-bottom:5px;">New Regime Tax</div><div style="font-size:1.8rem;font-weight:800;font-family:'Playfair Display',serif;" id="tax_new">₹0</div><div style="font-size:10px;color:var(--muted);margin-top:2px;" id="tax_new_eff">Eff: 0%</div></div>
      <div class="gold-line" style="margin:12px 0;"></div>
      <div style="background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);border-radius:10px;padding:12px;">
        <div style="font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">Best Regime</div>
        <div style="font-size:1rem;font-weight:800;color:#4ade80;" id="tax_rec">—</div>
        <div style="font-size:10px;color:var(--muted);margin-top:2px;" id="tax_saving">You save ₹0</div>
      </div>
    </div>
  </div>`;
}
function wireIndiaTax(){
  ['tax_inc','tax_80c','tax_80d','tax_hl','tax_nps'].forEach(id=>{
    const el=document.getElementById(id);
    if(el){el.removeEventListener('input',calcIndiaTax);el.addEventListener('input',calcIndiaTax);}
  });
  calcIndiaTax();
}
function calcIndiaTax(){
  const inc=+document.getElementById('tax_inc').value;
  const c80=+document.getElementById('tax_80c').value;
  const c80d=+document.getElementById('tax_80d').value;
  const hl=+document.getElementById('tax_hl').value;
  const nps=+document.getElementById('tax_nps').value;
  document.getElementById('v_tax_inc').textContent=fmtK(inc,'₹');
  document.getElementById('v_tax_80c').textContent=fmtK(c80,'₹');
  document.getElementById('v_tax_80d').textContent=fmtK(c80d,'₹');
  document.getElementById('v_tax_hl').textContent=fmtK(hl,'₹');
  document.getElementById('v_tax_nps').textContent=fmtK(nps,'₹');
  const oldTaxable=Math.max(inc-50000-Math.min(c80,150000)-Math.min(c80d,75000)-Math.min(hl,200000)-Math.min(nps,50000),0);
  const oldTax=calcOldTax(oldTaxable);
  const newTax=calcNewTax(Math.max(inc-75000,0));
  document.getElementById('tax_old').textContent=fmtK(oldTax,'₹');
  document.getElementById('tax_old_eff').textContent='Eff: '+(oldTax/inc*100).toFixed(1)+'%';
  document.getElementById('tax_new').textContent=fmtK(newTax,'₹');
  document.getElementById('tax_new_eff').textContent='Eff: '+(newTax/inc*100).toFixed(1)+'%';
  const better=oldTax<=newTax?'Old Regime':'New Regime';
  document.getElementById('tax_rec').textContent='✅ '+better+' saves more';
  document.getElementById('tax_saving').textContent='Annual saving: '+fmtK(Math.abs(oldTax-newTax),'₹');
}
function calcOldTax(i){let t=0;if(i>1000000)t=112500+(i-1000000)*0.30;else if(i>500000)t=12500+(i-500000)*0.20;else if(i>250000)t=(i-250000)*0.05;if(i<=500000)t=0;return t*1.04;}
function calcNewTax(i){let t=0,p=0;for(const[l,r]of[[300000,0],[600000,.05],[900000,.10],[1200000,.15],[1500000,.20],[Infinity,.30]]){if(i>p){t+=Math.min(i-p,l-p)*r;p=l;}}if(i<=700000)t=0;return t*1.04;}

function buildUSATax(){
  return`
  <div class="grid-2" style="margin-bottom:20px;">
    <div class="card">
      <div style="font-size:22px;margin-bottom:10px;">📊</div>
      <h4 style="font-weight:700;margin-bottom:10px;font-size:14px;">Federal Tax Brackets 2026</h4>
      <table><thead><tr><th>Rate</th><th>Single</th><th>Married Filing Jointly</th></tr></thead>
      <tbody>
        <tr><td><span class="badge-gold">10%</span></td><td>$0 – $11,925</td><td>$0 – $23,850</td></tr>
        <tr><td><span class="badge-gold">12%</span></td><td>$11,925 – $48,475</td><td>$23,850 – $96,950</td></tr>
        <tr><td><span class="badge-gold">22%</span></td><td>$48,475 – $103,350</td><td>$96,950 – $206,700</td></tr>
        <tr><td><span class="badge-gold">24%</span></td><td>$103,350 – $197,300</td><td>$206,700 – $394,600</td></tr>
        <tr><td><span class="badge-gold">32%</span></td><td>$197,300 – $250,525</td><td>$394,600 – $501,050</td></tr>
        <tr><td><span class="badge-gold">35%</span></td><td>$250,525 – $626,350</td><td>$501,050 – $751,600</td></tr>
        <tr><td><span class="badge-red">37%</span></td><td>$626,350+</td><td>$751,600+</td></tr>
      </tbody></table>
    </div>
    <div class="card">
      <div style="font-size:22px;margin-bottom:10px;">🏦</div>
      <h4 style="font-weight:700;margin-bottom:10px;font-size:14px;">Key Deductions & Limits (2026)</h4>
      <div style="display:flex;flex-direction:column;gap:10px;">
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.05);"><span style="font-size:12px;color:var(--muted);">Standard Deduction (Single)</span><span class="mono" style="font-size:12px;color:var(--gold-light);">$15,000</span></div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.05);"><span style="font-size:12px;color:var(--muted);">Standard Deduction (MFJ)</span><span class="mono" style="font-size:12px;color:var(--gold-light);">$30,000</span></div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.05);"><span style="font-size:12px;color:var(--muted);">401(k) Contribution Limit</span><span class="mono" style="font-size:12px;color:var(--gold-light);">$23,500</span></div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.05);"><span style="font-size:12px;color:var(--muted);">IRA Contribution Limit</span><span class="mono" style="font-size:12px;color:var(--gold-light);">$7,000</span></div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.05);"><span style="font-size:12px;color:var(--muted);">HSA Limit (Self)</span><span class="mono" style="font-size:12px;color:var(--gold-light);">$4,300</span></div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.05);"><span style="font-size:12px;color:var(--muted);">LTCG Rate (income dependent)</span><span class="mono" style="font-size:12px;color:var(--gold-light);">0% / 15% / 20%</span></div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;"><span style="font-size:12px;color:var(--muted);">Estate Tax Exemption</span><span class="mono" style="font-size:12px;color:var(--gold-light);">$13.99M</span></div>
      </div>
    </div>
  </div>
  <div class="grid-2">
    <div class="card"><div style="font-size:22px;margin-bottom:10px;">💼</div><h4 style="font-weight:700;margin-bottom:7px;font-size:13px;">Retirement Accounts</h4><p style="font-size:11px;color:var(--muted);line-height:1.7;">401(k): pre-tax contributions reduce taxable income. Employer match = free money — always contribute enough to get the full match first. Roth IRA: after-tax but grows and withdraws tax-free. Mega Backdoor Roth available at some employers up to $69,000 total.</p></div>
    <div class="card"><div style="font-size:22px;margin-bottom:10px;">📈</div><h4 style="font-weight:700;margin-bottom:7px;font-size:13px;">SALT & Itemized Deductions</h4><p style="font-size:11px;color:var(--muted);line-height:1.7;">State And Local Tax (SALT) deduction capped at $10,000. Mortgage interest deductible on up to $750K of principal. Medical expenses >7.5% of AGI deductible. Consider whether itemizing beats the standard deduction for your situation.</p></div>
  </div>`;
}

function buildEuropeTax(){
  return`
  <div class="grid-2" style="margin-bottom:20px;">
    <div class="card"><div style="font-size:22px;margin-bottom:10px;">🇩🇪</div><h4 style="font-weight:700;margin-bottom:7px;font-size:13px;">Germany</h4><p style="font-size:11px;color:var(--muted);line-height:1.7;">Progressive 0%–45%. Basic allowance: €11,784. Solidarity surcharge 5.5% on high earners. Capital gains: 25% flat (Abgeltungsteuer) + solidarity. Church tax optional 8–9%. Sparerpauschbetrag: €1,000 capital gains allowance.</p></div>
    <div class="card"><div style="font-size:22px;margin-bottom:10px;">🇫🇷</div><h4 style="font-weight:700;margin-bottom:7px;font-size:13px;">France</h4><p style="font-size:11px;color:var(--muted);line-height:1.7;">11%–45% income tax + social charges (17.2% on investment income). PFU (Prélèvement Forfaitaire Unique): 30% flat tax on investments. Assurance Vie: tax advantages after 8 years. PEA: tax-free EU equity gains after 5 years (€150K limit).</p></div>
    <div class="card"><div style="font-size:22px;margin-bottom:10px;">🇬🇧</div><h4 style="font-weight:700;margin-bottom:7px;font-size:13px;">United Kingdom</h4><p style="font-size:11px;color:var(--muted);line-height:1.7;">Personal allowance £12,570 (2025/26). Basic 20% (£12,570–£50,270). Higher 40% (£50,270–£125,140). Additional 45% (£125,140+). CGT: 18%/24% (residential), 10%/20% (other assets). ISA: £20,000/yr tax-free. SIPP pension: 25% tax-free lump sum.</p></div>
    <div class="card"><div style="font-size:22px;margin-bottom:10px;">🇳🇱</div><h4 style="font-weight:700;margin-bottom:7px;font-size:13px;">Netherlands</h4><p style="font-size:11px;color:var(--muted);line-height:1.7;">Box 1 (income): up to 49.5%. Box 2 (substantial interest): 24.5%/33%. Box 3 (savings/investments): notional yield tax — currently under reform. Hypotheekrenteaftrek: mortgage interest deductible at max 36.97%. No wealth tax on pension assets.</p></div>
    <div class="card"><div style="font-size:22px;margin-bottom:10px;">🇪🇸</div><h4 style="font-weight:700;margin-bottom:7px;font-size:13px;">Spain</h4><p style="font-size:11px;color:var(--muted);line-height:1.7;">Income tax 19%–47% (varies by region). Savings income: 19%–28% flat. Plan de Pensiones: deductible up to €1,500 individual + €8,500 employer. Beckham Law: 24% flat rate for qualifying expats. Non-resident: 19% (EU) or 24% (non-EU).</p></div>
    <div class="card"><div style="font-size:22px;margin-bottom:10px;">🇮🇹</div><h4 style="font-weight:700;margin-bottom:7px;font-size:13px;">Italy</h4><p style="font-size:11px;color:var(--muted);line-height:1.7;">IRPEF: 23%–43% on income. Capital gains: 26% flat. PIR (Piano Individuale di Risparmio): tax-free gains after 5yr if 70% in Italian assets. Flat tax for new residents: €100K/yr on foreign income. Regional/municipal surtaxes apply.</p></div>
  </div>`;
}

function buildWorldTax(){
  return`
  <div class="grid-2" style="margin-bottom:20px;">
    <div class="card"><div style="font-size:22px;margin-bottom:10px;">🇸🇬</div><h4 style="font-weight:700;margin-bottom:7px;font-size:13px;">Singapore — Low-Tax Hub</h4><p style="font-size:11px;color:var(--muted);line-height:1.7;">Progressive 0%–24%. No capital gains tax. No dividend tax. CPF: 20% employee + 17% employer (up to age 55). SRS: Supplementary Retirement Scheme for tax deferral. Very favourable for global wealth accumulation.</p></div>
    <div class="card"><div style="font-size:22px;margin-bottom:10px;">🇦🇺</div><h4 style="font-weight:700;margin-bottom:7px;font-size:13px;">Australia</h4><p style="font-size:11px;color:var(--muted);line-height:1.7;">Progressive 19%–45% + 2% Medicare levy. Super: 11.5% employer contributions (rising to 12%). Concessional cap: A$30K/yr. Non-concessional: A$120K/yr. CGT discount: 50% for assets held >12 months. HECS-HELP repayments income-contingent.</p></div>
    <div class="card"><div style="font-size:22px;margin-bottom:10px;">🇨🇦</div><h4 style="font-weight:700;margin-bottom:7px;font-size:13px;">Canada</h4><p style="font-size:11px;color:var(--muted);line-height:1.7;">Federal 15%–33% + provincial tax (5%–25%). RRSP: deductible contributions, tax-deferred growth (18% of income, max C$31,560). TFSA: C$7,000/yr completely tax-free. Capital gains inclusion rate raised to 2/3 in 2024 for gains over C$250K.</p></div>
    <div class="card"><div style="font-size:22px;margin-bottom:10px;">🇦🇪</div><h4 style="font-weight:700;margin-bottom:7px;font-size:13px;">UAE — Zero Tax</h4><p style="font-size:11px;color:var(--muted);line-height:1.7;">No personal income tax. No capital gains tax. Corporate tax: 9% above AED 375K profit (from 2023). VAT: 5%. No withholding tax on dividends. Popular for global entrepreneurs — requires genuine residency and economic substance.</p></div>
    <div class="card"><div style="font-size:22px;margin-bottom:10px;">🇯🇵</div><h4 style="font-weight:700;margin-bottom:7px;font-size:13px;">Japan</h4><p style="font-size:11px;color:var(--muted);line-height:1.7;">Income tax 5%–45% + 10% inhabitant tax. NISA: ¥3.6M/yr tax-free growth (lifetime ¥18M). iDeCo: pension with deductible contributions. Exit tax on assets >¥100M when leaving Japan. Complex for foreigners.</p></div>
    <div class="card"><div style="font-size:22px;margin-bottom:10px;">🇧🇷</div><h4 style="font-weight:700;margin-bottom:7px;font-size:13px;">Brazil</h4><p style="font-size:11px;color:var(--muted);line-height:1.7;">IRPF: 7.5%–27.5% on income. Dividends currently exempt (reform pending). Capital gains: 15%–22.5%. PGBL/VGBL: pension products with deduction up to 12% of gross income. High social security contributions (INSS up to 14%).</p></div>
  </div>`;
}

// ================================================================
// EDUCATION & GLOSSARY
// ================================================================
const concepts=[
  {title:'What is Compound Interest and why it matters',body:'Compound interest is earned on both principal and previously earned interest. At 10% returns, $10,000 becomes $27,000 in 10 years, $67,000 in 20 years, and $174,000 in 30 years — purely through reinvesting returns. Starting 5 years earlier can double your final corpus.'},
  {title:'How to build an Emergency Fund',body:'An emergency fund is 3–6 months of expenses in liquid instruments. It protects you from derailing long-term investments during unexpected expenses — job loss, medical emergencies. Rule: Build emergency fund FIRST before any equity investment.'},
  {title:'Asset Allocation — Balancing Equity vs Debt',body:'Classic rule: Equity % = 110 minus your age. At 30 → 80% equity. At 50 → 60% equity. Equity gives higher returns with volatility; bonds/debt give stability. Rebalance annually. Match allocation to goal time horizon.'},
  {title:'What is XIRR and how to measure fund returns',body:'XIRR accounts for the timing of cash flows — essential for regular investment plans. A fund showing 15% absolute return over 3 years is only ~4.8% CAGR. Always compare trailing 3yr, 5yr, and 10yr returns across funds.'},
  {title:'Low-Cost Index Funds vs Active Management',body:'Decades of data show 90%+ of active funds underperform their benchmark index over 15+ years. A low-cost S&P 500 or MSCI World index fund with 0.05–0.20% expense ratio beats most actively managed funds charging 1–2% annually.'},
  {title:'Inflation — The Silent Wealth Destroyer',body:'At 5% inflation, purchasing power halves every 14 years. Your investments must beat inflation meaningfully. Equity has historically returned 8–14% vs 3–7% inflation globally — a positive real return of 5–8%.'},
];
const milestones=[
  {age:'22–25',title:'Foundation',items:['Emergency fund (3–6mo)','Term + Health insurance','First investment','Credit history']},
  {age:'25–30',title:'Accelerate',items:['Save 20–30% of income','Max tax-advantaged accounts','No consumer debt','Clear student loans']},
  {age:'30–40',title:'Asset Building',items:['Real estate (goal-aligned)','Increase contributions','Review insurance','Global diversification']},
  {age:'40–50',title:'Consolidation',items:['Shift to balanced portfolio','Children education corpus','50% of FIRE target','Estate planning']},
  {age:'50–60',title:'Pre-Retirement',items:['Reduce equity gradually','Clear all major loans','Max pension contributions','Withdrawal strategy']},
  {age:'60+',title:'Freedom Phase',items:['4% SWR activated','Low-risk instruments','Health top-up cover','Will & legacy']},
];
function buildEdu(){
  const ac=document.getElementById('accordion_container');ac.innerHTML='';
  concepts.forEach(c=>{
    const d=document.createElement('div');d.className='card';d.style.cssText='padding:0;overflow:hidden;';
    d.innerHTML=`<div onclick="toggleAcc(this)" style="padding:14px 18px;display:flex;justify-content:space-between;align-items:center;cursor:pointer;"><span style="font-size:12px;font-weight:600;">${c.title}</span><span class="aic" style="font-size:16px;color:var(--gold);transition:transform .3s;flex-shrink:0;margin-left:8px;">+</span></div><div class="accordion-content"><div style="padding:0 18px 16px;font-size:12px;color:var(--muted);line-height:1.7;border-top:1px solid rgba(255,255,255,.05);">${c.body}</div></div>`;
    ac.appendChild(d);
  });
  document.getElementById('timeline_content').innerHTML=milestones.map((m,i)=>`<div style="display:grid;grid-template-columns:80px 1fr;gap:14px;padding:12px 0;border-bottom:${i===milestones.length-1?'none':'1px solid rgba(255,255,255,.05)'};"><div><div style="font-size:10px;font-weight:700;color:var(--gold-light);">${m.age}</div><div style="font-size:11px;font-weight:600;margin-top:2px;">${m.title}</div></div><div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;">${m.items.map(it=>`<span style="background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);border-radius:100px;padding:2px 10px;font-size:10px;color:var(--muted);">${it}</span>`).join('')}</div></div>`).join('');
}
function toggleAcc(h){
  const c=h.nextElementSibling,i=h.querySelector('.aic'),open=c.classList.contains('open');
  document.querySelectorAll('.accordion-content').forEach(x=>x.classList.remove('open'));
  document.querySelectorAll('.aic').forEach(x=>x.textContent='+');
  if(!open){c.classList.add('open');i.textContent='−';}
}
const glossaryData=[
  {term:'SIP',def:'Systematic Investment Plan. Fixed amount invested regularly in a mutual fund, enabling rupee/dollar cost averaging.'},
  {term:'CAGR',def:'Compound Annual Growth Rate. Annualised growth rate accounting for compounding.'},
  {term:'NAV',def:'Net Asset Value. Per-unit price of a mutual fund: (Total Assets − Liabilities) ÷ Units.'},
  {term:'ELSS',def:'Equity Linked Savings Scheme (India). Mutual fund qualifying under Section 80C, 3-year lock-in.'},
  {term:'PPF',def:'Public Provident Fund (India). Government savings at 7.1% tax-free, 15-year lock-in.'},
  {term:'NPS',def:'National Pension System (India). Market-linked retirement scheme with extra ₹50K deduction under 80CCD(1B).'},
  {term:'401(k)',def:'US employer-sponsored retirement plan with pre-tax contributions reducing taxable income. 2026 limit: $23,500.'},
  {term:'Roth IRA',def:'US after-tax retirement account. Contributions non-deductible but growth and qualified withdrawals tax-free.'},
  {term:'ISA',def:'Individual Savings Account (UK). Tax-free investment wrapper — £20,000/yr allowance. Stocks & Shares or Cash.'},
  {term:'ETF',def:'Exchange-Traded Fund. Basket of securities trading on exchange like a stock. Typically low cost.'},
  {term:'EMI',def:'Equated Monthly Instalment. Fixed monthly repayment of principal + interest on loans.'},
  {term:'FIRE',def:'Financial Independence, Retire Early. Corpus = 25× annual expenses so investments sustain lifestyle forever.'},
  {term:'HLV',def:'Human Life Value. Life insurance need = PV of future income until retirement.'},
  {term:'XIRR',def:'Extended Internal Rate of Return. Standard metric for periodic investment returns accounting for cash flow timing.'},
  {term:'4% Rule',def:'Withdrawing 4% of corpus annually sustains a portfolio for 30+ years (Trinity Study, 1998). Conservative: 3.5%.'},
  {term:'Expense Ratio',def:'Annual fee charged by a mutual fund as % of AUM. Index funds typically 0.03–0.20%; active funds 0.5–2%.'},
  {term:'Alpha',def:'Excess return above benchmark. A fund at 15% vs index at 12% has alpha of 3%.'},
  {term:'Beta',def:'Volatility vs market. Beta >1 = more volatile than market; <1 = less volatile.'},
  {term:'AUM',def:'Assets Under Management. Total market value of investments a fund house manages.'},
  {term:'Rebalancing',def:'Realigning portfolio back to target allocation annually by selling overperformers and buying underperformers.'},
  {term:'Corpus',def:'Total accumulated investment portfolio value, often referenced as retirement or goal corpus.'},
  {term:'SWR',def:'Safe Withdrawal Rate. Percentage of portfolio withdrawn annually without depleting it. Standard: 4%.'},
  {term:'Dollar-Cost Averaging',def:'Investing a fixed amount at regular intervals regardless of price — reduces timing risk.'},
  {term:'Diversification',def:'Spreading investments across assets, geographies, and sectors to reduce risk without proportionally reducing returns.'},
  {term:'S&P 500',def:'US index tracking 500 large-cap companies. Global benchmark for equity performance (~10.5% hist. annual return).'},
  {term:'Nifty 50',def:"India's benchmark index of 50 largest companies on NSE (~13% hist. annual return)."},
  {term:'MSCI World',def:'Index tracking ~1,500 large/mid-cap stocks across 23 developed markets. Core holding in global portfolios.'},
  {term:'Assurance Vie',def:'French tax-advantaged investment wrapper. Major tax benefits after 8 years of holding.'},
  {term:'Super (Superannuation)',def:'Australian mandatory retirement savings — currently 11.5% of salary contributed by employer.'},
  {term:'CPF',def:'Central Provident Fund (Singapore). Mandatory social security savings: 20% employee + 17% employer.'},
];
function buildGlossary(){
  renderGlossary(glossaryData);
  document.getElementById('gloss_search').oninput=function(){
    const q=this.value.toLowerCase();
    renderGlossary(glossaryData.filter(g=>g.term.toLowerCase().includes(q)||g.def.toLowerCase().includes(q)));
  };
}
function renderGlossary(data){
  const c=document.getElementById('glossary_list');c.innerHTML='';
  const grp={};data.forEach(g=>{const l=g.term[0].toUpperCase();if(!grp[l])grp[l]=[];grp[l].push(g);});
  Object.keys(grp).sort().forEach(letter=>{
    let html=`<div style="font-size:10px;font-weight:800;letter-spacing:3px;color:var(--gold);margin:20px 0 8px;text-transform:uppercase;">${letter}</div>`;
    grp[letter].forEach(g=>{html+=`<div style="display:grid;grid-template-columns:130px 1fr;gap:14px;padding:11px 0;border-bottom:1px solid rgba(255,255,255,.04);"><div style="font-size:12px;font-weight:700;color:var(--cream);">${g.term}</div><div style="font-size:11px;color:var(--muted);line-height:1.7;">${g.def}</div></div>`;});
    const s=document.createElement('div');s.innerHTML=html;c.appendChild(s);
  });
}

// ================================================================
// CSV EXPORT
// ================================================================
function downloadSIPCSV(){
  const rows=document.querySelectorAll('#sip_tbody tr');
  let csv='Year,Invested,Portfolio Value,Gains,Returns %\n';
  rows.forEach(r=>{const c=r.querySelectorAll('td');csv+=[c[0].textContent,c[1].textContent,c[2].textContent,c[3].textContent,c[4].textContent].join(',')+'\n';});
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download='MoneyVeda_SIP.csv';a.click();
}

// ================================================================
// EVENT WIRING
// ================================================================
['sip_p','sip_r','sip_t'].forEach(id=>document.getElementById(id).addEventListener('input',calcSIP));
['emi_p','emi_r','emi_t'].forEach(id=>document.getElementById(id).addEventListener('input',calcEMI));
['fire_age','fire_exp','fire_saved','fire_inv','fire_ret','fire_inf'].forEach(id=>document.getElementById(id).addEventListener('input',calcFIRE));
['roi_p','roi_r','roi_t'].forEach(id=>document.getElementById(id).addEventListener('input',calcROI));
['ins_inc','ins_age','ins_ret','ins_liab','ins_exist'].forEach(id=>document.getElementById(id).addEventListener('input',calcInsurance));

window.onload=function(){setMode('india');};
</script>

<script>
// ================================================================
// LIVE SIDEBAR & TICKER
// ================================================================
const STATIC_FALLBACK={
  india:[
    {label:'SENSEX',value:'74,532',pct:'+0.44',up:true},{label:'NIFTY 50',value:'23,114',pct:'+0.49',up:true},
    {label:'NIFTY BANK',value:'54,018',pct:'-2.36',up:false},{label:'GOLD',value:'₹6,842',pct:'+0.43',up:true},
    {label:'USD/INR',value:'93.75',pct:'-0.12',up:false},
  ],
  usa:[
    {label:'S&P 500',value:'6,606',pct:'-0.27',up:false},{label:'NASDAQ',value:'22,090',pct:'-0.28',up:false},
    {label:'DOW',value:'43,215',pct:'-0.15',up:false},{label:'GOLD',value:'$4,617',pct:'+0.31',up:true},
    {label:'USD/EUR',value:'0.9241',pct:'+0.12',up:true},
  ],
  europe:[
    {label:'EURO STOXX 50',value:'5,372',pct:'-1.62',up:false},{label:'DAX',value:'22,391',pct:'-1.45',up:false},
    {label:'FTSE 100',value:'8,673',pct:'-2.35',up:false},{label:'GOLD',value:'€4,263',pct:'+0.21',up:true},
    {label:'EUR/USD',value:'1.0823',pct:'-0.12',up:false},
  ],
  world:[
    {label:'S&P 500',value:'6,606',pct:'-0.27',up:false},{label:'MSCI WORLD',value:'3,841',pct:'-0.31',up:false},
    {label:'BITCOIN',value:'$84,200',pct:'-1.80',up:false},{label:'GOLD',value:'$4,617',pct:'+0.31',up:true},
    {label:'OIL (WTI)',value:'$68.40',pct:'-0.90',up:false},
  ]
};
let sidebarTimer=null;
async function loadSidebarLive(){
  try{
    const res=await fetch('/api/market?mode='+currentMode,{signal:AbortSignal.timeout(5000)});
    if(!res.ok) throw new Error('non-200');
    const data=await res.json();
    if(data.fallback) throw new Error('fallback');
    const fb=STATIC_FALLBACK[currentMode]||STATIC_FALLBACK.india;
    const items=data.tickers.map((t,i)=>
      t.ok?{label:t.label,value:String(t.value),pct:(t.pct>=0?'+':'')+t.pct,up:t.pct>=0}:(fb[i]||{label:t.label,value:'—',pct:'—',up:null})
    ).slice(0,5);
    renderSidebar(items,true);
  }catch{renderSidebar(STATIC_FALLBACK[currentMode]||STATIC_FALLBACK.india,false);}
}
function renderSidebar(items,live){
  const el=document.getElementById('sidebar-market');
  document.getElementById('sidebar-live-dot').style.background=live?'#4ade80':'#9090A8';
  document.getElementById('sidebar-updated').textContent=live?new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}):'Snapshot';
  el.innerHTML=items.map(t=>{
    const c=t.up===true?'#4ade80':t.up===false?'#f87171':'var(--muted)';
    const arrow=t.up===true?'▲':t.up===false?'▼':'';
    return`<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:7px;padding:3px 0;border-bottom:1px solid rgba(255,255,255,.04);">
      <span style="font-size:10px;color:var(--muted);">${t.label}</span>
      <div style="text-align:right;"><span style="font-size:11px;font-family:'DM Mono',monospace;color:var(--cream);display:block;">${t.value}</span>
      <span style="font-size:9px;color:${c};">${arrow} ${t.pct}%</span></div></div>`;
  }).join('');
}
function startSidebarRefresh(){
  if(sidebarTimer)clearInterval(sidebarTimer);
  loadSidebarLive();
  sidebarTimer=setInterval(loadSidebarLive,30000);
}

let tickerAnimation=null;
async function loadTickerData(mode){
  try{const res=await fetch('/api/market?mode='+mode);const data=await res.json();if(data.tickers)renderTicker(mode,data.tickers);}
  catch(e){renderTickerFallback(mode);}
}
function renderTickerFallback(mode){
  const fb=STATIC_FALLBACK[mode]||STATIC_FALLBACK.india;
  renderTickerItems(mode,fb.map(t=>({...t,ok:true,value:parseFloat(String(t.value).replace(/[^0-9.]/g,''))||0,pct:parseFloat(t.pct)||0,up:t.up})));
}
function renderTicker(mode,tickers){
  const live=tickers.filter(t=>t.ok);
  if(!live.length){renderTickerFallback(mode);return;}
  renderTickerItems(mode,live);
}
function renderTickerItems(mode,items){
  const track=document.getElementById('ticker-track');if(!track)return;
  const modeColors={india:'#C9A84C',usa:'#60a5fa',europe:'#a5b4fc',world:'#4ade80'};
  const modeFlags={india:'🇮🇳',usa:'🇺🇸',europe:'🇪🇺',world:'🌍'};
  const html=items.map(t=>{
    const up=t.up;const color=up?'#22C55E':'#EF4444';
    const arrow=up?'▲':'▼';
    const val=typeof t.value==='number'?t.value.toLocaleString('en-US',{maximumFractionDigits:2}):t.value;
    const pct=(up?'+':'')+t.pct+'%';
    return`<div style="display:inline-flex;align-items:center;padding:0 18px 0 16px;border-right:1px solid rgba(255,255,255,.05);height:44px;">
      <span style="font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#6b7280;margin-right:9px;">${t.label}</span>
      <span style="font-size:13px;font-weight:600;color:#F0EDE6;font-family:'DM Mono',monospace;margin-right:7px;">${val}</span>
      <span style="display:inline-flex;align-items:center;gap:2px;background:${up?'rgba(34,197,94,.1)':'rgba(239,68,68,.1)'};border:1px solid ${up?'rgba(34,197,94,.25)':'rgba(239,68,68,.25)'};border-radius:4px;padding:2px 7px;">
        <span style="font-size:7px;color:${color};">${arrow}</span>
        <span style="font-size:10px;font-weight:700;color:${color};font-family:'DM Mono',monospace;">${pct}</span>
      </span></div>`;
  }).join('');
  const badge=`<div style="display:inline-flex;align-items:center;padding:0 16px;height:44px;border-right:1px solid rgba(201,168,76,.2);flex-shrink:0;"><span style="font-size:9px;font-weight:800;letter-spacing:2px;color:${modeColors[mode]};font-family:'DM Sans',sans-serif;">${modeFlags[mode]} LIVE</span></div>`;
  track.innerHTML=badge+html+badge+html;
  startTickerScroll(track);
}
function startTickerScroll(track){
  if(tickerAnimation)cancelAnimationFrame(tickerAnimation);
  let pos=0;
  function step(){const half=track.scrollWidth/2;pos+=0.45;if(pos>=half)pos=0;track.style.transform='translateX('+(-pos)+'px)';tickerAnimation=requestAnimationFrame(step);}
  tickerAnimation=requestAnimationFrame(step);
}
const lt=document.getElementById('live-ticker');
if(lt){
  lt.addEventListener('mouseenter',function(){if(tickerAnimation)cancelAnimationFrame(tickerAnimation);});
  lt.addEventListener('mouseleave',function(){const t=document.getElementById('ticker-track');if(t&&t.innerHTML)startTickerScroll(t);});
}
setInterval(function(){loadTickerData(currentMode);},30000);
</script>

<!-- ============================================================ -->
<!-- LESSON MODAL -->
<!-- ============================================================ -->
<div id="lesson-modal" style="display:none;position:fixed;inset:0;z-index:2000;align-items:center;justify-content:center;padding:16px;">
  <div id="lesson-overlay" onclick="closeLesson()" style="position:absolute;inset:0;background:rgba(0,0,0,.75);backdrop-filter:blur(6px);"></div>
  <div style="position:relative;background:var(--dark2);border:1px solid rgba(201,168,76,.25);border-radius:18px;max-width:560px;width:100%;max-height:85vh;overflow-y:auto;padding:28px;box-shadow:0 24px 80px rgba(0,0,0,.6);">
    <button onclick="closeLesson()" style="position:absolute;top:16px;right:16px;background:rgba(255,255,255,.07);border:none;color:var(--cream);width:32px;height:32px;border-radius:50%;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center;">✕</button>
    <div id="lesson-icon" style="font-size:36px;margin-bottom:12px;"></div>
    <div id="lesson-tag" style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--gold);font-weight:700;margin-bottom:8px;"></div>
    <h2 id="lesson-title" style="font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:900;margin-bottom:12px;line-height:1.2;"></h2>
    <div id="lesson-body" style="font-size:13px;color:var(--muted);line-height:1.8;"></div>
    <div id="lesson-example" style="margin-top:20px;background:rgba(201,168,76,.07);border:1px solid rgba(201,168,76,.2);border-radius:12px;padding:16px;display:none;">
      <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--gold);margin-bottom:8px;">EXAMPLE</div>
      <div id="lesson-example-body" style="font-size:12px;color:var(--cream);line-height:1.7;"></div>
    </div>
    <div id="lesson-tip" style="margin-top:16px;background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.2);border-radius:12px;padding:14px;display:none;">
      <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#4ade80;margin-bottom:6px;">💡 PRO TIP</div>
      <div id="lesson-tip-body" style="font-size:12px;color:var(--cream);line-height:1.7;"></div>
    </div>
    <button onclick="closeLesson()" style="margin-top:22px;width:100%;padding:12px;background:linear-gradient(135deg,var(--gold),var(--gold-light));border:none;border-radius:10px;color:#0A0A0F;font-weight:800;font-size:13px;cursor:pointer;font-family:'DM Sans',sans-serif;letter-spacing:.5px;">Got it ✓</button>
  </div>
</div>

<!-- ============================================================ -->
<!-- ONBOARDING / CONNECT MODAL -->
<!-- ============================================================ -->
<div id="onboard-modal" style="display:none;position:fixed;inset:0;z-index:2000;align-items:center;justify-content:center;padding:16px;">
  <div style="position:absolute;inset:0;background:rgba(0,0,0,.8);backdrop-filter:blur(8px);"></div>
  <div style="position:relative;background:var(--dark2);border:1px solid rgba(201,168,76,.3);border-radius:20px;max-width:480px;width:100%;padding:32px;box-shadow:0 32px 100px rgba(0,0,0,.7);">

    <!-- Step 1: Welcome -->
    <div id="ob-step-1">
      <div style="text-align:center;margin-bottom:24px;">
        <div style="font-size:40px;margin-bottom:10px;">👋</div>
        <div style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--gold);margin-bottom:8px;">WELCOME TO MONEYVEDA</div>
        <h2 style="font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:900;margin-bottom:8px;">Your Personal Finance Hub</h2>
        <p style="font-size:12px;color:var(--muted);line-height:1.7;">Let's set up your profile so we can personalise calculations, tax rules and benchmarks for you.</p>
      </div>
      <div style="display:flex;flex-direction:column;gap:12px;margin-bottom:24px;">
        <div>
          <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:6px;">Your Name</label>
          <input id="ob-name" type="text" placeholder="e.g. Raj Sharma" class="num-input" style="font-family:'DM Sans',sans-serif;font-size:14px;">
        </div>
        <div>
          <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:6px;">Age</label>
          <input id="ob-age" type="number" placeholder="e.g. 28" class="num-input" style="font-family:'DM Sans',sans-serif;font-size:14px;" min="18" max="80">
        </div>
        <div>
          <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:6px;">Monthly Income</label>
          <input id="ob-income" type="number" placeholder="e.g. 80000" class="num-input" style="font-family:'DM Sans',sans-serif;font-size:14px;">
        </div>
        <div>
          <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:6px;">Financial Goal</label>
          <select id="ob-goal" class="num-input" style="font-family:'DM Sans',sans-serif;font-size:13px;">
            <option value="">Select your primary goal…</option>
            <option value="wealth">Build long-term wealth (SIP/MF)</option>
            <option value="home">Buy a home (EMI planning)</option>
            <option value="fire">Retire early (FIRE)</option>
            <option value="tax">Save on taxes</option>
            <option value="insurance">Get insured</option>
            <option value="learn">Just learning about finance</option>
          </select>
        </div>
      </div>
      <button onclick="obNext()" style="width:100%;padding:14px;background:linear-gradient(135deg,var(--gold),var(--gold-light));border:none;border-radius:12px;color:#0A0A0F;font-weight:800;font-size:14px;cursor:pointer;font-family:'DM Sans',sans-serif;letter-spacing:.5px;">Continue →</button>
      <button onclick="closeOnboard()" style="width:100%;padding:10px;background:transparent;border:none;color:var(--muted);font-size:12px;cursor:pointer;margin-top:8px;font-family:'DM Sans',sans-serif;">Skip for now</button>
    </div>

    <!-- Step 2: Guide -->
    <div id="ob-step-2" style="display:none;">
      <div style="text-align:center;margin-bottom:24px;">
        <div style="font-size:36px;margin-bottom:10px;">🗺️</div>
        <div style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--gold);margin-bottom:8px;">QUICK GUIDE</div>
        <h2 style="font-family:'Playfair Display',serif;font-size:1.5rem;font-weight:900;margin-bottom:8px;">Here's what you can do</h2>
      </div>
      <div id="ob-guide-content" style="display:flex;flex-direction:column;gap:10px;margin-bottom:24px;"></div>
      <button onclick="obFinish()" style="width:100%;padding:14px;background:linear-gradient(135deg,var(--gold),var(--gold-light));border:none;border-radius:12px;color:#0A0A0F;font-weight:800;font-size:14px;cursor:pointer;font-family:'DM Sans',sans-serif;letter-spacing:.5px;">Start Exploring 🚀</button>
    </div>

  </div>
</div>

<!-- Connect button (floating) -->
<button id="connect-btn" onclick="openOnboard()" title="Your Profile & Guide" style="position:fixed;bottom:80px;right:18px;z-index:1500;width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,var(--gold),var(--gold-light));border:none;cursor:pointer;box-shadow:0 4px 20px rgba(201,168,76,.4);font-size:20px;display:flex;align-items:center;justify-content:center;transition:transform .2s;-webkit-tap-highlight-color:transparent;touch-action:manipulation;">👤</button>

<style>
@media(min-width:769px){
  #connect-btn{bottom:24px;}
}
</style>

<script>
var LESSONS = {
  "start-early": {
    icon:"⚡", tag:"Power of Compounding",
    title:"Why Starting Early Changes Everything",
    body:"Compounding means earning returns on your returns. The longer your money stays invested, the more dramatic this effect becomes — growing exponentially, not linearly.<br><br>Time in the market is the single most powerful variable in wealth creation. More than picking the right stock. More than finding the highest return. More than saving a larger amount.",
    example:"<strong>Same amount per month. Massive difference:</strong><br><br>Start at <strong style='color:#4ade80'>Age 25</strong> → 3.5 Cr by 60 (35 yrs @ 12%)<br>Start at <strong style='color:#f87171'>Age 35</strong> → 1.2 Cr by 60 (25 yrs @ 12%)<br>Start at <strong style='color:#f87171'>Age 45</strong> → 38L by 60 (15 yrs @ 12%)<br><br>Same monthly amount. A 10-year delay costs <strong style='color:#f87171'>2.3 Crore extra.</strong>",
    tip:"Set up an auto-debit SIP on the 1st of every month so you invest before you spend. Even a small amount started today beats a large amount started 5 years from now."
  },
  "rule-72": {
    icon:"📐", tag:"Mental Math Shortcut",
    title:"The Rule of 72 — Your Doubling Calculator",
    body:"Divide 72 by your annual return rate to find how many years it takes your money to double. No calculator needed — works in your head instantly.<br><br>The number 72 is chosen because it gives the most accurate result across common return rates (6%–15%).",
    example:"<strong>Doubling time at different returns:</strong><br><br>Savings A/C 3.5% → doubles in <strong style='color:#f87171'>20.6 years</strong><br>Fixed Deposit 7% → doubles in <strong style='color:#f59e0b'>10.3 years</strong><br>PPF 7.1% → doubles in <strong style='color:#f59e0b'>10.1 years</strong><br>Nifty 50 avg 12% → doubles in <strong style='color:#4ade80'>6 years</strong><br>Equity MF avg 14% → doubles in <strong style='color:#4ade80'>5.1 years</strong>",
    tip:"Use Rule of 72 in reverse — want to double money in 8 years? You need 72÷8 = 9% return. That instantly tells you which asset classes to target."
  },
  "cost-averaging": {
    icon:"📊", tag:"SIP Strategy",
    title:"Cost Averaging — Your Market Crash Shield",
    body:"When you invest a fixed amount monthly (SIP), you automatically buy more units when prices are low and fewer when prices are high. This brings your average cost down over time — regardless of market timing.<br><br>This is why SIPs actually benefit from market crashes.",
    example:"<strong>10,000/month SIP example:</strong><br><br>Jan: NAV 100 → buy <strong>100 units</strong><br>Feb: NAV 80 (crash) → buy <strong>125 units</strong><br>Mar: NAV 90 → buy <strong>111 units</strong><br>Apr: NAV 110 → buy <strong>90 units</strong><br><br>Average NAV = 95. Your avg cost = <strong style='color:#4ade80'>93.60</strong> — beating the average automatically!",
    tip:"Never pause your SIP during a market crash. That is exactly when you buy the most units at the cheapest price."
  },
  "global-diversification": {
    icon:"🌍", tag:"Portfolio Strategy",
    title:"Global Diversification — Reduce Risk, Grow Steady",
    body:"Spreading investments across geographies means your portfolio is not tied to any single economy, politics, or currency. When one market falls, others may hold or rise.<br><br>Currency diversification adds another layer of protection.",
    example:"<strong>2022 Market Performance:</strong><br><br>India Nifty 50: <strong style='color:#4ade80'>+4.3%</strong><br>USA S&P 500: <strong style='color:#f87171'>-19.4%</strong><br>Brazil Bovespa: <strong style='color:#4ade80'>+4.7%</strong><br>UK FTSE 100: <strong style='color:#4ade80'>+0.9%</strong><br><br>A globally diversified portfolio smoothed out the US crash significantly.",
    tip:"Low-cost MSCI World ETFs give exposure to 1,500+ companies across 23 developed countries in a single instrument."
  },
  "emi-prepay": {
    icon:"💰", tag:"Loan Strategy",
    title:"Prepay Your Loan — The Best Risk-Free Return",
    body:"Every rupee you prepay on your home loan saves you interest at the full loan rate — which is currently 8-9%. That is a guaranteed, risk-free return higher than FDs, PPF, or even many equity funds net of tax.",
    example:"<strong>50L loan at 8.5% for 20 years:</strong><br><br>Normal: EMI 43,391 · Total interest 54.1L<br>Prepay 1L in Year 1: saves <strong style='color:#4ade80'>4.8L interest</strong>, cuts 2.5 years<br>Prepay 1 extra EMI/year: saves <strong style='color:#4ade80'>8L+</strong>, cuts 4 years<br><br>The earlier you prepay, the more you save — interest is front-loaded.",
    tip:"Always ask your bank to reduce tenure (not EMI) when prepaying. Reducing tenure saves far more interest than reducing EMI."
  },
  "emi-tax": {
    icon:"📋", tag:"Tax Planning",
    title:"Home Loan Tax Benefits — Double Deduction",
    body:"A home loan gives you two simultaneous tax deductions under Indian tax law — making it one of the most tax-efficient financial instruments available to salaried employees.",
    example:"<strong>On a 60L home loan at 8.5%:</strong><br><br>Section 80C: Principal repaid up to <strong style='color:#4ade80'>1.5L/yr</strong> — saves 46,800/yr at 30% slab<br>Section 24(b): Interest paid up to <strong style='color:#4ade80'>2L/yr</strong> — saves 62,400/yr<br><br>Combined annual tax saving: <strong style='color:#4ade80'>1,09,200/yr</strong> for 3-4 years",
    tip:"Under the New Tax Regime, Section 24(b) and 80C deductions are NOT available. This is the biggest reason many home loan borrowers are better off in the Old Regime."
  },
  "emi-vs-rent": {
    icon:"🏠", tag:"Buy vs Rent",
    title:"Buy vs Rent — The Real Calculation",
    body:"Buying feels safer but is not always the smarter financial decision. The real comparison must account for opportunity cost — what would the down payment earn if invested instead?",
    example:"<strong>1 Cr property in Mumbai:</strong><br><br>Down payment 20L → if invested at 12% for 20yr = <strong style='color:#4ade80'>1.93 Cr</strong><br>EMI 75K/mo vs rent 25K/mo → extra 50K/mo SIP for 20yr = <strong style='color:#4ade80'>4.99 Cr</strong><br>Property appreciation 6%/yr for 20yr = 3.2 Cr<br><br>Renting + investing: 6.9 Cr. Buying: 3.2 Cr. <strong style='color:#f87171'>Big difference.</strong>",
    tip:"Buying makes emotional and financial sense when: you plan to stay 10+ years, the price-to-rent ratio is below 20x, and the city has strong appreciation history."
  },
  "fire-4pct": {
    icon:"🔥", tag:"FIRE Rule",
    title:"The 4% Rule — How It Was Discovered",
    body:"The 4% rule comes from the Trinity Study (1998), which analyzed 30-year retirement periods from 1926-1995. It found that withdrawing 4% of your portfolio in year 1, then adjusting for inflation annually, had a 95%+ success rate across all historical periods.",
    example:"<strong>Monthly expenses 75,000:</strong><br><br>Annual expenses: 9L<br>FIRE corpus needed (25x): <strong style='color:#4ade80'>2.25 Cr</strong><br>Monthly safe withdrawal: 75,000<br>Portfolio survives: 30+ years in 95% of historical scenarios<br><br>At 3% withdrawal (33x): essentially perpetual — corpus grows.",
    tip:"For Indian investors, use a 3-3.5% withdrawal rate. India has higher inflation (6% vs 2-3% in the US), so the 4% rule is slightly aggressive for INR-based retirements."
  },
  "fire-types": {
    icon:"🎯", tag:"FIRE Lifestyle",
    title:"Lean FIRE, Fat FIRE, Barista FIRE",
    body:"FIRE is not one-size-fits-all. Different people have different income levels, lifestyles, and risk tolerances — leading to very different retirement targets.",
    example:"<strong>Monthly expenses determine your FIRE type:</strong><br><br>Under 30K/mo: <strong style='color:#60a5fa'>Lean FIRE</strong> — frugal, corpus 90L-1Cr<br>30-75K/mo: <strong style='color:#4ade80'>Regular FIRE</strong> — comfortable, corpus 1-2.25Cr<br>75K-2L/mo: <strong style='color:#C9A84C'>Fat FIRE</strong> — luxurious, corpus 2.25-6Cr<br>Part-time work: <strong style='color:#a78bfa'>Barista FIRE</strong> — smaller corpus, earn 15-20K to cover basics",
    tip:"Barista FIRE is underrated — working 2-3 days a week at something you enjoy covers daily expenses, letting your corpus compound untouched for 5-7 more years before full retirement."
  },
  "fire-inflation": {
    icon:"📉", tag:"Inflation Risk",
    title:"Inflation — The Silent Retirement Killer",
    body:"At 6% inflation, your purchasing power halves every 12 years. A corpus that supports 75K/month today will only support 37K/month in real terms by 2037 — unless your investments grow faster than inflation.",
    example:"<strong>75,000/month today at 6% inflation:</strong><br><br>In 10 years: needs <strong style='color:#f87171'>1,34,000/mo</strong> to maintain same lifestyle<br>In 20 years: needs <strong style='color:#f87171'>2,40,000/mo</strong><br>In 30 years: needs <strong style='color:#f87171'>4,30,000/mo</strong><br><br>Your FIRE corpus must grow at least 6%/yr just to stay even.",
    tip:"Keep 60-70% of your FIRE corpus in equity even after retirement. Bonds and FDs alone will not beat inflation over a 30-year horizon. A 60/40 equity-debt split is the historical sweet spot."
  },
  "roi-cagr": {
    icon:"📈", tag:"Performance Metric",
    title:"CAGR — The Only Return Metric That Matters",
    body:"Compounded Annual Growth Rate (CAGR) tells you the smooth annual rate at which an investment grew, eliminating the noise of year-to-year volatility. It is the standard for comparing any two investments.",
    example:"<strong>Investment grew from 1L to 3.1L in 10 years:</strong><br><br>Simple math says 210% return — but that ignores time.<br>CAGR = (3.1/1)^(1/10) - 1 = <strong style='color:#4ade80'>12% per year</strong><br><br>Now you can compare: FD at 7% CAGR vs Nifty at 13% CAGR vs Gold at 9.5% CAGR — apples to apples.",
    tip:"Always demand CAGR when evaluating any investment product. Absolute returns (200% in 10 years!) are meaningless without knowing the time period."
  },
  "roi-xirr": {
    icon:"🧮", tag:"SIP Returns",
    title:"CAGR vs XIRR — Why SIPs Need XIRR",
    body:"CAGR works for lump sum investments. For SIPs with multiple investments at different times, you need XIRR (Extended Internal Rate of Return) — it accounts for the timing of each investment.",
    example:"<strong>Why CAGR misleads for SIPs:</strong><br><br>You invest 1L/month for 10 years = 12L total<br>Final value = 23L. Simple CAGR on 12L = 92% = 6.8% CAGR<br>But your first payment had 10 years to grow, last had 1 month.<br>XIRR correctly calculates: <strong style='color:#4ade80'>12.4% annualised</strong>",
    tip:"Use the XIRR function in Excel or Google Sheets to calculate true SIP returns. Input each SIP date/amount as negative cash flows and final value as positive."
  },
  "roi-rebalance": {
    icon:"⚖️", tag:"Portfolio Management",
    title:"Rebalancing — Sell High, Buy Low Automatically",
    body:"Rebalancing means restoring your target asset allocation (e.g. 70% equity, 30% debt) once a year. When equities rally, you sell some equity and buy debt. When equities crash, you buy more equity. It forces you to sell high and buy low — systematically.",
    example:"<strong>Starting: 70% equity, 30% debt</strong><br><br>After a bull run: equity becomes 85% of portfolio<br>Rebalance: sell equity, buy debt to restore 70/30<br>After a crash: equity drops to 55%<br>Rebalance: sell debt, buy equity at low prices<br><br>Studies show annual rebalancing adds <strong style='color:#4ade80'>0.5-1.5% CAGR</strong> vs no rebalancing.",
    tip:"Rebalance once a year on your birthday — easy to remember, avoids over-trading. Do not rebalance more than twice a year as transaction costs erode the benefit."
  },
  "cmp-when-sip": {
    icon:"📅", tag:"Investment Timing",
    title:"When SIP Wins — Volatility Is Your Friend",
    body:"SIPs outperform lump sum when markets are volatile or trending sideways. Because you buy at multiple price points, you catch both highs and lows — resulting in a lower average cost than a single entry point.",
    example:"<strong>2008-2018 (volatile decade):</strong><br><br>Lump sum 12L in Jan 2008 (market peak): final value 38L = <strong style='color:#f59e0b'>12% CAGR</strong><br>SIP 10K/month same period: invested 12L, final value 51L = <strong style='color:#4ade80'>16.2% CAGR</strong><br><br>Volatility cost the lump sum investor — and rewarded the SIP investor.",
    tip:"For salaried investors, SIP is almost always the right choice — not just for returns, but for financial discipline. Automating the investment removes emotion from the equation."
  },
  "cmp-when-ls": {
    icon:"💸", tag:"Investment Timing",
    title:"When Lump Sum Wins — Catch the Bottom",
    body:"Lump sum beats SIP in consistently rising markets. If you invest a large amount at a market bottom or at the start of a multi-year bull run, every rupee benefits from the full period of growth.",
    example:"<strong>March 2020 (COVID crash bottom):</strong><br><br>Lump sum 12L at Nifty 7,500: grew to 52L in 3 years = <strong style='color:#4ade80'>63% CAGR</strong><br>SIP 33K/month same period: invested 12L, grew to 18L = <strong style='color:#f59e0b'>28% CAGR</strong><br><br>Perfect market timing with lump sum was 2.25x better.",
    tip:"The problem: nobody can reliably time market bottoms. Studies show that time IN the market beats time OF the market for 90%+ of investors. SIP removes the guesswork."
  },
  "cmp-hybrid": {
    icon:"🔀", tag:"Advanced Strategy",
    title:"STP — The Smart Hybrid Strategy",
    body:"Systematic Transfer Plan (STP): park your lump sum in a liquid/debt fund first, then automatically transfer a fixed amount to equity every month. You get the safety of gradual equity entry AND your idle cash earns 6-7% in debt.",
    example:"<strong>You receive 24L bonus:</strong><br><br>Put 24L in liquid fund (earning 7%)<br>Set STP: transfer 2L/month to equity fund<br>Month 1-12: entering equity gradually, no timing risk<br>Liquid fund balance earns 7% while waiting<br><br>Result: better than pure SIP (idle cash earns) + safer than pure lump sum.",
    tip:"STP is the professional way to deploy bonuses, RSU vesting, property sale proceeds, or inheritance into equity markets. Most major AMCs offer STP with zero exit load."
  }
};

function showLesson(id) {
  var l = LESSONS[id];
  if (!l) return;
  document.getElementById("lesson-icon").textContent = l.icon;
  document.getElementById("lesson-tag").textContent = l.tag;
  document.getElementById("lesson-title").textContent = l.title;
  document.getElementById("lesson-body").innerHTML = l.body;
  var ex = document.getElementById("lesson-example");
  var tip = document.getElementById("lesson-tip");
  if (l.example) { ex.style.display="block"; document.getElementById("lesson-example-body").innerHTML=l.example; }
  else ex.style.display="none";
  if (l.tip) { tip.style.display="block"; document.getElementById("lesson-tip-body").textContent=l.tip; }
  else tip.style.display="none";
  document.getElementById("lesson-modal").style.display="flex";
}

function closeLesson() {
  document.getElementById("lesson-modal").style.display="none";
}

var GOAL_GUIDES = {
  wealth:   [{icon:"📈",title:"Investment Planner",desc:"Set your monthly SIP and see your corpus grow year by year with compounding."},{icon:"💹",title:"ROI & Compound",desc:"Compare FD, PPF, Gold, Nifty 50 over 20 years side by side."},{icon:"📋",title:"Tax Optimizer",desc:"Invest in ELSS to save up to 46,800/yr under Section 80C."}],
  home:     [{icon:"🏠",title:"EMI & Mortgage Planner",desc:"Calculate exact monthly EMI, total interest and Section 24(b) tax benefit."},{icon:"📋",title:"Tax Optimizer",desc:"Home loan interest gives up to 2L deduction under Sec 24(b) every year."},{icon:"📈",title:"Investment Planner",desc:"Start a SIP now to build your down payment corpus."}],
  fire:     [{icon:"🔥",title:"FIRE Calculator",desc:"Find your FIRE number — corpus that funds your lifestyle forever using 4% rule."},{icon:"📈",title:"Investment Planner",desc:"Aggressive monthly SIPs are the fastest path to financial independence."},{icon:"💹",title:"ROI & Compound",desc:"Model scenarios when your corpus hits 5Cr, 10Cr, 20Cr."}],
  tax:      [{icon:"📋",title:"Tax Optimizer",desc:"Compare Old vs New regime instantly. Find the one that saves you more."},{icon:"📈",title:"Investment Planner",desc:"ELSS SIPs give market returns AND Section 80C tax savings simultaneously."},{icon:"🏠",title:"EMI Planner",desc:"Home loan = dual benefit: principal 80C + interest 24b = up to 3.5L saved."}],
  insurance:[{icon:"🛡️",title:"Insurance Planner",desc:"Use the HLV method to calculate exactly how much life cover you need."},{icon:"📋",title:"Tax Optimizer",desc:"Health insurance premiums save tax under 80D — up to 75,000/yr."},{icon:"🔥",title:"FIRE Calculator",desc:"Proper insurance protects your FIRE corpus from medical emergencies."}],
  learn:    [{icon:"🎓",title:"Financial Academy",desc:"Structured modules from emergency fund basics to advanced FIRE strategy."},{icon:"📖",title:"Finance Glossary",desc:"Every term in plain language — SIP, NAV, CAGR, XIRR and 50+ more."},{icon:"📊",title:"All Calculators",desc:"The best way to learn is to play with numbers. Try every calculator!"}],
  "":       [{icon:"📈",title:"Investment Planner",desc:"Start with SIP — the most powerful wealth creation tool."},{icon:"🔥",title:"FIRE Calculator",desc:"Discover your financial independence number."},{icon:"📋",title:"Tax Optimizer",desc:"Are you in the right tax regime? Find out instantly."}]
};

var userProfile = {};

function buildGuideHTML(profile, isNew) {
  var goalLabels={wealth:"Build Wealth",home:"Buy a Home",fire:"Retire Early",tax:"Save Tax",insurance:"Get Insured",learn:"Learning Finance","":"Exploring"};
  var guide = GOAL_GUIDES[profile.goal||""] || GOAL_GUIDES[""];
  var label = goalLabels[profile.goal||""] || "Exploring";
  var header = isNew
    ? "<div style=\"background:rgba(201,168,76,.08);border:1px solid rgba(201,168,76,.2);border-radius:12px;padding:14px;margin-bottom:8px;\"><div style=\"font-size:10px;color:var(--muted);margin-bottom:4px;\">WELCOME</div><div style=\"font-size:15px;font-weight:700;color:var(--cream);\">Hi " + profile.name + "! 👋</div><div style=\"font-size:11px;color:var(--gold-light);margin-top:2px;\">Goal: " + label + " · Age: " + (profile.age||"—") + "</div></div>"
    : "<div style=\"background:rgba(201,168,76,.08);border:1px solid rgba(201,168,76,.2);border-radius:12px;padding:14px;margin-bottom:8px;\"><div style=\"font-size:10px;color:var(--muted);margin-bottom:4px;\">YOUR PROFILE</div><div style=\"font-size:15px;font-weight:700;color:var(--cream);\">" + (profile.name||"User") + "</div><div style=\"font-size:11px;color:var(--gold-light);margin-top:2px;\">Goal: " + label + " · Age: " + (profile.age||"—") + "</div></div>";
  var cards = guide.map(function(g){
    return "<div style=\"display:flex;gap:12px;align-items:flex-start;background:var(--dark3);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:12px;margin-bottom:6px;\"><div style=\"font-size:22px;flex-shrink:0;\">" + g.icon + "</div><div><div style=\"font-size:12px;font-weight:700;color:var(--cream);margin-bottom:3px;\">" + g.title + "</div><div style=\"font-size:11px;color:var(--muted);line-height:1.5;\">" + g.desc + "</div></div></div>";
  }).join("");
  var editBtn = isNew ? "" : "<button onclick=\"resetProfile()\" style=\"width:100%;padding:8px;background:transparent;border:1px solid rgba(255,255,255,.1);border-radius:8px;color:var(--muted);font-size:11px;cursor:pointer;margin-top:4px;touch-action:manipulation;\">✏️ Edit Profile</button>";
  return header + cards + editBtn;
}

function openOnboard() {
  try { userProfile = JSON.parse(localStorage.getItem("wh_profile")||"{}"); } catch(e) { userProfile={}; }
  if (userProfile.name) { showProfileCard(); return; }
  document.getElementById("ob-step-1").style.display="block";
  document.getElementById("ob-step-2").style.display="none";
  document.getElementById("ob-name").value = userProfile.name||"";
  document.getElementById("ob-age").value = userProfile.age||"";
  document.getElementById("ob-income").value = userProfile.income||"";
  document.getElementById("ob-goal").value = userProfile.goal||"";
  document.getElementById("onboard-modal").style.display="flex";
}

function showProfileCard() {
  document.getElementById("ob-step-1").style.display="none";
  document.getElementById("ob-step-2").style.display="block";
  document.getElementById("ob-guide-content").innerHTML = buildGuideHTML(userProfile, false);
  document.getElementById("onboard-modal").style.display="flex";
}

function resetProfile() {
  userProfile = {};
  try { localStorage.removeItem("wh_profile"); } catch(e) {}
  document.getElementById("ob-step-1").style.display="block";
  document.getElementById("ob-step-2").style.display="none";
  document.getElementById("ob-name").value="";
  document.getElementById("ob-age").value="";
  document.getElementById("ob-income").value="";
  document.getElementById("ob-goal").value="";
}

function obNext() {
  var name = document.getElementById("ob-name").value.trim();
  var age = document.getElementById("ob-age").value.trim();
  var income = document.getElementById("ob-income").value.trim();
  var goal = document.getElementById("ob-goal").value;
  if (!name) { document.getElementById("ob-name").focus(); return; }
  userProfile = {name:name, age:age, income:income, goal:goal};
  try { localStorage.setItem("wh_profile", JSON.stringify(userProfile)); } catch(e) {}
  if (age) {
    var a = parseInt(age);
    var el = document.getElementById("fire_age"); if(el){el.value=a; document.getElementById("v_fire_age").textContent=a;}
    var el2 = document.getElementById("ins_age"); if(el2){el2.value=a; document.getElementById("v_ins_age").textContent=a;}
  }
  document.getElementById("ob-step-1").style.display="none";
  document.getElementById("ob-step-2").style.display="block";
  document.getElementById("ob-guide-content").innerHTML = buildGuideHTML(userProfile, true);
}

function obFinish() {
  closeOnboard();
  var goalNav={wealth:"sip",home:"emi",fire:"fire",tax:"tax",insurance:"insurance",learn:"edu"};
  navTo(goalNav[userProfile.goal||""]||"sip");
}

function closeOnboard() {
  document.getElementById("onboard-modal").style.display="none";
}

setTimeout(function(){
  try {
    var p = JSON.parse(localStorage.getItem("wh_profile")||"{}");
    if (!p.name && !localStorage.getItem("wh_visited")) {
      localStorage.setItem("wh_visited","1");
      openOnboard();
    } else if (p.name) {
      applyProfileToSliders(p);
    }
  } catch(e) {}
}, 1500);

// ============================================================
// PROFILE AUTO-FILL SLIDERS
// ============================================================
function applyProfileToSliders(p) {
  if (!p) return;
  var age = parseInt(p.age);
  var income = parseFloat(p.income);
  if (age && age >= 18 && age <= 65) {
    ["fire_age","ins_age"].forEach(function(id){
      var el = document.getElementById(id);
      var vEl = document.getElementById("v_" + id.replace("_","_"));
      if (el) { el.value = age; }
    });
    var fa = document.getElementById("fire_age");
    if (fa) { fa.value = age; document.getElementById("v_fire_age").textContent = age; }
    var ia = document.getElementById("ins_age");
    if (ia) { ia.value = Math.min(age,55); document.getElementById("v_ins_age").textContent = Math.min(age,55); }
  }
  if (income && income > 0) {
    var r = REGIONS[currentMode];
    // Set SIP to ~20% of monthly income
    var sipAmt = Math.round(income * 0.20 / r.sipStep) * r.sipStep;
    sipAmt = Math.max(r.sipMin, Math.min(r.sipMax, sipAmt));
    var sipEl = document.getElementById("sip_p");
    if (sipEl) { sipEl.value = sipAmt; }
    // Set insurance income
    var annualInc = income * 12;
    var insEl = document.getElementById("ins_inc");
    if (insEl) {
      var clipped = Math.max(r.insIncMin, Math.min(r.insIncMax, annualInc));
      insEl.value = clipped;
    }
  }
}

// Also call applyProfileToSliders when obNext saves profile
var _origObNext = obNext;
obNext = function() {
  _origObNext();
  try {
    var p = JSON.parse(localStorage.getItem("wh_profile")||"{}");
    if (p.name) applyProfileToSliders(p);
  } catch(e) {}
};

// ============================================================
// SHARE RESULT
// ============================================================
function shareResult(tab) {
  var lines = [];
  var url = "https://moneyveda.org";
  if (tab === "sip") {
    var corpus = document.getElementById("sip_total").textContent;
    var invested = document.getElementById("sip_invested").textContent;
    var gains = document.getElementById("sip_gains").textContent;
    var mult = document.getElementById("sip_xbadge").textContent;
    var p = document.getElementById("sip_p").value;
    var r = document.getElementById("sip_r").value;
    var t = document.getElementById("sip_t").value;
    lines = [
      "My SIP Wealth Projection",
      "Monthly SIP: " + fmtSym(+p),
      "Return: " + r + "% for " + t + " years",
      "Total Corpus: " + corpus,
      "Amount Invested: " + invested,
      "Wealth Gained: " + gains + " (" + mult + ")",
      "Calculate yours: " + url
    ];
  }
  var text = lines.join("\n");
  if (navigator.share) {
    navigator.share({ title: "MoneyVeda Result", text: text, url: url })
      .catch(function(){});
  } else if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(function(){
      showToast("Result copied to clipboard!");
    });
  } else {
    showToast("Copy: " + corpus);
  }
}

function showToast(msg) {
  var t = document.createElement("div");
  t.textContent = msg;
  t.style.cssText = "position:fixed;bottom:90px;left:50%;transform:translateX(-50%);background:#22222C;color:#F5F0E8;border:1px solid rgba(201,168,76,.3);padding:10px 20px;border-radius:100px;font-size:12px;z-index:3000;font-family:DM Sans,sans-serif;white-space:nowrap;box-shadow:0 4px 20px rgba(0,0,0,.5);";
  document.body.appendChild(t);
  setTimeout(function(){ t.style.opacity="0"; t.style.transition="opacity .4s"; setTimeout(function(){ t.remove(); }, 400); }, 2200);
}

// ============================================================
// COMPARE CALCULATOR
// ============================================================
var cmpChart = null;
function buildCompare() {
  var pEl = document.getElementById("cmp_p"); if (!pEl) return;
  var p = +pEl.value;
  var r = +document.getElementById("cmp_r").value;
  var t = +document.getElementById("cmp_t").value;
  var s = fmtSym(p);
  document.getElementById("cmp_p_val").textContent = s;
  document.getElementById("cmp_r_val").textContent = r.toFixed(1) + "%";
  document.getElementById("cmp_t_val").textContent = t + " yrs";

  var months = t * 12;
  var mr = r / 12 / 100;
  var lumpsum = p * months; // same total money

  // SIP final value
  var sipFinal = p * (((Math.pow(1+mr, months)-1)/mr)*(1+mr));
  var sipGains = sipFinal - lumpsum;

  // Lump sum final value (invest total upfront)
  var lsFinal = lumpsum * Math.pow(1 + r/100, t);
  var lsGains = lsFinal - lumpsum;

  document.getElementById("cmp_sip_corpus").textContent = fmtSym(sipFinal);
  document.getElementById("cmp_sip_detail").textContent = "Invested " + fmtSym(lumpsum) + " · Gains " + fmtSym(sipGains);
  document.getElementById("cmp_ls_corpus").textContent = fmtSym(lsFinal);
  document.getElementById("cmp_ls_detail").textContent = "Invested " + fmtSym(lumpsum) + " · Gains " + fmtSym(lsGains);

  // Winner badges
  var sipWins = sipFinal >= lsFinal;
  document.getElementById("cmp_sip_winner").textContent = sipWins ? "🏆 WINNER" : "";
  document.getElementById("cmp_ls_winner").textContent = !sipWins ? "🏆 WINNER" : "";
  document.getElementById("cmp_sip_box").style.borderColor = sipWins ? "rgba(201,168,76,.6)" : "rgba(201,168,76,.25)";
  document.getElementById("cmp_ls_box").style.borderColor = !sipWins ? "rgba(201,168,76,.6)" : "rgba(201,168,76,.25)";

  // Verdict
  var diff = Math.abs(sipFinal - lsFinal);
  var winner = sipWins ? "SIP" : "Lump Sum";
  var loser = sipWins ? "Lump Sum" : "SIP";
  document.getElementById("cmp_verdict").innerHTML =
    "<strong style='color:var(--gold-light)'>" + winner + " wins</strong> by <strong style='color:#4ade80'>" + fmtSym(diff) + "</strong> over " + t + " years.<br><br>" +
    "With the same total capital of <strong>" + fmtSym(lumpsum) + "</strong>, " + winner.toLowerCase() + " delivers " + fmtSym(sipWins ? sipFinal : lsFinal) + " vs " + loser.toLowerCase() + "'s " + fmtSym(sipWins ? lsFinal : sipFinal) + ".<br><br>" +
    (sipWins
      ? "SIP wins here because spreading investments over " + t + " years means early months benefit from compounding AND you reduce timing risk. The monthly compounding frequency of SIP also adds up significantly over long periods."
      : "Lump sum wins here because investing the full capital upfront means every rupee compounds for the entire " + t + " years. In steadily rising markets, more time in the market always wins.");

  // Chart
  var labels = [], sipData = [], lsData = [];
  for (var y = 1; y <= t; y++) {
    labels.push("Yr " + y);
    var m2 = y * 12;
    var mr2 = r / 12 / 100;
    var sipY = p * (((Math.pow(1+mr2,m2)-1)/mr2)*(1+mr2));
    var lsY = lumpsum * Math.pow(1+r/100, y);
    sipData.push(Math.round(sipY));
    lsData.push(Math.round(lsY));
  }

  if (cmpChart) { try { cmpChart.destroy(); } catch(e) {} }
  var ctx = document.getElementById("cmpChart").getContext("2d");
  cmpChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        { label: "SIP", data: sipData, borderColor: "#C9A84C", backgroundColor: "rgba(201,168,76,.1)", borderWidth: 2, pointRadius: 0, fill: true, tension: 0.4 },
        { label: "Lump Sum", data: lsData, borderColor: "#6366f1", backgroundColor: "rgba(99,102,241,.08)", borderWidth: 2, pointRadius: 0, fill: true, tension: 0.4 }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: "#9090A8", font: { size: 11 } } },
        tooltip: { callbacks: { label: function(c){ return " " + c.dataset.label + ": " + fmtSym(c.raw); } } }
      },
      scales: {
        x: { ticks: { color: "#9090A8", font: { size: 9 } }, grid: { color: "rgba(255,255,255,.04)" } },
        y: { ticks: { color: "#9090A8", font: { size: 9 }, callback: function(v){ return fmtSym(v); } }, grid: { color: "rgba(255,255,255,.04)" } }
      }
    }
  });
}
</script>


<script>
// ============================================================
// NEW CALCULATORS — MoneyVeda additions (safe, isolated block)
// ============================================================

function calcPPF(){
  var y=+document.getElementById('ppf_y').value;
  var t=+document.getElementById('ppf_t').value;
  document.getElementById('v_ppf_y').textContent=fmtSym(y);
  document.getElementById('v_ppf_t').textContent=t;
  var rate=0.071,balance=0,totalInv=0,rows='';
  for(var yr=1;yr<=t;yr++){
    var interest=Math.round((balance+y)*rate);
    balance=balance+y+interest; totalInv+=y;
    rows+='<tr><td><span class="badge-gold">'+yr+'</span></td><td class="mono">'+fmtSym(y)+'</td><td class="mono" style="color:#4ade80;">'+fmtSym(interest)+'</td><td class="mono" style="color:var(--gold-light);">'+fmtSym(balance)+'</td></tr>';
  }
  document.getElementById('ppf_maturity').textContent=fmtSym(balance);
  document.getElementById('ppf_invested').textContent=fmtSym(totalInv);
  document.getElementById('ppf_interest').textContent=fmtSym(balance-totalInv);
  document.getElementById('ppf_tbody').innerHTML=rows;
  document.getElementById('ppf_tax').textContent=fmtSym(Math.min(y,150000)*0.30)+'/yr saved';
}

function calcEPF(){
  var sal=+document.getElementById('epf_sal').value;
  var age=+document.getElementById('epf_age').value;
  var grow=+document.getElementById('epf_grow').value/100;
  document.getElementById('v_epf_sal').textContent=fmtSym(sal);
  document.getElementById('v_epf_age').textContent=age;
  document.getElementById('v_epf_grow').textContent=Math.round(grow*100);
  var rate=0.0825,years=58-age,empTotal=0,erTotal=0,balance=0,curSal=sal;
  for(var yr=1;yr<=years;yr++){
    var ec=curSal*12*0.12, er=curSal*12*0.0367;
    var contrib=ec+er, int=(balance+contrib)*rate;
    balance+=contrib+int; empTotal+=ec; erTotal+=er; curSal*=(1+grow);
  }
  document.getElementById('epf_corpus').textContent=fmtSym(balance);
  document.getElementById('epf_employee').textContent=fmtSym(empTotal);
  document.getElementById('epf_employer').textContent=fmtSym(erTotal);
  var rc=document.getElementById('epf_result_card');
  if(rc) rc.innerHTML='<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;"><div style="text-align:center;padding:16px;background:rgba(201,168,76,.08);border:1px solid rgba(201,168,76,.2);border-radius:12px;"><div style="font-size:9px;color:var(--muted);text-transform:uppercase;margin-bottom:6px;">Years to Retire</div><div style="font-size:1.8rem;font-weight:800;color:var(--gold-light);font-family:Playfair Display,serif;">'+years+'</div></div><div style="text-align:center;padding:16px;background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.15);border-radius:12px;"><div style="font-size:9px;color:var(--muted);text-transform:uppercase;margin-bottom:6px;">Monthly Deduction Now</div><div style="font-size:1.8rem;font-weight:800;color:#4ade80;font-family:Playfair Display,serif;">'+fmtSym(sal*0.12)+'</div></div></div><div style="margin-top:12px;font-size:11px;color:var(--muted);padding:10px;background:rgba(255,255,255,.03);border-radius:8px;">💡 Consider VPF to invest more at the same guaranteed 8.25% rate. EPF interest is tax-free up to ₹2.5L/yr contribution.</div>';
}

function calcNPS(){
  var p=+document.getElementById('nps_p').value;
  var age=+document.getElementById('nps_age').value;
  var eq=+document.getElementById('nps_eq').value/100;
  document.getElementById('v_nps_p').textContent=fmtSym(p);
  document.getElementById('v_nps_age').textContent=age;
  document.getElementById('v_nps_eq').textContent=Math.round(eq*100);
  var debt=0.75-eq, ret=eq*0.11+debt*0.07+(0.25-debt)*0.09;
  var years=60-age, months=years*12, mr=ret/12;
  var corpus=p*(((Math.pow(1+mr,months)-1)/mr)*(1+mr));
  var lumpsum=corpus*0.60, pension=corpus*0.40*0.06/12;
  document.getElementById('nps_corpus').textContent=fmtSym(corpus);
  document.getElementById('nps_lumpsum').textContent=fmtSym(lumpsum);
  document.getElementById('nps_pension').textContent=fmtSym(pension)+'/mo';
  document.getElementById('nps_tax').textContent=fmtSym(Math.min(p*12,50000)*0.30)+'/yr';
  var alloc=document.getElementById('nps_alloc');
  if(alloc) alloc.innerHTML='<div style="margin-bottom:8px;font-size:11px;"><div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;"><span style="width:70px;color:var(--muted);font-size:11px;">Equity</span><div style="flex:1;height:7px;background:var(--dark4);border-radius:4px;overflow:hidden;"><div style="width:'+Math.round(eq*100)+'%;height:100%;background:var(--gold);border-radius:4px;"></div></div><span style="width:36px;color:var(--gold-light);font-size:11px;">'+Math.round(eq*100)+'%</span></div><div style="display:flex;align-items:center;gap:8px;"><span style="width:70px;color:var(--muted);font-size:11px;">Debt</span><div style="flex:1;height:7px;background:var(--dark4);border-radius:4px;overflow:hidden;"><div style="width:'+Math.round((1-eq)*100)+'%;height:100%;background:#6366f1;border-radius:4px;"></div></div><span style="width:36px;color:#a5b4fc;font-size:11px;">'+Math.round((1-eq)*100)+'%</span></div></div><div style="font-size:11px;color:var(--muted);">Blended return: <strong style="color:var(--gold-light);">'+(ret*100).toFixed(2)+'%</strong> · '+(years)+' years to age 60</div>';
}

function calcStepSIP(){
  var p=+document.getElementById('ss_p').value;
  var step=+document.getElementById('ss_step').value/100;
  var r=+document.getElementById('ss_r').value;
  var t=+document.getElementById('ss_t').value;
  document.getElementById('v_ss_p').textContent=fmtSym(p);
  document.getElementById('v_ss_step').textContent=Math.round(step*100);
  document.getElementById('v_ss_r').textContent=r.toFixed(1);
  document.getElementById('v_ss_t').textContent=t;
  var mr=r/12/100, stepCorpus=0, flatCorpus=0, cur=p, rows='';
  for(var y=1;y<=t;y++){
    for(var m=0;m<12;m++){
      stepCorpus=stepCorpus*(1+mr)+cur;
      flatCorpus=flatCorpus*(1+mr)+p;
    }
    rows+='<tr><td><span class="badge-gold">'+y+'</span></td><td class="mono">'+fmtSym(cur)+'</td><td class="mono" style="color:var(--gold-light);">'+fmtSym(stepCorpus)+'</td><td class="mono" style="color:var(--muted);">'+fmtSym(flatCorpus)+'</td><td class="mono" style="color:#4ade80;">+'+fmtSym(stepCorpus-flatCorpus)+'</td></tr>';
    cur=cur*(1+step);
  }
  document.getElementById('ss_corpus').textContent=fmtSym(stepCorpus);
  document.getElementById('ss_flat').textContent=fmtSym(flatCorpus);
  document.getElementById('ss_extra').textContent='+'+fmtSym(stepCorpus-flatCorpus);
  document.getElementById('ss_tbody').innerHTML=rows;
}

function calcSSA(){
  var age=+document.getElementById('ssa_age').value;
  var dep=+document.getElementById('ssa_dep').value;
  document.getElementById('v_ssa_age').textContent=age;
  document.getElementById('v_ssa_dep').textContent=fmtSym(dep);
  var rate=0.082, totalYears=21-age, depositYears=15, balance=0, totalInv=0, rows='';
  for(var yr=1;yr<=totalYears;yr++){
    var depositing=(yr<=depositYears), deposit=depositing?dep:0;
    var interest=Math.round((balance+deposit)*rate);
    balance+=deposit+interest; if(depositing) totalInv+=dep;
    rows+='<tr><td><span class="badge-gold">'+yr+'</span></td><td class="mono">'+(depositing?fmtSym(dep):'—')+'</td><td class="mono" style="color:#f472b6;">'+fmtSym(interest)+'</td><td class="mono" style="color:var(--gold-light);">'+fmtSym(balance)+'</td></tr>';
  }
  document.getElementById('ssa_maturity').textContent=fmtSym(balance);
  document.getElementById('ssa_invested').textContent=fmtSym(totalInv);
  document.getElementById('ssa_interest').textContent=fmtSym(balance-totalInv);
  document.getElementById('ssa_tbody').innerHTML=rows;
}

function calcCrorepati(){
  var target=+document.getElementById('cr_target').value;
  var t=+document.getElementById('cr_t').value;
  var r=+document.getElementById('cr_r').value;
  document.getElementById('v_cr_target').textContent=fmtSym(target);
  document.getElementById('v_cr_t').textContent=t;
  document.getElementById('v_cr_r').textContent=r.toFixed(1);
  document.getElementById('cr_target_label').textContent=fmtSym(target);
  document.getElementById('cr_t_label').textContent=t+' years';
  var mr=r/12/100, months=t*12;
  var monthly=target*mr/(((Math.pow(1+mr,months)-1))*(1+mr));
  document.getElementById('cr_monthly').textContent=fmtSym(monthly);
  document.getElementById('cr_verdict').innerHTML='<b>'+fmtSym(target)+'</b> in <b>'+t+' yrs</b> at '+r+'% → invest <b>'+fmtSym(monthly)+'/mo</b> ('+fmtSym(monthly/30)+'/day). Start earlier = invest less.';
}

function setCrorepatiTarget(val){
  var el=document.getElementById('cr_target');
  if(el){el.value=val; calcCrorepati();}
}

var _currentHabit='coffee';
function setHabit(type, monthly){
  _currentHabit=type;
  ['coffee','swiggy','cigarette','ott','custom'].forEach(function(h){
    var el=document.getElementById('hp-'+h);
    if(el){el.style.background='transparent';el.style.borderColor='rgba(255,255,255,.1)';el.style.color='var(--muted)';}
  });
  var active=document.getElementById('hp-'+type);
  if(active){active.style.background='rgba(201,168,76,.12)';active.style.borderColor='rgba(201,168,76,.4)';active.style.color='var(--gold-light)';}
  if(monthly>0){var el=document.getElementById('hab_p');if(el)el.value=monthly;}
  calcHabit();
}

function calcHabit(){
  var p=+document.getElementById('hab_p').value;
  var t=+document.getElementById('hab_t').value;
  var r=+document.getElementById('hab_r').value;
  document.getElementById('v_hab_p').textContent=fmtSym(p);
  document.getElementById('v_hab_t').textContent=t;
  document.getElementById('v_hab_r').textContent=r.toFixed(1);
  var spent=p*12*t, mr=r/12/100, months=t*12;
  var corpus=p*(((Math.pow(1+mr,months)-1)/mr)*(1+mr));
  var names={coffee:'Daily Coffee',swiggy:'Food Delivery',cigarette:'Cigarettes',ott:'OTT Subscriptions',custom:'This Habit'};
  var name=names[_currentHabit]||'This Habit';
  document.getElementById('hab_spent').textContent=fmtSym(spent);
  document.getElementById('hab_spent_sub').textContent='Spent on '+name+' over '+t+' years';
  document.getElementById('hab_corpus').textContent=fmtSym(corpus);
  document.getElementById('hab_corpus_sub').textContent='At '+r+'% SIP returns · Gains: '+fmtSym(corpus-spent);
  document.getElementById('hab_verdict').innerHTML='Your '+name+' habit costs '+fmtSym(p)+'/month. Over '+t+' years you spend '+fmtSym(spent)+' — gone forever. Invest that same '+fmtSym(p)+'/month at '+r+'% returns and you would have '+fmtSym(corpus)+' — a '+((corpus/spent).toFixed(1))+'x multiplier.';
}

function renderContact(){
  // Contact page is static HTML — nothing dynamic needed
}

function submitContact(){
  var name    = document.getElementById('ct_name').value.trim();
  var email   = document.getElementById('ct_email').value.trim();
  var topic   = document.getElementById('ct_topic').value;
  var msg     = document.getElementById('ct_message').value.trim();
  var errEl   = document.getElementById('ct_error');
  var sucEl   = document.getElementById('ct_success');
  var btn     = document.querySelector('[onclick="submitContact()"]');
  errEl.style.display='none';
  sucEl.style.display='none';

  // Validation
  if(!name)  { errEl.textContent='Please enter your name.'; errEl.style.display='block'; document.getElementById('ct_name').focus(); return; }
  if(!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { errEl.textContent='Please enter a valid email address.'; errEl.style.display='block'; document.getElementById('ct_email').focus(); return; }
  if(!topic) { errEl.textContent='Please select a topic.'; errEl.style.display='block'; return; }
  if(msg.length < 10) { errEl.textContent='Message too short — please add more detail (min 10 characters).'; errEl.style.display='block'; document.getElementById('ct_message').focus(); return; }

  // Show loading state on button
  if(btn){ btn.textContent='Sending…'; btn.disabled=true; btn.style.opacity='0.7'; }

  // Simulate submission (replace with real API call when ready)
  setTimeout(function(){
    // Reset button
    if(btn){ btn.textContent='Send Message →'; btn.disabled=false; btn.style.opacity='1'; }
    // Show success
    sucEl.textContent = '✅ Thank you, ' + name + '! Your message has been received. We\'ll get back to you soon.';
    sucEl.style.display = 'block';
    // Clear form
    document.getElementById('ct_name').value    = '';
    document.getElementById('ct_email').value   = '';
    document.getElementById('ct_topic').value   = '';
    document.getElementById('ct_message').value = '';
  }, 800);
}

// Extend shareResult for new tabs
var _origShareResult = shareResult;
function shareResult(tab){
  var url='https://moneyveda.org';
  if(tab==='crorepati'){
    var m=document.getElementById('cr_monthly').textContent;
    var tgt=document.getElementById('v_cr_target').textContent;
    var yrs=document.getElementById('v_cr_t').textContent;
    var text='🏆 I calculated my goal on MoneyVeda!\nTarget: '+tgt+' in '+yrs+' years\nMonthly SIP needed: '+m+'\nCalculate yours 👉 '+url+' #MoneyVeda';
    if(navigator.share) navigator.share({title:'MoneyVeda',text:text,url:url}).catch(function(){});
    else if(navigator.clipboard) navigator.clipboard.writeText(text).then(function(){showToast('Copied to clipboard!');});
    return;
  }
  if(tab==='habit'){
    var spent=document.getElementById('hab_spent').textContent;
    var corpus=document.getElementById('hab_corpus').textContent;
    var p=document.getElementById('v_hab_p').textContent;
    var t=document.getElementById('v_hab_t').textContent;
    var text='😱 My daily habit will cost me '+spent+' over '+t+' years!\nIf I invested '+p+'/month instead: '+corpus+'\nCalculate yours 👉 '+url+' #MoneyVeda';
    if(navigator.share) navigator.share({title:'MoneyVeda',text:text,url:url}).catch(function(){});
    else if(navigator.clipboard) navigator.clipboard.writeText(text).then(function(){showToast('Copied to clipboard!');});
    return;
  }
  _origShareResult(tab);
}


// ============================================================
// MARKET PULSE — India RSS News via /api/news
// ============================================================
var _newsCache = null;
var _newsCacheTime = 0;
var _newsFetching = false;
var NEWS_CACHE_MS = 30 * 60 * 1000; // 30 min client-side cache

function fetchNews(forceRefresh) {
  // Only show for India
  var strip = document.getElementById('news-strip');
  if (!strip) return;
  if (currentMode !== 'india') { strip.style.display = 'none'; return; }
  strip.style.display = 'block';

  // Use client cache if fresh
  if (!forceRefresh && _newsCache && (Date.now() - _newsCacheTime) < NEWS_CACHE_MS) {
    renderNews(_newsCache);
    return;
  }
  if (_newsFetching) return;
  _newsFetching = true;

  // Set live dot to pulsing orange (fetching)
  var dot = document.getElementById('news-live-dot');
  if (dot) { dot.style.background = '#f59e0b'; }

  fetch('/api/news?region=india')
    .then(function(res) { return res.json(); })
    .then(function(data) {
      _newsFetching = false;
      if (data && data.articles && data.articles.length > 0) {
        _newsCache = data.articles;
        _newsCacheTime = Date.now();
        renderNews(data.articles);
        if (dot) dot.style.background = '#4ade80';
        var upd = document.getElementById('news-updated');
        if (upd) upd.textContent = 'Updated ' + new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
      } else {
        renderNewsError();
      }
    })
    .catch(function(err) {
      _newsFetching = false;
      console.warn('News fetch failed:', err.message);
      renderNewsError();
      if (dot) dot.style.background = '#ef4444';
    });
}

function renderNews(articles) {
  var grid = document.getElementById('news-grid');
  if (!grid) return;
  // Show max 4 cards in the strip
  var shown = articles.slice(0, 4);
  grid.innerHTML = shown.map(function(a) {
    var badgeStyle = 'background:' + (a.color ? a.color+'22' : 'rgba(201,168,76,.12)') + ';color:' + (a.color || 'var(--gold-light)') + ';border:1px solid ' + (a.color ? a.color+'44' : 'rgba(201,168,76,.25)') + ';';
    // Truncate title to 80 chars
    var title = a.title.length > 85 ? a.title.slice(0, 82) + '…' : a.title;
    return '<a href="' + a.link + '" target="_blank" rel="noopener noreferrer" class="news-card">' +
      '<div class="news-card-top">' +
        '<span style="font-size:13px;">' + (a.emoji || '📰') + '</span>' +
        '<span class="news-badge" style="' + badgeStyle + '">' + a.source + '</span>' +
        '<span class="news-time">' + (a.timeLabel || '') + '</span>' +
      '</div>' +
      '<div class="news-title">' + title + '</div>' +
    '</a>';
  }).join('');
}

function renderNewsError() {
  var grid = document.getElementById('news-grid');
  if (!grid) return;
  grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:16px;font-size:12px;color:var(--muted);">Unable to load news. <button onclick="fetchNews(true)" style="background:none;border:none;color:var(--gold-light);cursor:pointer;font-size:12px;text-decoration:underline;">Try again</button></div>';
}

// Auto-fetch on page load + every 30 min
setTimeout(function() { fetchNews(false); }, 1500);
setInterval(function() { fetchNews(false); }, NEWS_CACHE_MS);

// Add SEBI disclaimer to sidebar
(function(){
  var sidebarBottom=document.querySelector('#sidebar [style*="8px;color:var(--muted)"]');
  if(sidebarBottom){
    var disc=document.createElement('div');
    disc.id='sidebar-disclaimer';
    disc.style.cssText='font-size:8px;color:rgba(144,144,168,.6);margin-top:10px;line-height:1.5;border-top:1px solid rgba(255,255,255,.05);padding-top:8px;';
    disc.textContent='⚠️ For educational purposes only. Not SEBI-registered. Consult a qualified adviser before investing.';
    sidebarBottom.parentNode.appendChild(disc);
  }
})();
</script>
</body>
</html>
