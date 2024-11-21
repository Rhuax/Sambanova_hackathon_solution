from openai import OpenAI
from typing import List, Dict, Optional, Generator
from prompts import *
import logging

SAMBA_NOVA_API_KEY = ""
def get_client():
    """
    Creates and returns an Samba Nova client instance
    """
    return OpenAI(api_key=SAMBA_NOVA_API_KEY,base_url="https://api.sambanova.ai/v1",)

def generate_chat_completion(
    prompt: str, 
    previous_messages: Optional[List[Dict[str, str]]] = None,
    system_prompt: str = REQUIREMENTS_ANALYZER_PROMPT,
    model: str = "Meta-Llama-3.1-70B-Instruct",
    temperature: float = 0.3,
    top_p: float = 1
) -> Generator[str, None, None]:
    """
    Generates a chat completion using the OpenAI API with streaming
    
    Args:
        prompt (str): The user's input prompt
        previous_messages (List[Dict[str, str]], optional): List of previous messages in the conversation
            Each message should be a dict with 'role' and 'content' keys
        system_prompt (str): The system prompt to set the behavior of the AI
        model (str): The model to use (defaults to gpt-4)
        
    Yields:
        str: Chunks of the generated response as they become available
    """
    client = get_client()
    
    # Start with the system message
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add previous messages if they exist
    if previous_messages:
        messages.extend(previous_messages)
    
    # Add the current prompt
    messages.append({"role": "user", "content": prompt})
    
    # Create a streaming response
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        temperature=temperature,
        top_p=top_p
    )
    
    # Yield each chunk as it arrives
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content
        # Log the finish reason when the stream ends
        if chunk.choices[0].finish_reason is not None:
            logging.info(f"Stream finished with reason: {chunk.choices[0].finish_reason}")