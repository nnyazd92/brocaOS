#!/usr/bin/env python3
"""
Apply v5.7.3 patches to address feedback
"""

import re
from pathlib import Path

def read_patch(patch_name):
    """Read patch content"""
    patch_file = Path(patch_name)
    if patch_file.exists():
        with open(patch_file, 'r') as f:
            return f.read()
    else:
        print(f"Error: {patch_file} not found")
        return None

def apply_lovelock_patch(tex_content):
    """Replace Theorem (Exclusivity) with Lemma (IR Consistency with Lovelock)"""
    print("Applying Lovelock patch...")
    
    # Find Theorem (Exclusivity) section
    theorem_start = r'\\subsection\{Theorem: Exclusivity of the Informational Action\}'
    theorem_end = r'\\paragraph\{Research Directions Enabled by Information-Theoretic Framing\}'
    
    theorem_match = re.search(theorem_start + r'.*?' + theorem_end, tex_content, re.DOTALL)
    
    if theorem_match:
        theorem_section = theorem_match.group(0)
        print(f"Found Theorem (Exclusivity) section ({len(theorem_section)} chars)")
        
        # Read the patch
        patch = read_patch("patch_v5.7.3_01_lovelock_fix.tex")
        if patch:
            # Replace the theorem section with the patch
            new_content = tex_content.replace(theorem_section, patch)
            print("✅ Theorem (Exclusivity) replaced with Lemma (IR Consistency)")
            return new_content
        else:
            print("❌ Failed to read patch")
            return tex_content
    else:
        print("❌ Could not find Theorem (Exclusivity) section")
        return tex_content

def apply_graph_laplacian_patch(tex_content):
    """Replace Theorem (Isotropic Emergence) with Conjecture"""
    print("\nApplying Graph Laplacian patch...")
    
    # Find Theorem (Isotropic Emergence)
    theorem_pattern = r'\\tagtheo.*?Theorem.*?Isotropic Emergence.*?(?=\\item|\\paragraph|\\subsection)'
    theorem_match = re.search(theorem_pattern, tex_content, re.DOTALL | re.IGNORECASE)
    
    if theorem_match:
        theorem_text = theorem_match.group(0)
        print(f"Found Theorem (Isotropic Emergence) ({len(theorem_text)} chars)")
        
        # Read the patch
        patch = read_patch("patch_v5.7.3_02_graph_laplacian_fix.tex")
        if patch:
            # Replace theorem with conjecture
            new_content = tex_content.replace(theorem_text, patch)
            print("✅ Theorem (Isotropic Emergence) replaced with Conjecture")
            return new_content
        else:
            print("❌ Failed to read patch")
            return tex_content
    else:
        print("❌ Could not find Theorem (Isotropic Emergence)")
        return tex_content

def apply_curvature_fork_patch(tex_content):
    """Strengthen curvature fork separation"""
    print("\nApplying Curvature Fork patch...")
    
    # Find the curvature fork section
    fork_start = r'\\subsection\{The Curvature Fork: Physical vs. Informational\}'
    fork_end = r'\\subsection\{The Curvature-Qualia Mapping\}'
    
    fork_match = re.search(fork_start + r'.*?' + fork_end, tex_content, re.DOTALL)
    
    if fork_match:
        fork_section = fork_match.group(0)
        print(f"Found Curvature Fork section ({len(fork_section)} chars)")
        
        # Read the patch
        patch = read_patch("patch_v5.7.3_03_curvature_fork_strengthen.tex")
        if patch:
            # Replace the section
            new_content = tex_content.replace(fork_section, patch)
            print("✅ Curvature Fork section strengthened")
            return new_content
        else:
            print("❌ Failed to read patch")
            return tex_content
    else:
        print("❌ Could not find Curvature Fork section")
        return tex_content

def apply_units_bridge_patch(tex_content):
    """Clarify units bridge status"""
    print("\nApplying Units Bridge patch...")
    
    # Find the dimensional bridge section
    bridge_pattern = r'\\tagass.*?The Dimensional Bridge.*?(?=\\section|\\subsection)'
    bridge_match = re.search(bridge_pattern, tex_content, re.DOTALL)
    
    if bridge_match:
        bridge_text = bridge_match.group(0)
        print(f"Found Dimensional Bridge section ({len(bridge_text)} chars)")
        
        # Read the patch
        patch = read_patch("patch_v5.7.3_04_units_bridge_fix.tex")
        if patch:
            # Insert patch after the bridge section
            # We'll replace from the bridge to the next section
            next_section = re.search(r'\\section\{Track 1: Formal Toy Models\}', tex_content[bridge_match.end():])
            if next_section:
                end_pos = bridge_match.end() + next_section.start()
                before = tex_content[:bridge_match.end()]
                after = tex_content[end_pos:]
                new_content = before + "\n\n" + patch + "\n\n" + after
                print("✅ Units Bridge clarification added")
                return new_content
        else:
            print("❌ Failed to read patch")
            return tex_content
    else:
        print("❌ Could not find Dimensional Bridge section")
        return tex_content

def main():
    # Read current file
    tex_file = Path("L_TOEC_MASTER_V5.7.2.tex")
    backup_file = Path("L_TOEC_MASTER_V5.7.2.tex.backup")
    
    if not tex_file.exists():
        print(f"Error: {tex_file} not found")
        return
    
    # Create backup
    import shutil
    shutil.copy2(tex_file, backup_file)
    print(f"Created backup: {backup_file}")
    
    with open(tex_file, 'r') as f:
        tex_content = f.read()
    
    print("APPLYING v5.7.3 PATCHES")
    print("=" * 60)
    
    # Apply patches in order
    tex_content = apply_lovelock_patch(tex_content)
    tex_content = apply_graph_laplacian_patch(tex_content)
    tex_content = apply_curvature_fork_patch(tex_content)
    tex_content = apply_units_bridge_patch(tex_content)
    
    # Write updated file
    output_file = Path("L_TOEC_MASTER_V5.7.3.tex")
    with open(output_file, 'w') as f:
        f.write(tex_content)
    
    print("\n" + "=" * 60)
    print(f"✅ Created updated file: {output_file}")
    print(f"📊 Original size: {Path(backup_file).stat().st_size} bytes")
    print(f"📊 Updated size: {output_file.stat().st_size} bytes")
    
    # Run verification
    print("\n" + "=" * 60)
    print("RUNNING VERIFICATION")
    print("=" * 60)
    
    import subprocess
    result = subprocess.run(["python3", "verify_v5.7.3_fixes.py"], 
                          capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

if __name__ == '__main__':
    main()
