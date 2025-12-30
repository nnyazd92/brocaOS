#!/usr/bin/env python3
"""
v6.2.2 Governance Verifier
Enforces the critical feedback fixes from v6.2.1 critique.
"""

import re
import sys
from pathlib import Path

class GovernanceVerifier:
    def __init__(self, tex_file):
        self.tex_file = tex_file
        with open(tex_file, 'r') as f:
            self.content = f.read()
        self.errors = []
        self.warnings = []
        
    def check_dm_ratio_tag(self):
        """Check Dark Matter Ratio is not tagged as Theorem"""
        # Check claims ledger
        dm_pattern = r'Dark Matter Ratio.*?\\\\tagtheo'
        if re.search(dm_pattern, self.content):
            self.errors.append("Dark Matter Ratio should not be \\\\tagtheo (should be \\\\tagmodel)")
        
        # Check derivation section
        dm_section = re.search(r'Derivation of the Dark Matter Ratio.*?\\\\tagtheo', self.content, re.DOTALL)
        if dm_section:
            self.errors.append("DM ratio derivation section should start with \\\\tagmodel not \\\\tagtheo")
            
    def check_poisson_derivation_present(self):
        """Check explicit variational derivation of Poisson gravity exists"""
        poisson_keywords = ['Explicit Variational Derivation of Poisson Gravity',
                           'Euler-Lagrange Derivation.*nabla.*tau',
                           'gradient penalty.*nabla']
        found = False
        for keyword in poisson_keywords:
            if re.search(keyword, self.content, re.IGNORECASE | re.DOTALL):
                found = True
                break
        if not found:
            self.errors.append("Missing explicit variational derivation of Poisson gravity")
            
    def check_curvature_fork_annotations(self):
        """Check curvature symbols in qualia sections are annotated"""
        # Find qualia/topos sections
        qualia_pattern = r'(?:qualia|topos|phenomenal).*?(?=\\\\section|\\\\subsection)'
        qualia_sections = re.finditer(qualia_pattern, self.content, re.IGNORECASE | re.DOTALL)
        
        for section in qualia_sections:
            section_text = section.group(0)
            # Check for unannotated curvature symbols
            curvature_symbols = [r'\\$R\\b', r'\\$R_{', r'\\$C_{', r'\\$K\\b']
            for symbol in curvature_symbols:
                matches = list(re.finditer(symbol, section_text))
                for match in matches:
                    # Check if annotated with _\text{info} or similar
                    context = section_text[max(0, match.start()-50):min(len(section_text), match.end()+50)]
                    if not ('info' in context or 'Info' in context or 'mathrm{info}' in context):
                        self.warnings.append(f"Unannotated curvature symbol in qualia section: {match.group()}")
                        
    def check_kappa_identifiability(self):
        """Check κ identifiability discussion exists"""
        ident_keywords = ['identifiability', 'degeneracy', r'\\Theta.*=.*\\kappa', 'parameter vector']
        found = False
        for keyword in ident_keywords:
            if re.search(keyword, self.content, re.IGNORECASE):
                found = True
                break
        if not found:
            self.warnings.append("Missing κ identifiability/parameter degeneracy analysis")
            
    def check_tag_separation(self):
        """Check Math/Bridge/Selection tag usage"""
        # Count occurrences of new tags
        new_tags = ['tagmath', 'tagbridge', 'tagselect', 'tagprog', 'tagmodel', 'tagderiv']
        tag_counts = {}
        for tag in new_tags:
            count = self.content.count(f'\\\\{tag}')
            tag_counts[tag] = count
            
        if sum(tag_counts.values()) == 0:
            self.warnings.append("New tags (Math/Bridge/Selection/Program/Model/Deriv) not used")
        else:
            print("Tag usage:")
            for tag, count in tag_counts.items():
                if count > 0:
                    print(f"  {tag}: {count}")
                    
    def check_6_irreps_math_tag(self):
        """Check '6 irreps' is tagged as Math not Theorem"""
        # Look for the theorem about 4D decompositions
        theorem_pattern = r'Admissible 4D Decompositions.*?\\\\tagtheo'
        if re.search(theorem_pattern, self.content, re.DOTALL):
            self.errors.append("'6 irreps' theorem should be \\\\tagmath not \\\\tagtheo")
            
    def verify_all(self):
        """Run all checks"""
        print(f"Verifying {self.tex_file} for v6.2.2 compliance...")
        print("=" * 60)
        
        self.check_dm_ratio_tag()
        self.check_poisson_derivation_present()
        self.check_curvature_fork_annotations()
        self.check_kappa_identifiability()
        self.check_tag_separation()
        self.check_6_irreps_math_tag()
        
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
    tex_file = "L_TOEC_MASTER_V6.2.2_upgraded.tex"
    if not Path(tex_file).exists():
        print(f"File {tex_file} not found!")
        sys.exit(1)
        
    verifier = GovernanceVerifier(tex_file)
    success = verifier.verify_all()
    
    # Also compile to check LaTeX
    print("\n" + "=" * 60)
    print("Attempting LaTeX compilation...")
    
    import subprocess
    try:
        # First pass
        result = subprocess.run(['pdflatex', '-interaction=nonstopmode', tex_file], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print("LaTeX compilation issues:")
            print(result.stderr[:500])
        else:
            print("✅ LaTeX compiled successfully")
    except Exception as e:
        print(f"Compilation error: {e}")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
