from __future__ import annotations

import html
import time
from collections import defaultdict
from datetime import timedelta
import pandas as pd
import streamlit as st

from app.config import APP_NAME, APP_VERSION, DAILY_MIX, OFFICIAL_BOOK_PATH
from app.data import load_questions, question_map
from app.database import (
    DatabaseConfigurationError,
    DatabaseError,
    DatabaseUnavailableError,
    ProfileAlreadyExistsError,
    authenticate_profile,
    create_profile,
    create_session,
    get_attempts_for_session,
    get_daily_session,
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
    local_date_key,
    now_local,
    ordered_options,
    select_questions,
    stable_seed,
    xp_from_data,
)
from app.ui import brand, card, feedback_panel, inject_css, question_header


st.set_page_config(
    page_title=f"{APP_NAME} · Licencia Clase B",
    page_icon="🚘",
    layout="centered",
    initial_sidebar_state="collapsed",
)

inject_css()
QUESTIONS = load_questions()
QUESTIONS_BY_ID = question_map()


def clean_name(value: str) -> str:
    return " ".join(value.strip().split())[:40]


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
    profile_id = profile["id"]
    attempts = get_user_attempts(profile_id)
    date_key = local_date_key()
    if mode == "daily":
        seed = stable_seed(profile_id, date_key, "daily")
    else:
        seed = stable_seed(profile_id, str(time.time_ns()), "practice")
    question_ids = select_questions(QUESTIONS, attempts, seed=seed, mix=DAILY_MIX)
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
    existing = get_daily_session(profile["id"], local_date_key())
    if existing:
        st.session_state["active_session_id"] = existing["id"]
        return existing["id"]
    return create_new_session(profile, "daily")


def session_progress(session: dict, attempts: list[dict]) -> tuple[int, int]:
    answered = {attempt["question_id"] for attempt in attempts}
    total = len(session["question_ids"])
    return len(answered), total


def first_unanswered(session: dict, attempts: list[dict]) -> str | None:
    answered = {attempt["question_id"] for attempt in attempts}
    for qid in session["question_ids"]:
        if qid not in answered:
            return qid
    return None


def _valid_pin(pin: str) -> bool:
    return pin.isdigit() and len(pin) == 6


def _start_profile_session(profile: dict) -> None:
    st.session_state["profile"] = {
        "id": str(profile["id"]),
        "display_name": str(profile["display_name"]),
    }
    st.session_state["pending_nav"] = "Inicio"
    st.session_state.pop("active_session_id", None)
    st.rerun()


