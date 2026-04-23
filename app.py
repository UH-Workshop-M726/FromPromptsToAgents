import streamlit as st
import asyncio
import os
from agents import run_robotic_chef_pipeline

st.set_page_config(page_title="Smart Budget RobotChef", layout="wide")
st.title("🤖 Smart Budget RobotChef")

if 'query' not in st.session_state:
    st.session_state.query = ""

col1, col2 = st.columns(2)
with col1:
    if st.button("Scenario 1: £12 Budget (High Protein)"):
        st.session_state.query = "I have £12 for two people, we need a high-protein meal. design a robot to cook it."
        st.rerun()
with col2:
    if st.button("Scenario 2: £20 Budget (Vegetarian/Balanced)"):
        st.session_state.query = "20 pound budget, two people, one person is vegetarian, plan a balanced meal + robot"
        st.rerun()

query = st.text_area("Custom Requirements:", value=st.session_state.query)

if st.button("Generate Design"):
    if query:
        with st.status("Initializing Systems...", expanded=True) as status:
            def update_status(text):
                status.update(label=text)

            try:
                # Run the pipeline
                results = asyncio.run(run_robotic_chef_pipeline(query, update_status))
                
                status.update(label="Design Complete!", state="complete", expanded=False)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.header("Culinary & Budget Analysis")
                    st.info(results.get("food_analysis", "No analysis data."))
                with c2:
                    st.header("Robotic Hardware Specs")
                    st.success(results.get("robot_design", "No hardware data."))
            
            except Exception as e:
                status.update(label="System Error", state="error")
                st.error(f"Critical Failure: {e}")
    else:
        st.warning("Please enter a query first.")