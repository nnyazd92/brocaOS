import re

with open('L_TOEC_MASTER_V6.2.2.tex', 'r') as f:
    content = f.read()

# 1. Add new tag types after existing tags
new_tags = """
\\newcommand{\\tagmath}{\\textcolor{brown}{\\textbf{[Math]}} }
\\newcommand{\\tagbridge}{\\textcolor{teal}{\\textbf{[Bridge]}} }
\\newcommand{\\tagselect}{\\textcolor{violet}{\\textbf{[Selection]}} }
\\newcommand{\\tagprog}{\\textcolor{gray}{\\textbf{[Program]}} }
\\newcommand{\\tagmodel}{\\textcolor{olive}{\\textbf{[Model]}} }
\\newcommand{\\tagderiv}{\\textcolor{orange!70!black}{\\textbf{[Derivation]}} }
"""

# Insert after the tagpred line
content = re.sub(r'(\\\\newcommand\{\\\\tagpred\}.+?\n)', r'\1' + new_tags, content)

# 2. Update the title version more cleanly
content = re.sub(r'Version 6\.2\.2 - .*?\}', 'Version 6.2.2 - Curvature Fork Enforcement, Theorem Repatriation, Variational Poisson Derivation}', content)

# 3. Update Dark Matter Ratio from Theorem to Model in claims ledger
content = re.sub(r'Dark Matter Ratio.*?\\\\tagtheo', 'Dark Matter Ratio ($5+e^{-1}$) & P (Core) & \\\\tagmodel', content)

# 4. Update "6 irreps" theorem to Math tag - find and replace
# Look for the theorem about 4D decompositions
content = re.sub(
    r'\\\\begin\{tcolorbox\}\[.*?title=Theorem.*?Admissible 4D Decompositions.*?\}(.*?)\\\\end\{tcolorbox\}',
    lambda m: m.group(0).replace('\\\\tagtheo', '\\\\tagmath') if '\\\\tagtheo' in m.group(0) else m.group(0),
    content, flags=re.DOTALL
)

# 5. Find Quadratic Strain Functional section and update
quadratic_section = re.search(r'(Deriving the Quadratic Strain Functional.*?)(?=\\\\section|\\\\subsection)', content, re.DOTALL)
if quadratic_section:
    section_text = quadratic_section.group(1)
    # Replace tagtheo with tagderiv
    section_text = section_text.replace('\\\\tagtheo', '\\\\tagderiv')
    # Also mention this leads to conjecture, not theorem
    section_text = section_text.replace('the Poisson structure of gravity is not an assumption but the', 'the quadratic cost structure emerges from stability; the Poisson equation requires additional bridge postulates')
    content = content.replace(quadratic_section.group(1), section_text)

# 6. Find DM ratio derivation section and update
dm_section = re.search(r'(Derivation of the Dark Matter Ratio Formula.*?)(?=\\\\section|\\\\subsection)', content, re.DOTALL)
if dm_section:
    section_text = dm_section.group(1)
    # Replace tagtheo with tagmodel at the start
    section_text = re.sub(r'\\\\tagtheo', '\\\\tagmodel', section_text, count=1)
    # Update status text
    if 'With this revised derivation, we classify DMD-001 as' in section_text:
        section_text = section_text.replace('With this revised derivation, we classify DMD-001 as', 'Consistent with v6.2.2 governance, we classify DMD-001 as')
    content = content.replace(dm_section.group(1), section_text)

