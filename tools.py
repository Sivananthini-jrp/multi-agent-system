from langchain_core.tools import tool


@tool
def calculate(expression: str) -> str:
    """Safely evaluate a basic math expression. Example: '2 + 2'."""
    try:
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "Error: only basic math allowed."
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Calculation error: {e}"


@tool
def word_count(text: str) -> str:
    """Count words and characters in text."""
    return f"Words: {len(text.split())}, Characters: {len(text)}"