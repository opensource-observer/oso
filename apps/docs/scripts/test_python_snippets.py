import os
import re
import sys
import glob

def extract_code_blocks(filepath):
    """Extracts python code blocks from a markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to capture python code blocks, allowing for indentation
    # Supports ```python and ```py
    # Captures the content of the block
    pattern = re.compile(r'^\s*```(?:python|py)\n(.*?)^\s*```', re.DOTALL | re.MULTILINE)
    blocks = pattern.findall(content)
    return blocks

def run_code_block(code, index, filepath):
    """Executes a single code block."""
    print(f"Running block {index} from {filepath}...")
    try:
        exec(code, {'__name__': '__main__'})
        print(f"Block {index} passed.")
        return True
    except Exception as e:
        print(f"Block {index} failed with error: {e}")
        return False

def main():
    # Only target specific files for now to be safe
    # Or scan all but filter
    # Let's start with scanning specific files known to have runnable code
    target_files = [
        "apps/docs/docs/get-started/python.md",
        # Add more files here as we verify them
    ]
    
    # Also support scanning based on arguments
    if len(sys.argv) > 1:
        target_files = sys.argv[1:]

    failed_count = 0
    total_count = 0

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    
    for relative_path in target_files:
        filepath = os.path.join(root_dir, relative_path)
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue

        print(f"Processing {filepath}...")
        blocks = extract_code_blocks(filepath)
        
        for i, block in enumerate(blocks):
            # Check for skip comment or unsafe operations if needed
            # For now, simplistic execution
            # Consider adding logic to check previous line for <!-- skip-test -->
            
            # Simple heuristic: if block contains "your_api_key", replace it with env var if available,
            # or skip if not.
            # Actually, the example in python.md sets it: os.environ["OSO_API_KEY"] = 'your_api_key'
            # We should probably Inject the real key from env if it's there.
            
            # Monkey-patching the code to use real key if present in env
            if os.environ.get("OSO_API_KEY"):
                if "your_api_key" in block:
                    block = block.replace("'your_api_key'", f"'{os.environ['OSO_API_KEY']}'")
                    block = block.replace('"your_api_key"', f"'{os.environ['OSO_API_KEY']}'")
            else:
                 print(f"Skipping block {i+1} due to missing OSO_API_KEY env var.")
                 continue

            total_count += 1
            if not run_code_block(block, i + 1, relative_path):
                failed_count += 1

    print(f"\nTest Summary: {total_count - failed_count}/{total_count} blocks passed.")
    if failed_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
