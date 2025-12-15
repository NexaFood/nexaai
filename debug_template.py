import re

path = 'templates/design_project_detail.html'

with open(path, 'r') as f:
    lines = f.readlines()

stack = []

# Regex to find tags
tag_pattern = re.compile(r'{%\s*(if|for|block|endif|endfor|endblock|elif|else)\s+.*?%}')

for i, line in enumerate(lines):
    line_num = i + 1
    matches = tag_pattern.finditer(line)
    for match in matches:
        tag_content = match.group(0)
        tag_type = match.group(1)
        
        if tag_type in ['if', 'for', 'block']:
            stack.append((tag_type, line_num, tag_content))
            print(f"{line_num}: OPEN {tag_type}")
        elif tag_type in ['endif', 'endfor', 'endblock']:
            if not stack:
                print(f"{line_num}: ERROR - Unmatched {tag_type}")
                break
            
            last_type, last_line, _ = stack[-1]
            expected_end = 'end' + last_type
            
            if tag_type == expected_end:
                stack.pop()
                print(f"{line_num}: CLOSE {last_type} (from {last_line})")
            else:
                print(f"{line_num}: ERROR - Mismatch! Found {tag_type}, expected {expected_end} (for open {last_type} at {last_line})")
                exit(1)
        elif tag_type in ['elif', 'else']:
            if not stack:
                 print(f"{line_num}: ERROR - Orphaned {tag_type}")
            else:
                 print(f"{line_num}: CONT {stack[-1][0]} (from {stack[-1][1]})")

if stack:
    print("ERROR - Unclosed tags at end of file:")
    for tag in stack:
        print(f"  {tag[0]} at line {tag[1]}")
else:
    print("Structure seems valid.")
