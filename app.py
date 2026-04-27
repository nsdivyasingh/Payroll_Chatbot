import streamlit as st

from chat_service import process_user_query
from tools import employee_exists

st.set_page_config(page_title="Payroll Assistant", layout="centered")

if "employee_id" not in st.session_state:
    st.session_state.employee_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Login gate
if st.session_state.employee_id is None:
    st.title("Employee Login")
    st.caption("Access is restricted to your own payroll records only.")
    emp_id_text = st.text_input("Employee ID")
    if st.button("Login", type="primary"):
        if not emp_id_text.isdigit():
            st.error("Employee ID must be numeric.")
            st.stop()
        emp_id = int(emp_id_text)
        if not employee_exists(emp_id):
            st.error("Employee ID not found.")
            st.stop()
        st.session_state.employee_id = emp_id
        st.session_state.messages = []
        st.success("Login successful.")
        st.rerun()
    st.stop()

# Main app
st.title("💼 Payroll Assistant")
st.caption(f"Logged in as Employee ID: {st.session_state.employee_id}")
if st.button("Logout"):
    st.session_state.employee_id = None
    st.session_state.messages = []
    st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask your payroll question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = process_user_query(
                user_query=prompt,
                employee_id=st.session_state.employee_id,
                history=st.session_state.messages,
            )
        answer = result.get("answer", "Sorry, I could not generate a response.")
        st.write(answer)
        if result.get("source") == "payroll" and result.get("tool_call"):
            with st.expander("Debug: Planner & Tool", expanded=False):
                st.json(result["tool_call"])
    st.session_state.messages.append({"role": "assistant", "content": answer})