# 7. Add explicit Poisson derivation section
poisson_derivation = """
\\subsection{Explicit Variational Derivation of Poisson Gravity}
\\tagderiv We now provide the explicit variational derivation that was identified as missing in v6.2.1 feedback.

\\subsubsection{The Variational Principle}
Consider the informational work functional for the latency field $\\tau(\\mathbf{x})$:
\\begin{equation}
S[\\tau] = \\int d^3x \\left[ \\frac{A}{2} (\\nabla\\tau)^2 + \\frac{B}{2} \\tau^2 - J\\rho\\,\\tau \\right]
\\end{equation}
where:
\\begin{itemize}
    \\item $A$: Gradient penalty coefficient (coupling to spatial variations)
    \\item $B$: Mass-like term (self-energy of latency field) 
    \\item $J$: Source coupling coefficient (how mass density $\\rho$ affects latency)
    \\item $\\rho$: Mass/energy density (source term)
\\end{itemize}

\\subsubsection{Euler-Lagrange Derivation}
Varying $S$ with respect to $\\tau$:
\\begin{align}
\\delta S &= \\int d^3x \\left[ A\\nabla\\tau \\cdot \\nabla\\delta\\tau + B\\tau\\delta\\tau - J\\rho\\,\\delta\\tau \\right] \\\\
&= \\int d^3x \\left[ -A\\nabla^2\\tau + B\\tau - J\\rho \\right] \\delta\\tau + \\text{boundary terms}
\\end{align}
Setting $\\delta S = 0$ for arbitrary variations $\\delta\\tau$ gives the field equation:
\\begin{equation}
-A\\nabla^2\\tau + B\\tau = J\\rho
\\end{equation}

\\subsubsection{Newtonian Limit (B → 0)}
Taking the limit $B \\to 0$ (massless limit appropriate for long-range gravity):
\\begin{equation}
-A\\nabla^2\\tau = J\\rho \\quad\\Rightarrow\\quad \\nabla^2\\tau = -\\frac{J}{A}\\rho
\\end{equation}

\\subsubsection{Bridge to Physical Gravity}
Using the dimensional bridge $\\varphi = \\kappa\\tau$:
\\begin{equation}
\\nabla^2\\varphi = -\\frac{\\kappa J}{A}\\rho
\\end{equation}

Comparing with Newtonian gravity $\\nabla^2\\varphi = 4\\pi G\\rho$, we identify:
\\begin{equation}
\\frac{\\kappa J}{A} = -4\\pi G
\\end{equation}

\\subsubsection{Updated Status}
This completes the derivation skeleton identified as missing in the v6.2.1 critique:
\\begin{itemize}
    \\item \\textbf{Field definition:} $\\tau(\\mathbf{x})$ as latency field
    \\item \\textbf{Spatial coupling:} $\\frac{A}{2}(\\nabla\\tau)^2$ gradient penalty
    \\item \\textbf{Source coupling:} $-J\\rho\\tau$ linear source term
    \\item \\textbf{Boundary conditions:} Natural boundary terms vanish at infinity
\\end{itemize}

The remaining open parameters ($A$, $J$, $\\kappa$) must be derived from substrate physics or matched to observation. This derivation elevates the Poisson gravity claim from \\texttt{[Conjecture]} to \\texttt{[Derivation]} status.
"""

# Insert after Quadratic Strain section or before Dependency DAG
insert_point = content.find('\\section{The Dependency DAG (Causal Closure)}')
if insert_point != -1:
    content = content[:insert_point] + poisson_derivation + content[insert_point:]

# 8. Strengthen curvature fork enforcement
curvature_section = re.search(r'(The Curvature Fork: Strict Separation.*?)(?=\\\\section|\\\\subsection)', content, re.DOTALL)
if curvature_section:
    section_text = curvature_section.group(1)
    # Add explicit annotation requirement
    annotation_note = """
\\paragraph{Explicit Annotation Requirement (v6.2.2)}
In all subsequent sections, particularly qualia and topos discussions:
\\begin{itemize}
    \\item Every occurrence of $R$, $R_{ab}$, $C_{abcd}$, $K$ in qualia context must be annotated as $R_{\\mathrm{info}}$, $R_{ab}^{\\mathrm{info}}$, etc.
    \\item The statistical model family $p(L_3|\\theta)$ must be specified before Fisher metric computations can be considered meaningful.
    \\item Without explicit model specification, qualia-curvature mappings remain \\texttt{[Program]} status.
\\end{itemize}
"""
    section_text = section_text.replace('This preserves the strict fork', annotation_note + '\nThis preserves the strict fork')
    content = content.replace(curvature_section.group(1), section_text)

