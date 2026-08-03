from __future__ import annotations

import html
from typing import Any

import streamlit as st


DIFFICULTY_LABEL = {
    "easy": "Fácil",
    "medium": "Media",
    "hard": "Difícil",
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --cp-bg: #f4f4f5;
          --cp-surface: #ffffff;
          --cp-surface-soft: #fafafa;
          --cp-ink: #171717;
          --cp-ink-soft: #262626;
          --cp-muted: #5f5f67;
          --cp-border: #dfdfe3;
          --cp-border-strong: #bdbdc6;
          --cp-accent: #2f2f35;
          --cp-accent-soft: #ededf0;
          --cp-shadow: 0 10px 28px rgba(20, 20, 24, 0.06);
        }

        html, body, [class*="css"]  {
          color: var(--cp-ink);
        }

        .stApp {
          background:
            radial-gradient(circle at top left, #ffffff 0%, #f7f7f8 36%, #f1f1f3 100%);
          color: var(--cp-ink);
        }

        .block-container {
          max-width: 760px;
          padding-top: 1rem;
          padding-bottom: 5rem;
        }

        #MainMenu, footer, header { visibility: hidden; }

        h1, h2, h3, h4, h5, h6 {
          color: var(--cp-ink);
          letter-spacing: -0.03em;
        }

        p, li, label, span, div {
          color: inherit;
        }

        .cp-brand {
          display:flex;
          align-items:center;
          gap:.8rem;
          margin:.1rem 0 .8rem;
        }

        .cp-logo {
          width:46px;
          height:46px;
          border-radius:14px;
          display:grid;
          place-items:center;
          background: linear-gradient(145deg, #3a3a40, #1f1f24);
          color:#ffffff;
          font-size:1.02rem;
          font-weight:800;
          letter-spacing:-0.02em;
          box-shadow: 0 10px 20px rgba(20, 20, 24, 0.16);
        }

        .cp-brand-name {
          font-size:1.35rem;
          font-weight:850;
          color:var(--cp-ink);
          line-height:1;
        }

        .cp-brand-sub {
          font-size:.8rem;
          color:var(--cp-muted);
          margin-top:.25rem;
        }

        .cp-hero {
          padding:1.3rem;
          border-radius:24px;
          background: linear-gradient(135deg, #1d1d22 0%, #2f2f36 60%, #44444d 100%);
          border: 1px solid rgba(255,255,255,0.08);
          box-shadow: 0 18px 38px rgba(20,20,24,0.16);
          margin:.65rem 0 1rem;
        }

        .cp-hero h1 {
          color:#ffffff;
          font-size:1.62rem;
          margin:0 0 .42rem;
        }

        .cp-hero p {
          color:rgba(255,255,255,.84);
          margin:0;
          font-size:.98rem;
          line-height:1.45;
        }

        .cp-card {
          background: var(--cp-surface);
          border:1px solid var(--cp-border);
          border-radius:20px;
          padding:1rem 1.05rem;
          box-shadow: var(--cp-shadow);
          margin:.7rem 0;
        }

        .cp-kicker {
          font-size:.75rem;
          text-transform:uppercase;
          letter-spacing:.08em;
          font-weight:800;
          color:var(--cp-muted);
          margin-bottom:.35rem;
        }

        .cp-title {
          font-size:1.12rem;
          font-weight:800;
          color:var(--cp-ink);
          line-height:1.35;
        }

        .cp-muted {
          color:var(--cp-muted);
          font-size:.92rem;
          line-height:1.45;
        }

        .cp-pill {
          display:inline-flex;
          align-items:center;
          padding:.28rem .62rem;
          border-radius:999px;
          background:var(--cp-accent-soft);
          color:var(--cp-ink-soft);
          border: 1px solid var(--cp-border);
          font-weight:760;
          font-size:.75rem;
          margin-right:.38rem;
        }

        .cp-good { border-left:5px solid #2f2f35; background:#fafafa; }
        .cp-bad { border-left:5px solid #575760; background:#f8f8f9; }
        .cp-tip { border-left:5px solid #8a8a93; background:#fbfbfb; }
        .cp-source { border-left:5px solid #3d3d44; background:#f7f7f8; }

        div[data-testid="stRadio"] > label { display:none; }

        div[role="radiogroup"] {
          gap: .15rem;
        }

        div[role="radiogroup"] label {
          background: var(--cp-surface);
          border:1px solid var(--cp-border);
          border-radius:14px;
          padding:.74rem .78rem;
          margin:.25rem 0;
          transition:.15s ease;
          color: var(--cp-ink) !important;
        }

        div[role="radiogroup"] label:hover {
          border-color: var(--cp-border-strong);
          background:#f7f7f8;
        }

        div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {
          border-color: #3a3a41;
          background:#f1f1f3;
          box-shadow: inset 0 0 0 1px #3a3a41;
        }

        div[role="radiogroup"] p {
          color: var(--cp-ink) !important;
        }

        div[data-testid="stButton"] button,
        div[data-testid="stFormSubmitButton"] button,
        div[data-testid="stDownloadButton"] button {
          min-height:46px;
          border-radius:14px;
          font-weight:780;
          border:1px solid var(--cp-border);
          background: var(--cp-surface);
          color: var(--cp-ink);
          box-shadow: none;
        }

        div[data-testid="stButton"] button:hover,
        div[data-testid="stFormSubmitButton"] button:hover,
        div[data-testid="stDownloadButton"] button:hover {
          border-color: var(--cp-border-strong);
          background: #f6f6f7;
          color: var(--cp-ink);
        }

        div[data-testid="stButton"] button[kind="primary"],
        div[data-testid="stFormSubmitButton"] button[kind="primary"] {
          background: var(--cp-accent);
          border-color: var(--cp-accent);
          color: #ffffff;
        }

        div[data-testid="stButton"] button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
          background: #1f1f24;
          border-color: #1f1f24;
          color: #ffffff;
        }

        div[data-testid="stMetric"] {
          background: var(--cp-surface);
          border:1px solid var(--cp-border);
          border-radius:16px;
          padding:.72rem .82rem;
          box-shadow: var(--cp-shadow);
        }

        div[data-testid="stMetricLabel"] * {
          color: var(--cp-muted) !important;
        }

        div[data-testid="stMetricValue"] {
          font-size:1.35rem;
          color: var(--cp-ink) !important;
        }

        div[data-baseweb="tab-list"] {
          gap: .35rem;
        }

        button[data-baseweb="tab"] {
          background: var(--cp-surface);
          border:1px solid var(--cp-border) !important;
          border-radius: 12px;
          color: var(--cp-ink) !important;
          padding: .45rem .8rem;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
          background: #ececef;
          border-color: var(--cp-border-strong) !important;
          color: var(--cp-ink) !important;
        }

        div[data-testid="stTextInput"] input {
          background: #ffffff;
          color: var(--cp-ink);
          border-radius: 12px;
        }

        div[data-testid="stTextInput"] label,
        div[data-testid="stCaptionContainer"],
        div[data-testid="stMarkdownContainer"],
        div[data-testid="stExpander"] details summary,
        .stAlert,
        .stInfo,
        .stWarning,
        .stError,
        .stSuccess {
          color: var(--cp-ink);
        }

        .stProgress > div > div > div > div {
          background: linear-gradient(90deg, #2c2c33 0%, #5b5b66 100%);
        }

        .cp-calendar-title {
          min-height:46px;
          display:flex;
          align-items:center;
          justify-content:center;
          color:var(--cp-ink);
          font-weight:820;
          text-align:center;
        }

        .cp-calendar-grid {
          display:grid;
          grid-template-columns:repeat(7, minmax(0, 1fr));
          gap:.34rem;
          margin-top:.65rem;
          background:var(--cp-surface);
          border:1px solid var(--cp-border);
          border-radius:18px;
          padding:.75rem;
          box-shadow:var(--cp-shadow);
        }

        .cp-weekday {
          display:grid;
          place-items:center;
          min-height:28px;
          color:var(--cp-muted);
          font-size:.72rem;
          font-weight:800;
          text-transform:uppercase;
        }

        .cp-day {
          aspect-ratio:1;
          border-radius:10px;
          display:grid;
          place-items:center;
          font-size:.76rem;
          font-weight:800;
          border:1px solid var(--cp-border);
          position:relative;
        }

        .cp-day.blank {
          background:transparent;
          border-color:transparent;
        }

        .cp-day.empty {
          background:#f2f2f4;
          color:#74747d;
        }

        .cp-day.done {
          background:#2f2f35;
          color:#ffffff;
          border-color:#2f2f35;
        }

        .cp-day.started {
          background:#d7d7dc;
          color:#202025;
          border-color:#a6a6ae;
        }

        .cp-day.practice {
          background:#ffffff;
          color:#2f2f35;
          border:2px solid #6e6e77;
        }

        .cp-day.today::after {
          content:"";
          position:absolute;
          width:5px;
          height:5px;
          border-radius:50%;
          bottom:4px;
          background:currentColor;
        }

        .cp-calendar-legend {
          display:flex;
          flex-wrap:wrap;
          gap:.65rem 1rem;
          margin:.7rem 0 .2rem;
          color:var(--cp-muted);
          font-size:.78rem;
        }

        .cp-calendar-legend span {
          display:inline-flex;
          align-items:center;
          gap:.38rem;
          color:var(--cp-muted);
        }

        .legend-box {
          width:11px;
          height:11px;
          border-radius:3px;
          display:inline-block;
          border:1px solid var(--cp-border-strong);
        }

        .legend-box.done { background:#2f2f35; border-color:#2f2f35; }
        .legend-box.started { background:#d7d7dc; border-color:#a6a6ae; }
        .legend-box.practice { background:#ffffff; border:2px solid #6e6e77; }

        .st-emotion-cache-1wmy9hl, .st-emotion-cache-ue6h4q, .st-emotion-cache-16txtl3 {
          color: var(--cp-ink);
        }

        @media (max-width: 520px) {
          .block-container {
            padding-left:.85rem;
            padding-right:.85rem;
            padding-top:.55rem;
          }
          .cp-hero { border-radius:20px; padding:1.05rem; }
          .cp-hero h1 { font-size:1.42rem; }
          .cp-card { border-radius:17px; }
          div[data-testid="stHorizontalBlock"] { gap:.45rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def brand() -> None:
    st.markdown(
        """
        <div class="cp-brand">
          <div class="cp-logo">C+</div>
          <div>
            <div class="cp-brand-name">Conduce+</div>
            <div class="cp-brand-sub">Aprendizaje seguro para licencia clase B</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(content: str, extra_class: str = "") -> None:
    st.markdown(f'<div class="cp-card {extra_class}">{content}</div>', unsafe_allow_html=True)


def question_header(question: dict[str, Any], current: int, total: int) -> None:
    difficulty = DIFFICULTY_LABEL[question["difficulty"]]
    prompt = html.escape(question["prompt"])
    topic = html.escape(question["topic"])
    st.markdown(
        f"""
        <div class="cp-card">
          <div class="cp-kicker">Pregunta {current} de {total}</div>
          <div style="margin-bottom:.7rem">
            <span class="cp-pill">{topic}</span>
            <span class="cp-pill">{difficulty}</span>
          </div>
          <div class="cp-title">{prompt}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def feedback_panel(
    question: dict[str, Any],
    selected_id: str,
    *,
    displayed_options: list[dict[str, Any]] | None = None,
) -> None:
    is_correct = selected_id == question["correct_id"]
    selected = next(o for o in question["options"] if o["id"] == selected_id)
    correct = next(o for o in question["options"] if o["id"] == question["correct_id"])
    source = question["source"]

    if is_correct:
        card(
            "<div class='cp-kicker'>Resultado</div>"
            "<div class='cp-title'>Respuesta correcta. Elegiste la alternativa más segura.</div>",
            "cp-good",
        )
    else:
        card(
            "<div class='cp-kicker'>Resultado</div>"
            f"<div class='cp-title'>La mejor respuesta era: {html.escape(correct['text'])}</div>"
            f"<p class='cp-muted'>{html.escape(selected['feedback'])}</p>",
            "cp-bad",
        )

    card(
        "<div class='cp-kicker'>Explicación</div>"
        f"<div>{html.escape(question['explanation'])}</div>",
    )
    card(
        "<div class='cp-kicker'>Consejo práctico</div>"
        f"<div>{html.escape(question['tip'])}</div>",
        "cp-tip",
    )
    card(
        "<div class='cp-kicker'>Fuente oficial</div>"
        f"<div><strong>{html.escape(source['document'])}</strong></div>"
        f"<div class='cp-muted'>Capítulo: {html.escape(source['chapter'])}<br>"
        f"Sección: {html.escape(source['section'])}<br>Página {source['page']}</div>",
        "cp-source",
    )

    if displayed_options is None:
        displayed_options = [
            {
                "display_id": chr(ord("A") + index),
                "option_id": option["id"],
                "text": option["text"],
                "feedback": option["feedback"],
            }
            for index, option in enumerate(question["options"])
        ]

    with st.expander("Revisar todas las alternativas"):
        for option in displayed_options:
            status = (
                "Respuesta correcta"
                if option["option_id"] == question["correct_id"]
                else "Por qué no"
            )
            st.markdown(
                f"**{html.escape(option['display_id'])}. {html.escape(option['text'])} — {status}**"
            )
            st.caption(option["feedback"])
