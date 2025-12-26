#!/usr/bin/env python3
"""
Apply dark matter identifiability patch to v5.7.1
"""

def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()

def write_file(filename, content):
    with open(filename, 'w') as f:
        f.write(content)

def main():
    source = 'L_TOEC_MASTER_V5.7.1.tex'
    output = 'L_TOEC_MASTER_V5.7.2.tex'
    
    print("=" * 60)
    print("Applying Dark Matter Identifiability Patch")
    print("=" * 60)
    
    content = read_file(source)
    patch = read_file('patch_v5.7.2_01_dm_identifiability.tex')
    
    # Find the dark matter derivation section
    # Look for "Derivation of the Dark Matter Ratio Formula"
    import re
    
    # Find the section and insert our patch after it
    pattern = r'(\\subsection\{Derivation of the Dark Matter Ratio Formula.*?\n\\subsection\{)'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        # Insert patch before the next subsection
        insert_pos = match.start(1) + len(match.group(1)) - len('\n\\subsection{')
        new_content = content[:insert_pos] + '\n\n' + patch + '\n\n' + content[insert_pos:]
        
        write_file(output, new_content)
        print(f"✅ Patch applied to: {output}")
        
        # Update line in claims table if it exists
        # Change "[Toy Model Result]" to "[Theorem]" for DMD-001
        new_content = new_content.replace(
            'Dark Matter Ratio ($5+e^{-1}$) & B & \\tagcal & DMD-001',
            'Dark Matter Ratio ($5+e^{-1}$) & B & \\tagtheo & DMD-001'
        )
        
        write_file(output, new_content)
        print("✅ Updated claims table: DMD-001 → [Theorem]")
        
    else:
        print("❌ Could not find dark matter derivation section")
        # Try alternative pattern
        pattern2 = r'\\subsection\{Derivation of the Dark Matter Ratio'
        match2 = re.search(pattern2, content)
        if match2:
            print(f"Found at position: {match2.start()}")
        else:
            print("Dark matter section not found")

if __name__ == '__main__':
    main()
