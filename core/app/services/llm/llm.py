import json
from typing import List, Dict, Tuple
from app.services.llm.prompts import CATEGORIZATION_PROMPT, SYSTEM_PROMPT_LLM_CHUNKING
from app.models.models import ItemDto, ItemChunkDto
from openai import OpenAI
from app.envirnoment import config

import logging
logger = logging.getLogger(__name__)

class OpenAILlmService:
    def __init__(self):
        self.openaiClient = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config["OPENROUTE_API_KEY"],
        )


    def categorize(self, json_list: List[ItemChunkDto]) -> List[ItemDto]:
        items : List[ItemDto] = []
        for i, entry in enumerate(json_list):
            completion = self.openaiClient.chat.completions.create(
                temperature=0,
                response_format={"type": "json_object"},
                model="openai/gpt-4o-mini",
                    messages=[
                    {
                        "role": "user",
                        "content": CATEGORIZATION_PROMPT
                    },
                    {
                        "role": "system",
                        "content": f"This is the content: {entry.model_dump()}"
                    }
                    ]
                ,
            )
            answer_string = completion.choices[0].message.content
            if answer_string is not None:
                answer_json = json.loads(answer_string)
                if answer_json is not None:
                    items.extend(answer_json.get("items", []))

            
    def parse_page_with_llm(self, page_text, model="openai/gpt-4o-mini", max_retries=3) -> ItemChunkDto:
        """
        Parse page text using LLM with retry mechanism for error handling.
        
        Args:
            page_text: Text content to be parsed
            model: LLM model to use
            max_retries: Maximum number of retry attempts
        
        Returns:
            List of parsed ItemDto objects
        """
        retry_count = 0
        last_error = None
        error_context = ""
        
        while retry_count <= max_retries:
            try:
                # Prepare messages - include error feedback on retries
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT_LLM_CHUNKING}
                ]
                
                # On retry, include the error context
                if retry_count > 0:
                    error_message = (
                        f"The previous attempt failed with error: {last_error}\n"
                        f"Please correct the following issues in your response: {error_context}\n"
                        f"This is retry attempt {retry_count} of {max_retries}."
                    )
                    messages.append({"role": "user", "content": page_text})
                    messages.append({"role": "assistant", "content": "I'll parse this content."})
                    messages.append({"role": "user", "content": error_message})
                else:
                    messages.append({"role": "user", "content": page_text})
                
                # Make API call
                logger.info(f"Sending request to LLM (attempt {retry_count + 1}/{max_retries + 1})")
                completion = self.openaiClient.chat.completions.create(
                    model=model,
                    max_tokens=4096,
                    temperature=0,
                    response_format={"type": "json_object"},
                    messages=messages,
                )
                
                if not completion.choices:
                    raise ValueError("No choices returned from OpenAI API")
                
                content = completion.choices[0].message.content
                # Parse the JSON response
                data = json.loads(content)
                
                # Validate required fields
                if "items" not in data:
                    raise ValueError("Response missing 'items' field")
                
                items = data.get("items", [])
                
                # Additional validation
                if not isinstance(items, list):
                    raise ValueError("'items' is not a list")
                
                if len(items) == 0:
                    logger.warning("No items found in the parsed content")
                
                # Convert to DTOs and validate each item
                parsed_items = []
                for i, item in enumerate(items):
                    try:
                        parsed_item = ItemChunkDto(
                            ref_no=item.get("ref_no"),
                            description=item.get("description"),
                            quantity=item.get("quantity"),
                            unit=item.get("unit"),
                        )
                        parsed_items.append(parsed_item)
                    except Exception as e:
                        raise ValueError(f"Failed to parse item at index {i}: {str(e)}")
                
                # Success - return parsed items
                logger.info(f"Successfully parsed {len(parsed_items)} items after {retry_count + 1} attempts")
                return parsed_items
                
            except json.JSONDecodeError as e:
                last_error = f"JSON parsing error: {str(e)}"
                error_context = "Your response isn't valid JSON. Please ensure proper JSON formatting."
                logger.warning(f"Retry {retry_count + 1}/{max_retries + 1}: {last_error}")
            
            except ValueError as e:
                last_error = f"Validation error: {str(e)}"
                error_context = f"Please fix the structure of your response: {str(e)}"
                logger.warning(f"Retry {retry_count + 1}/{max_retries + 1}: {last_error}")
            
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                error_context = "An unexpected error occurred. Please provide a properly formatted response."
                logger.warning(f"Retry {retry_count + 1}/{max_retries + 1}: {last_error}", exc_info=True)
            
            # Increment retry counter
            retry_count += 1
        
        # If we get here, all retries failed
        logger.error(f"Failed to parse content after {max_retries + 1} attempts. Last error: {last_error}")
        raise Exception(f"Failed to parse content after {max_retries + 1} attempts: {last_error}")


if __name__ == "__main__":
    with open('..\..\specWise\core\parsed_items_example_1.json', 'r') as datei:
        json_obj = json.load(datei)
