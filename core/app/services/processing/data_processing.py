from typing import List
from app.models.models import ItemDto, ItemChunkDto
from app.services.llm.llm import OpenAILlmService
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer


class DataProcessingService:
    def __init__(self):
        self.llm_service = OpenAILlmService()

    def extract_pages_as_text(self, pdf_path: str):
        pages = []
        for page_layout in extract_pages(pdf_path):
            lines = []
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    lines.append(element.get_text())
            pages.append("\n".join(lines))
        return pages

    def get_page_windows(self, pages, window_size=2):
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

    def process_data(self, pages):
        parsed_items: List[ItemChunkDto] = []
        for i, page_window in self.get_page_windows(pages, window_size=2):
            print(f"🧠 Parsing pages {i+1}-{i+2} / {len(pages)}")
            try:
                response: List[ItemChunkDto] = self.llm_service.parse_page_with_llm(
                    page_window
                )
                parsed_items.extend(response)
            except Exception as e:
                print(f"❌ Failed at pages {i+1}-{i+2}: {e}")

        seen = {}
        final_items = []

        for item in parsed_items:
            ref = item.ref_no.strip()
            desc = item.description.strip()

            if ref not in seen:
                seen[ref] = item
                final_items.append(item)
            else:
                existing_desc = seen[ref].description
                if desc not in existing_desc:
                    merged = f"{existing_desc.strip()} {desc}".strip()
                    seen[ref].description = merged

        return final_items
