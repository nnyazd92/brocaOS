#!/usr/bin/env python3
"""
Apply patches cleanly without breaking LaTeX
"""

import re

def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()

def write_file(filename, content):
    with open(filename, 'w') as f:
        f.write(content)

def apply_patch_02(content):
    """Apply Lovelock downgrade patch"""
    print("Applying Lovelock downgrade...")
    
    # Find the Theorem: Exclusivity section
    pattern = r'\\subsection\{Theorem: Exclusivity of the Informational Action\}.*?(?=\\subsection|\\section|\\Z)'
    
    patch = read_file('patch_v5.7_02_downgrade_lovelock.tex')
    
    # Use re.DOTALL to match across lines
    content = re.sub(pattern, patch, content, flags=re.DOTALL)
    
    return content

def apply_patch_03(content):
    """Apply Poisson functional patch"""
    print("Applying Poisson functional...")
    
    # Find after the Lovelock lemma
    pattern = r'\\subsection\{Lemma: IR Consistency with Lovelock.*?(?=\\subsection|\\section|\\Z)'
    
    # We need to insert after this section
    match = re.search(pattern, content, flags=re.DOTALL)
    if match:
        patch = read_file('patch_v5.7_03_explicit_poisson_functional.tex')
        insert_pos = match.end()
        content = content[:insert_pos] + '\n\n' + patch + content[insert_pos:]
    
    return content

def apply_patch_04(content):
    """Apply typed dependencies patch"""
    print("Applying typed dependencies...")
    
    # Find Claims and Status Ledger section
    pattern = r'\\section\{Claims and Status Ledger\}.*?(?=\\section|\\Z)'
    
    patch = read_file('patch_v5.7_04_typed_dependency_rules.tex')
    
    # Replace the entire section
    content = re.sub(pattern, patch, content, flags=re.DOTALL)
    
    return content

def apply_patch_01b(content):
    """Apply curvature fork section"""
    print("Applying curvature fork section...")
    
    # Find after Claims and Status Ledger
    pattern = r'\\section\{Claims and Status Ledger\}.*?(?=\\section|\\Z)'
    
    match = re.search(pattern, content, flags=re.DOTALL)
    if match:
        patch = read_file('patch_v5.7_01b_curvature_fork_section.tex')
        insert_pos = match.end()
        content = content[:insert_pos] + '\n\n' + patch + content[insert_pos:]
    
    return content

def main():
    source = 'L_TOEC_MASTER_V5.7.1.tex'
    output = 'L_TOEC_MASTER_V5.7.1_patched.tex'
    
    print("=" * 60)
    print("Clean Patch Application for L-ToEC v5.7.1")
    print("=" * 60)
    
    content = read_file(source)
    
    # Apply patches in logical order
    content = apply_patch_02(content)  # Lovelock downgrade
    content = apply_patch_03(content)  # Poisson functional
    content = apply_patch_04(content)  # Typed dependencies
    content = apply_patch_01b(content) # Curvature fork
    
    write_file(output, content)
    
    print(f"\n✅ Patches applied to: {output}")
    
    # Check line count
    orig_lines = len(read_file(source).split('\n'))
    new_lines = len(content.split('\n'))
    print(f"Original: {orig_lines} lines")
    print(f"Patched: {new_lines} lines")
    print(f"Added: {new_lines - orig_lines} lines")

if __name__ == '__main__':
    main()
