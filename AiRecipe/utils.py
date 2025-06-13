import re

def parse_ai_recipe_response(text):
    title = re.search(r"### Recipe Name:\s*(.+)", text)
    ingredients = re.search(r"#### Ingredients:\s*(.+?)#### Instructions:", text, re.DOTALL)
    instructions = re.search(r"#### Instructions:\s*(.+)", text, re.DOTALL)

    return {
        "title": title.group(1).strip() if title else "Untitled Recipe",
        "ingredients": ingredients.group(1).strip() if ingredients else "",
        "instructions": instructions.group(1).strip() if instructions else "",
    }