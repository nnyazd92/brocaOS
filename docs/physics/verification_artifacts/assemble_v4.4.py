import re

# Load parts
with open('docs/physics/L_TOEC_MASTER_V4.3.tex', 'r') as f:
    base = f.read()

# Update version and title
base = base.replace('Version 4.3 - Master Consolidation (Uniqueness & Stability)', 
                    'Version 4.4 - Master Consolidation (Exclusivity & Necessity)')
base = base.replace('This version (v4.3)', 'This version (v4.4)')
base = base.replace('Exclusivity & Necessity', r'Exclusivity \& Necessity')

# Add preamble
preamble_add = r"""
\usepackage[most]{tcolorbox}
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, arrows, positioning}

% Custom tcolorbox for Theorems
\newtcolorbox{mytheorem}[2][]{
  colback=green!5!white,
  colframe=green!75!black,
  fonttitle=\bfseries,
  title=#2,
  #1
}

% Custom tcolorbox for Axioms
\newtcolorbox{myaxiom}[2][]{
  colback=blue!5!white,
  colframe=blue!75!black,
  fonttitle=\bfseries,
  title=#2,
  #1
}
"""
base = base.replace(r'\usepackage{tocloft}', r'\usepackage{tocloft}' + preamble_add)

# Load new sections
with open('docs/physics/L_TOEC_V4.4_SECTION2.tex', 'r') as f:
    sec2 = f.read()
with open('docs/physics/L_TOEC_V4.4_SECTION3.tex', 'r') as f:
    sec3 = f.read()
with open('docs/physics/L_TOEC_V4.4_SECTION5.tex', 'r') as f:
    sec5 = f.read()
with open('docs/physics/L_TOEC_V4.4_DIAGRAMS.tex', 'r') as f:
    diagrams = f.read()

# Split base into sections using the exact string
sections = base.split(r'\section{')

# Insert diagrams after Introduction (sections[3])
sections[3] += diagrams

# Replace sections by matching titles
for i in range(len(sections)):
    if 'Track 1: Formal Toy Models' in sections[i]:
        # Replace the entire section content
        # We will replace the whole string including the delimiter later
        sections[i] = "REPLACE_SEC2"
    elif 'Particle Emergence: The Lattice Defect Model' in sections[i]:
        sections[i] = "REPLACE_SEC3"
    elif 'The Ouroboric Closure' in sections[i]:
        sections[i] = "REPLACE_SEC5"

# Re-assemble
new_content = sections[0]
for i in range(1, len(sections)):
    if sections[i] == "REPLACE_SEC2":
        new_content += sec2
    elif sections[i] == "REPLACE_SEC3":
        new_content += sec3
    elif sections[i] == "REPLACE_SEC5":
        new_content += sec5
    else:
        new_content += r'\section{' + sections[i]

with open('docs/physics/L_TOEC_MASTER_V4.4.tex', 'w') as f:
    f.write(new_content)
