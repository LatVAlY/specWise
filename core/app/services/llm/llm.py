from dataclasses import dataclass
import json
from typing import List, Dict, Optional, Tuple
from uuid import UUID

from agents import Agent, FunctionTool, ModelSettings, RunContextWrapper, Runner
from langchain_qdrant import Qdrant
from app.services.llm.prompts import CATEGORIZATION_PROMPT, SYSTEM_PROMPT_LLM_CHUNKING
from app.models.models import ItemDto, ItemChunkDto, TaskStatus
from openai import OpenAI
from app.envirnoment import config

import logging

from app.services.mongo_db import MongoDBService
from app.services.processing.vectore_client import VectoreDatabaseClient

logger = logging.getLogger(__name__)

@dataclass
class AgentContext:
    collection_id: str
    already_parsed_items: Optional[list] = None
class OpenAILlmService:
    def __init__(self):
        self.openaiClient = OpenAI(
            # base_url="https://openrouter.ai/api/v1",
            api_key=config["OPENAI_API_KEY"],
        )
        self.model= "gpt-4o-mini"
        self.mongo_db_service = MongoDBService()
        self.vector_db_service = VectoreDatabaseClient()

    def categorize(self, json_list: List[ItemChunkDto], task_id) -> List[ItemDto]:
        items: List[ItemDto] = []
        for entry in enumerate(json_list):
            logger.info(f"entry: {entry}")
            self.mongo_db_service.update_task_status(
                task_id=UUID(task_id),
                status=TaskStatus.in_progress,
                description=f"Categorizing item {entry[0] + 1} / {len(json_list)}",
            )
            completion = self.openaiClient.chat.completions.create(
                temperature=0,
                response_format={"type": "json_object"},
                model=self.model,
                messages=[
                    {"role": "system", "content": CATEGORIZATION_PROMPT},
                    {"role": "system", "content": f"This is already parsed items {items} \n This is the next item content: {entry}"},
                ],
            )
            answer_string = completion.choices[0].message.content
            if answer_string is not None:
                answer_json = json.loads(answer_string)
                if answer_json is not None:
                    logger.info(f"Answer JSON: {answer_json}")
                    if "items" in answer_json:
                        for item in answer_json["items"]:
                            # make the keys lower case
                            item = {k.lower(): v for k, v in item.items()}
                            item_dto = ItemDto(
                                sku=str(item.get("sku")),
                                name=item.get("name"),
                                text=item.get("text"),
                                quantity=item.get("quantity"),
                                quantityunit=item.get("quantityunit"),
                                price=item.get("price"),
                                priceunit=item.get("priceunit"),
                                commission=item.get("commission"),
                                confidence=item.get("confidence"),
                            )
                            items.append(item_dto)
        return items
    
    async def query_collection(self, ctx: RunContextWrapper[AgentContext], query: str) -> List[ItemChunkDto]:
        results = self.vector_db_service.query_collection(
            query=query,
            collection_name=ctx.context.collection_id,
            k=5,
        )
        items = [doc.page_content for doc in results]
        return items

    async def parse_page_with_llm(
        self, page_text, max_retries=3
    ) -> ItemChunkDto:
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
                messages = [{"role": "system", "content": SYSTEM_PROMPT_LLM_CHUNKING}]
                if retry_count > 0:
                    error_message = (
                        f"The previous attempt failed with error: {last_error}\n"
                        f"Please correct the following issues in your response: {error_context}\n"
                        f"This is retry attempt {retry_count} of {max_retries}."
                    )
                    messages.append({"role": "user", "content": page_text})
                    messages.append(
                        {"role": "assistant", "content": "I'll parse this content."}
                    )
                    messages.append({"role": "user", "content": error_message})
                else:
                    messages.append({"role": "user", "content": page_text})

                # Make API call
                logger.info(
                    f"Sending request to LLM (attempt {retry_count + 1}/{max_retries + 1})"
                )
                completion = self.openaiClient.chat.completions.create(
                    model=self.model,
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
                logger.info(
                    f"Successfully parsed {len(parsed_items)} items after {retry_count + 1} attempts"
                )
                return parsed_items

            except json.JSONDecodeError as e:
                last_error = f"JSON parsing error: {str(e)}"
                error_context = "Your response isn't valid JSON. Please ensure proper JSON formatting."
                logger.warning(
                    f"Retry {retry_count + 1}/{max_retries + 1}: {last_error}"
                )

            except ValueError as e:
                last_error = f"Validation error: {str(e)}"
                error_context = f"Please fix the structure of your response: {str(e)}"
                logger.warning(
                    f"Retry {retry_count + 1}/{max_retries + 1}: {last_error}"
                )

            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                error_context = "An unexpected error occurred. Please provide a properly formatted response."
                logger.warning(
                    f"Retry {retry_count + 1}/{max_retries + 1}: {last_error}",
                    exc_info=True,
                )

            # Increment retry counter
            retry_count += 1

        # If we get here, all retries failed
        logger.error(
            f"Failed to parse content after {max_retries + 1} attempts. Last error: {last_error}"
        )
        raise Exception(
            f"Failed to parse content after {max_retries + 1} attempts: {last_error}"
        )


if __name__ == "__main__":
    with open("..\..\specWise\core\parsed_items_example_1.json", "r") as datei:
        json_obj = json.load(datei)
