from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
import json
import os
import requests

# from core.app.services.processing.data_processing import DataProcessing


# api_key = os.getenv("OPENROUTER_API_KEY")


# SYSTEM_PROMPT = """
# You are a precise parser for German service specification documents (Leistungsverzeichnis).
# Each document contains a list of items that describe products or services used in construction or procurement.

# Your task is to extract every item that contains:
# - A reference number (Ordnungszahl), e.g., "01.1", "04.01.2", "1.2.10", "1.2.25", "1.2.35"
# - A free-text description (can span multiple lines)
# - A quantity (Menge) with unit, e.g., "1.000 Stk", "15 h", or "80,5 m²"

# The reference number can be in many different formats,
# if you think something can be a reference number then be conservative and generate the item.
# Missing an item is much worse than having an extra item.

# Do not ignore descriptions which start with or contain:
# - Symbols such as ***, ---, - etc.
# - Words such as Bedarfsposition or Alternativpostion

# Pay special attention to German number formatting:
# - The **comma** is a decimal separator (e.g., "80,5" means 80.5)
# - The **dot** is a thousands separator (e.g., "1.000" means 1000)
# - Some values like "1,000" are **not** 1000 — in German this means 1.0

# Units are usually abbreviated and may include:
# - "Stk", "St", "h", "m²", "kg", etc.

# Return only valid JSON in the exact format:

# {
#   "items": [
#     {
#       "ref_no": "string",
#       "description": "string",
#       "quantity": float,
#       "unit": "string"
#     },
#     ...
#   ]
# }

# Strictly output only JSON — no markdown, commentary, or extra text.
# If multiple items are on the same page, return them all in the array.
# If a value is missing or unclear, make your best guess based on the context.
# """


# def extract_pages_as_text(pdf_path):
#     pages = []
#     for page_layout in extract_pages(pdf_path):
#         lines = []
#         for element in page_layout:
#             if isinstance(element, LTTextContainer):
#                 lines.append(element.get_text())
#         pages.append("\n".join(lines))
#     return pages


# def get_page_windows(pages, window_size=2):
#     """
#     Yields joined page text in overlapping windows, with page headers.
#     For example: [Page 1 + Page 2], [Page 2 + Page 3], ...
#     """
#     for i in range(len(pages) - window_size + 1):
#         chunk = ""
#         for j in range(window_size):
#             page_num = i + j + 1
#             chunk += f"\n\n### PAGE {page_num}\n{pages[i + j]}"
#         yield (i, chunk)


# def parse_page_with_llm(page_text, system_prompt, api_key, model="openai/gpt-4o-mini"):
#     url = "https://openrouter.ai/api/v1/chat/completions"

#     headers = {
#         "Authorization": f"Bearer {api_key}",
#         "Content-Type": "application/json",
#         # Optional headers:
#         "HTTP-Referer": "http://localhost:3000",  # or your project URL
#         "X-Title": "specwise-pdf-parser",
#     }

#     payload = {
#         "model": model,
#         "response_format": {"type": "json_object"},
#         "temperature": 0,
#         "max_tokens": 4096,
#         "messages": [
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": page_text},
#         ],
#     }

#     response = requests.post(url, headers=headers, data=json.dumps(payload))

#     if response.status_code != 200:
#         raise Exception(f"OpenRouter API error {response.status_code}: {response.text}")

#     data = response.json()

#     return json.loads(data["choices"][0]["message"]["content"])


# if __name__ == "__main__":
#     pages = extract_pages_as_text(test_pdf_path)
#     parsed_items = []

#     for i, page_window in get_page_windows(pages, window_size=2):
#         print(f"🧠 Parsing pages {i+1}-{i+2}")
#         try:
#             response = parse_page_with_llm(page_window, SYSTEM_PROMPT, api_key)
#             parsed_items.extend(response["items"])
#         except Exception as e:
#             print(f"❌ Failed at pages {i+1}-{i+2}: {e}")

#     seen = {}
#     final_items = []

#     for item in parsed_items:
#         ref = item["ref_no"]
#         desc = item["description"].strip()

#         if ref not in seen:
#             # First time seeing this ref_no
#             seen[ref] = item
#             final_items.append(item)
#         else:
#             # Ref already exists → merge descriptions
#             existing_desc = seen[ref]["description"]
#             if desc not in existing_desc:
#                 merged = f"{existing_desc.strip()} {desc}".strip()
#                 seen[ref]["description"] = merged

#     with open(f"parsed_items_example_{example_num}.json", "w", encoding="utf-8") as f:
#         json.dump(final_items, f, ensure_ascii=False, indent=2)


