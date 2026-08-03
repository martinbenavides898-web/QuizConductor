from __future__ import annotations

import time
from collections import defaultdict
from datetime import date

import altair as alt
import pandas as pd
import streamlit as st
from PIL import Image

from app.analytics import (
    activity_day_sets,
    build_accuracy_trend,
    month_weeks,
    move_month,
)
from app.config import (
    APP_NAME,
    APP_VERSION,
    DAILY_MIX,
    ICON_PATH,
    OFFICIAL_BOOK_PATH,
)
from app.data import load_questions, question_map
from app.database import (
    DatabaseConfigurationError,
    DatabaseError,
    DatabaseUnavailableError,
    create_session,
    get_attempts_for_session,
    get_daily_session,
    get_or_create_single_profile,
    get_session,
    get_user_attempts,
    get_user_sessions,
    healthcheck,
    mark_completed,
    save_attempt,
)
from app.engine import (
    build_session_summary,
    calculate_streak,
    displayed_options,
    local_date_key,
    now_local,
    ordered_options,
    select_questions,
    stable_seed,
    xp_from_data,
)
from app.ui import brand, card, feedback_panel, inject_css, question_header


PAGE_ICON = Image.open(ICON_PATH) if ICON_PATH.exists() else None
st.set_page_config(
    page_title=f"{APP_NAME} · Licencia Clase B",
    page_icon=PAGE_ICON,
    layout="centered",
    initial_sidebar_state="collapsed",
)

inject_css()
QUESTIONS = load_questions()
QUESTIONS_BY_ID = question_map()
MONTH_NAMES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)
WEEKDAY_NAMES = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")


def go_to(page: str) -> None:
    st.session_state["pending_nav"] = page
    st.rerun()


def prepare_navigation() -> str:
    if "pending_nav" in st.session_state:
        st.session_state["main_nav"] = st.session_state.pop("pending_nav")
    return st.radio(
        "Navegación",
        ["Inicio", "Desafío", "Progreso", "Fuente"],
        horizontal=True,
        key="main_nav",
        label_visibility="collapsed",
    )


def create_new_session(profile: dict, mode: str) -> str:
    profile_id = str(profile["id"])
    attempts = get_user_attempts(profile_id)
    date_key = local_date_key()
    seed = (
        stable_seed(profile_id, date_key, "daily")
        if mode == "daily"
        else stable_seed(profile_id, str(time.time_ns()), "practice")
    )
    question_ids = select_questions(QUESTIONS, attempts, seed=seed, mix=DAILY_MIX)
    expected_total = sum(DAILY_MIX.values())
    if len(question_ids) != expected_total:
        raise DatabaseError(
            f"El banco no pudo generar las {expected_total} preguntas requeridas."
        )

    session_id = create_session(
        profile_id=profile_id,
        mode=mode,
        date_key=date_key,
        question_ids=question_ids,
        created_at=now_local().isoformat(),
    )
    st.session_state["active_session_id"] = session_id
    st.session_state.pop("feedback_question_id", None)
    return session_id


def get_or_create_daily(profile: dict) -> str:
    profile_id = str(profile["id"])
    existing = get_daily_session(profile_id, local_date_key())
    if existing:
        st.session_state["active_session_id"] = str(existing["id"])
        return str(existing["id"])
    return create_new_session(profile, "daily")


def session_progress(session: dict, attempts: list[dict]) -> tuple[int, int]:
    valid_question_ids = {str(question_id) for question_id in session["question_ids"]}
    answered = {
        str(attempt["question_id"])
        for attempt in attempts
        if str(attempt["question_id"]) in valid_question_ids
    }
    total = len(valid_question_ids)
    return len(answered), total


def first_unanswered(session: dict, attempts: list[dict]) -> str | None:
    answered = {str(attempt["question_id"]) for attempt in attempts}
    for question_id in session["question_ids"]:
        if question_id not in answered:
            return str(question_id)
    return None


