#!/bin/bash
echo "Finalizing L-ToEC v6.2.2 upgrade..."

# 1. Add missing tag definitions
sed -i '/\\newcommand{\\tagpred}/a \
\\newcommand{\\tagmath}{\\textcolor{brown}{\\textbf{[Math]}} }\
\\newcommand{\\tagbridge}{\\textcolor{teal}{\\textbf{[Bridge]}} }\
\\newcommand{\\tagselect}{\\textcolor{violet}{\\textbf{[Selection]}} }\
\\newcommand{\\tagprog}{\\textcolor{gray}{\\textbf{[Program]}} }\
\\newcommand{\\tagmodel}{\\textcolor{olive}{\\textbf{[Model]}} }\
\\newcommand{\\tagderiv}{\\textcolor{orange!70!black}{\\textbf{[Derivation]}} }' L_TOEC_MASTER_V6.2.2_upgraded.tex

# 2. Check for DM ratio in claims ledger and update if needed
sed -i 's/Dark Matter Ratio.*\\tagtheo/Dark Matter Ratio (\$5+e^{-1}\$) \& P (Core) \& \\tagmodel/' L_TOEC_MASTER_V6.2.2_upgraded.tex

# 3. Update "6 irreps" to use tagmath
sed -i '/Admissible 4D Decompositions/,/\\end{tcolorbox}/s/\\tagtheo/\\tagmath/' L_TOEC_MASTER_V6.2.2_upgraded.tex

# 4. Check for Quadratic Strain section
echo "Checking for Poisson derivation..."
if grep -q "Explicit Variational Derivation of Poisson Gravity" L_TOEC_MASTER_V6.2.2_upgraded.tex; then
    echo "✓ Poisson derivation present"
else
    echo "✗ Poisson derivation missing"
fi

# 5. Create final compiled version
echo "Creating final v6.2.2..."
cp L_TOEC_MASTER_V6.2.2_upgraded.tex L_TOEC_MASTER_V6.2.2_FINAL.tex

# 6. Run verification
python3 verify_v6.2.2.py

# 7. Compile PDF
echo "Compiling PDF..."
pdflatex -interaction=nonstopmode L_TOEC_MASTER_V6.2.2_FINAL.tex > /dev/null 2>&1
pdflatex -interaction=nonstopmode L_TOEC_MASTER_V6.2.2_FINAL.tex > /dev/null 2>&1

if [ -f "L_TOEC_MASTER_V6.2.2_FINAL.pdf" ]; then
    echo "✅ Success: L_TOEC_MASTER_V6.2.2_FINAL.pdf created"
    ls -lh L_TOEC_MASTER_V6.2.2_FINAL.*
else
    echo "❌ PDF compilation failed"
fi