def render_login() -> None:
    brand()
    st.markdown(
        """
        <div class="cp-hero">
          <h1>Aprende a conducir con criterio</h1>
          <p>Tu avance queda guardado en la nube y puedes retomarlo desde cualquier dispositivo.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_tab, register_tab = st.tabs(["Entrar", "Crear perfil"])

    with login_tab:
        with st.form("login_form"):
            name = st.text_input(
                "Nombre de usuario",
                placeholder="Ejemplo: Valentina",
                max_chars=40,
                key="login_name",
            )
            pin = st.text_input(
                "Clave de 6 dígitos",
                type="password",
                max_chars=6,
                key="login_pin",
            )
            submitted = st.form_submit_button(
                "Entrar a Conduce+", type="primary", use_container_width=True
            )
        if submitted:
            normalized = clean_name(name)
            if len(normalized) < 2 or not _valid_pin(pin):
                st.error("Escribe tu usuario y una clave numérica de 6 dígitos.")
            else:
                profile = authenticate_profile(normalized, pin)
                if profile:
                    _start_profile_session(profile)
                else:
                    st.error("Usuario o clave incorrectos.")

    with register_tab:
        st.caption("El nombre será tu identificador para recuperar el progreso.")
        with st.form("register_form"):
            new_name = st.text_input(
                "Elige un nombre de usuario",
                placeholder="Ejemplo: Valentina",
                max_chars=40,
                key="register_name",
            )
            new_pin = st.text_input(
                "Crea una clave de 6 dígitos",
                type="password",
                max_chars=6,
                key="register_pin",
            )
            confirm_pin = st.text_input(
                "Repite la clave",
                type="password",
                max_chars=6,
                key="register_pin_confirm",
            )
            registered = st.form_submit_button(
                "Crear perfil", type="primary", use_container_width=True
            )
        if registered:
            normalized = clean_name(new_name)
            if len(normalized) < 2:
                st.error("El nombre debe tener al menos 2 caracteres.")
            elif not _valid_pin(new_pin):
                st.error("La clave debe contener exactamente 6 números.")
            elif new_pin != confirm_pin:
                st.error("Las claves no coinciden.")
            else:
                try:
                    profile = create_profile(normalized, new_pin)
                except ProfileAlreadyExistsError as exc:
                    st.error(str(exc))
                else:
                    st.success("Perfil creado. Tu progreso ya está protegido en Supabase.")
                    _start_profile_session(profile)

    st.caption("No compartas tu clave. Conduce+ nunca la guarda en texto legible.")


def render_home(profile: dict) -> None:
    profile_id = profile["id"]
    user_name = profile["display_name"]
    safe_name = html.escape(user_name)
    attempts = get_user_attempts(profile_id)
    sessions = get_user_sessions(profile_id)
    streak = calculate_streak(sessions)
    xp = xp_from_data(attempts, sessions)
    level = xp // 200 + 1
    daily = get_daily_session(profile_id, local_date_key())
    daily_attempts = get_attempts_for_session(daily["id"]) if daily else []
    daily_done = bool(daily and daily["status"] == "completed")

    st.markdown(
        f"""
        <div class="cp-hero">
          <h1>Hola, {safe_name} 👋</h1>
          <p>Hoy entrenaremos decisiones seguras, no respuestas de memoria.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("🔥 Racha", f"{streak} días")
    c2.metric("⭐ Nivel", level)
    c3.metric("XP", xp)

    if daily_done:
        card(
            "<div class='cp-kicker'>Desafío diario</div>"
            "<div class='cp-title'>✅ Completado por hoy</div>"
            "<p class='cp-muted'>Puedes revisar tu análisis o continuar con una práctica nueva.</p>",
            "cp-good",
        )
        col1, col2 = st.columns(2)
        if col1.button("Ver análisis", type="primary", use_container_width=True):
            st.session_state["active_session_id"] = daily["id"]
            go_to("Desafío")
        if col2.button("Práctica nueva", use_container_width=True):
            create_new_session(profile, "practice")
            go_to("Desafío")
    else:
        answered = len(daily_attempts)
        title = "Continuar desafío" if answered else "Comenzar desafío"
        card(
            "<div class='cp-kicker'>Desafío diario</div>"
            f"<div class='cp-title'>{answered}/10 preguntas completadas</div>"
            "<p class='cp-muted'>Mezcla adaptativa: 3 fáciles, 4 medias y 3 difíciles.</p>",
        )
        st.progress(answered / 10 if answered else 0.0)
        if st.button(title, type="primary", use_container_width=True):
            get_or_create_daily(profile)
            go_to("Desafío")

    st.markdown("### Tu entrenamiento")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚡ Práctica rápida", use_container_width=True):
            create_new_session(profile, "practice")
            go_to("Desafío")
    with col2:
        if st.button("📈 Ver progreso", use_container_width=True):
            go_to("Progreso")

    if attempts:
        overall = sum(int(a["is_correct"]) for a in attempts) / len(attempts) * 100
        card(
            "<div class='cp-kicker'>Resumen acumulado</div>"
            f"<div class='cp-title'>{overall:.0f}% de precisión en {len(attempts)} respuestas</div>"
            "<p class='cp-muted'>El algoritmo prioriza temas débiles sin abandonar el repaso general.</p>",
        )
    else:
        card(
            "<div class='cp-kicker'>Cómo funciona</div>"
            "<div class='cp-title'>Responde, entiende y vuelve a aplicar</div>"
            "<p class='cp-muted'>Cada corrección explica la decisión, muestra la fuente oficial y entrega un consejo práctico.</p>",
        )


def render_quiz(profile: dict) -> None:
    profile_id = profile["id"]
    session_id = st.session_state.get("active_session_id")
    session = get_session(session_id) if session_id else None
    if not session:
        session_id = get_or_create_daily(profile)
        session = get_session(session_id)

    if str(session["profile_id"]) != profile_id:
        st.session_state.pop("active_session_id", None)
        st.error("La sesión activa no corresponde al usuario actual.")
        return

    attempts = get_attempts_for_session(session["id"])
    answered_count, total = session_progress(session, attempts)
    mode_label = "Desafío diario" if session["mode"] == "daily" else "Práctica rápida"

    st.markdown(
        f"<div class='cp-kicker'>{mode_label}</div>",
        unsafe_allow_html=True,
    )
    st.progress(answered_count / total if total else 0.0)

    feedback_qid = st.session_state.get("feedback_question_id")

    # After an answer, keep its correction visible until the user advances,
    # including the correction for the final question.
    if feedback_qid:
        feedback_attempt = next((a for a in attempts if a["question_id"] == feedback_qid), None)
        if feedback_attempt:
            feedback_question = QUESTIONS_BY_ID[feedback_qid]
            feedback_index = session["question_ids"].index(feedback_qid) + 1
            question_header(feedback_question, feedback_index, total)
            feedback_panel(feedback_question, feedback_attempt["selected_id"])
            if st.button("Siguiente pregunta", type="primary", use_container_width=True):
                st.session_state.pop("feedback_question_id", None)
                st.rerun()
            return
        st.session_state.pop("feedback_question_id", None)

    qid = first_unanswered(session, attempts)
    if qid is None:
        if session["status"] != "completed":
            mark_completed(session["id"], now_local().isoformat())
            session = get_session(session["id"])
        render_results(profile, session, attempts)
        return

    question = QUESTIONS_BY_ID[qid]
    current = session["question_ids"].index(qid) + 1
    question_header(question, current, total)

    start_key = f"started_{session['id']}_{qid}"
    if start_key not in st.session_state:
        st.session_state[start_key] = time.monotonic()

    options = ordered_options(question, session["id"])
    option_lookup = {f"{option['id']}) {option['text']}": option["id"] for option in options}
    labels = list(option_lookup)
    selected_label = st.radio(
        "Selecciona una alternativa",
        labels,
        index=None,
        key=f"answer_{session['id']}_{qid}",
        label_visibility="collapsed",
    )

    if st.button("Confirmar respuesta", type="primary", use_container_width=True, disabled=selected_label is None):
        selected_id = option_lookup[selected_label]
        elapsed_ms = int((time.monotonic() - st.session_state[start_key]) * 1000)
        inserted = save_attempt(
            session_id=session["id"],
            profile_id=profile_id,
            question_id=qid,
            topic=question["topic"],
            difficulty=question["difficulty"],
            selected_id=selected_id,
            correct_id=question["correct_id"],
            response_ms=elapsed_ms,
            answered_at=now_local().isoformat(),
        )
        if inserted:
            st.session_state["feedback_question_id"] = qid
        st.rerun()

    st.caption("Tu respuesta se guarda al confirmar. No se puede modificar después.")


def render_results(profile: dict, session: dict, attempts: list[dict]) -> None:
    summary = build_session_summary(attempts, QUESTIONS_BY_ID)
    accuracy = summary["accuracy"]
    if accuracy >= 80:
        headline = "Muy buena jornada 🚘"
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
            "<div class='cp-kicker'>📊 Análisis de tu conducción de hoy</div>"
            f"<div class='cp-title'>Tu principal refuerzo será: {weak['topic']}</div>"
            f"<p class='cp-muted'>Lograste {weak['correct']} de {weak['total']} en este tema. "
            "Los próximos desafíos aumentarán gradualmente su presencia sin abandonar el resto del temario.</p>",
            "cp-source",
        )
    if summary["strongest"] and summary["strongest"] != summary["weakest"]:
        strong = summary["strongest"]
        card(
            "<div class='cp-kicker'>💪 Punto fuerte</div>"
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
        df = pd.DataFrame(rows).set_index("Tema")
        st.bar_chart(df, horizontal=True)

    col1, col2 = st.columns(2)
    if col1.button("Nueva práctica", type="primary", use_container_width=True):
        create_new_session(profile, "practice")
        st.rerun()
    if col2.button("Ver progreso", use_container_width=True):
        go_to("Progreso")


def render_progress(profile: dict) -> None:
    profile_id = profile["id"]
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
    avg_seconds = sum(a["response_ms"] for a in attempts) / len(attempts) / 1000

    st.markdown("## Tu progreso")
    c1, c2 = st.columns(2)
    c1.metric("Precisión general", f"{accuracy:.0f}%")
    c2.metric("Preguntas respondidas", len(attempts))
    c3, c4 = st.columns(2)
    c3.metric("🔥 Racha actual", f"{streak} días")
    c4.metric("Tiempo promedio", f"{avg_seconds:.0f} s")

    topic_rows = defaultdict(lambda: {"correct": 0, "total": 0})
    for attempt in attempts:
        topic_rows[attempt["topic"]]["total"] += 1
        topic_rows[attempt["topic"]]["correct"] += int(attempt["is_correct"])
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
            f"<p class='cp-muted'>{weakest['Precisión']:.0f}% de precisión</p>",
            "cp-tip",
        )
    with col2:
        card(
            "<div class='cp-kicker'>Punto fuerte</div>"
            f"<div class='cp-title'>{strongest['Tema']}</div>"
            f"<p class='cp-muted'>{strongest['Precisión']:.0f}% de precisión</p>",
            "cp-good",
        )

    daily_rows = defaultdict(lambda: {"correct": 0, "total": 0})
    for attempt in attempts:
        day = attempt["answered_at"][:10]
        daily_rows[day]["total"] += 1
        daily_rows[day]["correct"] += int(attempt["is_correct"])
    trend_df = pd.DataFrame(
        [
            {
                "Fecha": pd.to_datetime(day),
                "Precisión": values["correct"] / values["total"] * 100,
            }
            for day, values in sorted(daily_rows.items())
        ]
    ).set_index("Fecha")
    st.markdown("### Evolución")
    st.line_chart(trend_df)

    st.markdown("### Calendario de actividad")
    completed_days = {
        s["date_key"] for s in sessions if s["mode"] == "daily" and s["status"] == "completed"
    }
    today = now_local().date()
    cells = []
    for offset in range(20, -1, -1):
        day = today - timedelta(days=offset)
        cls = "done" if day.isoformat() in completed_days else "empty"
        cells.append(f"<div class='cp-day {cls}'>{day.day}</div>")
    st.markdown(f"<div class='cp-calendar'>{''.join(cells)}</div>", unsafe_allow_html=True)

    st.markdown("### Logros")
    achievements = [
        ("Primer recorrido", len(attempts) >= 10, "Completa 10 preguntas"),
        ("Conductor constante", streak >= 3, "Mantén una racha de 3 días"),
        ("Criterio en desarrollo", len(attempts) >= 30, "Responde 30 preguntas"),
        ("Precisión segura", len(attempts) >= 20 and accuracy >= 80, "Supera 80% con 20 respuestas"),
    ]
    for title, unlocked, description in achievements:
        icon = "🏆" if unlocked else "🔒"
        st.markdown(f"{icon} **{title}** — {description}")

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
        "Este MVP no afirma reproducir las preguntas exactas del examen. Entrena la comprensión del contenido oficial y la toma de decisiones seguras."
    )
    if OFFICIAL_BOOK_PATH.exists():
        with OFFICIAL_BOOK_PATH.open("rb") as fh:
            st.download_button(
                "Descargar libro oficial incluido",
                data=fh.read(),
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
        "La aplicación detuvo la operación para evitar perder o duplicar progreso. "
        "Cuando Supabase vuelva a responder, presiona el botón y continúa."
    )
    if st.button("Reintentar conexión", type="primary", use_container_width=True):
        st.rerun()


def logout() -> None:
    st.session_state.clear()
    st.rerun()


def main() -> None:
    healthcheck()

    if "profile" not in st.session_state:
        render_login()
        return

    profile = st.session_state["profile"]
    with st.sidebar:
        st.caption(f"Sesión: {profile['display_name']}")
        if st.button("Cerrar sesión", use_container_width=True):
            logout()

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
