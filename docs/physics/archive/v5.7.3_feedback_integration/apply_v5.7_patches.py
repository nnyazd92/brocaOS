#!/usr/bin/env python3
"""
Apply v5.7 patches to L-ToEC document
Systematic patch-based development workflow
"""

import re
import os
from pathlib import Path

def read_file(filename):
    """Read file content"""
    with open(filename, 'r') as f:
        return f.read()

def write_file(filename, content):
    """Write file content"""
    with open(filename, 'w') as f:
        f.write(content)

def apply_patch_01_category_errors(content):
    """Apply patch 01: Category errors notation"""
    print("Applying patch 01: Category errors notation")
    
    # Find where to add new commands (after existing \newcommand definitions)
    pattern = r'(\\newcommand\{\\\w+\}\{.*?\}\s*)+'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        insert_pos = match.end()
        # Add new notation commands
        new_commands = """% New notation for curvature fork (v5.7.01)
\\newcommand{\\Cphys}{\\mathcal{C}_{\\mathrm{phys}}}
\\newcommand{\\Cinfo}{\\mathcal{C}_{\\mathrm{info}}}
\\newcommand{\\Ctopos}{\\mathcal{C}_{\\mathrm{topos}}}
"""
        content = content[:insert_pos] + new_commands + content[insert_pos:]
    
    return content

def apply_patch_02_downgrade_lovelock(content):
    """Apply patch 02: Downgrade Lovelock theorem to lemma"""
    print("Applying patch 02: Downgrade Lovelock theorem")
    
    # Find the Theorem: Exclusivity section
    pattern = r'\\subsection\{Theorem: Exclusivity of the Informational Action\}.*?(?=\\subsection|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        # Read the patch content
        patch_content = read_file('patch_v5.7_02_downgrade_lovelock.tex')
        # Replace the section
        content = content[:match.start()] + patch_content + content[match.end():]
    
    return content

def apply_patch_03_explicit_poisson(content):
    """Apply patch 03: Add explicit Poisson functional"""
    print("Applying patch 03: Add explicit Poisson functional")
    
    # Find where to add new section (after Track 1 sections)
    # Look for section about deriving Poisson or after Lovelock
    pattern = r'\\subsection\{Lemma: IR Consistency with Lovelock.*?(?=\\subsection|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        # Read the patch content
        patch_content = read_file('patch_v5.7_03_explicit_poisson_functional.tex')
        # Insert after the lemma
        insert_pos = match.end()
        content = content[:insert_pos] + '\n\n' + patch_content + content[insert_pos:]
    
    return content

def apply_patch_04_typed_dependencies(content):
    """Apply patch 04: Add typed dependency rules"""
    print("Applying patch 04: Add typed dependency rules")
    
    # Find the Claims and Status Ledger section
    pattern = r'\\section\{Claims and Status Ledger\}.*?(?=\\section|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        # Read the patch content
        patch_content = read_file('patch_v5.7_04_typed_dependency_rules.tex')
        # Insert at the end of the section
        insert_pos = match.end() - len(match.group().split('\n')[-1]) if match.group().strip().endswith('}') else match.end()
        content = content[:insert_pos] + '\n\n' + patch_content + content[insert_pos:]
    
    return content

def main():
    # Paths
    source_file = 'L_TOEC_MASTER_V5.7.tex'
    output_file = 'L_TOEC_MASTER_V5.7_patched.tex'
    
    print("=" * 60)
    print("L-ToEC v5.7 Patch Application Script")
    print("=" * 60)
    
    # Read source
    print(f"Reading source: {source_file}")
    content = read_file(source_file)
    
    # Apply patches in order
    content = apply_patch_01_category_errors(content)
    content = apply_patch_02_downgrade_lovelock(content)
    content = apply_patch_03_explicit_poisson(content)
    content = apply_patch_04_typed_dependencies(content)
    
    # Write output
    print(f"Writing output: {output_file}")
    write_file(output_file, content)
    
    print("\n✅ Patches applied successfully!")
    print(f"Output: {output_file}")
    
    # Show statistics
    original_lines = len(read_file(source_file).split('\n'))
    patched_lines = len(content.split('\n'))
    print(f"Original: {original_lines} lines")
    print(f"Patched: {patched_lines} lines")
    print(f"Added: {patched_lines - original_lines} lines")

if __name__ == '__main__':
    main()
