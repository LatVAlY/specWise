
def append_to_prompt(prompt: str, text: str) -> str:
    """
    Append text to the prompt and return the updated prompt.
    """
    return f"{prompt}\n{text}"

CATEGORIZATION_PROMPT = """"
### You are a helpful assistant that categorizes each JSON item into the following categories, only if the item exists also in our service offer list.

If you find text with a value starting with **"wie Pos."**, it indicates a reference to another item. In this case, you must populate the current item's **description only** with the description of the matching referenced item from the `all_already_parsed_items` list provided.

#### Reference Matching Logic:

* Look for the **most recent previous item** in the `all_items` list whose `commission` ends with the referenced number (e.g., `.10` or `10`) and is in the **same parent group**.

  * **Example (i):**
    `1.2.30: Wie Pos. 10.` → should match `1.2.10`, **not** `1.1.10`.
  * **Example (ii):**
    `1.4.40: Wie Pos. 25.` → should match `1.4.25`, **not** `1.2.25`.
* Only copy the **description** from the referenced item and append it. Keep all other values (quantity, price, etc.) from the current item.

---

### GUIDELINES:

* **From each entry, extract the description and compare semantically with our service offer list.**
* **Use semantic understanding (including synonyms and context) to determine the category.**
* **If the description contains “Alternative” or “Wahlposition”, prepend `"Alternative"` to the name.**
* **Rate the confidence of the categorization on a scale from 0 to 1** based on the criteria below:

  * `1.0`: Exact match from service offer
  * `0.8`: Strong synonym or phrase-level match
  * `0.5`: Weak or partial semantic match
  * `< 0.5`: Unclear or insufficient match (skip the item)
* **If no match is found, skip the item without mention.**
* **If dimensions (e.g., “750 x 2.125 mm”) appear in the description, append them in parentheses to the `name`.**
* **If required fields (e.g., description or commission) are missing, skip the item entirely. Optional fields may be set to null.**
---

### IMPORTANT:
* **You must use the SKU for the respected item given**
* **You must use the item title for the respected item given, do not reuse some other item title!!**
* **If the item is referenced like "wie Pos. 10" then you must only use the description of the referensed title, nothing else**


### Service Offer List with SKU Numbers:

* **Holztüren, Holzzargen**: `620001`
* **Stahltüren, Stahlzargen, Rohrrahmentüren**: `670001`
* **Haustüren**: `660001`
* **Glastüren**: `610001`
* **Tore**: `680001`
* If the description includes combinations like **“Holztürblatt mit Stahlzarge”**, then use `620001`.
* If the description includes **“Verglasung mit Stahlzarge”**, then use `670001`.
* **Beschläge**: `240001`
* **Türstopper**: `330001`
* **Lüftungsgitter**: `450001`
* **Türschließer**: `290001`
* **Schlösser / E-Öffner**: `360001`
* **Wartung**: `DL8110016`
* **Stundenlohnarbeiten**: `DL5010008`
* **Sonstige Arbeiten (e.g., Baustelleneinrichtung, Aufmaß, Mustertürblatt, etc.)**: `DL5019990`

---

### Output Format:

Return your result in the following JSON structure. Use lowercase keys exactly as shown:

{
  "items": [
    {
      "sku": "string",
      "name": "string",
      "text": "string",
      "quantity": int default 0,
      "quantityunit": "string" default "Stk",
      "price": float default 0,
      "priceunit": "string" default "EUR",
      "commission": "string",
      "confidence": float
    },
    ...
  ]
}

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

## GUIDLINES:

- If the description includes `"wie Vorposition"` then the ref_no is the one of the item directly before the target_item in the all_items list,
  do **not** populate a reference unless the intent is absolutely clear.
- If the item appears to be a supplement (e.g., "Zulage", or an add-on to another item), skip adding a reference even if a reference-like phrase is present.
- If a valid reference is found, add a new field: `"references_id"` with the matched `ref_no` as its value.

Do not ignore descriptions which start with or contain:
- Symbols such as ***, ---, - etc. 
- Words such as Bedarfsposition or Alternativpostion

Pay special attention to German number formatting:
- The **comma** is a decimal separator (e.g., "80,5" means 80.5)
- The **dot** is a thousands separator (e.g., "1.000" means 1000)
- Some values like "1,000" are **not** 1000 — in German this means 1.0

Units are usually abbreviated and may include:
- "Stk", "St", "h", "m²", "kg", etc.

- In cases like `"wie Pos. 10"` (without a full `ref_no`), match the closest item in `all_items` **above** the target_item whose `ref_no` ends in `.10` or `10`. 
  Examples:

  (i)
  1.2.30: Wie Pos 10.
  Should map to 1.2.10 and NOT 1.1.10.

  (ii)
  1.4.40: Wie Pos 25.
  Should map to 1.4.25 and NOT 1.2.25.

  
Important if you find Wahlposition you must add to the description "Alternative" word

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
