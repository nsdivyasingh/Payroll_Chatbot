import streamlit as st

from chat_service import process_user_query
from tools import employee_exists

st.set_page_config(page_title="Payroll Chatbot", layout="centered")

if "employee_id" not in st.session_state:
    st.session_state.employee_id = None

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
        st.success("Login successful.")
        st.rerun()
    st.stop()

# Main app
st.title("Payroll Assistant")
st.caption(f"Logged in as Employee ID: {st.session_state.employee_id}")
if st.button("Logout"):
    st.session_state.employee_id = None
    st.rerun()

user_query = st.text_input("Ask your payroll question")

if st.button("Ask", type="primary"):
    if not user_query.strip():
        st.warning("Please enter a question.")
        st.stop()

    result = process_user_query(
        user_query=user_query,
        employee_id=st.session_state.employee_id,
    )

    st.subheader("Answer")
    st.write(result["answer"])

    if result.get("source") == "payroll" and result.get("tool_call"):
        with st.expander("Debug: Planner & Tool", expanded=False):
            st.json(result["tool_call"])