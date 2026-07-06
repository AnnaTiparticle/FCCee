#!/usr/bin/env python3
"""
Generate a CLD_o2_v07_ARC2 geometry variant where the Plexiglass insert only
partially fills the (fixed, 200mm) TrackerECalGap envelope, sized according
to a requested fraction of a radiation length (X0).

ARC2 is its own independent geometry base (a copy of the corrected ARC1
structure, sitting alongside baseline/ARC1 in geometry/) -- all X0 variants
generated here derive from CLD_o2_v07_ARC2, not from ARC1. ARC2 itself was
copied from ARC1 AFTER the ECal silicon slices were fixed to match the
true k4geo reference (0.50mm single sensitive layer, not the earlier
12um/38um MAPS split) -- so every variant produced by this script correctly
isolates the Plexiglass-fill effect, with nothing else differing from
reference except the TrackerECalGap fill fraction.

X0(Plexiglass) = 340.75 mm  (measured directly from this DD4hep build's
material table on 2026-07-02 via material.radLength() on G4_PLEXIGLASS;
NOT taken from an external literature lookup, since it needs to match
this exact material definition).

The outer 200mm envelope (TrackerECalGap_inner_radius -> outer_radius) is
left completely unchanged -- only the *filled* radial extent of the
Plexiglass section changes. Anything between the fill radius and the
envelope's outer radius is left unfilled (vacuum/air, whatever the parent
volume defaults to), NOT additional Plexiglass.

Usage:
    python3 generate_arc_x0_variant.py 0.05
    python3 generate_arc_x0_variant.py 0.15
    python3 generate_arc_x0_variant.py 0.30
    python3 generate_arc_x0_variant.py 0.45
    python3 generate_arc_x0_variant.py 0.587   # ~ max that fits in 200mm

Creates:
    geometry/CLD_o2_v07_ARC2_X0_<fraction>/   (copy of CLD_o2_v07_ARC2 with
                                                the TrackerECalGap section
                                                rewritten for this fill)

Run from Camp2/ (so relative "geometry/" path resolves correctly), or set
CAMP2_DIR and this will use that instead.
"""
import os
import re
import shutil
import sys

SOURCE_GEOM = "CLD_o2_v07_ARC2"
X0_PLEXIGLASS_MM = 340.75
GAP_ENVELOPE_MM = 200.0
MAX_FRACTION = GAP_ENVELOPE_MM / X0_PLEXIGLASS_MM  # ~0.587


def main(fraction_arg):
    try:
        x0_fraction = float(fraction_arg)
    except ValueError:
        print(f"ERROR: '{fraction_arg}' is not a valid number.")
        sys.exit(1)

    if x0_fraction <= 0 or x0_fraction > MAX_FRACTION:
        print(f"ERROR: fraction must be in (0, {MAX_FRACTION:.4f}] "
              f"given the fixed {GAP_ENVELOPE_MM}mm envelope.")
        sys.exit(1)

    fill_mm = x0_fraction * X0_PLEXIGLASS_MM
    label = f"{x0_fraction:g}"

    camp2_dir = os.environ.get("CAMP2_DIR", os.getcwd())
    src = os.path.join(camp2_dir, "geometry", SOURCE_GEOM)
    dst_name = f"CLD_o2_v07_ARC2_X0_{label}"
    dst = os.path.join(camp2_dir, "geometry", dst_name)

    if not os.path.isdir(src):
        print(f"ERROR: source geometry not found at {src}")
        print(f"Did you run: cp -r geometry/CLD_o2_v07_ARC1 geometry/{SOURCE_GEOM} ?")
        sys.exit(1)

    if os.path.isdir(dst):
        print(f"ERROR: {dst} already exists. Remove it first if you want to regenerate.")
        sys.exit(1)

    shutil.copytree(src, dst)

    gap_file = os.path.join(dst, "TrackerECalGap_o1_v01.xml")
    if not os.path.isfile(gap_file):
        print(f"ERROR: expected {gap_file} not found in copied geometry.")
        sys.exit(1)

    with open(gap_file) as f:
        content = f.read()

    section_pattern = re.compile(
        r'(<section\s+start="0\*mm"\s+end="TrackerECalGap_half_length"\s+'
        r'rMin="TrackerECalGap_inner_radius"\s+rMax=")TrackerECalGap_outer_radius(")',
    )
    new_content, n = section_pattern.subn(
        rf'\g<1>TrackerECalGap_inner_radius + {fill_mm:.4f}*mm\g<2>',
        content,
    )
    if n == 0:
        print("ERROR: could not find the expected <section> line to rewrite.")
        print("File contents were:")
        print(content)
        sys.exit(1)

    comment = (
        f"\n    <comment>AUTO-GENERATED variant: Plexiglass fill = {x0_fraction} X0 "
        f"({fill_mm:.2f}mm of {X0_PLEXIGLASS_MM}mm X0), inside the unchanged "
        f"{GAP_ENVELOPE_MM}mm TrackerECalGap envelope. Remainder of envelope is "
        f"unfilled (vacuum/air). Derived from {SOURCE_GEOM}, which matches the "
        f"true k4geo reference ECal (0.50mm Si) plus the 200mm gap insert.</comment>\n"
    )
    new_content = new_content.replace("<lccdd>", "<lccdd>" + comment, 1)

    with open(gap_file, "w") as f:
        f.write(new_content)

    print(f"Created {dst}")
    print(f"  Plexiglass fill: {fill_mm:.2f}mm ({x0_fraction} X0)")
    print(f"  Unfilled remainder of 200mm envelope: {GAP_ENVELOPE_MM - fill_mm:.2f}mm")
    print(f"  Geometry folder name for steering file: {dst_name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 generate_arc_x0_variant.py <x0_fraction>")
        print(f"  (max feasible fraction with 200mm envelope: {MAX_FRACTION:.4f})")
        sys.exit(1)
    main(sys.argv[1])
