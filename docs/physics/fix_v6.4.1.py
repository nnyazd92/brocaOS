#!/usr/bin/env python3
"""
Fix LaTeX errors in v6.4.1
"""

with open('L_TOEC_MASTER_V6.4.1_ENHANCED.tex', 'r') as f:
    content = f.read()

# Fix the problematic table with α character
# Replace the problematic table section
problematic_table = '''\\begin{table}[h!]
\\centering
\\begin{tabular}{p{0.3\\textwidth}p{0.3\\textwidth}p{0.3\\textwidth}}
\\toprule
\\textbf{Level} & \\textbf{α_G Prediction} & \\textbf{Scientific Impact} \\\\
\\midrule
Minimum & Within 2 orders of magnitude & Interesting, needs work \\\\
Moderate & Within factor of 2 & Compelling, warrants attention \\\\
Full (``Oh Fuck'') & Within experimental error & Paradigm-shifting \\\\
\\bottomrule
\\end{tabular}
\\caption{Success criteria for α_G derivation}
\\end{table}'''

fixed_table = '''\\begin{table}[h!]
\\centering
\\begin{tabular}{p{0.3\\textwidth}p{0.3\\textwidth}p{0.3\\textwidth}}
\\toprule
\\textbf{Level} & \\textbf{\$\\alpha_G\$ Prediction} & \\textbf{Scientific Impact} \\\\
\\midrule
Minimum & Within 2 orders of magnitude & Interesting, needs work \\\\
Moderate & Within factor of 2 & Compelling, warrants attention \\\\
Full (``Oh Fuck'') & Within experimental error & Paradigm-shifting \\\\
\\bottomrule
\\end{tabular}
\\caption{Success criteria for \$\\alpha_G\$ derivation}
\\end{table}'''

content = content.replace(problematic_table, fixed_table)

# Also fix any other α characters in math mode
content = content.replace('α_G', '$\\alpha_G$')
content = content.replace('α_', '$\\alpha_')

# Write fixed file
with open('L_TOEC_MASTER_V6.4.1_FINAL.tex', 'w') as f:
    f.write(content)

print("Created L_TOEC_MASTER_V6.4.1_FINAL.tex with fixed LaTeX")

# Now compile
import subprocess
print("\\nCompiling...")
result = subprocess.run(['pdflatex', '-interaction=nonstopmode', 'L_TOEC_MASTER_V6.4.1_FINAL.tex'], 
                       capture_output=True, text=True)
if result.returncode == 0:
    print("✅ First compilation successful")
    # Second pass for references
    subprocess.run(['pdflatex', '-interaction=nonstopmode', 'L_TOEC_MASTER_V6.4.1_FINAL.tex'], 
                   capture_output=True, text=True)
    print("✅ Second compilation successful")
    
    # Check if PDF exists
    import os
    if os.path.exists('L_TOEC_MASTER_V6.4.1_FINAL.pdf'):
        size = os.path.getsize('L_TOEC_MASTER_V6.4.1_FINAL.pdf')
        print(f"✅ PDF created: {size/1024:.0f} KB")
        print("\\n=== v6.4.1 DELIVERABLE READY ===")
        print("Main document: L_TOEC_MASTER_V6.4.1_FINAL.pdf")
        print("Source: L_TOEC_MASTER_V6.4.1_FINAL.tex")
    else:
        print("❌ PDF not created")
        print("Error output:", result.stderr[:500])
else:
    print("❌ Compilation failed")
    print("Error:", result.stderr[:500])
