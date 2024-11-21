from openai_helpers import generate_chat_completion
from prompts import *
from utils import *
from trello_utils import *
import streamlit as st

def create_wbs_and_dependecy_graph(client_need,tab_wbs,tab_dependency_graph):
    response_stream = generate_chat_completion(f"This is the raw client email: {client_need}", system_prompt=WBS_CREATOR_PROMPT)
    wbs = ""
    for chunk in response_stream:
        wbs += chunk
        print(chunk, end="")
        
    wbs, function_call = process_wbs(wbs)
    with tab_wbs:
        st.markdown("``` <br>  "+wbs)
    with tab_dependency_graph:
        # Display the dependency graph with high quality
        st.image(
            generate_dependency_graph(function_call[0]["parameters"]["nodes"],function_call[0]["parameters"]["edges"]),
            use_container_width=True,
            output_format='PNG'
        )
    return wbs, function_call[0]["parameters"]["nodes"],function_call[0]["parameters"]["edges"]


def create_gantt_chart(tab_gantt, client_need, wbs, dependency_graph_nodes, dependency_graph_edges):
    max_retries = 4
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response_stream = generate_chat_completion(f"This is the raw client email: {client_need}\n This is the WBS: {wbs}\n Think step by step and create a full and complete GANTT chart.", system_prompt=GANTT_CHART_CREATOR_PROMPT, temperature=0.2, top_p=0.9)
            gantt = ""
            for chunk in response_stream:
                gantt += chunk
                print(chunk, end="")
            
            tasks, _, excel_filename = process_gantt(gantt_text=gantt)
            break
        except Exception as e:
            retry_count += 1
            if retry_count == max_retries:
                raise Exception(f"Failed to process GANTT chart after {max_retries} attempts: {str(e)}")
            print(f"Attempt {retry_count} failed, retrying...")
            
    
    with tab_gantt:
        # Create a fragment to prevent rerun on download
        with st.container():
            # Read the Excel file as binary and encode in base64
            import base64
            with open(excel_filename, 'rb') as f:
                excel_data = base64.b64encode(f.read()).decode()
            
            st.markdown(f"""
                <iframe name="dummyframe" id="dummyframe" style="display: none;"></iframe>
                <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{excel_data}" 
                   download="{excel_filename}" 
                   target="dummyframe" 
                   class="css-1cpxqw2">
                    📥 Download Excel
                </a>
                """,
                unsafe_allow_html=True
            )
            
        # Display Gantt chart
        fig = generate_gantt_chart(tasks)
        st.plotly_chart(
            fig, 
            use_container_width=True,
            config={
                'displayModeBar': True,
                'scrollZoom': True,
                'modeBarButtonsToAdd': ['zoom', 'pan', 'zoomIn', 'zoomOut', 'resetScale'],
                'responsive': True
            },
            height=800
        )
    
    return tasks

def create_team_structure(tab_team_structure, client_need, tasks):
    response_stream = generate_chat_completion(f"This is the raw client email: {client_need}\n These are the tasks: {tasks}", system_prompt=TEAM_STRUCTURE_CREATOR_PROMPT)
    team = ""
    for chunk in response_stream:
        team += chunk
        print(chunk, end="")
    team_structure, team_structure_dict = process_team_structure(team)
    
    logger.info(team_structure)
    with tab_team_structure:
        st.markdown(team_structure)
    return team_structure_dict

def create_cost_estimate(tab_cost_estimate, client_need, tasks, team_structure_dict):
    response_stream = generate_chat_completion(f"This is the raw client email: {client_need}\n These are the tasks: {tasks}\n This is the team structure: {team_structure_dict}",system_prompt=COST_ESTIMATOR_PROMPT)
    estimate = ""
    for chunk in response_stream:
        estimate += chunk
        print(chunk, end="")
    
    function_call_salary_result=asyncio.run(process_estimate(estimate))
    m=[{"role": "user", "content": f"This is the raw client email: {client_need}\n These are the tasks: {tasks}\n This is the team structure: {team_structure_dict}"},{"role":"assistant", "content":estimate}]
    
    response_stream = generate_chat_completion(function_call_salary_result, previous_messages=m, system_prompt=COST_ESTIMATOR_PROMPT)
    estimate = ""
    for chunk in response_stream:
      estimate += chunk
      print(chunk, end="")

    with tab_cost_estimate:
        st.markdown(estimate)



def create_trello_cards(tab,user_input, tasks, team_structure):
    response_stream=generate_chat_completion(f"Requirements: {user_input}\n Tasks: {tasks}\n Team structure: {team_structure}", system_prompt=PROMPT_CARD_CREATOR_FOR_TRELLO)
    trello_output=""
    for chunk in response_stream:
        trello_output+=chunk
        print(chunk, end="")
    
    res=asyncio.run(process_trello_function_calls(trello_output))
    logger.info(res)
    response_stream=generate_chat_completion(f"Board ID: {res[0][0]}",previous_messages=[{"role":"user", "content":f"Requirements: {user_input}\n Tasks: {tasks}\n Team structure: {team_structure}"},{"role":"assistant", "content":trello_output}], system_prompt=PROMPT_CARD_CREATOR_FOR_TRELLO)
    trello_output=""
    for chunk in response_stream:
        trello_output+=chunk
        print(chunk, end="")
    asyncio.run(process_trello_function_calls(trello_output))
    with tab:
        st.success("Trello cards created successfully")
        st.write(f"Trello board URL: https://trello.com/b/{res[0][1]}")
if __name__ == '__main__':
    pass