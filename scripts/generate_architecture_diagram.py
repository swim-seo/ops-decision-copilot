"""
AI 운영 코파일럿 — Architecture Diagram Generator
Outputs: architecture_diagram.png (1920x1080, portfolio-ready)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.font_manager as fm

# ── 한글 지원 폰트 설정 ───────────────────────────────────────────────────────
def _set_korean_font():
    for name in ["Malgun Gothic", "NanumGothic", "AppleGothic", "UnDotum"]:
        try:
            fm.findfont(fm.FontProperties(family=name), fallback_to_default=False)
            matplotlib.rc("font", family=name)
            return name
        except Exception:
            pass
    return "sans-serif"

_FONT = _set_korean_font()
matplotlib.rcParams["axes.unicode_minus"] = False

# ── Canvas ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(20, 11.25), facecolor="#0f172a")
ax  = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 20)
ax.set_ylim(0, 11.25)
ax.axis("off")
ax.set_facecolor("#0f172a")

# ── Color Palette ─────────────────────────────────────────────────────────────
C = {
    "bg":       "#0f172a",
    "panel":    "#1e293b",
    "border":   "#334155",
    "ui":       "#2563eb",
    "ui_light": "#3b82f6",
    "llm":      "#7c3aed",
    "llm_light":"#a78bfa",
    "rag":      "#0891b2",
    "rag_light":"#22d3ee",
    "kg":       "#059669",
    "kg_light": "#34d399",
    "data":     "#d97706",
    "data_light":"#fbbf24",
    "supa":     "#10b981",
    "supa_light":"#6ee7b7",
    "white":    "#f1f5f9",
    "gray":     "#94a3b8",
    "dimgray":  "#64748b",
    "arrow":    "#475569",
    "domain1":  "#f43f5e",
    "domain2":  "#f97316",
    "domain3":  "#eab308",
    "domain4":  "#22c55e",
    "domain5":  "#06b6d4",
    "domain6":  "#8b5cf6",
}

def box(ax, x, y, w, h, color, alpha=0.18, radius=0.18, lw=1.5, border=None):
    border = border or color
    rect = FancyBboxPatch((x, y), w, h,
        boxstyle=f"round,pad=0",
        facecolor=color, alpha=alpha,
        edgecolor=border, linewidth=lw,
        zorder=2)
    ax.add_patch(rect)

def solid_box(ax, x, y, w, h, color, alpha=1.0, radius=0.12, lw=0, border=None):
    border = border or color
    rect = FancyBboxPatch((x, y), w, h,
        boxstyle=f"round,pad=0",
        facecolor=color, alpha=alpha,
        edgecolor=border, linewidth=lw,
        zorder=3)
    ax.add_patch(rect)

def label(ax, x, y, text, size=9, color="#f1f5f9", bold=False, ha="center", va="center", zorder=4):
    weight = "bold" if bold else "normal"
    ax.text(x, y, text, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, zorder=zorder,
            fontfamily=_FONT)

def arrow(ax, x1, y1, x2, y2, color="#475569", lw=1.2, style="-|>", alpha=0.7):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle=style, color=color,
                        lw=lw, alpha=alpha,
                        connectionstyle="arc3,rad=0.0"),
        zorder=5)

def dashed_arrow(ax, x1, y1, x2, y2, color="#475569", lw=1.0, alpha=0.55):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color=color,
                        lw=lw, alpha=alpha, linestyle="dashed",
                        connectionstyle="arc3,rad=0.0"),
        zorder=5)

# ═════════════════════════════════════════════════════════════════════════════
# TITLE
# ═════════════════════════════════════════════════════════════════════════════
label(ax, 10, 10.75, "AI 운영 코파일럿 (Ops Decision Copilot) — System Architecture",
      size=15, bold=True, color=C["white"])
label(ax, 10, 10.40,
      "Domain-Adaptive AI Assistant  ·  Streamlit + Claude API + ChromaDB RAG + Supabase + Knowledge Graph",
      size=9, color=C["gray"])

# ── thin separator line ───────────────────────────────────────────────────────
ax.axhline(10.2, xmin=0.02, xmax=0.98, color=C["border"], lw=0.8)

# ═════════════════════════════════════════════════════════════════════════════
# LAYER BACKGROUNDS
# ═════════════════════════════════════════════════════════════════════════════
# Layer 1 – User Interface
box(ax, 0.3, 7.8, 19.4, 2.1, C["ui"],      alpha=0.10, lw=1.5, border=C["ui"])
label(ax, 0.95, 9.6, "① UI Layer", size=7.5, color=C["ui_light"], ha="left")

# Layer 2 – Core Processing
box(ax, 0.3, 3.7, 19.4, 3.85, C["llm"], alpha=0.07, lw=1.5, border=C["llm"])
label(ax, 0.95, 7.35, "② Core Processing (modules/)", size=7.5, color=C["llm_light"], ha="left")

# Layer 3 – Data & External Services
box(ax, 0.3, 0.35, 19.4, 3.1, C["supa"], alpha=0.07, lw=1.5, border=C["supa"])
label(ax, 0.95, 3.25, "③ Data & External Services", size=7.5, color=C["supa_light"], ha="left")

# ═════════════════════════════════════════════════════════════════════════════
# LAYER 1 — STREAMLIT UI
# ═════════════════════════════════════════════════════════════════════════════
step_colors = [C["ui"], "#0369a1", C["kg"]]
step_labels = [
    ("Step 1", "도메인 설정", "Domain Select"),
    ("Step 2", "파일 업로드", "File Upload"),
    ("Step 3", "결과 / 채팅", "Results & Chat"),
]
step_x = [1.2, 5.5, 9.8]
for i, (sc, (s, k, e)) in enumerate(zip(step_colors, step_labels)):
    sx = step_x[i]
    solid_box(ax, sx, 8.15, 3.4, 1.4, sc, alpha=0.25, border=sc, lw=2)
    label(ax, sx+1.7, 9.2, s, size=9, bold=True, color=C["white"])
    label(ax, sx+1.7, 8.85, k, size=8.5, bold=True, color=C["white"])
    label(ax, sx+1.7, 8.5, e, size=7.5, color=C["gray"])

# Step arrows
for sx in [(4.6, 5.5), (8.9, 9.8)]:
    arrow(ax, sx[0], 8.85, sx[1], 8.85, color=C["ui_light"], lw=2, style="-|>")

# Step 3 sub-items
step3_items = ["KG Graph", "ERD View", "Chat Q&A", "Daily Briefing", "AI Analysis", "Query Planner"]
step3_colors = [C["kg"], C["kg"], C["ui"], C["data"], C["llm"], C["rag"]]
for j, (item, sc) in enumerate(zip(step3_items, step3_colors)):
    col = j % 3
    row = j // 3
    ix = 14.1 + col * 1.7
    iy = 9.0 - row * 0.48
    solid_box(ax, ix, iy - 0.18, 1.52, 0.32, sc, alpha=0.3, border=sc, lw=1)
    label(ax, ix + 0.76, iy - 0.02, item, size=7, color=C["white"])

label(ax, 14.95, 9.5, "Step 3 Features", size=7.5, color=C["gray"], bold=True)
solid_box(ax, 13.9, 7.85, 5.7, 1.7, C["ui"], alpha=0.08, border=C["ui"], lw=1)

# ═════════════════════════════════════════════════════════════════════════════
# LAYER 2 — CORE PROCESSING MODULES
# ═════════════════════════════════════════════════════════════════════════════
modules = [
    # (x, y, w, h, color, icon, title, subtitle)
    (0.55, 5.65, 2.9, 1.5,  C["llm"],  "[AI]", "Domain Adapter",    "DomainConfig\nClaude Analysis"),
    (3.65, 5.65, 2.9, 1.5,  C["rag"],  "[VEC]","RAG Engine",         "ChromaDB\nSemantic Search"),
    (6.75, 5.65, 2.9, 1.5,  C["kg"],   "[KG]", "Knowledge Graph",    "NetworkX\nERD + Entity Rel."),
    (9.85, 5.65, 2.9, 1.5,  C["ui"],   "[MSG]","Chat Copilot",       "Route: data|doc\n|combined"),
    (12.95,5.65, 2.9, 1.5,  C["data"], "[DAT]","Data Chat Engine",   "Pandas Analysis\nPlotly Charts"),
    (16.05,5.65, 3.0, 1.5,  C["llm"],  "[MAP]","Query Planner",      "3-pass Recommend\nRule+FK+RAG"),

    (0.55, 3.9,  2.9, 1.5,  C["rag"],  "[DOC]","Document Parser",    "PDF/DOCX/CSV\nPython AST"),
    (3.65, 3.9,  2.9, 1.5,  C["kg"],   "[TPL]","Prompt Loader",      "Domain-aware\nPrompt Templates"),
    (6.75, 3.9,  2.9, 1.5,  C["data"], "[TBL]","Data Analyst",       "CSV/Supabase\nSchema Registry"),
    (9.85, 3.9,  2.9, 1.5,  C["ui"],   "[DB]", "Supabase Client",    "REST API\nPaginated Query"),
    (12.95,3.9,  2.9, 1.5,  C["llm"],  "[BOT]","Claude Client",      "Sonnet 4.6\nRetry + Stream"),
    (16.05,3.9,  3.0, 1.5,  C["supa"], "[CFG]","Config",             "Secrets / API Keys\nPaths + Constants"),
]

for (mx, my, mw, mh, mc, icon, title, sub) in modules:
    solid_box(ax, mx, my, mw, mh, mc, alpha=0.18, border=mc, lw=1.5)
    # icon badge
    solid_box(ax, mx+0.12, my+mh-0.42, 0.55, 0.28, mc, alpha=0.7, border=mc, lw=0)
    label(ax, mx+0.395, my+mh-0.28, icon, size=6.5, bold=True, color=C["white"])
    label(ax, mx+0.82+mw/2-0.55, my+mh-0.28, title, size=8.5, bold=True, color=C["white"], ha="left")
    label(ax, mx + mw/2, my + mh*0.38, sub, size=7.2, color=C["gray"])

# ═════════════════════════════════════════════════════════════════════════════
# LAYER 3 — EXTERNAL SERVICES + DOMAIN DATA
# ═════════════════════════════════════════════════════════════════════════════
# External services
services = [
    (0.55, 0.55, 3.8, 1.8, C["llm"],  "API", "Anthropic Claude API",
     "claude-sonnet-4-6\nText Gen · Entity Extract\nDomain Analysis"),
    (4.65, 0.55, 3.8, 1.8, C["rag"],  "VDB", "ChromaDB (Vector DB)",
     "paraphrase-multilingual\nMiniLM-L12-v2 Embeddings\nLocal Persistent Store"),
    (8.75, 0.55, 3.8, 1.8, C["supa"], " PG", "Supabase PostgreSQL",
     "REST API · Upsert\nRow-Level Security\n~80,000 rows · 6 domains"),
    (12.85,0.55, 3.8, 1.8, C["kg"],   " KG", "NetworkX + PyVis",
     "Knowledge Graph Engine\nERD · Entity Relations\nInteractive HTML"),
    (16.95,0.55, 2.6, 1.8, C["data"], "PLT", "Plotly",
     "Interactive Charts\nLine · Bar · Scatter\nStream to Streamlit"),
]

for (sx, sy, sw, sh, sc, icon, title, sub) in services:
    solid_box(ax, sx, sy, sw, sh, sc, alpha=0.2, border=sc, lw=1.8)
    # icon badge
    solid_box(ax, sx+0.14, sy+sh-0.42, 0.52, 0.28, sc, alpha=0.8, border=sc, lw=0)
    label(ax, sx+0.4, sy+sh-0.28, icon, size=7, bold=True, color=C["white"])
    label(ax, sx+0.84, sy+sh-0.28, title, size=8.5, bold=True, color=C["white"], ha="left")
    for j, line in enumerate(sub.split("\n")):
        label(ax, sx+sw/2, sy+sh-0.68-j*0.3, line, size=7.2, color=C["gray"])

# Domain data pills
domains = [
    ("Beauty / 뷰티",        C["domain1"]),
    ("Supply Chain / 공급망", C["domain2"]),
    ("Energy / 에너지",       C["domain3"]),
    ("Manufacturing / 제조",  C["domain4"]),
    ("Logistics / 물류",      C["domain5"]),
    ("Finance / 금융",        C["domain6"]),
]
label(ax, 10.75, 2.72, "6 Domain Datasets  (CSV  /  Supabase)", size=7.5, color=C["gray"], bold=True)
for i, (dlabel, dc) in enumerate(domains):
    dx = 8.65 + (i % 3) * 2.15
    dy = 2.38 - (i // 3) * 0.42
    solid_box(ax, dx, dy, 2.0, 0.34, dc, alpha=0.25, border=dc, lw=1.2)
    label(ax, dx+1.0, dy+0.17, dlabel, size=7.5, color=C["white"])

# ═════════════════════════════════════════════════════════════════════════════
# DATA FLOW ARROWS
# ═════════════════════════════════════════════════════════════════════════════
# UI → Modules
arrow(ax,  3.05, 8.15,  2.0,  7.15, color=C["ui_light"],  lw=1.5, alpha=0.6)  # Step1→DomainAdapter
arrow(ax,  6.3,  8.15,  5.1,  7.15, color=C["rag_light"], lw=1.5, alpha=0.6)  # Step2→RAGEngine
arrow(ax,  6.3,  8.15,  8.2,  7.15, color=C["kg_light"],  lw=1.5, alpha=0.6)  # Step2→KG
arrow(ax, 11.35, 8.15, 11.3,  7.15, color=C["ui_light"],  lw=1.5, alpha=0.6)  # Step3→ChatCopilot

# Within Module rows (top row)
arrow(ax,  3.45, 6.42,  3.65, 6.42, color=C["llm_light"], lw=1.2, alpha=0.5)
arrow(ax,  6.55, 6.42,  6.75, 6.42, color=C["rag_light"], lw=1.2, alpha=0.5)
arrow(ax,  9.65, 6.42,  9.85, 6.42, color=C["kg_light"],  lw=1.2, alpha=0.5)
arrow(ax, 12.75, 6.42, 12.95, 6.42, color=C["ui_light"],  lw=1.2, alpha=0.5)
arrow(ax, 15.85, 6.42, 16.05, 6.42, color=C["data_light"],lw=1.2, alpha=0.5)

# Modules → External Services
arrow(ax, 13.9, 5.65, 13.9,  2.35, color=C["llm_light"], lw=1.3, alpha=0.5)  # ClaudeClient→API
arrow(ax,  5.1, 5.65,  6.55, 2.35, color=C["rag_light"], lw=1.3, alpha=0.5)  # RAG→ChromaDB
arrow(ax, 11.4, 3.9,  10.65, 2.35, color=C["supa_light"],lw=1.3, alpha=0.5)  # SupabaseClient→PG
arrow(ax,  8.2, 5.65, 14.75, 2.35, color=C["kg_light"],  lw=1.3, alpha=0.5)  # KG→NetworkX

# Domain data → Supabase
dashed_arrow(ax, 12.85, 1.45, 12.55, 1.45, color=C["supa_light"], lw=1.2, alpha=0.5)

# ═════════════════════════════════════════════════════════════════════════════
# LEGEND
# ═════════════════════════════════════════════════════════════════════════════
legend_items = [
    (C["ui"],   "UI / Workflow"),
    (C["llm"],  "LLM / AI"),
    (C["rag"],  "RAG / Vector"),
    (C["kg"],   "Knowledge Graph"),
    (C["data"], "Data Analysis"),
    (C["supa"], "Database / Config"),
]
lx = 0.55
for color, name in legend_items:
    solid_box(ax, lx, 0.12, 0.22, 0.18, color, alpha=0.8, border=color, lw=0)
    label(ax, lx + 0.28, 0.21, name, size=6.8, color=C["gray"], ha="left")
    lx += 1.62

label(ax, 19.7, 0.15, "github.com/swim-seo/ops-decision-copilot",
      size=7, color=C["dimgray"], ha="right")

# ═════════════════════════════════════════════════════════════════════════════
# SAVE
# ═════════════════════════════════════════════════════════════════════════════
for dpi, suffix in [(150, ""), (300, "_hires")]:
    out = f"architecture_diagram{suffix}.png"
    plt.savefig(out, dpi=dpi, bbox_inches="tight",
                facecolor=C["bg"], edgecolor="none")
    print(f"Saved ({dpi}dpi) → {out}")
plt.close()