def render_home(profile: dict) -> None:
    profile_id = str(profile["id"])
    attempts = get_user_attempts(profile_id)
    sessions = get_user_sessions(profile_id)
    streak = calculate_streak(sessions)
    xp = xp_from_data(attempts, sessions)
    level = xp // 200 + 1
    daily = get_daily_session(profile_id, local_date_key())
    daily_attempts = get_attempts_for_session(str(daily["id"])) if daily else []
    daily_done = bool(daily and daily["status"] == "completed")
    total_questions = len(daily["question_ids"]) if daily else sum(DAILY_MIX.values())

    st.markdown(
        """
        <div class="cp-hero">
          <h1>Conduce con calma y criterio</h1>
          <p>Entrena decisiones seguras, comprende tus errores y refuerza lo que más necesitas.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Racha", f"{streak} días")
    c2.metric("Nivel", level)
    c3.metric("XP", xp)

    if daily_done:
        card(
            "<div class='cp-kicker'>Desafío diario</div>"
            "<div class='cp-title'>Completado por hoy</div>"
            "<p class='cp-muted'>Puedes revisar el resultado o iniciar una práctica adicional.</p>",
            "cp-good",
        )
        col1, col2 = st.columns(2)
        if col1.button("Ver análisis", type="primary", use_container_width=True):
            st.session_state["active_session_id"] = str(daily["id"])
            go_to("Desafío")
        if col2.button("Práctica nueva", use_container_width=True):
            create_new_session(profile, "practice")
            go_to("Desafío")
    else:
        answered = len(daily_attempts)
        title = "Continuar desafío" if answered else "Comenzar desafío"
        card(
            "<div class='cp-kicker'>Desafío diario</div>"
            f"<div class='cp-title'>{answered}/{total_questions} preguntas completadas</div>"
            "<p class='cp-muted'>La selección combina dificultad, repaso y temas que necesitan refuerzo.</p>",
        )
        st.progress(answered / total_questions if total_questions else 0.0)
        if st.button(title, type="primary", use_container_width=True):
            get_or_create_daily(profile)
            go_to("Desafío")

    st.markdown("### Tu entrenamiento")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Práctica rápida", use_container_width=True):
            create_new_session(profile, "practice")
            go_to("Desafío")
    with col2:
        if st.button("Ver progreso", use_container_width=True):
            go_to("Progreso")

    if attempts:
        overall = sum(int(a["is_correct"]) for a in attempts) / len(attempts) * 100
        card(
            "<div class='cp-kicker'>Resumen acumulado</div>"
            f"<div class='cp-title'>{overall:.0f}% de precisión en {len(attempts)} respuestas</div>"
            "<p class='cp-muted'>El historial completo se conserva en Supabase y alimenta la selección adaptativa.</p>",
        )
    else:
        card(
            "<div class='cp-kicker'>Cómo funciona</div>"
            "<div class='cp-title'>Responde, entiende y vuelve a aplicar</div>"
            "<p class='cp-muted'>Cada corrección explica la decisión, muestra la fuente oficial y entrega un consejo práctico.</p>",
        )


def render_quiz(profile: dict) -> None:
    profile_id = str(profile["id"])
    session_id = st.session_state.get("active_session_id")
    session = get_session(str(session_id)) if session_id else None
    if not session:
        session_id = get_or_create_daily(profile)
        session = get_session(session_id)

    if not session:
        raise DatabaseUnavailableError("No se pudo recuperar la sesión activa.")
    if str(session["profile_id"]) != profile_id:
        st.session_state.pop("active_session_id", None)
        st.error("La sesión activa no corresponde al progreso guardado.")
        return

    attempts = get_attempts_for_session(str(session["id"]))
    answered_count, total = session_progress(session, attempts)
    mode_label = "Desafío diario" if session["mode"] == "daily" else "Práctica rápida"

    st.markdown(f"<div class='cp-kicker'>{mode_label}</div>", unsafe_allow_html=True)
    st.progress(answered_count / total if total else 0.0)

    feedback_question_id = st.session_state.get("feedback_question_id")
    if feedback_question_id:
        feedback_attempt = next(
            (a for a in attempts if a["question_id"] == feedback_question_id), None
        )
        if feedback_attempt:
            question = QUESTIONS_BY_ID[feedback_question_id]
            question_index = session["question_ids"].index(feedback_question_id) + 1
            display_rows = displayed_options(question, str(session["id"]))
            question_header(question, question_index, total)
            feedback_panel(
                question,
                str(feedback_attempt["selected_id"]),
                displayed_options=display_rows,
            )
            is_final_answer = answered_count >= total
            button_label = "Ver resultados" if is_final_answer else "Siguiente pregunta"
            if st.button(button_label, type="primary", use_container_width=True):
                st.session_state.pop("feedback_question_id", None)
                st.rerun()
            return
        st.session_state.pop("feedback_question_id", None)

    question_id = first_unanswered(session, attempts)
    if question_id is None:
        if session["status"] != "completed":
            mark_completed(str(session["id"]), now_local().isoformat())
            session = get_session(str(session["id"])) or session
        render_results(profile, session, attempts)
        return

    question = QUESTIONS_BY_ID[question_id]
    current = session["question_ids"].index(question_id) + 1
    question_header(question, current, total)

    start_key = f"started_{session['id']}_{question_id}"
    if start_key not in st.session_state:
        st.session_state[start_key] = time.monotonic()

    rows = displayed_options(question, str(session["id"]))
    label_to_option_id = {
        f"{row['display_id']}. {row['text']}": row["option_id"] for row in rows
    }
    selected_label = st.radio(
        "Selecciona una alternativa",
        list(label_to_option_id),
        index=None,
        key=f"answer_{session['id']}_{question_id}",
        label_visibility="collapsed",
    )

    if st.button(
        "Confirmar respuesta",
        type="primary",
        use_container_width=True,
        disabled=selected_label is None,
    ):
        selected_id = label_to_option_id[selected_label]
        elapsed_ms = int((time.monotonic() - st.session_state[start_key]) * 1000)
        inserted = save_attempt(
            session_id=str(session["id"]),
            profile_id=profile_id,
            question_id=question_id,
            topic=question["topic"],
            difficulty=question["difficulty"],
            selected_id=selected_id,
            correct_id=question["correct_id"],
            response_ms=elapsed_ms,
            answered_at=now_local().isoformat(),
        )
        if inserted:
            st.session_state["feedback_question_id"] = question_id
        st.rerun()

    st.caption("La respuesta queda guardada al confirmar y después no puede modificarse.")


def render_results(profile: dict, session: dict, attempts: list[dict]) -> None:
    summary = build_session_summary(attempts, QUESTIONS_BY_ID)
    accuracy = summary["accuracy"]
    if accuracy >= 80:
        headline = "Muy buena jornada"
    elif accuracy >= 60:
        headline = "Buen avance, todavía hay que reforzar"
    else:
        headline = "Hoy encontramos puntos importantes para trabajar"

    st.markdown(
        f"""
        <div class="cp-hero">
          <h1>{headline}</h1>
          <p>Respondiste correctamente {summary['correct']} de {summary['total']} preguntas.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Precisión", f"{accuracy:.0f}%")
    c2.metric("Correctas", f"{summary['correct']}/{summary['total']}")
    c3.metric("Tiempo medio", f"{summary['avg_seconds']:.0f} s")

    if summary["weakest"]:
        weak = summary["weakest"]
        card(
            "<div class='cp-kicker'>Análisis de tu sesión</div>"
            f"<div class='cp-title'>Tu principal refuerzo será: {weak['topic']}</div>"
            f"<p class='cp-muted'>Lograste {weak['correct']} de {weak['total']} en este tema. "
            "Las próximas selecciones aumentarán gradualmente su presencia sin abandonar el resto del temario.</p>",
            "cp-source",
        )
    if summary["strongest"] and summary["strongest"] != summary["weakest"]:
        strong = summary["strongest"]
        card(
            "<div class='cp-kicker'>Punto fuerte</div>"
            f"<div class='cp-title'>{strong['topic']}</div>"
            f"<p class='cp-muted'>{strong['correct']} de {strong['total']} respuestas correctas.</p>",
            "cp-good",
        )

    rows = [
        {"Tema": item["topic"], "Precisión": round(item["accuracy"], 1)}
        for item in summary["topics"]
    ]
    if rows:
        st.markdown("### Rendimiento por tema")
        st.bar_chart(pd.DataFrame(rows).set_index("Tema"), horizontal=True)

    col1, col2 = st.columns(2)
    if col1.button("Nueva práctica", type="primary", use_container_width=True):
        create_new_session(profile, "practice")
        st.rerun()
    if col2.button("Volver al inicio", use_container_width=True):
        go_to("Inicio")


def render_accuracy_evolution(attempts: list[dict]) -> None:
    trend = build_accuracy_trend(attempts, today=now_local().date(), window_days=30)
    if trend.empty:
        st.caption("Todavía no hay datos suficientes para construir la evolución.")
        return

    cumulative_data = trend.dropna(subset=["Precisión acumulada"])
    daily_data = trend.dropna(subset=["Precisión diaria"])
    cumulative_long = cumulative_data.rename(columns={"Precisión acumulada": "Valor"})
    daily_long = daily_data.rename(columns={"Precisión diaria": "Valor"})

    cumulative_line = alt.Chart(cumulative_long).mark_line(
        point=True,
        strokeWidth=3,
        color="#2f2f35",
    ).encode(
        x=alt.X("Fecha:T", title=None, axis=alt.Axis(format="%d %b", labelAngle=0)),
        y=alt.Y("Valor:Q", title="Precisión (%)", scale=alt.Scale(domain=[0, 100])),
        tooltip=[
            alt.Tooltip("Fecha:T", title="Fecha", format="%d-%m-%Y"),
            alt.Tooltip("Valor:Q", title="Precisión acumulada", format=".0f"),
        ],
    )

    daily_points = alt.Chart(daily_long).mark_line(
        point=True,
        strokeWidth=2,
        strokeDash=[5, 4],
        color="#92929b",
    ).encode(
        x=alt.X("Fecha:T", title=None, axis=alt.Axis(format="%d %b", labelAngle=0)),
        y=alt.Y("Valor:Q", title="Precisión (%)", scale=alt.Scale(domain=[0, 100])),
        tooltip=[
            alt.Tooltip("Fecha:T", title="Fecha", format="%d-%m-%Y"),
            alt.Tooltip("Valor:Q", title="Precisión diaria", format=".0f"),
            alt.Tooltip("Respuestas:Q", title="Respuestas"),
        ],
    )

    chart = (cumulative_line + daily_points).properties(height=280)
    st.altair_chart(chart, use_container_width=True)
    st.caption(
        "Línea continua: precisión acumulada. Línea segmentada: precisión de cada día con actividad."
    )


def render_activity_calendar(sessions: list[dict], attempts: list[dict]) -> None:
    today = now_local().date()
    if "calendar_year" not in st.session_state or "calendar_month" not in st.session_state:
        st.session_state["calendar_year"] = today.year
        st.session_state["calendar_month"] = today.month

    year = int(st.session_state["calendar_year"])
    month = int(st.session_state["calendar_month"])

    prev_col, title_col, today_col, next_col = st.columns([0.7, 2.4, 0.8, 0.7])
    if prev_col.button("‹", use_container_width=True, help="Mes anterior"):
        year, month = move_month(year, month, -1)
        st.session_state["calendar_year"] = year
        st.session_state["calendar_month"] = month
        st.rerun()
    title_col.markdown(
        f"<div class='cp-calendar-title'>{MONTH_NAMES[month - 1].capitalize()} {year}</div>",
        unsafe_allow_html=True,
    )
    if today_col.button("Hoy", use_container_width=True):
        st.session_state["calendar_year"] = today.year
        st.session_state["calendar_month"] = today.month
        st.rerun()
    if next_col.button("›", use_container_width=True, help="Mes siguiente"):
        year, month = move_month(year, month, 1)
        st.session_state["calendar_year"] = year
        st.session_state["calendar_month"] = month
        st.rerun()

    completed_days, started_daily_days, activity_days = activity_day_sets(
        sessions, attempts
    )
    weeks = month_weeks(year, month)
    headers = "".join(f"<div class='cp-weekday'>{name}</div>" for name in WEEKDAY_NAMES)
    cells: list[str] = []
    for week in weeks:
        for day_number in week:
            if day_number == 0:
                cells.append("<div class='cp-day blank'></div>")
                continue
            current = date(year, month, day_number)
            classes = ["cp-day"]
            title = "Sin actividad"
            if current in completed_days:
                classes.append("done")
                title = "Desafío diario completado"
            elif current in started_daily_days:
                classes.append("started")
                title = "Desafío diario iniciado"
            elif current in activity_days:
                classes.append("practice")
                title = "Práctica registrada"
            else:
                classes.append("empty")
            if current == today:
                classes.append("today")
            cells.append(
                f"<div class='{' '.join(classes)}' title='{title}'>{day_number}</div>"
            )

    st.markdown(
        f"<div class='cp-calendar-grid'>{headers}{''.join(cells)}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="cp-calendar-legend">
          <span><i class="legend-box done"></i> Desafío completado</span>
          <span><i class="legend-box started"></i> Desafío iniciado</span>
          <span><i class="legend-box practice"></i> Práctica</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_progress(profile: dict) -> None:
    profile_id = str(profile["id"])
    attempts = get_user_attempts(profile_id)
    sessions = get_user_sessions(profile_id)
    if not attempts:
        card(
            "<div class='cp-kicker'>Progreso</div>"
            "<div class='cp-title'>Aún no hay respuestas registradas</div>"
            "<p class='cp-muted'>Completa tu primer desafío para activar estadísticas y recomendaciones.</p>",
        )
        if st.button("Comenzar ahora", type="primary", use_container_width=True):
            get_or_create_daily(profile)
            go_to("Desafío")
        return

    streak = calculate_streak(sessions)
    xp = xp_from_data(attempts, sessions)
    correct = sum(int(a["is_correct"]) for a in attempts)
    accuracy = correct / len(attempts) * 100
    avg_seconds = sum(int(a["response_ms"]) for a in attempts) / len(attempts) / 1000

    st.markdown("## Tu progreso")
    c1, c2 = st.columns(2)
    c1.metric("Precisión general", f"{accuracy:.0f}%")
    c2.metric("Preguntas respondidas", len(attempts))
    c3, c4 = st.columns(2)
    c3.metric("Racha actual", f"{streak} días")
    c4.metric("Tiempo promedio", f"{avg_seconds:.0f} s")

    topic_rows = defaultdict(lambda: {"correct": 0, "total": 0})
    for attempt in attempts:
        topic_rows[str(attempt["topic"])]["total"] += 1
        topic_rows[str(attempt["topic"])]["correct"] += int(attempt["is_correct"])
    topic_df = pd.DataFrame(
        [
            {
                "Tema": topic,
                "Precisión": round(values["correct"] / values["total"] * 100, 1),
                "Respuestas": values["total"],
            }
            for topic, values in topic_rows.items()
        ]
    ).sort_values(["Precisión", "Respuestas"], ascending=[True, False])

    st.markdown("### Precisión por tema")
    st.bar_chart(topic_df.set_index("Tema")[["Precisión"]], horizontal=True)

    weakest = topic_df.iloc[0]
    strongest = topic_df.sort_values("Precisión", ascending=False).iloc[0]
    col1, col2 = st.columns(2)
    with col1:
        card(
            "<div class='cp-kicker'>A reforzar</div>"
            f"<div class='cp-title'>{weakest['Tema']}</div>"
            f"<p class='cp-muted'>{weakest['Precisión']:.0f}% de precisión en {int(weakest['Respuestas'])} respuestas.</p>",
            "cp-tip",
        )
    with col2:
        card(
            "<div class='cp-kicker'>Punto fuerte</div>"
            f"<div class='cp-title'>{strongest['Tema']}</div>"
            f"<p class='cp-muted'>{strongest['Precisión']:.0f}% de precisión en {int(strongest['Respuestas'])} respuestas.</p>",
            "cp-good",
        )

    st.markdown("### Evolución")
    render_accuracy_evolution(attempts)

    st.markdown("### Calendario de actividad")
    render_activity_calendar(sessions, attempts)

    st.markdown("### Logros")
    achievements = [
        ("Primer recorrido", len(attempts) >= 10, "Completa 10 preguntas"),
        ("Conductor constante", streak >= 3, "Mantén una racha de 3 días"),
        ("Criterio en desarrollo", len(attempts) >= 30, "Responde 30 preguntas"),
        (
            "Precisión segura",
            len(attempts) >= 20 and accuracy >= 80,
            "Supera 80% con al menos 20 respuestas",
        ),
    ]
    for title, unlocked, description in achievements:
        status = "Disponible" if unlocked else "Pendiente"
        st.markdown(f"**{title}** — {description} ({status})")

    st.caption(f"Experiencia acumulada: {xp} XP · Nivel {xp // 200 + 1}")


def render_source() -> None:
    st.markdown("## Fuente oficial")
    card(
        "<div class='cp-kicker'>Contenido utilizado</div>"
        "<div class='cp-title'>Libro para la Conducción en Chile</div>"
        "<p class='cp-muted'>Automovilistas · Licencia Clase B · CONASET · Chile, julio de 2024.</p>",
        "cp-source",
    )
    st.markdown(
        "El banco inicial contiene **42 preguntas trazables** al documento oficial. "
        "Cada corrección muestra capítulo, sección y página. No se utilizan bancos de preguntas de terceros."
    )
    st.info(
        "La aplicación entrena comprensión y toma de decisiones seguras; no afirma reproducir las preguntas exactas del examen municipal."
    )
    if OFFICIAL_BOOK_PATH.exists():
        with OFFICIAL_BOOK_PATH.open("rb") as file_handle:
            st.download_button(
                "Descargar libro oficial incluido",
                data=file_handle.read(),
                file_name="Libro_para_la_Conduccion_en_Chile_Clase_B_CONASET_2024.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
    st.markdown("### Cobertura actual")
    topic_counts = pd.Series([q["topic"] for q in QUESTIONS]).value_counts()
    st.dataframe(
        topic_counts.rename_axis("Tema").reset_index(name="Preguntas"),
        hide_index=True,
        use_container_width=True,
    )
    st.caption(f"Conduce+ v{APP_VERSION} · Banco inicial sujeto a ampliación y revisión editorial.")


def render_configuration_error(error: Exception) -> None:
    brand()
    st.error(str(error))
    st.markdown("### Configuración necesaria")
    st.markdown(
        """
1. Ejecuta `supabase/schema.sql` en el **SQL Editor** de tu proyecto Supabase.
2. En Streamlit Cloud abre **App settings → Secrets**.
3. Pega tus credenciales con este formato:
        """
    )
    st.code(
        '[supabase]\nurl = "https://TU-PROYECTO.supabase.co"\nsecret_key = "sb_secret_REEMPLAZAR"',
        language="toml",
    )
    st.warning("Nunca subas la Secret key a GitHub.")


def render_database_error(error: Exception) -> None:
    brand()
    st.error(str(error))
    st.info(
        "La operación se detuvo para evitar perder o duplicar progreso. "
        "Cuando Supabase vuelva a responder, reintenta la conexión."
    )
    if st.button("Reintentar conexión", type="primary", use_container_width=True):
        st.rerun()


def main() -> None:
    healthcheck()

    if "profile" not in st.session_state:
        profile = get_or_create_single_profile("Perfil principal")
        st.session_state["profile"] = {
            "id": str(profile["id"]),
            "display_name": str(profile["display_name"]),
        }

    profile = st.session_state["profile"]
    brand()
    nav = prepare_navigation()

    if nav == "Inicio":
        render_home(profile)
    elif nav == "Desafío":
        render_quiz(profile)
    elif nav == "Progreso":
        render_progress(profile)
    elif nav == "Fuente":
        render_source()

    st.markdown("---")
    st.caption(f"Conduce+ v{APP_VERSION} · Progreso sincronizado con Supabase")


try:
    main()
except DatabaseConfigurationError as exc:
    render_configuration_error(exc)
except DatabaseUnavailableError as exc:
    render_database_error(exc)
except DatabaseError as exc:
    render_database_error(exc)
