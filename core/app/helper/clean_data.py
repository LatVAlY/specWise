from typing import Any, Dict, List

from app.models.models import ItemDto


def expand_references(self, items: List[ItemDto]) -> List[Dict[str, Any]]:
    """Expand references like 'wie Pos. 10' to full descriptions."""
    expanded_items = []

    for item in items:
        if "wie Pos." in item.description:
            ref_pos = (
                item.description.split("wie Pos.")[1].strip().split(",")[0].strip()
            )

            for ref_item in items:
                if ref_item.ref_no.endswith(ref_pos):
                    new_item = item.copy()
                    new_item.description = (
                        ref_item.description + "\n" + item.description
                    )
                    expanded_items.append(new_item)
                    break
            else:
                expanded_items.append(item)
        else:
            expanded_items.append(item)

    return expanded_items
