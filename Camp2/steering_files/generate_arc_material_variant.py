#!/usr/bin/env python3
"""
Generate a CLD_o2_v07_ARCmat_<material> geometry variant where the
TrackerECalGap (fixed 200mm envelope) is filled completely with a
specified material instead of Plexiglass.
"""
import os
import shutil
import sys

SOURCE_GEOM = "CLD_o2_v07_ARC1"
VALID_MATERIALS = {"Aluminum", "Iron", "Copper", "Lead", "Tungsten"}


def main(material):
    if material not in VALID_MATERIALS:
        print(f"ERROR: '{material}' not in expected set {sorted(VALID_MATERIALS)}")
        sys.exit(1)

    camp2_dir = os.environ.get("CAMP2_DIR", os.getcwd())
    src = os.path.join(camp2_dir, "geometry", SOURCE_GEOM)
    dst_name = f"CLD_o2_v07_ARCmat_{material}"
    dst = os.path.join(camp2_dir, "geometry", dst_name)

    if not os.path.isdir(src):
        print(f"ERROR: source geometry not found at {src}")
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

    old_str = 'material="Plexiglass"'
    new_str = f'material="{material}"'
    if old_str not in content:
        print(f"ERROR: could not find {old_str!r} in {gap_file}")
        sys.exit(1)
    new_content = content.replace(old_str, new_str)

    comment = (
        f"\n    <comment>AUTO-GENERATED variant: full 200mm TrackerECalGap "
        f"envelope filled with {material} (was Plexiglass in ARC1). "
        f"Derived from {SOURCE_GEOM}.</comment>\n"
    )
    new_content = new_content.replace("<lccdd>", "<lccdd>" + comment, 1)

    with open(gap_file, "w") as f:
        f.write(new_content)

    print(f"Created {dst}")
    print(f"  Fill material: {material} (full 200mm envelope)")
    print(f"  Geometry folder name for steering file: {dst_name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 generate_arc_material_variant.py <MaterialName>")
        print(f"  Valid materials: {sorted(VALID_MATERIALS)}")
        sys.exit(1)
    main(sys.argv[1])
