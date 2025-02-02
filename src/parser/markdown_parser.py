import re

class MarkdownParser:
    def __init__(self):
        pass

    def parse(self, markdown_file):
        with open(markdown_file, 'r') as f:
            content = f.read()
        # Extract markers within double square brackets
        markers = re.findall(r'\[\[(.*?)\]\]', content)
        # Remove markers to get plain text
        plain_text = re.sub(r'\[\[.*?\]\]', '', content).strip()
        return {'text': plain_text, 'markers': markers}
