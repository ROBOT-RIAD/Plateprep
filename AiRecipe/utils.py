import re

def parse_ai_recipe_response(text):
    title = re.search(r"### Recipe Name:\s*(.+)", text)
    description = re.search(r"### Description:\s*(.+?)#### Ingredients:", text, re.DOTALL)
    ingredients = re.search(r"#### Ingredients:\s*(.+?)#### Instructions:", text, re.DOTALL)
    instructions = re.search(r"#### Instructions:\s*(.+)", text, re.DOTALL)

    return {
        "title": title.group(1).strip() if title else "Untitled Recipe",
        "description": description.group(1).strip() if description else "",
        "ingredients": ingredients.group(1).strip() if ingredients else "",
        "instructions": instructions.group(1).strip() if instructions else "",
    }