CATEGORIZATION_PROMPT = """"
You are a helpful assistant that categorizes text into one of the following categories:
1
"""




SYSTEM_PROMPT_LLM_CHUNKING = """
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