def expand_referenced_descriptions(items, api_key, model="openai/gpt-4o-mini"):
    """
    Takes a list of parsed Leistungsverzeichnis items, finds internal references like "wie Pos. X",
    and adds a new field 'referenced_description' using an LLM via OpenRouter.
    """

    SYSTEM_PROMPT = """
    You are refining data from a German service specification (Leistungsverzeichnis).

    Each item has a `ref_no`, a `description`, and possibly references to another item via phrases like:
    - "wie Pos. 10"
    - "siehe Pos. 1.2.35"
    - "entspricht Pos. X"

    Your task:
    - For each `target_item`, if a reference is detected in its description, set a new field: `references_id`
    - The value of `references_id` must exactly match a `ref_no` that appears in the full `all_items` list

    Only modify `target_items`. Do not add, remove, or reorder items.
    If no valid reference is found, omit the `references_id` field.

    Return ONLY the modified `target_items` list, using this schema:
    [
    {
        "ref_no": "string",
        "description": "string",
        "quantity": float,
        "unit": "string",
        "references_id": "string (optional)"
    },
    ...
    ]

    Strictly output only valid JSON — no extra text, no markdown, no commentary.
    """

    # OpenRouter endpoint and headers
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "specwise-reference-expander",
    }

    # Build request payload
    payload = {
        "model": model,
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "max_tokens": 4096,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps({"items": items}, ensure_ascii=False),
            },
        ],
    }

    # Make the request
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # Handle errors
    if response.status_code != 200:
        raise Exception(f"OpenRouter API error {response.status_code}: {response.text}")

    # Parse response
    data = response.json()
    return data["choices"][0]["message"]["content"]


def chunk_list(lst, size=10):
    """Yield successive `size`-sized chunks from list `lst`."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


SYSTEM_PROMPT = """
You are refining a single item from a German service specification document (Leistungsverzeichnis).

Each item has:
- a `ref_no` (like "01.1" or "1.2.35")
- a `description` that might reference another position using text like:
  - "wie Pos. X"
  - "siehe Pos. X"
  - "entspricht Pos. X"

Your task:
- Examine the `description` of `target_item` carefully.
- If it contains a clear and explicit reference to another position listed in `all_items`, extract the corresponding `ref_no`.
- Only extract references if the wording is **specific and unambiguous**.
- In cases like `"wie Pos. 10"` (without a full `ref_no`), match the closest item in `all_items` **above** the target_item whose `ref_no` ends in `.10` or `10`. 
  Examples:

  (i)
  1.2.30: Wie Pos 10.
  Should map to 1.2.10 and NOT 1.1.10.

  (ii)
  1.4.40: Wie Pos 25.
  Should map to 1.4.25 and NOT 1.2.25.

- If the description includes `"wie Vorposition"` then the ref_no is the one of the item directly before the target_item in the all_items list,
  do **not** populate a reference unless the intent is absolutely clear.
- If the item appears to be a supplement (e.g., "Zulage", or an add-on to another item), skip adding a reference even if a reference-like phrase is present.
- If a valid reference is found, add a new field: `"references_id"` with the matched `ref_no` as its value.

Only modify the given `target_item`.

Return a **single JSON object** using this schema:

{
  "ref_no": "string",
  "description": "string",
  "quantity": float,
  "unit": "string",
  "references_id": "string (optional)"
}

Strictly return only JSON — no markdown, no commentary.
Ensure all quotes and braces are properly closed.
"""


def resolve_single_item(item, all_items, api_key, model="openai/gpt-4o-mini"):

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "specwise-ref-id-single",
    }

    payload = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "max_tokens": 2048,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {"target_item": item, "all_items": all_items}, ensure_ascii=False
                ),
            },
        ],
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code != 200:
        raise Exception(f"OpenRouter API error {response.status_code}: {response.text}")

    raw = response.json()["choices"][0]["message"]["content"]

    # Clean and parse
    trimmed = raw.strip()
    try:
        return json.loads(trimmed)
    except json.JSONDecodeError as e:
        print("❌ Failed to parse response:\n", trimmed[:500])
        raise e


def resolve_all_items_one_by_one(items, api_key):
    updated = []

    for i, item in enumerate(items):
        print(f"🔍 Resolving item {i+1}/{len(items)}: {item['ref_no']}")
        try:
            new_item = resolve_single_item(item, items, api_key)
            updated.append(new_item)
        except Exception as e:
            print(f"⚠️ Skipping item {item['ref_no']} due to error: {e}")
            updated.append(item)  # fallback to original

    return updated


api_key = os.getenv("OPENROUTER_API_KEY")
example_num = 1
test_pdf_path = (
    f"app/docs/data-for-participants/Example-{example_num}/service-specification.pdf"
)

if __name__ == "__main__":
    # data_processing = DataProcessing()

    # data = data_processing.process_data(test_pdf_path)

    with open(f"parsed_items_example_{example_num}.json", "r", encoding="utf-8") as f:
        items = json.load(f)

    data_expanded = resolve_all_items_one_by_one(items, api_key=api_key)

    with open(
        f"parsed_items_example_{example_num}_expanded.json", "w", encoding="utf-8"
    ) as f:
        json.dump(data_expanded, f, ensure_ascii=False, indent=2)
