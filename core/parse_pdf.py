from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
import json
import os
import requests

api_key = os.getenv("OPENROUTER_API_KEY")


SYSTEM_PROMPT = """
You are a precise parser for German service specification documents (Leistungsverzeichnis).
Each document contains a list of items that describe products or services used in construction or procurement.

Your task is to extract every item that contains:
- A reference number (Ordnungszahl), e.g., "01.1", "04.01.2", "1.2.10", "1.2.25", "1.2.35"
- A free-text description (can span multiple lines)
- A quantity (Menge) with unit, e.g., "1.000 Stk", "15 h", or "80,5 m²"

The reference number can be in many different formats, 
if you think something can be a reference number then be conservative and generate the item.
Missing an item is much worse than having an extra item.

Do not ignore descriptions which start with or contain:
- Symbols such as ***, ---, - etc. 
- Words such as Bedarfsposition or Alternativpostion

Pay special attention to German number formatting:
- The **comma** is a decimal separator (e.g., "80,5" means 80.5)
- The **dot** is a thousands separator (e.g., "1.000" means 1000)
- Some values like "1,000" are **not** 1000 — in German this means 1.0

Units are usually abbreviated and may include:
- "Stk", "St", "h", "m²", "kg", etc.

Return only valid JSON in the exact format:

{
  "items": [
    {
      "ref_no": "string",
      "description": "string",
      "quantity": float,
      "unit": "string"
    },
    ...
  ]
}

Strictly output only JSON — no markdown, commentary, or extra text.
If multiple items are on the same page, return them all in the array.
If a value is missing or unclear, make your best guess based on the context.
"""


def extract_pages_as_text(pdf_path):
    pages = []
    for page_layout in extract_pages(pdf_path):
        lines = []
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                lines.append(element.get_text())
        pages.append("\n".join(lines))
    return pages


def get_page_windows(pages, window_size=2):
    """
    Yields joined page text in overlapping windows, with page headers.
    For example: [Page 1 + Page 2], [Page 2 + Page 3], ...
    """
    for i in range(len(pages) - window_size + 1):
        chunk = ""
        for j in range(window_size):
            page_num = i + j + 1
            chunk += f"\n\n### PAGE {page_num}\n{pages[i + j]}"
        yield (i, chunk)


def parse_page_with_llm(page_text, system_prompt, api_key, model="openai/gpt-4o-mini"):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # Optional headers:
        "HTTP-Referer": "http://localhost:3000",  # or your project URL
        "X-Title": "specwise-pdf-parser",
    }

    payload = {
        "model": model,
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "max_tokens": 4096,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": page_text},
        ],
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code != 200:
        raise Exception(f"OpenRouter API error {response.status_code}: {response.text}")

    data = response.json()

    return json.loads(data["choices"][0]["message"]["content"])


example_num = 2
test_pdf_path = (
    f"../data-for-participants/Example-{example_num}/service-specification.pdf"
)

if __name__ == "__main__":
    pages = extract_pages_as_text(test_pdf_path)
    parsed_items = []

    for i, page_window in get_page_windows(pages, window_size=2):
        print(f"🧠 Parsing pages {i+1}-{i+2}")
        try:
            response = parse_page_with_llm(page_window, SYSTEM_PROMPT, api_key)
            parsed_items.extend(response["items"])
        except Exception as e:
            print(f"❌ Failed at pages {i+1}-{i+2}: {e}")

    seen = {}
    final_items = []

    for item in parsed_items:
        ref = item["ref_no"]
        desc = item["description"].strip()

        if ref not in seen:
            # First time seeing this ref_no
            seen[ref] = item
            final_items.append(item)
        else:
            # Ref already exists → merge descriptions
            existing_desc = seen[ref]["description"]
            if desc not in existing_desc:
                merged = f"{existing_desc.strip()} {desc}".strip()
                seen[ref]["description"] = merged

    with open(f"parsed_items_example_{example_num}.json", "w", encoding="utf-8") as f:
        json.dump(final_items, f, ensure_ascii=False, indent=2)
