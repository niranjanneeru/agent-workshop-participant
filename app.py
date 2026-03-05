import streamlit as st
from langchain_core.messages import AIMessage
from src.agents.chat import ChatAgent

st.set_page_config(page_title="Chat Agent", page_icon="💬")
st.title("💬 Chat Agent")

@st.cache_resource
def get_agent():
    return ChatAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("What would you like to know?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        result = get_agent().chat(prompt, "default", 1)
        msgs = result.get("messages", [])
        content = msgs[-1].content if msgs else "No response"
        st.markdown(content)
    st.session_state.messages.append({"role": "assistant", "content": content})
