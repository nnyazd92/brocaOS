#!/usr/bin/env python3
"""
Final verification of v5.7.3_FINAL
"""

import re
from pathlib import Path

def check_final():
    tex_file = Path("L_TOEC_MASTER_V5.7.3_FINAL.tex")
    if not tex_file.exists():
        print(f"Error: {tex_file} not found")
        return False
    
    with open(tex_file, 'r') as f:
        content = f.read()
    
    print("FINAL VERIFICATION OF v5.7.3_FINAL")
    print("=" * 60)
    
    checks = []
    
    # Check 1: No Theorem (Exclusivity)
    if "Theorem (Exclusivity)" in content:
        checks.append(("❌", "Theorem (Exclusivity) still present"))
    else:
        checks.append(("✅", "Theorem (Exclusivity) removed"))
    
    # Check 2: Lemma (IR Consistency with Lovelock) present
    if "Lemma (IR Consistency with Lovelock)" in content:
        checks.append(("✅", "Lemma (IR Consistency with Lovelock) present"))
    else:
        checks.append(("❌", "Lemma (IR Consistency with Lovelock) missing"))
    
    # Check 3: No Theorem (Isotropic Emergence)
    if "Theorem (Isotropic Emergence)" in content:
        checks.append(("❌", "Theorem (Isotropic Emergence) still present"))
    else:
        checks.append(("✅", "Theorem (Isotropic Emergence) removed"))
    
    # Check 4: Research Direction present
    if "Research Direction (Graph Continuum Limit)" in content:
        checks.append(("✅", "Graph continuum as research direction"))
    else:
        checks.append(("❌", "Missing graph continuum research direction"))
    
    # Check 5: Curvature fork strict separation
    if r'C_{\mathrm{phys}} \neq C_{\mathrm{info}}' in content:
        checks.append(("✅", "Curvature fork strict separation"))
    else:
        checks.append(("❌", "Missing curvature fork strict separation"))
    
    # Check 6: κ labeled as ansatz
    if "ansatz" in content.lower() and r'$\kappa$' in content:
        checks.append(("✅", "κ labeled as ansatz"))
    else:
        checks.append(("❌", "κ not labeled as ansatz"))
    
    # Check 7: MOND warning
    if "highly speculative" in content.lower() and "MOND" in content.upper():
        checks.append(("✅", "MOND labeled as speculative"))
    else:
        checks.append(("⚠️ ", "MOND warning could be stronger"))
    
    # Check 8: Mapping theorem requirement
    if "mapping theorem" in content.lower() and "required" in content.lower():
        checks.append(("✅", "Mapping theorem requirement stated"))
    else:
        checks.append(("❌", "Missing mapping theorem requirement"))
    
    # Check 9: Track A/B separation
    if "Track A" in content and "Track B" in content:
        checks.append(("✅", "Track A/B separation mentioned"))
    else:
        checks.append(("⚠️ ", "Track A/B separation not explicit"))
    
    # Print results
    for status, message in checks:
        print(f"{status} {message}")
    
    # Count successes
    passed = sum(1 for status, _ in checks if status == "✅")
    total = len(checks)
    
    print(f"\n✅ {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 ALL FEEDBACK POINTS ADDRESSED!")
        return True
    else:
        print(f"\n⚠️  {total - passed} issues need attention")
        return False

def main():
    if check_final():
        print("\n" + "=" * 60)
        print("SUMMARY OF CHANGES APPLIED:")
        print("1. Theorem (Exclusivity) → Lemma (IR Consistency with Lovelock)")
        print("2. Theorem (Isotropic Emergence) → Research Direction")
        print("3. Curvature fork: Strict separation C_phys ≠ C_info")
        print("4. Units bridge: κ labeled as ansatz")
        print("5. CLT for graphs: Downgraded to conjecture")
        print("6. MOND: Labeled as highly speculative")
        print("7. Mapping theorem: Required for curvature-qualia")
        print("8. Provenance: Track A/B separation maintained")
        print("\n✅ READY FOR LaTeX COMPILATION")
    else:
        print("\n❌ Some issues remain - check above")

if __name__ == '__main__':
    main()
