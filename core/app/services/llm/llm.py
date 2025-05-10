import json
import requests
from typing import List, Dict, Tuple
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


    def categorize(self, json_list: List) -> Dict[int, Tuple[str, str]]:
        for i, entry in enumerate(json_list):
            if entry["reference_id"] is not None:
                for parent_chunk in json_list:
                    if parent_chunk["reference_id"] is not None and parent_chunk["ref_no"] == entry["reference_id"]:
                        long_text_of_parent = entry["description"] + parent_chunk["description"]

            dict_chunk_to_response = {}
            completion = self.openaiClient.chat.completions.create(
                model="openai/gpt-4o-mini",
                    messages=[
                    {
                        "role": "system",
                        "content": CATEGORIZATION_PROMPT
                    },
                    {
                        "role": "user",
                        "content": f"This is the content: {entry}.\nUse the following description to match the sku number and for every other data we asked you, you dismiss the following, longer description: {long_text_of_parent}"
                    }
                    ]
                ,
            )
            # Prepare response:
            answer_string = completion.choices[0].message.content
            if answer_string is not None:
                answer_json = json.loads(answer_string)
                # print(f"Processed {i+1}|{len(json_list)}")
                dict_chunk_to_response[i] = (entry, answer_json['choices'][0]['message']['content'])  # Returns only the answer text.
        return dict_chunk_to_response


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


if __name__ == "__main__":
    with open('..\..\specWise\core\parsed_items_example_1.json', 'r') as datei:
        json_obj = json.load(datei)

    dict = OpenAILlmService().categorize(json_obj)
    for i, value in dict.items():
        print("Chunk: ", i, " ", value)