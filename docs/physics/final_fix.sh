#!/bin/bash
echo "Finalizing v6.3 upgrades..."

# Create a clean Python script
cat > fix_v6.3.py << 'PYEOF'
import re

with open('L_TOEC_MASTER_V6.3_upgraded.tex', 'r') as f:
    content = f.read()

# 1. Replace MOND section
print("Replacing MOND section...")
mond_pattern = r'(\\\\paragraph\{Connection to Modified Gravity\}.*?)(?=\\\\paragraph|\\\\subsubsection|\\\\subsection)'
mond_match = re.search(mond_pattern, content, re.DOTALL)
if mond_match:
    new_mond = '''\\\\paragraph{Precise Modified-Poisson Framework (Replacing ``MOND-like'')}
\\\\tagmodel To avoid speculative ``MOND-like'' language, we formulate a precise testable modification of the Poisson equation:

\\\\begin{equation}
\\\\nabla\\\\cdot\\\\left[\\\\mu\\\\left(\\\\frac{|\\\\nabla\\\\varphi|}{a_0}\\\\right)\\\\nabla\\\\varphi\\\\right] = 4\\\\pi G\\\\rho
\\\\end{equation}

where $\\\\mu(x)$ is an interpolating function with limits:
\\\\begin{itemize}
\\\\item $\\\\mu(x) \\\\to 1$ for $x \\\\gg 1$ (Newtonian regime)
\\\\item $\\\\mu(x) \\\\to x$ for $x \\\\ll 1$ (deep-MOND regime)
\\\\end{itemize}

\\\\subsubsection{Substrate Origin Hypothesis}
We \\\\emph{hypothesize} (not claim) that substrate graph irregularities could induce an effective $\\\\mu(x)$ with:
\\\\begin{equation}
\\\\mu(x) = \\\\frac{x}{\\\\sqrt{1 + x^2}} \\\\quad\\\\text{(standard MOND interpolator)}
\\\\end{equation}

\\\\subsubsection{Testable Distinction from Empirical MOND}
L-ToEC would predict this modification arises from:
\\\\begin{itemize}
\\\\item \\\\textbf{Substrate sampling artifacts:} Discrete mapping at low acceleration scales.
\\\\item \\\\textbf{Computational resource limits:} UOS budget exhaustion in low-density regions.
\\\\item \\\\textbf{Predictable transition scale:} $a_0 \\\\sim f_U c$ (tied to Universal Clock).
\\\\end{itemize}

\\\\tagconj This remains a conjecture until: (1) derived from substrate dynamics, (2) shown to match galaxy rotation curves, (3) predicts new observables beyond empirical MOND fits.'''
    
    content = content.replace(mond_match.group(1), new_mond)

