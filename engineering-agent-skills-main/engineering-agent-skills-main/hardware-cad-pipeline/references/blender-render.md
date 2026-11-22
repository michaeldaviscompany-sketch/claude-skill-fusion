# Blender headless — materials, lighting, animation, web frame sequences

Blender is the render stage: engineering parts come in as GLB, cosmetic/soft geometry is built here, and everything a customer sees comes out. Run it headless so renders are reproducible scripts, not GUI sessions.

## Contents
- [Headless invocation](#headless-invocation)
- [Blender 5: the slotted-action API change](#blender-5-the-slotted-action-api-change)
- [Importing engineering parts (the glTF trap)](#importing-engineering-parts-the-gltf-trap)
- [Materials by node-name role](#materials-by-node-name-role)
- [Studio lighting rigs](#studio-lighting-rigs)
- [Keyframed lighting across a rotation](#keyframed-lighting-across-a-rotation)
- [EEVEE vs Cycles](#eevee-vs-cycles)
- [WebP frame sequences for scroll sites](#webp-frame-sequences-for-scroll-sites)
- [Trap catalogue](#trap-catalogue)

## Headless invocation

```bash
brew install --cask blender     # notarized cask — Blender 5.x
blender -b -P render_scene.py                    # -b = background, no GUI
blender -b -P render_scene.py -- --route A       # args after -- reach your
                                                 # script via sys.argv
```

The script builds (or opens) the scene and calls `bpy.ops.render.render(write_still=True)` or steps frames itself. Keep the whole scene construction in the script — a `.blend` file with hand-edits is the render-stage equivalent of "fixing the STEP in a GUI": unreproducible.

## Blender 5: the slotted-action API change

Blender 5 rewrote the animation data model to **slotted actions**: an `Action` now contains *slots*, and f-curves hang off a slot's channelbag rather than directly off `action.fcurves`. **Animation code written for Blender 3/4 breaks** — the old direct-fcurve paths either error or silently animate nothing.

Two ways to cope:

1. **Prefer high-level keyframing** — `obj.keyframe_insert(data_path="rotation_euler", frame=n)` and `light.data.keyframe_insert(data_path="energy", frame=n)` still work and route through slots for you. Most render scripts never need to touch f-curves directly.
2. If you must edit curves (easing, cyclic modifiers), go through the slot:

```python
act = obj.animation_data.action
slot = obj.animation_data.action_slot            # the slot this object uses
channelbag = act.layers[0].strips[0].channelbag(slot)
for fc in channelbag.fcurves:                    # NOT act.fcurves
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
```

When you hit an `AttributeError` in animation code that "used to work", check the Blender version before debugging your logic.

## Importing engineering parts (the glTF trap)

glTF's convention is **Y-up, metres**. A pipeline exporting via trimesh may write raw **Z-up, millimetre** coordinates instead; Blender's importer then lays the model on its side at 1000× scale — a 200 mm part becomes a 200 m building lying down.

Handle it explicitly, once, in the import helper — never by eyeballed rotations per object:

```python
import bpy, math
from mathutils import Matrix

FIX = Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Scale(0.001, 4)
# maps raw Z-up mm  ->  Blender Z-up metres, assuming the importer already
# applied its own -90° X (Y-up -> Z-up) to data that was never Y-up.
# VERIFY on the first part: check dimensions read ~0.2 m, not 200 m,
# and "up" is up, then reuse the same FIX everywhere.

def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in set(bpy.data.objects) - before]
    for o in new:
        if o.parent is None:
            o.matrix_world = FIX @ o.matrix_world
    return new
```

The exact fix matrix depends on what your exporter wrote — the non-negotiable part is: **measure one imported part against a known dimension, document the fix in the script, and apply it uniformly.** (Better: fix the exporter to write Y-up metres; see `assemblies-and-exports.md`.)

## Materials by node-name role

Key material assignment off **node-name prefixes**, with an explicit role→material map. This is the contract with the export stage (which preserved node names in the GLB precisely for this) and it is what makes colorways swap cleanly across a whole assembly:

```python
ROLE_MATERIALS = {                     # role prefix -> material name
    "pod_":        "shell_primary",
    "faceplate_":  "accent",
    "hose_":       "hose_rubber",
    "mask_":       "shell_primary",
    "face_seal":   "silicone_soft",
    "strap":       "fabric_webbing",
}

COLORWAYS = {
    "stealth": {"shell_primary": (0.05, 0.05, 0.06), "accent": (0.10, 0.10, 0.12)},
    "sport":   {"shell_primary": (0.90, 0.91, 0.93), "accent": (0.85, 0.20, 0.15)},
}

def assign(objects, colorway):
    mats = build_materials(COLORWAYS[colorway])      # your PBR setup
    for o in objects:
        for prefix, role in ROLE_MATERIALS.items():
            if o.name.startswith(prefix):
                o.data.materials.clear()
                o.data.materials.append(mats[role])
                break
        else:
            print(f"WARN: no material role for {o.name}")   # never silent
```

Why this beats per-object assignment: rendering three colorways of a 15-part assembly is a one-word change, a renamed part fails loudly instead of rendering in default grey, and the map itself documents the product's material story. Warn (or fail) on unmatched names — an unmatched name usually means the exporter dropped or renamed a node.

## Studio lighting rigs

A dependable product-shot rig, scripted:

```python
def area(name, loc, rot, size, energy, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, 'AREA')
    d.size, d.energy, d.color = size, energy, color
    o = bpy.data.objects.new(name, d)
    o.location, o.rotation_euler = loc, rot
    bpy.context.collection.objects.link(o)
    return o

key  = area("key",  (1.2, -1.0, 1.4), (0.9, 0, 0.6), 1.0, 400)
fill = area("fill", (-1.4, -0.8, 0.8), (1.2, 0, -0.8), 2.0, 120)  # soft, ~1/3 key
rim  = area("rim",  (0.2, 1.6, 1.2),  (-1.0, 0, 3.1), 0.6, 600)  # edge separation
```

Plus a large dark floor plane with a subtle roughness gradient, and either a neutral HDRI at low strength or a plain dark world. Rim light is what makes dark products read against dark backgrounds — if a stealth colorway vanishes, raise the rim, not the exposure.

## Keyframed lighting across a rotation

For the "lighting transforms as the product rotates" hero move, keyframe light energy/position against the turntable frame range — light state becomes a function of rotation angle:

```python
FRAMES = 192
pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert("rotation_euler", frame=1)
pivot.rotation_euler = (0, 0, math.tau)
pivot.keyframe_insert("rotation_euler", frame=FRAMES)

for f, energy in ((1, 600), (96, 60), (192, 600)):   # rim dips mid-rotation
    rim.data.energy = energy
    rim.data.keyframe_insert("energy", frame=f)
```

Set interpolation to LINEAR on the turntable curve (via the slotted-action path above) so the loop speed is constant, and make frame 1 and frame N+1 identical states so the web loop is seamless.

## EEVEE vs Cycles

- **EEVEE** (rasterizer): seconds per frame. Use for iteration, layout, and full draft sequences. Its screen-space effects can miss reflections/shadows from off-screen geometry.
- **Cycles** (path tracer): the finals, and specifically **anything where lighting quality is the content** — rim-light transitions, soft-shadow falloff, silicone subsurface. On Apple Silicon enable the Metal device (`bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'METAL'`), use the denoiser, and 128–256 samples is usually enough for product shots.

The workflow is EEVEE until the sequence is *choreographed*, then one Cycles pass overnight if needed. Don't Cycles-render a sequence you haven't EEVEE-previewed end to end — a wrong camera path costs 100× more to discover at 2 min/frame.

## WebP frame sequences for scroll sites

Scroll-scrubbed product animation on the web wants individual frames, not video (video seeking is imprecise and jank-prone). Render **zero-padded WebP frames plus a poster**:

```python
s = bpy.context.scene
s.render.image_settings.file_format = 'WEBP'
s.render.image_settings.quality = 85          # ~50-100 KB/frame at 1600 px
s.render.filepath = "//frames/pod_turntable_"  # -> pod_turntable_0001.webp ...
s.frame_start, s.frame_end = 1, 192
bpy.ops.render.render(animation=True)

s.frame_set(1)                                 # poster = the first frame,
s.render.filepath = "//frames/poster"          # shown before JS loads
bpy.ops.render.render(write_still=True)
```

Zero-padding matters because the frontend computes filenames from scroll position; a missing pad breaks frame 10+. Keep the count modest (96–192 frames for a full rotation) and let the site preload progressively.

## Trap catalogue

Symptoms first, because that's how you meet them:

- **Model lies on its side, absurdly large/small** → the glTF orientation/units trap (above). Fix at import, uniformly.
- **Duplicate bodies, geometry poking through the model** → **the append trap**: `bpy.ops.wm.append` pulls an object's *dependencies* — parents, armatures — in with it. Appending two eye meshes from a character file dragged in their parent bodies: three overlapping bodies, limbs poking through clothes. After any append, count objects, print the new names, and delete what you didn't ask for. Better: append with `set_fake=False`, then walk `obj.parent` chains and unparent (`keep_transform=True`) before deleting parents.
- **Render is black/empty but the scene looks fine in code** → check the **camera position relative to the floor plane** before touching materials or lights. A camera below the floor renders the underside of an opaque plane: black frames, zero errors. Print `camera.location` and the floor's Z first — this one has burned hours on materials that were never broken.
- **Flickering/striped surfaces** → coincident faces z-fighting. Two objects sharing a face plane (an imported part sitting exactly on the floor, a decal plane on a surface) must be offset by a hair (0.1–0.5 mm at product scale) or booleaned properly.
- **Animation code silently does nothing / AttributeError on `action.fcurves`** → Blender 5 slotted actions (above).
- **Parts render in default grey** → node names didn't survive the export; check the GLB with `trimesh.load(path).graph.nodes` and fix the exporter, don't hand-assign.
- **EEVEE final looks worse than the preview** → off-screen reflections/shadows missing; that's the rasterizer's nature, switch the shot to Cycles.

And the meta-trap: verify a *rendered frame*, not the script's exit code. One glance at frame 1 and the midpoint frame catches every trap above.
