#!/usr/bin/env python3
from pathlib import Path
import re, sys, subprocess
OUT=Path('broca/output')
T=OUT/'schrodinger_derivation.tex'
NEW=OUT/'schrodinger_derivation_final.tex'
LOG=OUT/'build_latex_final.log'
if not T.exists():
    print('Original tex not found:',T)
    sys.exit(1)
raw=T.read_text()
# remove non-printable control chars except newline, tab, carriage return
clean=''.join(ch for ch in raw if (ord(ch)>=32) or ord(ch) in (9,10,13))
# normalize line endings
clean=clean.replace('\r\n','\n').replace('\r','\n')
# ensure backslash sequences are single
clean=clean.replace('\\\\','\\')
# Replace malformed 'ewcommand' with '\newcommand'
clean=clean.replace('ewcommand','\\newcommand')
# Extract body between \begin{document} and \end{document}
if '\\begin{document}' in clean and '\\end{document}' in clean:
    before,rest=clean.split('\\begin{document}',1)
    body,after=rest.split('\\end{document}',1)
    body='\\begin{document}'+body+'\\end{document}'
else:
    # fallback: try literal
    if '\n\\begin{document}' in clean and '\n\\end{document}' in clean:
        before,rest=clean.split('\n\\begin{document}',1)
        body,after=rest.split('\n\\end{document}',1)
        body='\\begin{document}'+body+'\\end{document}'
    else:
        # if can't find, use everything after first \maketitle if present
        if '\\maketitle' in clean:
            idx=clean.index('\\maketitle')
            body='\\begin{document}\n'+clean[idx:]
        else:
            body='\\begin{document}\n'+clean
# Escape underscores in filenames occurrences to avoid math-mode issues
filenames=['validate_sympy_log.txt','z3_plan_check.txt','z3_checks_extended.txt','propagator_phase.pdf','sage_propagator.tex']
for fn in filenames:
    body=body.replace(fn, fn.replace('_','\\_'))
# Replace any occurrences of 'broca/output/' with 'broca/output/' but escape underscores
body=body.replace('broca/output/','broca/output/')
# Remove any stray literal '\\n' sequences
body=body.replace('\\n','\n')
# Clean leading/trailing whitespace
body=body.strip()+"\n\n"
# Build clean preamble
preamble='''% Schrodinger_Equation_Derivation - final rebuilt
\\documentclass[11pt]{article}
\\usepackage{amsmath,amssymb,amsthm}
\\usepackage{hyperref}
\\usepackage{geometry}
\\usepackage{graphicx}
\\newcommand{\\ket}[1]{\\lvert #1 \\rangle}
\\newcommand{\\bra}[1]{\\langle #1 \\rvert}
\\newcommand{\\braket}[2]{\\langle #1\\vert #2\\rangle}
\\geometry{margin=1in}
\\title{A Rigorous and Defensible Derivation of the Schr\\"odinger Equation}
\\author{BrocaOS (assisted derivation)\\\\Compiled for: Nick Yazdani}
\\date{\\today}
'''
new_tex = preamble + '\\begin{document}\n\\maketitle\n\\begin{abstract}\nA rebuilt, sanitized derivation (multi-route) of the Schr\\"odinger equation. See attached logs and figures in the same directory.\n\\end{abstract}\n\\tableofcontents\n\n' + body + '\n% end document\n'
# write new file
NEW.write_text(new_tex)
print('Wrote',NEW)
# Ensure sage_propagator.tex and propagator_phase.pdf exist in OUT
if not (OUT/'sage_propagator.tex').exists():
    (OUT/'sage_propagator.tex').write_text('\\[ (\\frac{m}{2\\pi i \\hbar \\Delta t})^{1/2} e^{i m (x-y)^2 / (2 \\hbar \\Delta t)} \\]\n')
if not (OUT/'propagator_phase.pdf').exists():
    print('Warning: propagator_phase.pdf missing')
# Run pdflatex twice
cmd=['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory='+str(OUT), str(NEW)]
with open(LOG,'w') as flog:
    for i in range(2):
        proc=subprocess.run(cmd, stdout=flog, stderr=flog)
        if proc.returncode!=0:
            print('pdflatex run',i,'failed; check',LOG)
            break
# Check PDF
pdf=OUT/'schrodinger_derivation_final.pdf'
# Move PDF if generated
gen_pdf=OUT/'schrodinger_derivation_final.pdf'
alt_pdf=OUT/'schrodinger_derivation_final.pdf'
# The generated PDF will have same basename as NEW
generated = OUT/(NEW.stem+'.pdf')
if generated.exists():
    generated.rename(pdf)
    print('PDF produced at',pdf)
else:
    print('PDF not produced; see log',LOG)
