import requests
import re
import asyncio
import json
import logging
logger = logging.getLogger(__name__)
logger.disabled = False
logger.setLevel(logging.INFO)

current_board_id=""

async def add_card_to_trello(card_name:str,card_description:str,start_date:str,end_date:str, id_list:str):
    if id_list=="{board_id}":
        id_list=current_board_id # Fix for some edge cases of the GenAI model outputting {board_id} instead of the actual board id
    url = f"https://api.trello.com/1/cards?key={TRELLO_API_KEY}&token={TRELLO_TOKEN}"
    response = requests.post(url, json={"name": card_name, "desc": card_description, "idList": id_list, "start": start_date, "due": end_date})
    return response.json()

async def create_board_on_trello(board_name:str):
    global current_board_id
    url = f"https://api.trello.com/1/boards/?key={TRELLO_API_KEY}&token={TRELLO_TOKEN}"
    response = requests.post(url, json={"name": board_name})
    logger.info(response.json())
    board_id= response.json()["id"]
    current_board_id=board_id
    url = f"https://api.trello.com/1/boards/{board_id}/lists?key={TRELLO_API_KEY}&token={TRELLO_TOKEN}"
    response = requests.post(url, json={"name": "To Do"})
    logger.info(response.json())
    return response.json()["id"], board_id

async def process_trello_function_calls(trello_output:str):
    function_call_pattern = r'<function_call>(.*?)</function_call>'
    function_call = re.search(function_call_pattern, trello_output, re.DOTALL)
    tasks = []
    if function_call:
        function_call = json.loads(function_call.group(1).strip())
        for call in function_call:
            logger.info(call["name"])
            if call["name"] == "create_board_on_trello":
                tasks.append(create_board_on_trello(call["parameters"]["board_name"]))
            elif call["name"] == "add_card_to_trello":
                tasks.append(add_card_to_trello(**call["parameters"]))
    results = await asyncio.gather(*tasks)
    return results
