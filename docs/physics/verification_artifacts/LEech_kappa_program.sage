"""
Leech-lattice κ program (skeleton)

Goal:
  - Construct the Leech lattice Λ24 (via Sage's lattice code or explicit construction).
  - Enumerate (or sample) minimal vectors.
  - Choose a 4D physical subspace H ⊂ R^24 via a 4×24 projection matrix Π.
  - Compute projected-norm statistics such as
        Z_Λ(H) ≈ (J/a^2)(1/|M|) Σ_{m∈M} ||Π m||^2
    where M is the set of minimal vectors.

This is a *programmatic* artifact: it documents how to do the computation
and provides a concrete starting point, but it does not yet commit to
specific UOS dynamics.

Run in a Sage environment, e.g.:
    sage LEech_kappa_program.sage
"""

from sage.all import *

# ---------------------------------------------------------------------------
# 1. Construct (or load) the Leech lattice Λ24
# ---------------------------------------------------------------------------

def build_leech_lattice():
    """Return a Leech lattice Λ24 as a QuadraticForm or Lattice.

    Sage has Leech-related constructions in different versions; we try a
    few options and fall back to a placeholder if necessary.
    """
    try:
        # Option 1: built-in even unimodular positive definite 24D form
        # In many Sage versions, QuadraticForm.lattice() can be used to
        # obtain the Leech lattice via a named constructor. This is version-
        # dependent, so this may need adjustment.
        #
        # Placeholder: use a canonical Leech QF if available.
        from sage.quadratic_forms.quadratic_form_catalog import QuadraticForm
        Q = QuadraticForm("Leech")  # may raise if catalog key differs
        L = Q.lattice()
        print("[info] Built Leech lattice from quadratic form catalog.")
        return L
    except Exception as e:
        print("[warn] Could not construct Leech lattice from catalog:", e)

    # Fallback: construct a generic even unimodular 24D lattice
    # NOTE: This is *not* guaranteed to be the actual Leech lattice; it is a
    # placeholder showing how the rest of the pipeline works.
    print("[warn] Falling back to a generic even unimodular 24D lattice (placeholder).")
    Q = QuadraticForm(24, lambda i, j: 2 if i == j else 0)
    L = Q.lattice()
    return L


# ---------------------------------------------------------------------------
# 2. Enumerate (or sample) minimal vectors
# ---------------------------------------------------------------------------

def minimal_vectors(lattice, max_count=None):
    """Return a list of minimal vectors of `lattice`.

    Parameters
    ----------
    lattice : Lattice
        A positive-definite lattice object.
    max_count : int or None
        If not None, stop after collecting this many minimal vectors.
    """
    try:
        mv = lattice.shortest_vectors()  # often available
        if max_count is not None and len(mv) > max_count:
            mv = mv[:max_count]
        print(f"[info] Found {len(mv)} candidate minimal vectors.")
        return mv
    except Exception as e:
        print("[warn] lattice.shortest_vectors() not available:", e)

    # Fallback: brute-force search up to a given norm bound (expensive)
    # This is included as an explicit placeholder; tune bounds carefully
    # before using in practice.
    B = 4   # squared norm bound placeholder; adjust for Leech if needed
    mv = []
    min_norm = None
    for v in lattice:  # beware: infinite, so in practice restrict search
        n = v.norm()    # squared length
        if min_norm is None or n < min_norm:
            min_norm = n
            mv = [v]
        elif n == min_norm:
            mv.append(v)
        if max_count is not None and len(mv) >= max_count:
            break
    print(f"[info] Brute-force search: min norm = {min_norm}, count = {len(mv)}.")
    return mv


# ---------------------------------------------------------------------------
# 3. Define a 4D physical subspace H via projection Π : R^24 → R^4
# ---------------------------------------------------------------------------

def random_4d_projection(dim=24, seed=0):
    """Return a random 4×dim real matrix Π with orthonormal rows.

    This defines a 4D subspace H = im(Π^T) ⊂ R^dim and a projection Π.
    """
    set_random_seed(seed)
    M = random_matrix(RDF, 4, dim)
    # Orthonormalize rows (Gram–Schmidt) to get an isometry on row space.
    Q, _ = M.QR()
    # Q is 4×dim with orthonormal rows
    return Q


def project_vector(v, P):
    """Project a lattice vector v ∈ R^24 to R^4 via Π = P.

    Parameters
    ----------
    v : lattice vector (e.g. sage.modules.free_module_element.FreeModuleElement)
    P : 4×24 matrix (RDF or RR)

    Returns
    -------
    4D vector over RDF.
    """
    vec = vector(RDF, list(v))
    return P * vec


# ---------------------------------------------------------------------------
# 4. Compute projected-norm statistics Z_Λ(H)
# ---------------------------------------------------------------------------

def projected_norm_statistics(min_vecs, P):
    """Compute basic statistics over projected minimal vectors.

    Z_eff ≈ (1/|M|) Σ_{m∈M} ||Π m||^2

    Returns
    -------
    dict with keys: 'count', 'avg_norm2', 'min_norm2', 'max_norm2'.
    """
    norms2 = []
    for m in min_vecs:
        p = project_vector(m, P)
        norms2.append(p.norm()**2)
    if not norms2:
        return {"count": 0, "avg_norm2": None, "min_norm2": None, "max_norm2": None}
    norms2 = vector(RR, norms2)
    return {
        "count": len(norms2),
        "avg_norm2": float(norms2.mean()),
        "min_norm2": float(min(norms2)),
        "max_norm2": float(max(norms2)),
    }


# ---------------------------------------------------------------------------
# 5. Top-level driver (for quick experimentation)
# ---------------------------------------------------------------------------

def main(max_minimal_vectors=1000, seed=0):
    print("[step] Building Leech (or placeholder) lattice …")
    L = build_leech_lattice()

    print("[step] Enumerating minimal vectors (possibly truncated) …")
    mv = minimal_vectors(L, max_count=max_minimal_vectors)

    print("[step] Constructing random 4D projection Π …")
    P = random_4d_projection(dim=L.dimension(), seed=seed)

    print("[step] Computing projected-norm statistics …")
    stats = projected_norm_statistics(mv, P)
    print("[result] minimal vectors used:", stats["count"])
    print("[result] avg ||Π m||^2:", stats["avg_norm2"])
    print("[result] min ||Π m||^2:", stats["min_norm2"])
    print("[result] max ||Π m||^2:", stats["max_norm2"])


if __name__ == "__main__":
    # Example: tune max_minimal_vectors downward initially to keep runtime
    # small while debugging. Once the Leech constructor is stable, we can
    # push this up to the full set of 196560 minimal vectors.
    main(max_minimal_vectors=1000, seed=0)

