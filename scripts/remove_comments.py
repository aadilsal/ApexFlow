import os
import re
import sys

# Configuration
IGNORE_DIRS = {
    'node_modules', '.venv', '.git', '__pycache__', '.dvc', 
    'dist', 'build', '.next', 'coverage'
}
TARGET_EXTENSIONS = {
    '.py': 'python',
    '.ts': 'js',
    '.tsx': 'js',
    '.js': 'js',
    '.jsx': 'js'
}

def remove_python_comments(text):
    """
    Remove Python comments using regex.
    Preserves comments inside strings.
    """
    # Pattern groups:
    # 1. Triple-quoted strings (double or single)
    # 2. String literals (double or single)
    # 3. Comments (# followed by anything)
    pattern = r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"(?:\\.|[^"\\])*"|\'(?:\\.|[^"\\])*\')|(#.*)'
    
    def replacer(match):
        # If group 2 (comment) is matched, replace with empty string
        if match.group(2):
            return ""
        # Otherwise, it's a string, return as is
        return match.group(1)
        
    return re.sub(pattern, replacer, text)

def remove_js_comments(text):
    """
    Remove JS/TS comments using regex.
    Preserves comments inside strings.
    """
    # Pattern groups:
    # 1. String literals (double, single, backtick)
    # 2. Multi-line comments (/* ... */)
    # 3. Single-line comments (// ...)
    pattern = r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^"\\])*\'|`(?:\\.|[^`\\])*`)|(/\*[\s\S]*?\*/|//.*)'
    
    def replacer(match):
        # If group 2 is matched, it's a comment
        if match.group(2):
             return " " if match.group(2).startswith("/*") else "" # Replace block comment with space effectively/safely, or empty?
             # Empty for // is fine. 
             # Empty for /* */ might join tokens incorrectly: var a/* */b -> var ab.
             # So safely replace block comments with a space.
        # Otherwise keep string
        return match.group(1)
        
    # First pass: replace comments
    # Note: Regex literals in JS (/abc/) are tricky and not handled here.
    # This assumes standard code where comments are not embedded in regex that looks like comments.
    result = re.sub(pattern, replacer, text)
    return result

def clean_file(filepath, lang):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if lang == 'python':
            new_content = remove_python_comments(content)
        elif lang == 'js':
            new_content = remove_js_comments(content)
        else:
            return

        if content != new_content:
            print(f"Cleaning: {filepath}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

def main():
    root_dir = os.getcwd()
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]

    print(f"Scanning directory: {root_dir}")
    print("Removing comments...")

    for root, dirs, files in os.walk(root_dir):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in TARGET_EXTENSIONS:
                filepath = os.path.join(root, file)
                clean_file(filepath, TARGET_EXTENSIONS[ext])

    print("Done.")

if __name__ == "__main__":
    main()
