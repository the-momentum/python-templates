import asyncio
import time
import os

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from openai import AuthenticationError
from pydantic_core._pydantic_core import ValidationError

# Try to authenticate with streamlit secrets
# if .env doesn't provide an api key
try:
    from app.config import settings
    os.environ["API_KEY"] = settings.api_key
except ValidationError:
    try:
        os.environ["API_KEY"] = st.secrets["API_KEY"]
    except StreamlitSecretNotFoundError:
        st.warning("Provide a valid API key.")
        raise

from app.agent import AgentManager


agent_manager = AgentManager()

if os.environ.get("API_KEY") == "":
    st.warning("Please provide an API key in .streamlit/secrets.toml to continue...")
else:
    try:
        asyncio.run(agent_manager.initialize())
    except ExceptionGroup:
        st.markdown("Couldn't initialize the agent...")


if "chats" not in st.session_state:
    st.session_state.chats = 1
if "active_chat" not in st.session_state:
    st.session_state.active_chat = 1


# ----------------------------------------------------------------------------------------------------------------------

st.title("Your AI Assistant")


st.divider()


# ---------- sidebar ----------

with st.sidebar:
    if st.button("New chat"):
        st.session_state.chats += 1
        st.session_state.active_chat = st.session_state.chats
    st.divider()
    st.session_state.chat_buttons = []
    for i in range(st.session_state["chats"]):
        i += 1
        if st.button(f"Chat {i}", key=f"chat{i}"):
            st.session_state.active_chat = i

# -----------------------------


if f"messages{st.session_state["active_chat"]}" not in st.session_state:
    st.session_state[f"messages{st.session_state["chats"]}"] = []

for message in st.session_state[f"messages{st.session_state["active_chat"]}"]:
    with st.chat_message(message["role"]):
        st.markdown(message["text"])

if prompt := st.chat_input("Ask me something"):
    st.session_state[f"messages{st.session_state["active_chat"]}"].append({"role": "human", "text": prompt})

    with st.chat_message("human"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        try:
            with st.spinner("running...", show_time=True):
                response = asyncio.run(agent_manager.handle_message(prompt))
        except AuthenticationError:
            st.warning("Please provide an api key in .env")
            response = ""
        except RuntimeError:
            st.warning("Agent not initialized.")
            response = ""

        # Split response into chunks to imitate AI behaviour
        for chunk in response.split():
            full_response += chunk + " "
            time.sleep(0.04)
            placeholder.markdown(full_response + "▌")
        placeholder.markdown(full_response)
        st.session_state[f"messages{st.session_state["active_chat"]}"].append({"role": "assistant", "text": full_response})


# ----------------------------------------------------------------------------------------------------------------------


