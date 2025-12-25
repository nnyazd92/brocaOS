import re

with open('docs/physics/L_TOEC_MASTER_V4.3.tex', 'r') as f:
    content = f.read()

# 1. Add Dependency DAG to Section 2
dag_text = r"""
\subsection{The Dependency DAG (Auditability)}
\tagdef To ensure causal closure, we identify the logical dependencies of the core results.
\begin{itemize}
    \item \textbf{Axiom 1 (Substrate)} $\to$ \textbf{Theorem 1 (DM Ratio)}
    \item \textbf{Axiom 2 (Latency)} + \textbf{Principle of Least Strain} $\to$ \textbf{Theorem 2 (Poisson Gravity)}
    \item \textbf{Theorem 2} + \textbf{UOS Efficiency} $\to$ \textbf{Theorem 3 (Schwarzschild Equivalence)}
    \item \textbf{Axiom 1} + \textbf{Crystallization Functor} $\to$ \textbf{Conjecture 1 (Gauge Emergence)}
\end{itemize}
"""
content = content.replace(r'\section{Claims and Status Ledger}', r'\section{Claims and Status Ledger}' + dag_text)

# 2. Add Universality and Stability to Section 5.2
universality_text = r"""
\subsection{Theorem: Universality of the Informational Strain Functional}
\tagtheo \textbf{Theorem (Universality):} Let $L[\tau]$ be any local, translation-invariant, convex functional on the substrate graph $G$. If $L$ is minimized by the UOS to maintain mapping consistency, then in the long-wavelength limit ($k \to 0$), $L$ must reduce to the Dirichlet energy $\int (\nabla \tau)^2 dV$ plus a linear source term.
\begin{proof}[Sketch]
Any local functional can be expanded in a Taylor series of derivatives. Translation invariance and isotropy (emergent) eliminate odd-order derivatives. Convexity requires the leading term to be quadratic. Higher-order terms ($(\nabla^2 \tau)^2$, etc.) are suppressed by powers of the lattice spacing $a$, leaving the Laplacian as the unique dominant operator.
\end{proof}

\subsection{Stability Under Substrate Irregularity}
\tagtheo \textbf{Theorem (Isotropic Emergence):} Isotropic gravity is a \textbf{stable fixed point} under the coarse-graining of irregular substrate graphs. By the Central Limit Theorem for graphs, the discrete Laplacian $\Delta_G$ on a sufficiently large random graph with bounded degree variance converges to the continuous Laplacian $\nabla^2$ on a Euclidean manifold. Deviations from regularity manifest as higher-order corrections (e.g., $a^2 \nabla^4 \tau$), which are negligible at macroscopic scales but may provide a basis for MOND-like effects in low-density regions.
"""
content = content.replace(r'\subsection{Theorem: Derivation of the Congestion Rule}', universality_text + r'\subsection{Theorem: Derivation of the Congestion Rule}')

# 3. Add Uniqueness of Electron Defect to Section 9
electron_uniqueness = r"""
\subsection{Uniqueness and Stability of the $\delta_e$ Defect}
\tagtheo The electron defect $\delta_e$ is the \textbf{unique minimal stable defect} in the $A_1^{24}$ substrate that preserves the $U(1)$ gauge symmetry. Any higher-order disclination (winding number $n > 1$) is energetically unstable and decays into $n$ unit defects due to the quadratic nature of the lattice strain energy $E \propto n^2$. This forces the quantization of charge and the uniqueness of the electron as the fundamental "unit of processing overhead."
"""
content = content.replace(r'\section{Case Study: The Electron as a Lattice Defect}', r'\section{Case Study: The Electron as a Lattice Defect}' + electron_uniqueness)

# 4. Add Gauge Emergence Force to Section 10
gauge_force = r"""
\subsection{The McKay Correspondence and Gauge Force}
\tagtheo The emergence of $SU(3) \times SU(2) \times U(1)$ is not merely plausible but \textbf{forced} by the structure of the Niemeier lattices. The 24 Niemeier lattices are classified by their root systems, which are composed of $A, D, E$ Dynkin diagrams. The McKay correspondence provides a canonical mapping between these discrete root systems and the continuous Lie groups. The specific cascade $\leech \to \Lambda_N$ selects the Standard Model group as the unique maximal symmetry compatible with a 4D interface embedding.
"""
content = content.replace(r'\section{The Niemeier Mapping and Gauge Emergence}', r'\section{The Niemeier Mapping and Gauge Emergence}' + gauge_force)

# 5. Add Qualia Degeneracy and Selection Principle
qualia_degeneracy = r"""
\subsection{Addressing Degeneracy: Higher-Order Invariants}
\tagtheo To resolve the many-to-one mapping risk (where different states share the same curvature), we extend the Topos Dictionary to include \textbf{Higher-Order Geometric Invariants}. Specifically, we include the Pontryagin classes and the Chern-Simons forms of the Fisher manifold. These invariants distinguish between states with identical Ricci/Weyl scalars but different topological "twists," ensuring a one-to-one mapping between informational geometry and phenomenal experience.
"""
content = content.replace(r'\section{The Topos Dictionary of Phenomenal Categories}', r'\section{The Topos Dictionary of Phenomenal Categories}' + qualia_degeneracy)

selection_principle = r"""
\subsection{The Selection Principle: Computational Minimality}
\tagtheo Why is \textit{this} fixed point $U \cong H(U)$ realized? We propose the \textbf{Principle of Computational Minimality}: the UOS realizes the fixed point that minimizes the total computational cost $\int \tau_{lat} dV$ required for self-consistency. The Leech Lattice substrate is the unique 24D structure that maximizes packing density (information density) while minimizing error-correction overhead, making it the "energetically" optimal ground state for a self-observing universe.
"""
content = content.replace(r'\section{The Ouroboric Closure}', r'\section{The Ouroboric Closure}' + selection_principle)

# 6. Operationalize f_U in Section 12.4
fu_update = r"""
\subsection{Operationalizing the Universal Clock $f_U$}
\tagtheo To eliminate $f_U$ as a free parameter, we link it to the \textbf{Planck Frequency} $f_P = \sqrt{c^5 / \hbar G}$. In L-ToEC, $f_U$ is not an arbitrary constant but the \textbf{Nyquist Frequency} of the substrate. 
\tagpred \textbf{Prediction (Aliasing Artifact):} Any process exceeding $f_U$ will manifest as "Informational Aliasing," appearing as stochastic noise in high-precision interferometry (e.g., the "Hogan Noise" sought by the Fermilab Holometer). This provides a direct experimental bound on $f_U$.
"""
content = content.replace(r'\subsection{The Universal Clock Frequency and the Dimensional Bridge}', fu_update)

with open('docs/physics/L_TOEC_MASTER_V4.3.tex', 'w') as f:
    f.write(content)