# 2. Add Fisher model before qualia
print("Adding Fisher geometry model...")
# Find qualia section
qualia_idx = content.find('qualia')
if qualia_idx != -1:
    # Go back to find subsection start
    sub_start = content.rfind('\\\\subsection', 0, qualia_idx)
    if sub_start != -1:
        model = '''\\\\subsection{Minimal Statistical Model for Fisher Geometry (v6.3)}
\\\\tagmodel To operationalize the Fisher metric in qualia mapping, we specify a minimal exponential family:

\\\\begin{equation}
p(L_3|\\\\theta) = \\\\exp\\\\left[\\\\theta^T T(L_3) - A(\\\\theta)\\\\right] h(L_3)
\\\\end{equation}

where:
\\\\begin{itemize}
\\\\item $L_3$: Interface state (neural/experiential configuration)
\\\\item $\\\\theta$: Natural parameters (substrate processing variables)
\\\\item $T(L_3)$: Sufficient statistics (perceptual features)
\\\\item $A(\\\\theta)$: Log-partition function
\\\\item $h(L_3)$: Base measure
\\\\end{itemize}

\\\\subsubsection{Concrete Toy Instantiation}
For analytical tractability, consider Gaussian model:
\\\\begin{equation}
p(\\\\mathbf{x}|\\\\boldsymbol{\\\\mu}, \\\\Sigma) = \\\\frac{1}{\\\\sqrt{(2\\\\pi)^k |\\\\Sigma|}} \\\\exp\\\\left[-\\\\frac{1}{2}(\\\\mathbf{x}-\\\\boldsymbol{\\\\mu})^T\\\\Sigma^{-1}(\\\\mathbf{x}-\\\\boldsymbol{\\\\mu})\\\\right]
\\\\end{equation}
where $\\\\mathbf{x} \\\\in \\\\mathbb{R}^k$ represents perceptual feature vector.

\\\\subsubsection{Fisher Metric Computation}
For Gaussian model, Fisher metric components:
\\\\begin{equation}
g_{\\\\mu_i\\\\mu_j} = \\\\Sigma^{-1}_{ij}, \\\\quad g_{\\\\Sigma_{ij}\\\\Sigma_{kl}} = \\\\frac{1}{2}\\\\text{Tr}\\\\left(\\\\Sigma^{-1}\\\\frac{\\\\partial\\\\Sigma}{\\\\partial\\\\Sigma_{ij}}\\\\Sigma^{-1}\\\\frac{\\\\partial\\\\Sigma}{\\\\partial\\\\Sigma_{kl}}\\\\right)
\\\\end{equation}

\\\\paragraph{Operational Status}
This specification:
\\\\begin{itemize}
\\\\item Makes Fisher metric computation explicit and well-defined
\\\\item Provides a foundation for numerical simulations
\\\\item Remains a toy model until neural/perceptual data is incorporated
\\\\item Status: \\\\texttt{[Model]} (explicit but not yet empirically grounded)
\\\\end{itemize}'''
        
        content = content[:qualia_idx] + model + content[qualia_idx:]

# 3. Add constant 5 clarification
print("Adding constant 5 clarification...")
if 'Uniqueness Argument' in content:
    # Simple insertion
    insert_point = content.find('Uniqueness Argument') + len('Uniqueness Argument')
    # Find next newline after some content
    next_newline = content.find('\\\\subsubsection', insert_point)
    if next_newline != -1:
        clarification = '''
\\\\paragraph{Selection Theorem vs Physical Law (v6.3 Clarification)}
The inference $24 = 6\\\\times 4 \\\\Rightarrow 5$ dark sectors is a \\\\textbf{selection theorem} within the L-ToEC architectural constraints, not a fundamental law of nature.

\\\\begin{itemize}
\\\\item \\\\textbf{Mathematical fact:} $Co_0$ has exactly six inequivalent 4D irreps (computationally verified).
\\\\item \\\\textbf{Architectural constraint:} Interface must be 4D for compatibility with GR.
\\\\item \\\\textbf{Selection principle:} Need $n>1$ copies for gauge structure.
\\\\item \\\\textbf{Physical identification:} ``Dark sectors'' = substrate subspaces not projected to interface.
\\\\end{itemize}

\\\\tagselect This remains a selection principle, not an empirical derivation. If future experiments revealed spacetime to be non-4D or gauge structure emerged differently, the factorization would change accordingly.'''
        
        content = content[:next_newline] + clarification + content[next_newline:]

with open('L_TOEC_MASTER_V6.3_FINAL.tex', 'w') as f:
    f.write(content)

print("Created L_TOEC_MASTER_V6.3_FINAL.tex")
PYEOF

python3 fix_v6.3.py

# Compile
echo "Compiling final version..."
pdflatex -interaction=nonstopmode L_TOEC_MASTER_V6.3_FINAL.tex > /dev/null 2>&1
pdflatex -interaction=nonstopmode L_TOEC_MASTER_V6.3_FINAL.tex > /dev/null 2>&1

if [ -f "L_TOEC_MASTER_V6.3_FINAL.pdf" ]; then
    echo "✅ SUCCESS: L_TOEC_MASTER_V6.3_FINAL.pdf created"
    ls -lh L_TOEC_MASTER_V6.3_FINAL.*
else
    echo "❌ Compilation failed"
fi
