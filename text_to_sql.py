"""Streamlit interface for asking questions about the analytics database."""

from html import escape

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from mailer import EmailNotConfiguredError, InvalidEmailError, send_email
from mydb import NotAllowedQueryError, execute_query, get_all_schemas, get_schema, get_tables


load_dotenv()

st.set_page_config(page_title="TextToSQL", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

        :root {
            --datagpt-ink: #172033;
            --datagpt-muted: #68738a;
            --datagpt-line: #e4e8f0;
            --datagpt-surface: #ffffff;
            --datagpt-canvas: #f7f8fc;
            --datagpt-accent: #5b57e8;
        }

        .stApp {
            background: var(--datagpt-canvas);
            color: var(--datagpt-ink);
            font-family: "Manrope", "Avenir Next", "Segoe UI", sans-serif;
            font-size: 17px;
        }

        .stApp button,
        .stApp input,
        .stApp textarea,
        .stApp [data-testid="stMarkdownContainer"] {
            font-family: "Manrope", "Avenir Next", "Segoe UI", sans-serif;
        }

        .block-container {
            max-width: none;
            width: 100%;
            padding: 5.75rem 2.25rem 3rem;
        }

        /* Keep Streamlit's own toolbar readable in light and dark modes. */
        [data-testid="stHeader"] {
            background: #172033 !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.14);
        }

        [data-testid="stHeader"] button,
        [data-testid="stHeader"] a,
        [data-testid="stHeader"] [role="button"],
        [data-testid="stHeader"] [data-testid="stToolbar"] * {
            color: #f8fafc !important;
        }

        [data-testid="stHeader"] svg {
            color: #f8fafc !important;
            fill: currentColor !important;
        }

        [data-testid="stHeader"] svg path {
            stroke: currentColor !important;
        }

        [data-testid="stSelectbox"] label,
        [data-testid="stTextInput"] label,
        [data-testid="stTextArea"] label {
            color: #4b5569 !important;
            font-size: 0.92rem !important;
            font-weight: 650 !important;
        }

        [data-testid="stSelectbox"] > div > div,
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea {
            border-color: var(--datagpt-line) !important;
            border-radius: 10px !important;
            background: var(--datagpt-surface) !important;
            box-shadow: none !important;
        }

        [data-testid="stSelectbox"] [data-baseweb="select"],
        [data-testid="stSelectbox"] [data-baseweb="select"] * {
            color: var(--datagpt-ink) !important;
            opacity: 1 !important;
        }

        [data-testid="stSelectbox"] [role="combobox"],
        [data-testid="stSelectbox"] [role="combobox"] *,
        [data-testid="stSelectbox"] input,
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea {
            color: var(--datagpt-ink) !important;
            -webkit-text-fill-color: var(--datagpt-ink) !important;
            opacity: 1 !important;
        }

        [data-testid="stTextInput"] input::placeholder,
        [data-testid="stTextArea"] textarea::placeholder {
            color: #7c8799 !important;
            -webkit-text-fill-color: #7c8799 !important;
            opacity: 1 !important;
        }

        [data-testid="stSelectbox"] [data-baseweb="select"] svg {
            fill: var(--datagpt-ink) !important;
            stroke: var(--datagpt-ink) !important;
        }

        [data-testid="stTextArea"] textarea {
            min-height: 104px !important;
            padding: 1rem !important;
            font-size: 1.05rem !important;
            line-height: 1.55 !important;
        }

        [data-testid="stButton"] > button {
            min-height: 42px;
            border-radius: 9px;
            font-size: 0.94rem;
            font-weight: 700;
        }

        [data-testid="stButton"] > button[kind="primary"] {
            border: 0;
            background: var(--datagpt-accent);
        }

        [data-testid="stButton"] > button[kind="primary"]:disabled {
            border: 1px solid #d9dee8;
            color: #8993a5;
            background: #e8ebf1;
            opacity: 1;
        }

        [data-testid="stButton"] > button[kind="secondary"] {
            min-height: 32px;
            padding: 0.25rem 0.7rem;
            border-color: var(--datagpt-line);
            border-radius: 999px;
            color: #505d73;
            background: var(--datagpt-surface);
            font-size: 0.84rem;
            font-weight: 600;
        }

        [data-testid="stExpander"] {
            border: 0 !important;
            border-radius: 9px;
            background: transparent;
        }

        .st-key-email_report_panel [data-testid="stExpander"] {
            border: 1px solid var(--datagpt-line) !important;
            border-radius: 10px;
            background: var(--datagpt-surface);
        }

        .st-key-email_report_panel [data-testid="stExpander"] summary {
            min-height: 46px;
            color: var(--datagpt-ink) !important;
            font-size: 0.94rem;
            font-weight: 750;
        }

        .st-key-email_report_panel [data-testid="stExpander"] summary * {
            color: var(--datagpt-ink) !important;
            -webkit-text-fill-color: var(--datagpt-ink) !important;
        }

        .brand-lockup {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 2.25rem;
        }

        .brand-mark {
            display: flex;
            align-items: end;
            gap: 3px;
            width: 36px;
            height: 36px;
            padding: 6px;
            border-radius: 10px;
            background: #eef0ff;
        }

        .brand-mark span { width: 6px; border-radius: 3px 3px 1px 1px; }
        .brand-mark span:nth-child(1) { height: 14px; background: #2cb66a; }
        .brand-mark span:nth-child(2) { height: 23px; background: #5b57e8; }
        .brand-mark span:nth-child(3) { height: 18px; background: #f36d56; }

        .brand-name { color: var(--datagpt-ink); font-size: 2.05rem; font-weight: 800; letter-spacing: -0.06em; white-space: nowrap; }
        .brand-tagline { margin-top: 3px; color: var(--datagpt-muted); font-size: 0.96rem; }

        .sidebar-shell {
            padding: 0.2rem 0 0.7rem;
        }
        .sidebar-brand { display: flex; align-items: center; gap: 0.6rem; margin: 0 0 1.25rem; padding: 0.25rem 0.2rem; }
        .sidebar-mark { display: flex; align-items: end; gap: 2px; width: 26px; height: 26px; padding: 4px; border-radius: 7px; background: #eef0ff; }
        .sidebar-mark span { width: 4px; border-radius: 2px 2px 1px 1px; }
        .sidebar-mark span:nth-child(1) { height: 10px; background: #2cb66a; }
        .sidebar-mark span:nth-child(2) { height: 17px; background: #5b57e8; }
        .sidebar-mark span:nth-child(3) { height: 13px; background: #f36d56; }
        .sidebar-workspace { color: #ffffff; font-size: 0.88rem; font-weight: 800; letter-spacing: -0.02em; white-space: nowrap; }
        .sidebar-caption { margin-top: 0.05rem; color: #aeb9cc; font-size: 0.68rem; font-weight: 600; }
        .sidebar-section { margin: 0.45rem 0 0.45rem; color: #92a1ba; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
        .st-key-sidebar_panel {
            min-height: calc(100vh - 9rem);
            padding: 0.8rem;
            border-radius: 14px;
            background: #172033;
            box-shadow: 0 14px 30px rgba(23, 32, 51, 0.12);
        }
        .st-key-sidebar_panel [data-testid="stButton"] > button[kind="secondary"] {
            min-height: 40px;
            border: 0;
            border-radius: 8px;
            color: #d4dced;
            background: transparent;
            font-size: 0.88rem;
            text-align: left;
        }
        .st-key-sidebar_panel [data-testid="stButton"] > button[kind="secondary"]:hover {
            color: #ffffff;
            background: rgba(255, 255, 255, 0.08);
        }
        .st-key-sidebar_panel [data-testid="stButton"] > button[kind="primary"] {
            background: #5b57e8;
            box-shadow: none;
        }
        .shell-divider { min-height: 660px; border-left: 1px solid var(--datagpt-line); }

        .workspace-eyebrow { color: var(--datagpt-accent); font-size: 0.8rem; font-weight: 800; letter-spacing: 0.11em; text-transform: uppercase; }
        .workspace-title { margin: 0.35rem 0 0.4rem; color: var(--datagpt-ink); font-size: 2.7rem; font-weight: 800; letter-spacing: -0.065em; }
        .workspace-copy { margin: 0 0 1.8rem; color: var(--datagpt-muted); font-size: 1.08rem; }
        [data-testid="stVerticalBlockBorderWrapper"] {
            margin-bottom: 1.3rem;
            border-color: var(--datagpt-line) !important;
            border-radius: 14px !important;
            background: var(--datagpt-surface);
        }
        .source-panel { padding: 0.15rem 0 0.1rem; }
        .source-heading { margin-bottom: 0.12rem; color: var(--datagpt-ink); font-size: 1.04rem; font-weight: 750; }
        .source-copy { margin-bottom: 0.8rem; color: var(--datagpt-muted); font-size: 0.9rem; }
        .source-connector { margin-top: 2.25rem; color: #9ba5b8; font-size: 1.3rem; font-weight: 700; text-align: center; }
        .prompt-title { margin: 0.3rem 0 0.4rem; color: var(--datagpt-ink); font-size: 1.55rem; font-weight: 800; letter-spacing: -0.04em; }
        .prompt-copy { margin-bottom: 0.65rem; color: var(--datagpt-muted); font-size: 0.98rem; }
        .example-questions { margin: 1rem 0 0.6rem; color: var(--datagpt-muted); font-size: 0.88rem; font-weight: 650; }
        .trust-badge { margin: 0.45rem 0 0; color: #4f5b70; font-size: 0.9rem; font-weight: 650; white-space: nowrap; }
        .trust-badge span { margin-right: 0.35rem; color: #32895c; }
        .results-heading { margin: 0 0 0.2rem; color: var(--datagpt-ink); font-size: 1.5rem; font-weight: 800; letter-spacing: -0.04em; }
        .results-copy { margin: 0 0 1.1rem; color: var(--datagpt-muted); font-size: 0.96rem; }
        @media (max-width: 760px) {
            .block-container { padding: 5rem 1rem 2rem; }
            .workspace-title { font-size: 2.1rem; }
            .shell-divider { min-height: 0; border-left: 0; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_available_schemas():
    """Fetch the list of databases/schemas once per session."""
    return get_all_schemas()


@st.cache_data(show_spinner=False)
def load_available_tables(schema_name: str):
    """Fetch the list of tables for a given schema, cached per schema."""
    return get_tables(schema_name)


@st.cache_data(show_spinner=False)
def load_table_schema(table_name: str, schema_name: str):
    """Fetch a single table's column schema, cached per (schema, table)."""
    return get_schema(table_name, schema_name=schema_name)


def generate_sql(client: OpenAI, table_name: str, schema, question: str) -> str:
    prompt = f"""Generate a MySQL query based on the schema below.

Table: {table_name}

Schema:
{schema.to_string(index=False)}

Question: {question}

Return only executable SQL. Do not use Markdown code fences. Use only SELECT or WITH queries.
"""
    response = client.responses.create(model="gpt-5.6-sol", input=prompt)
    return response.output_text.strip().removeprefix("```sql").removeprefix("```").removesuffix("```").strip()


def suggested_questions(table_name: str) -> list[str]:
    """Return a few useful quick prompts for the selected table."""
    table_specific_questions = {
        "activity": [
            "Who were the most active users this week?",
            "What are the peak activity hours?",
            "Show the latest 10 activity records.",
        ],
        "movie_data": [
            "Which movies generated the most revenue?",
            "What is the average rating by genre?",
            "How many movies were released each year?",
        ],
    }
    return table_specific_questions.get(
        table_name.lower(),
        [
            f"Show the top 5 rows from {table_name}.",
            f"How many records are in {table_name}?",
            f"What trends stand out in {table_name}?",
        ],
    )


def use_suggested_question(question: str) -> None:
    """Populate the question field when a quick prompt is selected."""
    st.session_state["question"] = question


def set_active_view(view: str) -> None:
    """Switch the workspace between analysis, history, and saved reports."""
    st.session_state["active_view"] = view


def reset_selected_table() -> None:
    """Choose a fresh table default after the database changes."""
    st.session_state.pop("selected_table", None)


def restore_report(report: dict) -> None:
    """Open a historical or saved report in the analysis workspace."""
    st.session_state["last_query"] = report["query"]
    st.session_state["last_result"] = report["result"]
    st.session_state["last_question"] = report["question"]
    st.session_state["last_table"] = report["table"]
    st.session_state["active_view"] = "ask"


def save_current_report() -> None:
    """Save the most recent report once, using its SQL as a stable identifier."""
    if "last_result" not in st.session_state:
        return

    report = {
        "question": st.session_state["last_question"],
        "query": st.session_state["last_query"],
        "result": st.session_state["last_result"],
        "table": st.session_state.get("last_table", "report"),
    }
    saved_reports = st.session_state["saved_reports"]
    if not any(saved_report["query"] == report["query"] for saved_report in saved_reports):
        saved_reports.insert(0, report)


st.markdown(
    """
    <div class="brand-lockup">
        <div class="brand-mark"><span></span><span></span><span></span></div>
        <div>
            <div class="brand-name">TextToSQL</div>
            <div class="brand-tagline">Ask questions about your analytics database.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    available_schemas = load_available_schemas()
except Exception as error:
    available_schemas = []
    st.error(f"Could not load available schemas: {error}")

if not available_schemas:
    st.stop()

DEFAULT_SCHEMA = "analytics"
DEFAULT_TABLE = "activity"
default_index = (
    available_schemas.index(DEFAULT_SCHEMA) if DEFAULT_SCHEMA in available_schemas else 0
)

if st.session_state.get("selected_schema") not in available_schemas:
    st.session_state["selected_schema"] = available_schemas[default_index]

st.session_state.setdefault("active_view", "ask")
st.session_state.setdefault("query_history", [])
st.session_state.setdefault("saved_reports", [])

with st.container():
    sidebar, shell_divider, workspace = st.columns([2.15, 0.04, 8.81], gap="medium")
    with sidebar:
        with st.container(key="sidebar_panel"):
            st.markdown(
                """
            <div class="sidebar-shell" aria-label="TextToSQL workspace navigation">
                    <div class="sidebar-brand">
                        <div class="sidebar-mark"><span></span><span></span><span></span></div>
                        <div><div class="sidebar-workspace">TextToSQL</div><div class="sidebar-caption">Analytics workspace</div></div>
                    </div>
                    <div class="sidebar-section">Workspace</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            active_view = st.session_state["active_view"]
            st.button(
                "✦  Ask",
                key="nav_ask",
                type="primary" if active_view == "ask" else "secondary",
                on_click=set_active_view,
                args=("ask",),
                use_container_width=True,
            )
            st.button(
                f"◷  History  ·  {len(st.session_state['query_history'])}",
                key="nav_history",
                type="primary" if active_view == "history" else "secondary",
                on_click=set_active_view,
                args=("history",),
                use_container_width=True,
            )
            st.button(
                f"🔖  Saved  ·  {len(st.session_state['saved_reports'])}",
                key="nav_saved",
                type="primary" if active_view == "saved" else "secondary",
                on_click=set_active_view,
                args=("saved",),
                use_container_width=True,
            )
    with shell_divider:
        st.markdown('<div class="shell-divider" aria-hidden="true"></div>', unsafe_allow_html=True)

if st.session_state["active_view"] == "ask":
    with workspace:
        st.markdown('<div class="workspace-eyebrow">New analysis</div>', unsafe_allow_html=True)
        st.markdown('<div class="workspace-title">Ask your data</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="workspace-copy">Choose a source, then ask a question in plain English.</div>',
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown(
                """
                <div class="source-panel">
                    <div class="source-heading">Data source</div>
                    <div class="source-copy">Select the database and table for this analysis.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            source_schema_column, source_connector_column, source_table_column = st.columns(
                [1, 0.12, 1], gap="small"
            )
            with source_schema_column:
                selected_schema = st.selectbox(
                    "1 · Database",
                    options=available_schemas,
                    index=default_index,
                    key="selected_schema",
                    on_change=reset_selected_table,
                )

            with source_connector_column:
                st.markdown('<div class="source-connector">→</div>', unsafe_allow_html=True)

            try:
                available_tables = load_available_tables(selected_schema)
            except Exception as error:
                available_tables = []
                st.error(f"Could not load tables for '{selected_schema}': {error}")

            if not available_tables:
                st.warning(f"No tables found in '{selected_schema}'.")
                st.stop()

            if st.session_state.get("selected_table") not in available_tables:
                st.session_state["selected_table"] = (
                    DEFAULT_TABLE if DEFAULT_TABLE in available_tables else available_tables[0]
                )

            with source_table_column:
                selected_table = st.selectbox(
                    "2 · Table",
                    options=available_tables,
                    key="selected_table",
                )

            try:
                schema = load_table_schema(selected_table, selected_schema)
                with st.expander(f"View {selected_table} schema", expanded=False):
                    st.dataframe(schema, hide_index=True, use_container_width=True)
            except Exception as error:
                schema = None
                st.error(f"Could not load the {selected_table} schema: {error}")

        st.markdown('<div class="prompt-title">What do you want to explore?</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="prompt-copy">TextToSQL will generate a read-only query and return the result.</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="example-questions">Quick prompts for this table</div>', unsafe_allow_html=True)
        question_buttons = st.columns(3, gap="small")
        for button_column, suggested_question in zip(question_buttons, suggested_questions(selected_table)):
            with button_column:
                st.button(
                    suggested_question,
                    key=f"prompt_{selected_table}_{suggested_question}",
                    on_click=use_suggested_question,
                    args=(suggested_question,),
                    use_container_width=True,
                )
        question = st.text_area(
            "Ask your question",
            placeholder=f"For example: Give me the top 5 rows from {selected_table}",
            label_visibility="collapsed",
            key="question",
        )
        run_button_column, trust_badge_column, _ = st.columns([1.25, 1.15, 5.6], gap="small")
        with run_button_column:
            run_clicked = st.button("Run query →", type="primary", disabled=not question or schema is None)
        with trust_badge_column:
            st.markdown('<div class="trust-badge"><span>🔒</span>Read-only queries</div>', unsafe_allow_html=True)

    if run_clicked:
        try:
            client = OpenAI()
            with st.spinner("Generating SQL and querying the database..."):
                query = generate_sql(client, selected_table, schema, question)
                result = execute_query(query)

            report = {"question": question, "query": query, "result": result, "table": selected_table}
            st.session_state["last_query"] = query
            st.session_state["last_result"] = result
            st.session_state["last_question"] = question
            st.session_state["last_table"] = selected_table
            st.session_state["query_history"].insert(0, report)
            st.rerun()
        except NotAllowedQueryError as error:
            st.session_state.pop("last_result", None)
            st.warning(f"🚫 Not allowed: {error}")
        except Exception as error:
            st.session_state.pop("last_result", None)
            st.error(f"Unable to complete the request: {error}")

    if "last_result" in st.session_state:
        with workspace:
            result = st.session_state["last_result"]
            query = st.session_state["last_query"]
            question_asked = st.session_state["last_question"]
            table_for_result = st.session_state.get("last_table", selected_table)

            with st.container(border=True):
                st.markdown('<div class="results-heading">Analysis result</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="results-copy">Answer for: {escape(question_asked)}</div>',
                    unsafe_allow_html=True,
                )
                st.subheader("Generated SQL")
                st.code(query, language="sql")
                st.subheader("Results")
                st.dataframe(result, hide_index=True, use_container_width=True)
                st.caption(f"{len(result):,} row(s) returned")
                current_report_is_saved = any(
                    saved_report["query"] == query for saved_report in st.session_state["saved_reports"]
                )
                save_button_column, save_hint_column, _ = st.columns([1.65, 2.6, 4.75], gap="small")
                with save_button_column:
                    st.button(
                        "✓ Saved to reports" if current_report_is_saved else "🔖 Save report",
                        key="save_result",
                        type="primary",
                        disabled=current_report_is_saved,
                        on_click=save_current_report,
                        use_container_width=True,
                    )
                with save_hint_column:
                    if current_report_is_saved:
                        st.caption("Available in the Saved section of your sidebar.")
                    else:
                        st.caption("Keep this result so you can reopen it from Saved later.")

                with st.container(key="email_report_panel"):
                    with st.expander("✉️ Email report"):
                        recipient = st.text_input("To", key="email_to", placeholder="you@company.com")
                        default_subject = f"TextToSQL report — {question_asked}"
                        subject = st.text_input("Subject", key="email_subject", value=default_subject)
                        message = st.text_area(
                            "Message (optional)",
                            key="email_message",
                            placeholder="Add a note…",
                        )

                        if st.button("Send email", type="primary"):
                            try:
                                body = message.strip() or "Please find the attached TextToSQL report."
                                body += f"\n\nQuestion: {question_asked}\nQuery:\n{query}"
                                csv_bytes = result.to_csv(index=False).encode("utf-8")

                                send_email(
                                    to_address=recipient,
                                    subject=subject,
                                    body=body,
                                    attachment_bytes=csv_bytes,
                                    attachment_filename=f"{table_for_result}_report.csv",
                                )
                                st.success(f"✓ Sent to {recipient}")
                            except (InvalidEmailError, EmailNotConfiguredError) as error:
                                st.warning(str(error))
                            except Exception as error:
                                st.error(f"Could not send email: {error}")
else:
    view_name = "Query history" if st.session_state["active_view"] == "history" else "Saved reports"
    reports = (
        st.session_state["query_history"]
        if st.session_state["active_view"] == "history"
        else st.session_state["saved_reports"]
    )
    with workspace:
        st.markdown('<div class="workspace-eyebrow">Workspace</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="workspace-title">{view_name}</div>', unsafe_allow_html=True)
        if not reports:
            st.info(f"No {view_name.lower()} yet. Run a query to see it here.")
        for report_index, report in enumerate(reports):
            with st.container(border=True):
                st.markdown(
                    f'<div class="results-heading">{escape(report["question"])}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="results-copy">Table: {escape(report["table"])}</div>',
                    unsafe_allow_html=True,
                )
                st.button(
                    "Open report",
                    key=f"open_{st.session_state['active_view']}_{report_index}",
                    on_click=restore_report,
                    args=(report,),
                )
