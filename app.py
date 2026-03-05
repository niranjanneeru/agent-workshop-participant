import json
import uuid

import streamlit as st
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from src.agents.chat import ChatAgent
from src.db import execute_query


def _is_displayable_content(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return True
    if stripped[0] not in ("{", "["):
        return True
    if ("order_id" in stripped or "user_id" in stripped) and (
        stripped.startswith("[{") or stripped.startswith("{")
    ):
        return False
    try:
        json.loads(stripped)
        return False
    except (json.JSONDecodeError, ValueError):
        return True


def _extract_display_content(content) -> str:
    if content is None:
        return ""
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            text = block.get("text") or block.get("content")
            if text is None:
                continue
            s = str(text).strip()
            if not s:
                continue
            if s.startswith("{") or s.startswith("["):
                try:
                    obj = json.loads(s)
                    if isinstance(obj, dict):
                        if "message" in obj and isinstance(obj["message"], str):
                            parts.append(obj["message"])
                        elif "content" in obj and isinstance(obj["content"], str):
                            parts.append(obj["content"])
                except (json.JSONDecodeError, ValueError, TypeError):
                    parts.append(s)
            else:
                parts.append(s)
        return "\n\n".join(parts) if parts else ""
    text = content if isinstance(content, str) else str(content)
    stripped = text.strip()
    if stripped.startswith("{") and "content" in stripped:
        try:
            obj = json.loads(stripped)
            if isinstance(obj, dict) and "content" in obj:
                return obj["content"] or ""
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    return text


st.set_page_config(page_title="Chat Agent", page_icon="💬", layout="centered")
st.title("💬 Chat Agent")


if "sessions" not in st.session_state:
    st.session_state.sessions = {}
if "user_threads" not in st.session_state:
    st.session_state.user_threads = {}
if "current_user_id" not in st.session_state:
    st.session_state.current_user_id = None
if "current_user_email" not in st.session_state:
    st.session_state.current_user_email = None
if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = None


@st.cache_resource
def get_agent():
    return ChatAgent()


def _new_thread_id(uid: int) -> str:
    return f"user_{uid}_{uuid.uuid4()}"


def _threads_for_user():
    uid = st.session_state.current_user_id
    if uid is None:
        return []
    if uid not in st.session_state.user_threads:
        first_tid = _new_thread_id(uid)
        st.session_state.user_threads[uid] = [first_tid]
        if first_tid not in st.session_state.sessions:
            st.session_state.sessions[first_tid] = []
    return st.session_state.user_threads[uid]


def _current_messages():
    tid = st.session_state.current_thread_id
    if tid is None:
        return []
    if tid not in st.session_state.sessions:
        st.session_state.sessions[tid] = []
    return st.session_state.sessions[tid]


for msg in _current_messages():
    with st.chat_message(
        msg["role"], avatar="🤖" if msg["role"] == "assistant" else None
    ):
        st.markdown(msg["content"])


def history_as_langchain():
    out = []
    for m in _current_messages():
        out.append(
            HumanMessage(content=m["content"])
            if m["role"] == "user"
            else AIMessage(content=m["content"])
        )
    return out


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


def _status_for_intent(intent: str) -> str:
    if "ORDER" in intent:
        return "Looking up your orders and tracking info…"
    if "PRODUCT" in intent:
        return "Searching the catalog and recommendations…"
    return "Thinking…"


if prompt := st.chat_input("What would you like to know?"):
    tid = st.session_state.current_thread_id
    uid = st.session_state.current_user_id
    if tid is None or uid is None:
        st.error("Please select a user and conversation.")
    else:
        _current_messages().append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        history = history_as_langchain()[:-1]
        full_response = ""
        final_content = None
        intent_name = "assistant"

        with st.chat_message("assistant"):
            reply_placeholder = st.empty()
            reply_placeholder.markdown("Thinking…")
            try:
                for chunk in get_agent().stream(
                    prompt,
                    tid,
                    uid,
                    history=history,
                ):
                    if not isinstance(chunk, tuple) or len(chunk) != 2:
                        continue
                    mode, data = chunk
                    if mode == "messages":
                        part = data[0] if isinstance(data, (list, tuple)) else data
                        meta = (
                            data[1]
                            if isinstance(data, (list, tuple)) and len(data) >= 2
                            else {}
                        )
                        node = meta.get("langgraph_node")
                        if node == "intent_agent":
                            continue
                        if node not in (
                            "order_management_agent",
                            "product_discovery_agent",
                            "general_assistant_agent",
                        ):
                            continue
                        if isinstance(part, BaseMessage) and part.content:
                            text = _extract_display_content(part.content)
                            if text and _is_displayable_content(text):
                                if not full_response.endswith(text):
                                    full_response += text
                                reply_placeholder.markdown(full_response + "▌")
                    elif mode == "updates" and isinstance(data, dict):
                        for node_output in data.values():
                            if not isinstance(node_output, dict):
                                continue
                            if node_output.get("intent") is not None:
                                intent_name = str(node_output["intent"])
                                if not full_response and final_content is None:
                                    reply_placeholder.markdown(
                                        _status_for_intent(intent_name)
                                    )
                            for msg in node_output.get("messages") or []:
                                if isinstance(msg, AIMessage) and msg.tool_calls:
                                    for tc in msg.tool_calls:
                                        with st.expander(
                                            f"🔧 {tc.get('name', 'tool')}",
                                            expanded=True,
                                        ):
                                            st.json(tc.get("args", {}))
                                elif isinstance(msg, ToolMessage):
                                    with st.expander("✅ Tool result", expanded=True):
                                        st.code(
                                            (
                                                msg.content
                                                if isinstance(msg.content, str)
                                                else str(msg.content)
                                            ),
                                            language="text",
                                        )
                                elif isinstance(msg, AIMessage) and msg.content:
                                    final_content = _extract_display_content(
                                        msg.content
                                    )
                                    if full_response:
                                        reply_placeholder.markdown(full_response)

                content = (
                    full_response
                    if full_response
                    else _extract_display_content(final_content or "")
                )
                if content and not full_response:
                    reply_placeholder.markdown(content)
                elif full_response:
                    reply_placeholder.markdown(full_response)
                _current_messages().append(
                    {"role": "assistant", "content": content, "name": intent_name}
                )
            except Exception as e:
                reply_placeholder.markdown(f"Error: {e}")
                _current_messages().append(
                    {"role": "assistant", "content": str(e), "name": "assistant"}
                )


def _on_email_change():
    choice = st.session_state.user_email_select
    uid = _user_id_from_email(choice) if choice else None
    if uid is not None:
        st.session_state.current_user_id = uid
        st.session_state.current_user_email = (choice or "").strip()
        if uid not in st.session_state.user_threads:
            first_tid = _new_thread_id(uid)
            st.session_state.user_threads[uid] = [first_tid]
            if first_tid not in st.session_state.sessions:
                st.session_state.sessions[first_tid] = []
            st.session_state.current_thread_id = first_tid
        else:
            st.session_state.current_thread_id = st.session_state.user_threads[uid][0]
    else:
        st.session_state.current_user_id = None
        st.session_state.current_user_email = None
        st.session_state.current_thread_id = None


def _on_thread_change():
    threads = _threads_for_user()
    display_order = list(reversed(threads))
    thread_options = [f"Chat {i + 1}" for i in range(len(display_order))]
    selected = st.session_state.thread_select
    idx = thread_options.index(selected) if selected in thread_options else 0
    if 0 <= idx < len(display_order):
        st.session_state.current_thread_id = display_order[idx]


with st.sidebar:
    st.header("User")
    emails = _emails_from_db()
    if emails:
        first_email = emails[0]
        uid = _user_id_from_email(first_email)
        if uid is not None:
            st.session_state.current_user_email = first_email.strip()
            st.session_state.current_user_id = uid
            if uid not in st.session_state.user_threads:
                first_tid = _new_thread_id(uid)
                st.session_state.user_threads[uid] = [first_tid]
                if first_tid not in st.session_state.sessions:
                    st.session_state.sessions[first_tid] = []
                st.session_state.current_thread_id = first_tid
            else:
                st.session_state.current_thread_id = st.session_state.user_threads[uid][0]
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
    if st.session_state.current_user_id is not None:
        st.subheader("Conversation")
        threads = _threads_for_user()
        display_order = list(reversed(threads))
        thread_options = [f"Chat {i + 1}" for i in range(len(display_order))]
        current_tid = st.session_state.current_thread_id
        thread_idx = (
            display_order.index(current_tid) if current_tid in display_order else 0
        )
        st.session_state.thread_select = thread_options[thread_idx]
        st.selectbox(
            "Conversation",
            options=thread_options,
            key="thread_select",
            on_change=_on_thread_change,
            help="Chat 1 = first conversation, last = most recent.",
        )
    with st.expander("Session state", expanded=False):
        uid = st.session_state.current_user_id
        thread_id = st.session_state.current_thread_id
        st.text(f"user_id: {uid}")
        st.text(f"email: {st.session_state.current_user_email or '(none)'}")
        st.text(f"thread_id: {thread_id or '(none)'}")
        n = len(_current_messages())
        st.text(f"messages in session: {n}")
    st.header("Options")
    if st.button("New chat"):
        if st.session_state.current_user_id is not None:
            uid = st.session_state.current_user_id
            new_tid = _new_thread_id(uid)
            st.session_state.user_threads[uid] = [
                new_tid,
                *st.session_state.user_threads[uid],
            ]
            st.session_state.sessions[new_tid] = []
            st.session_state.current_thread_id = new_tid
        st.rerun()
