#!/usr/bin/env python3
"""
Create v5.7.3 final by manually integrating patches
"""

def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()

def write_file(filename, content):
    with open(filename, 'w') as f:
        f.write(content)

def main():
    # Read original
    original = read_file("L_TOEC_MASTER_V5.7.2.tex")
    
    # Read patches
    lovelock_patch = read_file("patch_v5.7.3_01_lovelock_fix.tex")
    graph_patch = read_file("patch_v5.7.3_02_graph_laplacian_fix.tex")
    curvature_patch = read_file("patch_v5.7.3_03_curvature_fork_strengthen.tex")
    units_patch = read_file("patch_v5.7.3_04_units_bridge_fix.tex")
    
    print("Creating v5.7.3 final...")
    
    # Simple string replacement approach
    # 1. Replace Theorem (Exclusivity) section
    exclusivity_start = "\\subsection{Theorem: Exclusivity of the Informational Action}"
    exclusivity_end = "\\paragraph{Research Directions Enabled by Information-Theoretic Framing}"
    
    if exclusivity_start in original and exclusivity_end in original:
        start_idx = original.find(exclusivity_start)
        end_idx = original.find(exclusivity_end, start_idx)
        
        if start_idx != -1 and end_idx != -1:
            before = original[:start_idx]
            after = original[end_idx:]
            original = before + lovelock_patch + "\n\n" + after
            print("✅ Replaced Theorem (Exclusivity)")
        else:
            print("❌ Could not find Exclusivity section boundaries")
    else:
        print("❌ Could not find Exclusivity markers")
    
    # 2. Replace Theorem (Isotropic Emergence)
    isotropic_start = "\\tagtheo \\textbf{Theorem (Isotropic Emergence):}"
    if isotropic_start in original:
        # Find from start to next \item or \paragraph
        start_idx = original.find(isotropic_start)
        # Look for next \item or \paragraph
        next_item = original.find("\\item", start_idx + 50)
        next_para = original.find("\\paragraph", start_idx + 50)
        
        end_idx = min(next_item, next_para) if next_item != -1 and next_para != -1 else max(next_item, next_para)
        
        if end_idx != -1:
            before = original[:start_idx]
            after = original[end_idx:]
            original = before + graph_patch + "\n\n" + after
            print("✅ Replaced Theorem (Isotropic Emergence)")
        else:
            print("❌ Could not find end of Isotropic Emergence")
    else:
        print("❌ Could not find Isotropic Emergence")
    
    # 3. Replace curvature fork
    curvature_start = "\\subsection{The Curvature Fork: Physical vs. Informational}"
    curvature_end = "\\subsection{The Curvature-Qualia Mapping}"
    
    if curvature_start in original and curvature_end in original:
        start_idx = original.find(curvature_start)
        end_idx = original.find(curvature_end, start_idx)
        
        if start_idx != -1 and end_idx != -1:
            before = original[:start_idx]
            after = original[end_idx:]
            original = before + curvature_patch + "\n\n" + after
            print("✅ Replaced curvature fork section")
        else:
            print("❌ Could not find curvature fork boundaries")
    else:
        print("❌ Could not find curvature fork markers")
    
    # 4. Add units bridge clarification after the dimensional bridge
    bridge_marker = "\\tagass \\textbf{The Dimensional Bridge:}"
    track1_marker = "\\section{Track 1: Formal Toy Models}"
    
    if bridge_marker in original and track1_marker in original:
        bridge_idx = original.find(bridge_marker)
        track1_idx = original.find(track1_marker, bridge_idx)
        
        if bridge_idx != -1 and track1_idx != -1:
            # Insert units patch before Track 1
            before = original[:track1_idx]
            after = original[track1_idx:]
            original = before + "\n\n" + units_patch + "\n\n" + after
            print("✅ Added units bridge clarification")
        else:
            print("❌ Could not find insertion point for units bridge")
    else:
        print("❌ Could not find bridge or Track 1 markers")
    
    # Write final file
    write_file("L_TOEC_MASTER_V5.7.3_FINAL.tex", original)
    print("\n✅ Created L_TOEC_MASTER_V5.7.3_FINAL.tex")
    
    # Run verification
    print("\nRunning verification...")
    import subprocess
    result = subprocess.run(["python3", "verify_v5.7.3_final.py"], 
                          capture_output=True, text=True)
    print(result.stdout)

if __name__ == '__main__':
    main()
