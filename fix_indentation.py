"""
Fix indentation issues in white_blood_cell.py file
"""

def fix_indentation():
    with open('src/organisms/white_blood_cell.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Fix the if block at line 372-373
    if len(lines) >= 373 and 'if distance < 50:' in lines[371]:
        # Check if the next line has proper indentation
        if 'chase_speed *= 1.2' in lines[372]:
            # Indent the line with exactly 20 spaces (16 from parent + 4 more)
            lines[372] = '                    chase_speed *= 1.2  # Extra speed boost when close\n'
    
    # Fix the broken structure around line 1373-1380
    if len(lines) >= 1380:
        # We need to properly indent the pygame.draw.line within the for loop
        for i in range(1350, 1375):
            if "for i in range(line_segments):" in lines[i]:
                for_loop_line = i
                break
        
        # Find the if i % 2 == 0 block
        for i in range(for_loop_line + 1, for_loop_line + 20):
            if "if i % 2 == 0:" in lines[i]:
                if_line = i
                break
        
        # Find the pygame.draw.line line
        for i in range(1370, 1380):
            if "pygame.draw.line(" in lines[i]:
                pygame_line = i
                break
        
        # Adjust indentation for pygame.draw.line to be inside the for loop and if block
        if 'pygame.draw.line(' in lines[pygame_line]:
            # It should have same indentation as other lines inside the if block
            lines[pygame_line] = '                        pygame.draw.line(\n'
            # Also fix the next few lines
            for j in range(pygame_line + 1, pygame_line + 5):
                if j < len(lines):
                    stripped = lines[j].lstrip()
                    if stripped:
                        lines[j] = '                            ' + stripped
        
        # Check if there's an 'else:' that needs to be at the same level as the if
        for i in range(pygame_line + 4, pygame_line + 10):
            if i < len(lines) and 'else:' in lines[i]:
                # It should have same indentation as the original if
                lines[i] = '                ' + lines[i].lstrip()
                
                # Also fix the indentation of the block after the else
                for j in range(i + 1, i + 10):
                    if j < len(lines):
                        stripped = lines[j].lstrip()
                        if stripped and not stripped.startswith(('else', 'elif')):
                            lines[j] = '                    ' + stripped
    
    with open('src/organisms/white_blood_cell_fixed.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("File has been fixed and saved as src/organisms/white_blood_cell_fixed.py")

if __name__ == "__main__":
    fix_indentation() 