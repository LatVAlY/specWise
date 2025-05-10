
import json
from typing import List
from app.models.models import ItemDto
from app.services.llm.prompts import CATEGORIZATION_PROMPT, SYSTEM_PROMPT_LLM_CHUNKING
from openai import OpenAI
from app.envirnoment import config


class OpenAILlmService:
    def __init__(self):
        self.openaiClient = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config["OPENROUTE_API_KEY"],
        )

    def categorize(self) -> str:

        completion = self.client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": CATEGORIZATION_PROMPT},
                {"role": "user", "content": "What is the meaning of life?"},
            ],
        )

        print(completion.choices[0].message.content)

        return "return"

    def parse_page_with_llm(self, page_text, model="openai/gpt-4o-mini") -> ItemDto:

        completion = self.openaiClient.chat.completions.create(
            model=model,
            max_tokens=4096,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_LLM_CHUNKING},
                {"role": "user", "content": page_text},
            ],
        )
        if completion.status_code != 200:
            raise Exception(
                f"OpenRouter API error {completion.status_code}: {completion.text}"
            )
        content = completion.choices[0].message.content
        data = json.loads(content)
        items = data.get("items", [])
        parsed_items = [ItemDto().from_dict(item) for item in items]
        return parsed_items
        