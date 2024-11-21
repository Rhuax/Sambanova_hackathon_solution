import streamlit as st
import logging
from openai_helpers import generate_chat_completion
from utils import process_wbs, process_gantt, process_team_structure, process_estimate
from trello_utils import process_trello_function_calls
import plotly.express as px
from PIL import Image
import os
from main import create_wbs_and_dependecy_graph, create_gantt_chart,create_team_structure, create_cost_estimate, create_trello_cards

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set page config for wide layout
st.set_page_config(layout="wide")

def process_tab_content(user_input:str):
    logging.info("Starting process_tab_content")
    try:
        wbs, nodes, edges = create_wbs_and_dependecy_graph(user_input, st.session_state["tabs"][0], st.session_state["tabs"][1])
        logging.info("WBS and dependency graph created")
        
        logging.info("Starting Gantt chart creation...")
        try:
            tasks = create_gantt_chart(st.session_state["tabs"][2], user_input, wbs, nodes, edges)
            logging.info("Gantt chart creation completed successfully")
        except Exception as e:
            logging.error(f"Failed to create Gantt chart: {str(e)}", exc_info=True)
            return
        logging.info("Starting team structure creation...")
        team_structure = create_team_structure(st.session_state["tabs"][3],user_input, tasks)
        logging.info("Team structure creation completed successfully")
        create_cost_estimate(st.session_state["tabs"][4],user_input, tasks, team_structure)

        create_trello_cards(st.session_state["tabs"][5],user_input, tasks, team_structure)

    except Exception as e:
        logging.error(f"Error in process_tab_content: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")

def main():
    
    st.title("AI Project Plan Builder")
    
    # Initialize session state for each tab
    tab_names = [
        "Work Breakdown Structure",
        "Task Dependency Graph",
        "GANTT",
        "Team Structure",
        "Economics",
        "Trello"
    ]
    
    # Create two columns with different widths
    left_col, right_col = st.columns([1, 3])  # 1:3 ratio between left and right columns
    
    # Put text input and button in the left column
    with left_col:
        user_input = st.text_area("", height=150, placeholder="Enter your project description here...")
        if st.button("Plan For Me!"):
            if not user_input.strip():
                st.error("Please enter a project description before proceeding.")
            else:
                process_tab_content(user_input)
    
    # Put tabs in the right column
    with right_col:
        tabs = st.tabs(tab_names)
        st.session_state["tabs"] = tabs

if __name__ == "__main__":
    main()
