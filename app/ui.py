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
          --cp-blue: #1667d9;
          --cp-blue-dark: #0d3f8f;
          --cp-sky: #eaf3ff;
          --cp-ink: #152033;
          --cp-muted: #687386;
          --cp-border: #e3e8ef;
          --cp-bg: #f6f8fb;
          --cp-green: #159a62;
          --cp-red: #d5424a;
          --cp-amber: #a96305;
        }

        .stApp { background: var(--cp-bg); }
        .block-container {
          max-width: 760px;
          padding-top: 1rem;
          padding-bottom: 5.5rem;
        }
        #MainMenu, footer, header { visibility: hidden; }

        h1, h2, h3 { color: var(--cp-ink); letter-spacing: -0.035em; }
        p, li { color: var(--cp-ink); }

        .cp-brand {
          display:flex; align-items:center; gap:.72rem;
          margin:.15rem 0 .8rem;
        }
        .cp-logo {
          width:46px; height:46px; border-radius:15px;
          display:grid; place-items:center;
          background:linear-gradient(145deg,#1e7af0,#0d4fae);
          color:white; font-size:24px;
          box-shadow:0 8px 22px rgba(22,103,217,.22);
        }
        .cp-brand-name {font-size:1.35rem; font-weight:850; color:var(--cp-ink); line-height:1;}
        .cp-brand-sub {font-size:.78rem; color:var(--cp-muted); margin-top:.25rem;}

        .cp-hero {
          padding:1.25rem;
          border-radius:24px;
          background:linear-gradient(135deg,#0e4ca7 0%,#1971e6 62%,#38a0ff 100%);
          box-shadow:0 14px 38px rgba(14,76,167,.22);
          margin:.6rem 0 1rem;
        }
        .cp-hero h1 { color:white; font-size:1.65rem; margin:0 0 .45rem; }
        .cp-hero p { color:rgba(255,255,255,.86); margin:0; font-size:.98rem; }

        .cp-card {
          background:white;
          border:1px solid var(--cp-border);
          border-radius:20px;
          padding:1rem 1.05rem;
          box-shadow:0 7px 20px rgba(22,32,51,.05);
          margin:.7rem 0;
        }
        .cp-kicker {
          font-size:.75rem; text-transform:uppercase; letter-spacing:.08em;
          font-weight:800; color:var(--cp-blue); margin-bottom:.35rem;
        }
        .cp-title {font-size:1.13rem; font-weight:800; color:var(--cp-ink); line-height:1.35;}
        .cp-muted {color:var(--cp-muted); font-size:.9rem;}
        .cp-pill {
          display:inline-flex; align-items:center; gap:.3rem;
          padding:.28rem .55rem; border-radius:999px;
          background:var(--cp-sky); color:var(--cp-blue-dark);
          font-weight:750; font-size:.75rem; margin-right:.35rem;
        }
        .cp-good {border-left:5px solid var(--cp-green); background:#f3fbf7;}
        .cp-bad {border-left:5px solid var(--cp-red); background:#fff6f6;}
        .cp-tip {border-left:5px solid #f5a524; background:#fffaf0;}
        .cp-source {border-left:5px solid var(--cp-blue); background:#f5f9ff;}

        div[data-testid="stRadio"] > label { display:none; }
        div[role="radiogroup"] label {
          background:white;
          border:1px solid var(--cp-border);
          border-radius:14px;
          padding:.66rem .72rem;
          margin:.22rem 0;
          transition:.15s ease;
        }
        div[role="radiogroup"] label:hover { border-color:#82b5f4; background:#f8fbff; }

        div[data-testid="stButton"] button,
        div[data-testid="stFormSubmitButton"] button,
        div[data-testid="stDownloadButton"] button {
          min-height:46px;
          border-radius:14px;
          font-weight:780;
          border:1px solid #dce3ec;
        }
        div[data-testid="stButton"] button[kind="primary"],
        div[data-testid="stFormSubmitButton"] button[kind="primary"] {
          background:var(--cp-blue); border-color:var(--cp-blue);
        }

        div[data-testid="stMetric"] {
          background:white; border:1px solid var(--cp-border); border-radius:16px;
          padding:.72rem .82rem;
        }
        div[data-testid="stMetricValue"] {font-size:1.35rem;}

        .cp-calendar {display:grid; grid-template-columns:repeat(7,1fr); gap:.35rem; margin-top:.5rem;}
        .cp-day {aspect-ratio:1; border-radius:10px; display:grid; place-items:center; font-size:.72rem; font-weight:800;}
        .cp-day.done {background:#dff7eb; color:#08764a;}
        .cp-day.empty {background:#eef1f5; color:#8c95a3;}

        @media (max-width: 520px) {
          .block-container { padding-left:.85rem; padding-right:.85rem; padding-top:.55rem; }
          .cp-hero {border-radius:20px; padding:1.05rem;}
          .cp-hero h1 {font-size:1.45rem;}
          .cp-card {border-radius:17px;}
          div[data-testid="stHorizontalBlock"] {gap:.45rem;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def brand() -> None:
    st.markdown(
        """
        <div class="cp-brand">
          <div class="cp-logo">🚘</div>
          <div>
            <div class="cp-brand-name">Conduce+</div>
            <div class="cp-brand-sub">Aprende a decidir con seguridad</div>
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


def feedback_panel(question: dict[str, Any], selected_id: str) -> None:
    is_correct = selected_id == question["correct_id"]
    selected = next(o for o in question["options"] if o["id"] == selected_id)
    correct = next(o for o in question["options"] if o["id"] == question["correct_id"])
    source = question["source"]

    if is_correct:
        card("<div class='cp-kicker'>✅ Correcto</div><div class='cp-title'>Tomaste la decisión más segura.</div>", "cp-good")
    else:
        card(
            "<div class='cp-kicker'>❌ A revisar</div>"
            f"<div class='cp-title'>La respuesta correcta es: {html.escape(correct['text'])}</div>"
            f"<p class='cp-muted'>{html.escape(selected['feedback'])}</p>",
            "cp-bad",
        )

    card(
        "<div class='cp-kicker'>📖 Explicación</div>"
        f"<div>{html.escape(question['explanation'])}</div>",
    )
    card(
        "<div class='cp-kicker'>💡 Consejo práctico</div>"
        f"<div>{html.escape(question['tip'])}</div>",
        "cp-tip",
    )
    card(
        "<div class='cp-kicker'>📚 Fuente oficial</div>"
        f"<div><strong>{html.escape(source['document'])}</strong></div>"
        f"<div class='cp-muted'>Capítulo: {html.escape(source['chapter'])}<br>"
        f"Sección: {html.escape(source['section'])}<br>Página {source['page']}</div>",
        "cp-source",
    )

    with st.expander("Entender todas las alternativas"):
        for option in question["options"]:
            icon = "✅" if option["id"] == question["correct_id"] else "•"
            st.markdown(f"**{icon} {option['text']}**")
            st.caption(option["feedback"])
