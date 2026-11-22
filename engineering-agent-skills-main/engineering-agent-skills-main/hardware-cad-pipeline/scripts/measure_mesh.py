#!/usr/bin/env python3
"""
measure_mesh.py — measure a mesh (STL/GLB/OBJ/PLY...) the robust way.

Reports bounding box, watertightness, cross-sections at chosen Z heights, and an
angular radius profile (ray-cast from the part axis) that finds lugs, keyways,
tabs and bores far more reliably than eyeballing a section polyline.

Why ray-cast profiles instead of section polylines: a cross-section of a coarse
mesh gives you a sparse polyline whose vertices land wherever the tessellation
put them — measuring "the bore radius" off a handful of boundary vertices is
noisy. Casting many rays (default 720) from the axis and recording the first-hit
distance samples the *surface*, at uniform angular density, so plateaus in the
radius-vs-angle curve are real features.

Examples:
  measure_mesh.py part.stl
  measure_mesh.py part.stl --sections 0.5,2,5,8
  measure_mesh.py part.stl --profile 2.0 --rays 1440
  measure_mesh.py part.stl --profile 2.0 --json > profile.json

Requires: pip install trimesh numpy scipy shapely rtree
"""

import argparse
import json
import sys

try:
    import numpy as np
    import trimesh
except ImportError as e:
    sys.exit(
        f"Missing dependency: {e.name}.\n"
        "Install with:  pip install trimesh numpy scipy shapely rtree\n"
        "(Use a venv if your system pip is externally-managed:\n"
        "  python3 -m venv .venv && .venv/bin/pip install trimesh numpy scipy shapely rtree)"
    )


def load_mesh(path):
    m = trimesh.load(path, force="mesh")
    if m.is_empty:
        sys.exit(f"Loaded {path} but it contains no geometry.")
    m.process(validate=True)
    m.merge_vertices()
    return m


def report_basics(m, out):
    lo, hi = m.bounds
    ext = m.extents
    out["bounds_min"] = [round(float(v), 3) for v in lo]
    out["bounds_max"] = [round(float(v), 3) for v in hi]
    out["extents"] = [round(float(v), 3) for v in ext]
    out["watertight"] = bool(m.is_watertight)
    out["winding_consistent"] = bool(m.is_winding_consistent)
    out["triangles"] = int(len(m.faces))
    out["bodies"] = int(m.body_count)
    if m.is_watertight:
        out["volume_mm3"] = round(float(m.volume), 2)


def section_stats(m, z, axis_xy=None):
    """Cross-section at height z: per-loop centroid, area, min/max radius."""
    sec = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        return {"z": z, "loops": [], "note": "no intersection at this height"}
    planar, to3d = sec.to_2D()
    loops = []
    for poly in planar.polygons_full:
        cx, cy = (axis_xy if axis_xy is not None else poly.centroid.coords[0])
        pts = np.array(poly.exterior.coords)
        r = np.hypot(pts[:, 0] - cx, pts[:, 1] - cy)
        loop = {
            "area_mm2": round(poly.area, 2),
            "centroid": [round(poly.centroid.x, 3), round(poly.centroid.y, 3)],
            "r_min": round(float(r.min()), 3),
            "r_max": round(float(r.max()), 3),
        }
        # interior rings = holes (bores)
        for ring in poly.interiors:
            hp = np.array(ring.coords)
            hr = np.hypot(hp[:, 0] - cx, hp[:, 1] - cy)
            loop.setdefault("holes", []).append(
                {"r_min": round(float(hr.min()), 3),
                 "r_max": round(float(hr.max()), 3)})
        loops.append(loop)
    return {"z": z, "loops": loops}


