
from core.app.services.llm.prompts import CATEGORIZATION_PROMPT
from envirnoment import config
from openai import OpenAI


class OpenAILlm:
    def __init__(self, api_key: str):
        self.api_key = api_key
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
        ## other llms methods
        return "return"
