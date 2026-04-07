"""
pi0_interactive.py  —  interactive 3D scatter of raw hit positions.

Opens in any browser — rotate, zoom, pan freely.
Each dot = one fired cell.

Run: python pi0_interactive.py
Output: pi0_interactive.html
"""
import sys, os
_BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np

try:
    import uproot
except ImportError:
    sys.exit("uproot not found")

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    sys.exit("plotly not found — run: pip install plotly")

# ── config ─────────────────────────────────────────────────────────────────────
PI0_DIR   = os.path.join(_BASE, "Output", "pi0scan")
ENERGIES  = [20, 50, 100, 200]
CONFIG    = "100um"
MODE      = "digital"
THRESHOLD = 1e-6    # GeV = 1 keV
EVT       = 0       # which event to show (change if event 0 looks merged)

# ── load one event ─────────────────────────────────────────────────────────────
ECAL_RMIN = 2150.0   # mm, ECAL barrel inner radius
ECAL_RMAX = 2352.0   # mm, ECAL barrel outer radius

def load_event(fname, mode, evt=0):
    f    = uproot.open(fname)
    tree = f["events"]
    x = np.asarray(tree["ECalBarrelCollection.position.x"].array()[evt], dtype=float)
    y = np.asarray(tree["ECalBarrelCollection.position.y"].array()[evt], dtype=float)
    z = np.asarray(tree["ECalBarrelCollection.position.z"].array()[evt], dtype=float)
    e = np.asarray(tree["ECalBarrelCollection.energy"].array()[evt],     dtype=float)
    if mode == "digital":
        mask = e > THRESHOLD
        x, y, z = x[mask], y[mask], z[mask]
    # keep only hits near +x (shower direction) and inside ECAL barrel
    R = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y, x)
    mask = (R > ECAL_RMIN - 10) & (R < ECAL_RMAX + 10) & (np.abs(phi) < 0.15)
    return x[mask], y[mask], z[mask]

# ── build subplot grid (2x2) ───────────────────────────────────────────────────
fig = make_subplots(
    rows=2, cols=2,
    specs=[[{"type": "scatter3d"}, {"type": "scatter3d"}],
           [{"type": "scatter3d"}, {"type": "scatter3d"}]],
    subplot_titles=[f"E_π⁰ = {E} GeV  →  two {E//2} GeV γ's" for E in ENERGIES],
)

positions = [(1,1), (1,2), (2,1), (2,2)]

for (row, col), E in zip(positions, ENERGIES):
    fname = os.path.join(PI0_DIR, f"pi0_{E}GeV_{CONFIG}_SIM.edm4hep.root")
    if not os.path.exists(fname):
        print(f"  missing: {fname}");  continue

    x, y, z = load_event(fname, MODE, evt=EVT)
    print(f"  E={E:3d} GeV  nhits={len(x)}")

    fig.add_trace(
        go.Scatter3d(
            x=y, y=z, z=x,
            mode="markers",
            marker=dict(size=1.5, color="#1565C0", opacity=0.6),
            name=f"{E} GeV",
            showlegend=False,
        ),
        row=row, col=col,
    )

    # axis labels and fixed ranges per subplot
    scene_key = "scene" if (row == 1 and col == 1) else f"scene{(row-1)*2 + col}"
    fig.update_layout(**{scene_key: dict(
        xaxis=dict(title="y (mm)",        range=[-100, 100]),
        yaxis=dict(title="z (mm)",        range=[-100, 100]),
        zaxis=dict(title="depth x (mm)",  range=[ECAL_RMIN, ECAL_RMAX]),
        camera=dict(eye=dict(x=1.5, y=1.5, z=1.0)),
    )})

fig.update_layout(
    title=dict(text=f"π⁰ → γγ  raw hit positions — {CONFIG}  (event {EVT})",
               font=dict(size=16)),
    height=900,
    margin=dict(l=0, r=0, t=60, b=0),
)

out = "pi0_interactive_100um.html"
fig.write_html(out)
print(f"\nSaved {out}  —  open in any browser")