def angular_profile(m, z, n_rays, axis_xy):
    """Ray-cast radius-vs-angle at height z, from the axis outward.

    Returns per-angle first-hit radii and detected 'feature runs' — contiguous
    angular spans whose radius departs from the dominant level. Inner runs
    (radius well below the median) are tabs / lugs / ribs; outer runs (radius
    well above the median) are keyways / slots opening through the wall.
    """
    cx, cy = axis_xy
    ang = np.linspace(0, 2 * np.pi, n_rays, endpoint=False)
    origins = np.column_stack([np.full(n_rays, cx), np.full(n_rays, cy),
                               np.full(n_rays, z)])
    dirs = np.column_stack([np.cos(ang), np.sin(ang), np.zeros(n_rays)])
    radii = np.full(n_rays, np.nan)
    locs, idx_ray, _ = m.ray.intersects_location(origins, dirs,
                                                 multiple_hits=False)
    if len(idx_ray):
        d = np.hypot(locs[:, 0] - cx, locs[:, 1] - cy)
        radii[idx_ray] = d

    valid = radii[~np.isnan(radii)]
    if valid.size == 0:
        return {"z": z, "note": "no ray hits at this height (empty section?)"}

    # Dominant level = the bore/channel wall (the median radius). Features
    # are contiguous spans clearly inside it (tabs/lugs/ribs) or clearly
    # outside it (keyways/slots). Thresholds sit halfway to the extremes.
    r_med = float(np.median(valid))
    r_min = float(valid.min())
    r_max = float(valid.max())
    deg = np.degrees(ang)
    n = n_rays

    def find_runs(mask):
        if mask.all():
            return []  # the whole circle is one level, not a feature
        # Start scanning at a gap so a run straddling 0/360 is one run,
        # not two fragments.
        start = int(np.argmin(mask))
        ext = np.concatenate([mask, mask])
        runs, i = [], start
        while i < start + n:
            if ext[i]:
                j = i
                while ext[j]:
                    j += 1
                seg = radii[np.arange(i, j) % n]
                runs.append({
                    "start_deg": round(deg[i % n], 1),
                    "end_deg": round(deg[(j - 1) % n], 1),
                    "width_deg": round((j - i) * 360.0 / n, 1),
                    "center_deg": round(
                        (deg[i % n] + (j - i - 1) * 180.0 / n) % 360.0, 1),
                    "r_mean": round(float(np.nanmean(seg)), 3),
                })
                i = j
            else:
                i += 1
        runs.sort(key=lambda r: r["start_deg"])
        return runs

    out = {
        "z": z,
        "rays": n_rays,
        "hit_fraction": round(float(valid.size) / n_rays, 3),
        "r_min": round(r_min, 3),
        "r_median": round(r_med, 3),
        "r_max": round(r_max, 3),
        "inner_feature_runs": [],
        "outer_feature_runs": [],
    }
    if r_med - r_min > 0.2:
        t = r_min + 0.5 * (r_med - r_min)
        out["inner_threshold_r"] = round(t, 3)
        out["inner_feature_runs"] = find_runs(radii < t)  # NaN compares False
    if r_max - r_med > 0.2:
        t = r_med + 0.5 * (r_max - r_med)
        out["outer_threshold_r"] = round(t, 3)
        out["outer_feature_runs"] = find_runs(radii > t)
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Radii are measured about --axis-center (default: bbox center in "
               "XY). Heights are absolute Z in the mesh's own frame.")
    ap.add_argument("mesh", help="mesh file (STL/GLB/OBJ/PLY/...)")
    ap.add_argument("--sections", default="",
                    help="comma-separated Z heights for cross-section stats, "
                         "e.g. 0.5,2,5,8")
    ap.add_argument("--profile", default="",
                    help="comma-separated Z heights for ray-cast angular "
                         "radius profiles (feature finder)")
    ap.add_argument("--rays", type=int, default=720,
                    help="rays per angular profile (default 720 = 0.5°)")
    ap.add_argument("--axis-center", default="",
                    help="XY of the part axis as 'x,y' (default: bbox center)")
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable JSON instead of text")
    args = ap.parse_args()

    m = load_mesh(args.mesh)
    out = {"file": args.mesh}
    report_basics(m, out)

    if args.axis_center:
        axis_xy = tuple(float(v) for v in args.axis_center.split(","))
    else:
        lo, hi = m.bounds
        axis_xy = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)
    out["axis_center_xy"] = [round(float(axis_xy[0]), 3), round(float(axis_xy[1]), 3)]

    if args.sections:
        out["sections"] = [section_stats(m, float(z), axis_xy)
                           for z in args.sections.split(",")]
    if args.profile:
        out["profiles"] = [angular_profile(m, float(z), args.rays, axis_xy)
                           for z in args.profile.split(",")]

    if args.json:
        print(json.dumps(out, indent=2))
        return

    print(f"file            {out['file']}")
    print(f"extents (mm)    {out['extents'][0]} x {out['extents'][1]} x "
          f"{out['extents'][2]}")
    print(f"bounds          {out['bounds_min']} -> {out['bounds_max']}")
    print(f"watertight      {out['watertight']}   "
          f"winding-consistent {out['winding_consistent']}")
    print(f"triangles       {out['triangles']}   bodies {out['bodies']}")
    if "volume_mm3" in out:
        print(f"volume          {out['volume_mm3']} mm^3")
    print(f"axis center XY  {out['axis_center_xy']}")
    for s in out.get("sections", []):
        print(f"\nsection @ z={s['z']}")
        if not s.get("loops"):
            print(f"  {s.get('note', 'no loops')}")
        for lp in s.get("loops", []):
            print(f"  loop area {lp['area_mm2']} mm^2  centroid {lp['centroid']}"
                  f"  r {lp['r_min']}..{lp['r_max']}")
            for h in lp.get("holes", []):
                print(f"    hole  r {h['r_min']}..{h['r_max']}"
                      f"  (~Ø{2 * h['r_min']:.2f} if circular)")
    for p in out.get("profiles", []):
        print(f"\nangular profile @ z={p['z']}")
        if "note" in p:
            print(f"  {p['note']}")
            continue
        print(f"  hits {p['hit_fraction'] * 100:.0f}%  "
              f"r min/median/max = {p['r_min']} / {p['r_median']} / {p['r_max']}"
              f"  (Ø {2 * p['r_min']:.2f} / {2 * p['r_median']:.2f} / "
              f"{2 * p['r_max']:.2f})")
        for label, key, tkey in (
                ("inner features (tabs/lugs/ribs)", "inner_feature_runs",
                 "inner_threshold_r"),
                ("outer features (keyways/slots)", "outer_feature_runs",
                 "outer_threshold_r")):
            runs = p[key]
            if not runs:
                continue
            sym = "<" if key.startswith("inner") else ">"
            print(f"  {label}, r {sym} {p[tkey]}: {len(runs)} run(s)")
            for r in runs:
                print(f"    {r['start_deg']:>6}° -> {r['end_deg']:>6}°  "
                      f"width {r['width_deg']:>5}°  center {r['center_deg']:>6}°"
                      f"  r_mean {r['r_mean']}")
        if not p["inner_feature_runs"] and not p["outer_feature_runs"]:
            print("  no angular features at this height (clean bore)")


if __name__ == "__main__":
    main()
