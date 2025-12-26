#!/usr/bin/env python3
"""
Verify v5.7.3 fixes for feedback integration
"""

import re
from pathlib import Path

def check_lovelock_downgrade(tex_content):
    """Check if Theorem (Exclusivity) is downgraded to Lemma"""
    print("=" * 60)
    print("CHECKING LOVELOCK/EXCLUSIVITY FIX")
    print("=" * 60)
    
    # Check for Theorem (Exclusivity) - should be downgraded
    theorem_pattern = r'\\begin\{mytheorem\}\{Theorem.*Exclusivity'
    if re.search(theorem_pattern, tex_content):
        print("❌ Theorem (Exclusivity) still present - should be downgraded to Lemma")
        return False
    else:
        print("✅ Theorem (Exclusivity) downgraded (good)")
    
    # Check for Lemma (IR Consistency with Lovelock)
    lemma_pattern = r'\\begin\{mytheorem\}\{Lemma.*Lovelock'
    if re.search(lemma_pattern, tex_content):
        print("✅ Lemma (IR Consistency with Lovelock) present")
        
        # Check for explicit assumptions list
        assumptions = re.findall(r'\\item.*\\textbf\{Locality\:', tex_content)
        if assumptions:
            print(f"✅ Explicit assumptions listed: {len(assumptions)} found")
        else:
            print("❌ Missing explicit assumptions list")
            return False
            
        # Check for "What This Lemma Does Not Give" section
        if "Does not derive" in tex_content and "Does not justify" in tex_content:
            print("✅ Limitations clearly stated")
        else:
            print("❌ Missing limitations section")
            return False
    else:
        print("❌ Lemma (IR Consistency with Lovelock) missing")
        return False
    
    return True

def check_curvature_fork_separation(tex_content):
    """Check strict separation of physical vs informational curvature"""
    print("\n" + "=" * 60)
    print("CHECKING CURVATURE FORK SEPARATION")
    print("=" * 60)
    
    # Check for explicit notation
    if r'C_{\mathrm{phys}}' in tex_content and r'C_{\mathrm{info}}' in tex_content:
        print("✅ Explicit notation C_phys and C_info used")
    else:
        print("❌ Missing explicit curvature notation")
        return False
    
    # Check for prohibition statement
    if "prohibited" in tex_content.lower() and "cross-talk" in tex_content.lower():
        print("✅ Cross-talk prohibition stated")
    else:
        print("❌ Missing cross-talk prohibition")
        return False
    
    # Check for mapping theorem requirement
    if "mapping theorem" in tex_content.lower() and "required" in tex_content.lower():
        print("✅ Mapping theorem requirement stated")
    else:
        print("❌ Missing mapping theorem requirement")
        return False
    
    # Check qualia mapping uses C_info not C_phys
    qualia_section = re.search(r'Curvature-Qualia.*?(?=\\section|\\subsection|$)', tex_content, re.DOTALL | re.IGNORECASE)
    if qualia_section:
        qualia_text = qualia_section.group(0)
        if r'C_{\mathrm{info}}' in qualia_text and r'C_{\mathrm{phys}}' not in qualia_text:
            print("✅ Qualia mapping uses only C_info (correct)")
        else:
            print("❌ Qualia mapping may use C_phys (category error)")
            return False
    
    return True

def check_graph_laplacian_fix(tex_content):
    """Check graph Laplacian theorem is downgraded"""
    print("\n" + "=" * 60)
    print("CHECKING GRAPH LAPLACIAN FIX")
    print("=" * 60)
    
    # Check for Theorem (Isotropic Emergence) - should be downgraded
    theorem_pattern = r'\\tagtheo.*Theorem.*Isotropic Emergence'
    if re.search(theorem_pattern, tex_content):
        print("❌ Theorem (Isotropic Emergence) still present - should be downgraded")
        
        # Check if it mentions CLT for graphs
        if "CLT for graphs" in tex_content or "Central Limit Theorem for graphs" in tex_content:
            print("❌ Still claims CLT for graphs as theorem")
            return False
    else:
        print("✅ Theorem (Isotropic Emergence) downgraded")
    
    # Check for Conjecture/Research Direction
    conjecture_patterns = [
        r'\\begin\{tcolorbox\}.*Research Direction',
        r'\\begin\{tcolorbox\}.*Conjecture',
        r'Conjecture.*graph'
    ]
    
    found_conjecture = False
    for pattern in conjecture_patterns:
        if re.search(pattern, tex_content, re.IGNORECASE):
            found_conjecture = True
            break
    
    if found_conjecture:
        print("✅ Graph continuum as conjecture/research direction")
        
        # Check for precise mathematical formulation
        if "convergence notion" in tex_content.lower() or "scaling regime" in tex_content.lower():
            print("✅ Precise mathematical formulation specified")
        else:
            print("⚠️  Could be more precise about convergence")
            
        # Check for MOND warning
        if "highly speculative" in tex_content.lower() and "MOND" in tex_content.upper():
            print("✅ MOND connection properly labeled as speculative")
        else:
            print("⚠️  MOND connection should be labeled speculative")
    else:
        print("❌ Missing conjecture/research direction for graph continuum")
        return False
    
    return True

