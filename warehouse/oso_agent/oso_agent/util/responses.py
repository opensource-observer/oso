from markdown_it import MarkdownIt


def ensure_no_code_block(markdown_string: str):
    """Ensures that the given string is not wrapped in a markdown code block.

    This expects only a single code block. If there are multiple code blocks,
    it will return the entire string as is.
    """
    try:
        md = MarkdownIt()
        tokens = md.parse(markdown_string)

        code_blocks = []
        for token in tokens:
            if token.type == "fence":
                code_blocks.append(token.content)

        if len(code_blocks) != 1:
            return markdown_string

        return code_blocks[0]
    except Exception:
        return markdown_string
