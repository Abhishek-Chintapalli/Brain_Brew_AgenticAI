import streamlit as st

# ---------- Tiny inline SVGs for the landing page (no extra deps) ----------
PROF_SVG = """
<div class='art'>
  <svg viewBox="0 0 180 120" xmlns="http://www.w3.org/2000/svg" class="float">
    <defs>
      <linearGradient id="gradA" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#38bdf8"/>
        <stop offset="100%" stop-color="#10b981"/>
      </linearGradient>
    </defs>
    <rect x="8" y="18" rx="10" ry="10" width="120" height="70"
          fill="none" stroke="url(#gradA)" stroke-width="3"/>
    <line x1="20" y1="40" x2="116" y2="40" stroke="#38bdf8" stroke-width="2" opacity="0.6"/>
    <line x1="20" y1="55" x2="100" y2="55" stroke="#38bdf8" stroke-width="2" opacity="0.45"/>
    <line x1="20" y1="70" x2="90"  y2="70" stroke="#38bdf8" stroke-width="2" opacity="0.35"/>
    <circle cx="145" cy="38" r="11" fill="#c7f9cc" stroke="#10b981" stroke-width="2"/>
    <polygon points="132,28 158,28 145,20" fill="#0ea5e9"/>
    <rect x="138" y="52" width="16" height="20" rx="8" fill="#10b981" opacity="0.7"/>
    <line x1="120" y1="48" x2="142" y2="58" stroke="#10b981" stroke-width="3"/>
  </svg>
</div>
"""

STUDENT_SVG = """
<div class='art'>
  <svg viewBox="0 0 180 120" xmlns="http://www.w3.org/2000/svg" class="float">
    <defs>
      <linearGradient id="gradB" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#10b981"/>
        <stop offset="100%" stop-color="#38bdf8"/>
      </linearGradient>
    </defs>
    <rect x="30" y="45" width="120" height="35" rx="6" fill="none" stroke="url(#gradB)" stroke-width="3"/>
    <rect x="25" y="80" width="130" height="10" rx="5" fill="#0ea5e9" opacity="0.4"/>
    <circle cx="90" cy="30" r="11" fill="#bae6fd" stroke="#38bdf8" stroke-width="2"/>
    <path d="M70 50 Q90 65 110 50 L110 70 L70 70 Z" fill="#38bdf8" opacity="0.7"/>
  </svg>
</div>
"""

# Animated, crisp (vector) brain for title
BRAIN_SVG = """
<svg class="brain-svg" viewBox="0 0 210 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Brain Brew logo">
  <defs>
    <linearGradient id="brainGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"  stop-color="#f472b6"/>
      <stop offset="100%" stop-color="#db2777"/>
    </linearGradient>
    <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <path d="M78 24c-16 0-30 11-30 27 0 4 1 7 2 10-6 2-11 9-11 16 0 11 9 20 20 20h44c7 0 13-2 18-6l2-1
           c3 4 8 7 14 7 11 0 20-9 20-20 0-6-3-11-7-15 1-3 2-6 2-10 0-16-14-27-30-27-6 0-11 1-16 4-5-3-10-5-16-5
           -6 0-11 2-16 5-5-3-10-5-16-5z"
        fill="url(#brainGrad)" filter="url(#softGlow)" opacity="0.95"/>
  <path d="M64 50c6-6 14-9 22-9m-38 31c8-5 18-8 28-8m16-26c8 0 16 3 22 9m-12 16c8 0 16 3 22 9m-74-6c6 0 12 2 18 6
           m16-8c6 0 12 2 18 6"
        fill="none" stroke="#ffffff" stroke-opacity=".7" stroke-width="2" stroke-linecap="round"/>
  <circle cx="155" cy="32" r="5" fill="#fff" opacity=".9">
    <animate attributeName="r" values="4;6;4" dur="2.8s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values=".6;1;.6" dur="2.8s" repeatCount="indefinite"/>
  </circle>
</svg>
"""

