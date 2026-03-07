import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from src.agents.chat import ChatAgent
from src.db import execute_query

st.set_page_config(page_title="Chat Agent", page_icon="💬", layout="centered")
st.title("💬 Chat Agent")


@st.cache_resource
def get_agent():
    return ChatAgent()


if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_user_id" not in st.session_state:
    st.session_state.current_user_id = None
if "current_user_email" not in st.session_state:
    st.session_state.current_user_email = None


def _user_id_from_email(email: str) -> int | None:
    if not (email or "").strip():
        return None
    rows = execute_query(
        "SELECT user_id FROM users WHERE LOWER(email) = LOWER(%s)",
        (email.strip(),),
    )
    return rows[0]["user_id"] if rows else None


def _emails_from_db() -> list[str]:
    try:
        rows = execute_query(
            "SELECT email FROM users WHERE account_status = 'active' AND email IS NOT NULL ORDER BY user_id"
        )
        return [r["email"] for r in rows if r.get("email")]
    except Exception:
        return []


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


if prompt := st.chat_input("What would you like to know?"):
    uid = st.session_state.current_user_id
    if uid is None:
        st.error("Please select a user in the sidebar.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            result = get_agent().chat(prompt, "default", uid)
            msgs = result.get("messages", [])
            # Get the last AI message
            content = "No response"
            for m in reversed(msgs):
                if isinstance(m, AIMessage) and m.content:
                    content = m.content
                    break
            st.markdown(content)
        st.session_state.messages.append({"role": "assistant", "content": content})


def _on_email_change():
    choice = st.session_state.user_email_select
    uid = _user_id_from_email(choice) if choice else None
    if uid is not None:
        st.session_state.current_user_id = uid
        st.session_state.current_user_email = (choice or "").strip()
    else:
        st.session_state.current_user_id = None
        st.session_state.current_user_email = None
    st.session_state.messages = []


with st.sidebar:
    st.header("User")
    emails = _emails_from_db()
    if emails:
        first_email = emails[0]
        if st.session_state.current_user_id is None:
            uid = _user_id_from_email(first_email)
            if uid is not None:
                st.session_state.current_user_email = first_email.strip()
                st.session_state.current_user_id = uid
    options = emails
    current = st.session_state.current_user_email or ""
    default_idx = options.index(current) if current in options else 0
    st.selectbox(
        "Email",
        options=options,
        index=default_idx,
        key="user_email_select",
        on_change=_on_email_change,
        help="Select a user. Orders, cart, etc. are looked up for this user.",
    )
    with st.expander("Session state", expanded=False):
        uid = st.session_state.current_user_id
        st.text(f"user_id: {uid}")
        st.text(f"email: {st.session_state.current_user_email or '(none)'}")
        st.text(f"messages: {len(st.session_state.messages)}")
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()
