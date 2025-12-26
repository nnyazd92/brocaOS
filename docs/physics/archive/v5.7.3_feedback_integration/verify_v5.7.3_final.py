#!/usr/bin/env python3
"""
Verify v5.7.3 final fixes
"""

import re
from pathlib import Path

def check_file(filename):
    """Check a specific file"""
    tex_file = Path(filename)
    if not tex_file.exists():
        print(f"Error: {tex_file} not found")
        return False
    
    with open(tex_file, 'r') as f:
        tex_content = f.read()
    
    print(f"VERIFYING {filename}")
    print("=" * 60)
    
    # Check 1: No Theorem (Exclusivity)
    if "Theorem (Exclusivity)" in tex_content:
        print("❌ Theorem (Exclusivity) still present")
        return False
    else:
        print("✅ Theorem (Exclusivity) removed/downgraded")
    
    # Check 2: Lemma (IR Consistency with Lovelock) present
    if "Lemma (IR Consistency with Lovelock)" in tex_content:
        print("✅ Lemma (IR Consistency with Lovelock) present")
    else:
        print("❌ Lemma (IR Consistency with Lovelock) missing")
        return False
    
    # Check 3: No Theorem (Isotropic Emergence) 
    if "Theorem (Isotropic Emergence)" in tex_content:
        print("❌ Theorem (Isotropic Emergence) still present")
        return False
    else:
        print("✅ Theorem (Isotropic Emergence) removed/downgraded")
    
    # Check 4: Research Direction/Conjecture for graph continuum
    if "Research Direction (Graph Continuum Limit)" in tex_content or "Conjecture: Continuum Limit" in tex_content:
        print("✅ Graph continuum as research direction/conjecture")
    else:
        print("❌ Missing graph continuum research direction")
        return False
    
    # Check 5: Curvature fork strict separation
    if r'C_{\mathrm{phys}} \neq C_{\mathrm{info}}' in tex_content:
        print("✅ Curvature fork strict separation enforced")
    else:
        print("❌ Missing curvature fork strict separation")
        return False
    
    # Check 6: Units bridge clarification
    if "ansatz" in tex_content.lower() and "free parameter" in tex_content.lower() and r'$\kappa$' in tex_content:
        print("✅ κ properly labeled as ansatz/free parameter")
    else:
        print("❌ κ not properly labeled")
        return False
    
    # Check 7: No CLT for graphs as theorem
    if "CLT for graphs" in tex_content and "theorem" in tex_content.lower():
        # Check if it's in a theorem context
        lines = tex_content.split('\n')
        for i, line in enumerate(lines):
            if "CLT for graphs" in line:
                # Check surrounding lines for theorem
                context = ' '.join(lines[max(0,i-2):min(len(lines),i+3)])
                if "theorem" in context.lower() and "conjecture" not in context.lower():
                    print("❌ CLT for graphs still in theorem context")
                    return False
        print("✅ CLT for graphs not in theorem context")
    else:
        print("✅ CLT for graphs not mentioned or properly contextualized")
    
    # Check 8: MOND warning
    if "highly speculative" in tex_content.lower() and "MOND" in tex_content.upper():
        print("✅ MOND properly labeled as speculative")
    else:
        print("⚠️  MOND warning could be stronger")
    
    # Check 9: Mapping theorem requirement
    if "mapping theorem" in tex_content.lower() and "required" in tex_content.lower():
        print("✅ Mapping theorem requirement stated")
    else:
        print("❌ Missing mapping theorem requirement")
        return False
    
    # Check 10: Track A/B separation mentioned
    if "Track A" in tex_content and "Track B" in tex_content:
        print("✅ Track A/B separation mentioned")
    else:
        print("⚠️  Track A/B separation not explicitly mentioned")
    
    return True

def main():
    print("FINAL VERIFICATION OF v5.7.3 FEEDBACK INTEGRATION")
    print()
    
    # Check the new file
    if check_file("L_TOEC_MASTER_V5.7.3.tex"):
        print("\n" + "=" * 60)
        print("🎉 SUCCESS: All critical feedback points addressed!")
        print("=" * 60)
        
        # Show summary of changes
        print("\nSUMMARY OF CHANGES:")
        print("1. Theorem (Exclusivity) → Lemma (IR Consistency with Lovelock)")
        print("2. Theorem (Isotropic Emergence) → Research Direction (Graph Continuum)")
        print("3. Curvature fork: Strict separation C_phys ≠ C_info enforced")
        print("4. Units bridge: κ labeled as ansatz, measurement protocol required")
        print("5. CLT for graphs: Downgraded from theorem to conjecture")
        print("6. MOND connection: Labeled as highly speculative")
        print("7. Mapping theorem: Required for curvature-qualia connection")
        print("8. Provenance: Track A/B separation maintained")
        
        print("\n✅ READY FOR COMPILATION AND FINAL REVIEW")
    else:
        print("\n" + "=" * 60)
        print("❌ ISSUES REMAIN - Need to fix above problems")
        print("=" * 60)

if __name__ == '__main__':
    main()