# ============================ THEME ============================
def inject_theme():
    st.markdown(
        """
        <style>
        :root{
            --accent:#10b981; --bg:#0f172a; --panel:#111827; --border:#1f2937; --txt:#e5e7eb; --muted:#9ca3af;
            --hover1:#38bdf8; --hover2:#0ea5e9; --hoverOutline:rgba(56,189,248,.35);
        }
        html, body, [data-testid="stAppViewContainer"]{background:var(--bg); color:var(--txt);}
        section[data-testid="stSidebar"]{background:var(--panel); border-right:1px solid var(--border);}

        .stButton>button{
            background:linear-gradient(90deg,var(--accent),#059669);
            border:0; color:#fff !important; border-radius:12px;
            padding:.55rem 1rem; font-weight:600;
            transition:transform .15s ease, box-shadow .15s ease, background .15s ease;
        }
        .stButton>button:hover{
            background:linear-gradient(90deg,var(--hover1),var(--hover2));
            transform:translateY(-1px);
            box-shadow:0 6px 20px rgba(14,165,233,.24), 0 0 0 2px var(--hoverOutline) inset;
            color:#fff !important;
        }
        .stButton>button:focus:not(:hover){
            background:linear-gradient(90deg,var(--accent),#059669) !important;
            box-shadow:0 0 0 2px var(--hoverOutline) inset;
            color:#fff !important; outline:0;
        }
        .stButton>button:focus-visible{ outline:2px solid var(--hover1); outline-offset:2px; color:#fff !important; }
        .stButton>button:active{
            background:linear-gradient(90deg,var(--hover1),var(--hover2)) !important;
            transform:translateY(0); color:#fff !important;
        }
        .stButton>button * { color:#fff !important; }

        .card{background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:12px; margin-bottom:10px;}
        .chip{display:inline-block; padding:.1rem .5rem; border-radius:999px; background:rgba(16,185,129,.15);
              color:var(--accent); border:1px solid rgba(16,185,129,.35); font-size:.8rem; font-weight:700}
        input[type="radio"], input[type="checkbox"]{accent-color:var(--accent);}
        input[type="radio"]:focus-visible, input[type="checkbox"]:focus-visible{ outline:2px solid var(--hover1); outline-offset:2px; }
        [data-testid="stMetricValue"]{color:var(--accent)!important;}

        /* Hero */
        .hero { display:flex; flex-direction:column; align-items:center; text-align:center; margin: 6px 0 16px; }
        .hero .brand { font-size: clamp(44px, 7vw, 84px); font-weight: 900; letter-spacing: .4px; line-height: 1.04;
                       text-wrap: balance; }
        .hero .brand .accent { color: var(--accent); }
        .hero .tagline { margin-top: .35rem; font-size: clamp(13px, 1.6vw, 18px); opacity: .9; color: var(--muted); }

        /* Landing art */
        .art { width: 100%; max-width: 420px; margin: 2px auto 8px; }
        .art svg { width: 100%; height: 120px; display: block; }
        .float { animation: floaty 3.6s ease-in-out infinite; }

        /* Brain + title animations and gradient text */
        .logo-wrap { width: 120px; height: 120px; margin: 0 auto 6px; }
        .brain-svg { width: 100%; height: 100%; display: block; }
        .float-title { animation: floatyTitle 5.2s ease-in-out infinite; will-change: transform; }
        .float-brain { animation: floatyBrain 4.8s ease-in-out infinite, gentleTilt 12s ease-in-out infinite alternate; will-change: transform; }
        .gradient-text{
          background: linear-gradient(90deg, #93c5fd, #38bdf8, #10b981, #93c5fd);
          -webkit-background-clip: text; background-clip: text; color: transparent;
          background-size: 300% 100%;
          animation: gradientShift 7s ease-in-out infinite;
          filter: drop-shadow(0 2px 0 rgba(0,0,0,.08));
        }

        a, a:visited{ color:#93c5fd; } a:hover{ color:#bae6fd; text-decoration:underline; }

        @keyframes bb-pop { 0%{transform:translateY(10px) scale(.98); opacity:0;} 100%{transform:translateY(0) scale(1); opacity:1;} }
        @keyframes bb-float { 0%{transform:translateY(6px); opacity:0;} 100%{transform:translateY(0); opacity:1;} }
        @keyframes floaty { 0%,100%{transform:translateY(0px);} 50%{transform:translateY(-8px);} }
        @keyframes gradientShift { 0% { background-position: 0% 50%; } 50%{ background-position: 100% 50%; } 100%{ background-position: 0% 50%; } }
        @keyframes floatyTitle { 0%,100%{ transform: translateY(0); } 50%{ transform: translateY(-6px); } }
        @keyframes floatyBrain { 0%,100%{ transform: translateY(0); } 50%{ transform: translateY(-8px); } }
        @keyframes gentleTilt   { 0%{ transform: rotate(-2deg); } 100%{ transform: rotate(2deg); } }
        </style>
        """,
        unsafe_allow_html=True,
    )
