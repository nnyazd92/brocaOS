#!/usr/bin/env python3
"""
Apply v5.8.0 patches for new feedback integration
"""

import re
from pathlib import Path

def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()

def write_file(filename, content):
    with open(filename, 'w') as f:
        f.write(content)

def apply_particle_downgrades(content):
    """Apply particle physics downgrades"""
    print("Applying particle physics downgrades...")
    
    # Find the electron defect theorem section
    # Look for "Uniqueness and Stability of the \delta_e Defect"
    electron_start = r'\\subsection\{Uniqueness and Stability of the.*\\delta_e.*Defect\}'
    
    # Find from that subsection to next section
    lines = content.split('\n')
    in_section = False
    section_lines = []
    
    for i, line in enumerate(lines):
        if re.search(electron_start, line):
            in_section = True
            print(f"Found electron defect section at line {i+1}")
        
        if in_section:
            section_lines.append((i, line))
            
            # Check if we've reached next section
            if line.startswith('\\section{') and len(section_lines) > 1:
                # Remove the last line (the new section start)
                section_lines.pop()
                break
    
    if section_lines:
        # Read the patch
        patch = read_file("patch_v5.8.0_01_particle_downgrades.tex")
        
        # Find the range to replace
        start_line = section_lines[0][0]
        end_line = section_lines[-1][0]
        
        # Rebuild content
        before = '\n'.join(lines[:start_line])
        after = '\n'.join(lines[end_line + 1:])
        
        new_content = before + '\n' + patch + '\n' + after
        print("✅ Applied particle physics downgrades")
        return new_content
    else:
        print("❌ Could not find electron defect section")
        return content

def apply_kappa_open_problem(content):
    """Apply κ as open problem"""
    print("\nApplying κ as open problem...")
    
    # Find the units bridge section
    # Look for "The Dimensional Bridge" or section about κ
    bridge_marker = "The Dimensional Bridge"
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if bridge_marker in line:
            print(f"Found dimensional bridge at line {i+1}")
            
            # Look for next section after bridge
            for j in range(i + 1, len(lines)):
                if lines[j].startswith('\\section{') or lines[j].startswith('\\subsection{'):
                    print(f"Next section at line {j+1}")
                    
                    # Read patch
                    patch = read_file("patch_v5.8.0_02_kappa_open_problem.tex")
                    
                    # Insert patch before next section
                    before = '\n'.join(lines[:j])
                    after = '\n'.join(lines[j:])
                    
                    new_content = before + '\n\n' + patch + '\n\n' + after
                    print("✅ Applied κ as open problem")
                    return new_content
    
    print("❌ Could not find dimensional bridge")
    return content

def apply_constant5_strengthen(content):
    """Apply constant 5 strengthening"""
    print("\nApplying constant 5 strengthening...")
    
    # Look for representation theory section about constant 5
    markers = [
        "representation theory",
        "constant 5",
        "24 = 6",
        "Leech decomposition"
    ]
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if any(marker in line.lower() for marker in markers):
            print(f"Found representation theory at line {i+1}: {line[:50]}...")
            
            # Look for section containing this
            # Go backward to find section start
            section_start = i
            for j in range(i, max(0, i-20), -1):
                if lines[j].startswith('\\subsection{'):
                    section_start = j
                    print(f"Subsection starts at line {j+1}")
                    break
            
            # Look for next section
            section_end = len(lines)
            for j in range(section_start + 1, len(lines)):
                if lines[j].startswith('\\subsection{') or lines[j].startswith('\\section{'):
                    section_end = j
                    print(f"Subsection ends at line {j+1}")
                    break
            
            # Read patch
            patch = read_file("patch_v5.8.0_03_constant5_strengthen.tex")
            
            # Replace the section
            before = '\n'.join(lines[:section_start])
            after = '\n'.join(lines[section_end:])
            
            new_content = before + '\n' + patch + '\n' + after
            print("✅ Applied constant 5 strengthening")
            return new_content
    
    print("❌ Could not find representation theory section")
    return content

def main():
    # Read current file
    input_file = "L_TOEC_MASTER_V5.7.3.tex"
    output_file = "L_TOEC_MASTER_V5.8.0.tex"
    
    if not Path(input_file).exists():
        print(f"Error: {input_file} not found")
        return
    
    print(f"Creating v5.8.0 from {input_file}")
    print("=" * 60)
    
    # Create backup
    import shutil
    backup_file = f"{input_file}.v5.7.3.backup"
    shutil.copy2(input_file, backup_file)
    print(f"Created backup: {backup_file}")
    
    content = read_file(input_file)
    
    # Apply patches in order
    content = apply_particle_downgrades(content)
    content = apply_kappa_open_problem(content)
    content = apply_constant5_strengthen(content)
    
    # Write output
    write_file(output_file, content)
    print(f"\n✅ Created {output_file}")
    
    # Show stats
    original_lines = len(read_file(input_file).split('\n'))
    new_lines = len(content.split('\n'))
    print(f"Original: {original_lines} lines")
    print(f"New: {new_lines} lines")
    print(f"Delta: {new_lines - original_lines} lines")
    
    # Try to compile
    print("\n" + "=" * 60)
    print("Attempting LaTeX compilation...")
    
    import subprocess
    result = subprocess.run(["pdflatex", "-interaction=nonstopmode", output_file], 
                          capture_output=True, text=True, cwd=".")
    
    if result.returncode == 0:
        print("✅ LaTeX compilation successful")
        
        # Check for warnings
        if "Warning" in result.stdout:
            warnings = [line for line in result.stdout.split('\n') if "Warning" in line]
            print(f"⚠️  {len(warnings)} warnings (check log)")
    else:
        print("❌ LaTeX compilation failed")
        print("STDOUT:", result.stdout[-500:])
        print("STDERR:", result.stderr[-500:])

if __name__ == '__main__':
    main()
