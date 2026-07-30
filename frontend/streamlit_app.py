import os

import requests
import streamlit as st

BASE_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="RAG Chatbot")

st.title("📄 RAG Chatbot")

# ------------------------------------------------
# Session State Setup
# ------------------------------------------------

if "token" not in st.session_state:
    st.session_state.token = None

if "user" not in st.session_state:
    st.session_state.user = None

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []


# ------------------------------------------------
# Login / Register Helpers
# ------------------------------------------------

def login(email, password):
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password},
    )

    if response.status_code == 200:
        st.session_state.token = response.json()["access_token"]

        me_response = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {st.session_state.token}"},
        )
        st.session_state.user = me_response.json()
        st.success("Logged in successfully")
        st.rerun()
    else:
        st.error(response.json()["detail"])


def register(name, email, password):
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"name": name, "email": email, "password": password},
    )

    if response.status_code == 201:
        st.success("Registered successfully. Please login now.")
    else:
        st.error(response.json()["detail"])


# ------------------------------------------------
# Sidebar: Account
# ------------------------------------------------

with st.sidebar:
    st.header("Account")

    if st.session_state.token is None:

        login_tab, register_tab = st.tabs(["Login", "Register"])

        with login_tab:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")

            if st.button("Login"):
                login(email, password)

        with register_tab:
            name = st.text_input("Name", key="register_name")
            reg_email = st.text_input("Email", key="register_email")
            reg_password = st.text_input("Password", type="password", key="register_password")

            if st.button("Register"):
                register(name, reg_email, reg_password)

    else:
        st.write(f"Logged in as **{st.session_state.user['name']}**")
        st.write(f"Role: {st.session_state.user['role']}")

        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.user = None
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.rerun()


# ------------------------------------------------
# Stop here if not logged in
# ------------------------------------------------

if st.session_state.token is None:
    st.info("Please login or register from the sidebar to continue.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}


# ------------------------------------------------
# Document Upload (Admin Only)
# ------------------------------------------------

if st.session_state.user["role"] == "admin":

    st.subheader("Upload Document")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None and st.button("Upload"):
        files = {
            "file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")
        }

        upload_response = requests.post(
            f"{BASE_URL}/documents/upload",
            headers=headers,
            files=files,
        )

        if upload_response.status_code == 201:
            st.success(f"Uploaded {uploaded_file.name} successfully")
        else:
            st.error(upload_response.json()["detail"])

    st.subheader("Your Documents")

    docs_response = requests.get(f"{BASE_URL}/documents", headers=headers)

    if docs_response.status_code == 200:
        documents = docs_response.json()

        for document in documents:
            col1, col2 = st.columns([4, 1])
            col1.write(f"📄 {document['original_filename']}")

            if col2.button("Delete", key=f"delete_{document['id']}"):
                requests.delete(
                    f"{BASE_URL}/documents/{document['id']}",
                    headers=headers,
                )
                st.rerun()

    st.divider()


# ------------------------------------------------
# Chat Section
# ------------------------------------------------

st.subheader("Chat")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

question = st.chat_input("Ask a question about your documents")

if question:
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.write(question)

    chat_response = requests.post(
        f"{BASE_URL}/chat",
        headers=headers,
        json={
            "question": question,
            "conversation_id": st.session_state.conversation_id,
        },
    )

    if chat_response.status_code == 200:
        data = chat_response.json()
        answer = data["answer"]
        st.session_state.conversation_id = data["conversation_id"]

        with st.chat_message("assistant"):
            st.write(answer)

            if data["sources"]:
                st.caption("Sources:")
                for source in data["sources"]:
                    st.caption(f"- {source['filename']} (page {source['page_number']})")

        st.session_state.messages.append({"role": "assistant", "content": answer})
    else:
        st.error("Something went wrong. Please try again.")
