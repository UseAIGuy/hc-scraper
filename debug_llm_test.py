import json
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai import LLMConfig

HTML_SNIPPET = """
<html><body>
  <a class='venue-list-item' href='/foo/bar-123'>Green Garden</a>
  <a class='venue-list-item' href='/baz/qux-456'>Vegan Delight</a>
</body></html>
"""

def main():
    strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="ollama/llama2",
            base_url="http://localhost:11434"
        ),
        instruction=(
            "Return a JSON array where each element has keys 'name' and 'url' "
            "representing the text and href of anchor tags in the HTML."
        ),
        schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "url": {"type": "string"}
                },
                "required": ["name", "url"]
            }
        },
        extraction_type="schema",
        preprocess_html="nano",
        html_max_chars=5000,
        extra_args={"temperature": 0.1}
    )

    print("Calling LLM via Crawl4AI…")
    try:
        extracted = strategy.extract(HTML_SNIPPET)
        print("\nModel response:\n", extracted)
        # Pretty print if JSON
        try:
            print("\nJSON parsed:\n", json.dumps(json.loads(extracted), indent=2))
        except Exception:
            pass
    except Exception as e:
        import traceback, sys
        print("ERROR during extraction:")
        traceback.print_exc(file=sys.stdout)

if __name__ == "__main__":
    main() 