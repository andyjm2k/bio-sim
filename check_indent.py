"""
Check indentation issues in a Python file.
This script dumps the raw bytes of each line to identify indentation issues.
"""

def dump_line_bytes(filename, start_line, end_line):
    with open(filename, 'rb') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines[start_line-1:end_line], start_line):
        print(f"Line {i}: {line.hex()}")
        # Also print the line with visible characters for spaces/tabs
        text_line = line.decode('utf-8', errors='replace')
        visible = ""
        for char in text_line:
            if char == ' ':
                visible += '·'
            elif char == '\t':
                visible += '→'
            else:
                visible += char
        print(f"Readable: {visible}")

if __name__ == "__main__":
    dump_line_bytes("src/organisms/white_blood_cell.py", 367, 380) 