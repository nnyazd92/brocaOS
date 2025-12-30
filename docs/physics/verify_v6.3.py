#!/usr/bin/env python3
"""
v6.3 Governance Verifier
Checks implementation of v6.2.2 feedback fixes.
"""

import re
import sys
from pathlib import Path

class V6_3_Verifier:
    def __init__(self, tex_file):
        self.tex_file = tex_file
        with open(tex_file, 'r') as f:
            self.content = f.read()
        self.errors = []
        self.warnings = []
        
    def check_version(self):
        """Check version number updated"""
        if 'Version 6.3' not in self.content:
            self.errors.append("Document not updated to v6.3")
            
    def check_parametric_degeneracy(self):
        """Check Poisson derivation includes parametric degeneracy discussion"""
        keywords = ['parametric degeneracy', 'degeneracy structure', r'\\frac{\\kappa J}{A}', 'underdetermined']
        found = False
        for keyword in keywords:
            if re.search(keyword, self.content, re.IGNORECASE):
                found = True
                break
        if not found:
            self.warnings.append("Missing parametric degeneracy discussion in Poisson derivation")
            
    def check_mond_replacement(self):
        """Check MOND-like language replaced with precise formulation"""
        # Check for old MOND-like warning
        if 'MOND-like effects' in self.content and 'Warning: Speculative Connection' in self.content:
            self.errors.append("Old MOND-like warning still present")
        
        # Check for new precise formulation
        if not re.search(r'\\nabla\\cdot\\[.*\\mu.*\\nabla\\varphi', self.content):
            self.warnings.append("Missing precise modified-Poisson formulation")
            
    def check_fisher_model(self):
        """Check minimal statistical model for Fisher geometry"""
        fisher_keywords = ['exponential family', 'p(L_3|\\theta)', 'Fisher metric computation', 'Gaussian model']
        found_count = 0
        for keyword in fisher_keywords:
            if keyword in self.content:
                found_count += 1
        if found_count < 2:
            self.warnings.append("Insufficient Fisher geometry model specification")
            
    def check_falsification_section(self):
        """Check 'What Would Falsify' section exists"""
        if 'What Would Falsify L-ToEC' not in self.content:
            self.errors.append("Missing 'What Would Falsify' section")
        else:
            # Check for concrete falsifiers
            falsifiers = ['Gravitational wave above Nyquist', '4D spacetime violation', 
                         'Information conservation violation', 'Leech lattice irrelevance']
            found = 0
            for f in falsifiers:
                if f in self.content:
                    found += 1
            if found < 2:
                self.warnings.append("Falsification section lacks concrete examples")
                
    def check_constant5_clarification(self):
        """Check constant 5 clarified as selection theorem"""
        keywords = ['selection theorem', 'architectural constraint', 'not a fundamental law']
        found = False
        for keyword in keywords:
            if re.search(keyword, self.content, re.IGNORECASE):
                found = True
                break
        if not found:
            self.warnings.append("Constant 5 not clarified as selection theorem")
            
    def verify_all(self):
        """Run all checks"""
        print(f"Verifying {self.tex_file} for v6.3 compliance...")
        print("=" * 60)
        
        self.check_version()
        self.check_parametric_degeneracy()
        self.check_mond_replacement()
        self.check_fisher_model()
        self.check_falsification_section()
        self.check_constant5_clarification()
        
        # Report results
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  - {error}")
                
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
                
        if not self.errors and not self.warnings:
            print("\n✅ All checks passed!")
            
        print(f"\nTotal errors: {len(self.errors)}, warnings: {len(self.warnings)}")
        return len(self.errors) == 0

def main():
    tex_file = "L_TOEC_MASTER_V6.3_upgraded.tex"
    if not Path(tex_file).exists():
        print(f"File {tex_file} not found!")
        sys.exit(1)
        
    verifier = V6_3_Verifier(tex_file)
    success = verifier.verify_all()
    
    # Also check compilation
    print("\n" + "=" * 60)
    print("Checking LaTeX compilation...")
    
    import subprocess
    try:
        # Quick syntax check
        result = subprocess.run(['pdflatex', '-interaction=nonstopmode', '-draftmode', tex_file],
                              capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print("LaTeX compilation issues:")
            # Show first few errors
            lines = result.stderr.split('\n')
            error_lines = [l for l in lines if 'error' in l.lower()]
            for err in error_lines[:5]:
                print(f"  {err}")
        else:
            print("✅ LaTeX syntax check passed")
    except Exception as e:
        print(f"Compilation check error: {e}")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