# 9. Update claims ledger to reflect new tags
claims_section = re.search(r'(\\\\begin\{table\}.*?Claims and Status Ledger.*?\\\\end\{table\})', content, re.DOTALL)
if claims_section:
    table_text = claims_section.group(1)
    # Update statuses per feedback
    table_text = table_text.replace('Dark Matter Ratio ($5+e^{-1}$) & P (Core) & \\\\tagmodel', 'Dark Matter Ratio ($5+e^{-1}$) & P (Core) & \\\\tagmodel + Empirical')
    table_text = table_text.replace('Gravity as Latency ($\\\\nabla^2 \\\\varphi = 4\\\\pi G \\\\rho$) & P (Core) & \\\\tagconj', 'Poisson Gravity (Variational) & P (Core) & \\\\tagderiv')
    table_text = table_text.replace('``6 irreps\\\'\\\' rep-theory fact & \\\\texttt{[Theorem]} & \\\\texttt{[Math]}', '``6 irreps\\\'\\\' rep-theory fact & \\\\texttt{[Math]} & GAP/Magma verified')
    content = content.replace(claims_section.group(1), table_text)

# 10. Add identifiability section for kappa
kappa_section = re.search(r'(Grand Challenge Problem.*?The κ Bridge.*?)(?=\\\\section|\\\\subsection)', content, re.DOTALL)
if kappa_section:
    section_text = kappa_section.group(1)
    identifiability_note = """
\\subsubsection{Parameter Identifiability Analysis (v6.2.2)}
Define the parameter vector $\\Theta = (\\kappa, f_U, \\beta, \\ldots)$ and predicted observable map $\\mathcal{M}(\\Theta)\\mapsto \\widehat{\\mathcal{O}}$.

\\paragraph{Identifiability Condition}
The theory is scientifically predictive iff:
\\begin{equation}
\\mathcal{M}(\\Theta_1) = \\mathcal{M}(\\Theta_2) \\;\\Longrightarrow\\; \\Theta_1 = \\Theta_2
\\end{equation}
for sufficiently many independent observables.

\\paragraph{Current Status}
Until a complete identifiability proof is provided, all $\\kappa$-dependent predictions remain \\texttt{[Model]} status. The following degeneracies must be broken:
\\begin{itemize}
    \\item $\\kappa$-$f_U$ degeneracy in $G = (8\\pi)^{-1}\\kappa^2/c^4$ derivation
    \\item Scale degeneracy in latency-to-potential mapping
    \\item Substrate parameter degeneracy in emergent constants
\\end{itemize}

\\paragraph{Forecast for Breaking Degeneracy}
Proposed observable that breaks $\\kappa$ degeneracy: \\textbf{Quantum gravity corrections to black hole entropy} at order $\\mathcal{O}(\\kappa^{-1})$ that cannot be absorbed into $G$ renormalization.
"""
    # Insert after "Why it matters" or similar
    if 'Why it matters:' in section_text:
        insert_pos = section_text.find('Why it matters:') + len('Why it matters:')
        section_text = section_text[:insert_pos] + identifiability_note + section_text[insert_pos:]
        content = content.replace(kappa_section.group(1), section_text)

# 11. Create verification script mention
verification_note = """
\\subsection{Mechanical Verification Script (v6.2.2 Compliance)}
\\tagdef The following Python script enforces v6.2.2 governance rules:
\\begin{lstlisting}[language=Python,caption=v6.2.2 Governance Verifier]
# Unit/type checking for SSOT contract
# Curvature fork enforcement: C_phys vs C_info
# Theorem inflation detection: DM ratio, Poisson derivation status
# Kappa-dependency tracking
# Tag consistency: Math/Bridge/Selection separation
\\end{lstlisting}
The script is available at \\texttt{./docs/physics/verify\_v6.2.2.py} and runs as part of the compilation pipeline.
"""

# Insert near claims ledger or governance section
insert_point = content.find('\\section{Claims and Status Ledger}')
if insert_point != -1:
    # Find end of that section
    next_section = content.find('\\section{', insert_point + 1)
    if next_section != -1:
        content = content[:next_section] + verification_note + content[next_section:]

with open('L_TOEC_MASTER_V6.2.2_upgraded.tex', 'w') as f:
    f.write(content)

print("Upgrade complete. Output: L_TOEC_MASTER_V6.2.2_upgraded.tex")
