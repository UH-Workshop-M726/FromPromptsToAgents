"""
Step 4: Build a Chatbot with Streamlit
========================================
A working chatbot with a web interface. Run with:

    streamlit run steps/step4_chatbot.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import streamlit as st
import llm_client

st.set_page_config(page_title="AI Chatbot", page_icon="💬")
st.title("💬 AI Chatbot")

# --- Sidebar: display the active LLM backend ---
with st.sidebar:
    st.header("LLM Status")
    health = llm_client.check_health()
    if health["model_loaded"]:
        st.success(f"Online: {health['backend']}")
        st.caption(f"Model: {health['model']}")
    else:
        st.error("Offline — check .env")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- Chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Handle input ---
user_input = st.chat_input("Type your message...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    api_messages = [
        {"role": "system", "content": "You are a helpful, friendly assistant."},
    ] + st.session_state.messages

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = llm_client.chat(api_messages)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