def check_units_bridge_fix(tex_content):
    """Check units bridge clarification"""
    print("\n" + "=" * 60)
    print("CHECKING UNITS BRIDGE FIX")
    print("=" * 60)
    
    # Check for explicit ansatz labeling
    if "ansatz" in tex_content.lower() and r'$\kappa$' in tex_content:
        print("✅ κ explicitly labeled as ansatz")
    else:
        print("❌ κ not labeled as ansatz")
        return False
    
    # Check for measurement protocol
    if "measurement protocol" in tex_content.lower() or "experimental protocol" in tex_content.lower():
        print("✅ Measurement protocol discussed")
    else:
        print("❌ Missing measurement protocol")
        return False
    
    # Check for quarantine of G from |Co_0|
    if "calibration" in tex_content.lower() and "Co_0" in tex_content and "quarantine" in tex_content.lower():
        print("✅ G from |Co_0| properly quarantined as calibration")
    else:
        print("❌ G from |Co_0| not properly quarantined")
        return False
    
    # Check for protocol for κ-dependent claims
    if "protocol" in tex_content.lower() and "κ-dependent" in tex_content:
        print("✅ Protocol for κ-dependent claims established")
    else:
        print("❌ Missing protocol for κ-dependent claims")
        return False
    
    return True

def check_provenance_leakage(tex_content):
    """Check for provenance leakage fixes"""
    print("\n" + "=" * 60)
    print("CHECKING PROVENANCE LEAKAGE FIXES")
    print("=" * 60)
    
    # Check for typed dependency rules
    if "typed dependency" in tex_content.lower() or "dependency edges" in tex_content.lower():
        print("✅ Typed dependency rules mentioned")
    else:
        print("⚠️  Typed dependency rules not explicitly mentioned")
    
    # Check Track A/B separation
    if "Track A" in tex_content and "Track B" in tex_content:
        print("✅ Track A/B separation maintained")
        
        # Check that theorems don't depend on calibrations
        # Look for theorem statements and check context
        theorems = re.findall(r'\\begin\{mytheorem\}.*?\\end\{mytheorem\}', tex_content, re.DOTALL)
        for i, theorem in enumerate(theorems[:5]):  # Check first 5 theorems
            if "calibration" in theorem.lower() or "Co_0" in theorem:
                print(f"❌ Theorem {i+1} may depend on calibration")
                return False
        print("✅ Theorems appear independent of calibrations")
    else:
        print("❌ Track A/B separation not clear")
        return False
    
    return True

def main():
    tex_file = Path("L_TOEC_MASTER_V5.7.2.tex")
    if not tex_file.exists():
        print(f"Error: {tex_file} not found")
        return
    
    with open(tex_file, 'r') as f:
        tex_content = f.read()
    
    print("VERIFYING v5.7.3 FEEDBACK INTEGRATION")
    print("Based on feedback_recent.txt critique")
    print()
    
    results = []
    
    results.append(("Lovelock/Exclusivity", check_lovelock_downgrade(tex_content)))
    results.append(("Curvature Fork", check_curvature_fork_separation(tex_content)))
    results.append(("Graph Laplacian", check_graph_laplacian_fix(tex_content)))
    results.append(("Units Bridge", check_units_bridge_fix(tex_content)))
    results.append(("Provenance Leakage", check_provenance_leakage(tex_content)))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nOverall: {passed}/{total} checks passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All feedback points addressed!")
    else:
        print(f"\n⚠️  {total - passed} issues need attention")
        print("Apply the patches in this order:")
        print("1. patch_v5.7.3_01_lovelock_fix.tex")
        print("2. patch_v5.7.3_02_graph_laplacian_fix.tex")
        print("3. patch_v5.7.3_03_curvature_fork_strengthen.tex")
        print("4. patch_v5.7.3_04_units_bridge_fix.tex")

if __name__ == '__main__':
    main()
