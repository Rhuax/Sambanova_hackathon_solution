# Sambanova Hackathon - AI Agent Project Planner

This is my entry for the Sambanova Agent Hackathon. It uses super fast LLM APi from Sambanova to implement a GenAI Agentic solution for project planning.

Starting from a client need and request for a new project the tool calculates:
- Work Breakdown Structure (WBS): the list of the task to do to implement the whole project.
- Task Dependency Graph: a direct acylic graph of the task of the project where an edge/arrow represents a dependency between two tasks. It is useful to understand the most critical tasks in a project.
- GANTT: it calculates the GANTT by starting at the current date. It estimates the whole duration of the project, and for each task its start and end date. Moreover it tries to chronologically parallelize the task execution.
  - The GANTT is calculated with plotly and visualized as an interactive plot
  - The GANTT is also created through an excel file, where each row is a task and on the column there's the temporal breakdown with colored cells indicating the period in which the task will be executed.
- Team Structure: it estimates the team structure by generating:
  - The role
  - The skills
  - The seniority
  - The person supervisor (if any)
- Economics: it calculates the overall cost to implement the project by calculating personnel and non-personnel costs.
  - Personnel costs: it scrapes the average annual salary for each role from salary.com and multiplies automatically for the number of people with that role in the team.
  - Non-personnel costs: it estimates the cost based on the LLM knowledge
- Trello board: given all of the previous outputs it uses the official Trello APIs to automatically create a new board and add cards for each estimated task. Each card has a start date, end date and the role(s) of the people which will do that task as card description.
- 
**YOUTUBE VIDEO:**
  
[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/LtWxXh3y1oU/0.jpg)](https://www.youtube.com/watch?v=LtWxXh3y1oU)
