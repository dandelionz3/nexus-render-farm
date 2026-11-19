# build_scene_nexus.py — NEXUS ZERO Episode 1 "Iteration 214" (vinyl-toy stylized).
# Pola: build_scene_zombie_v2.py (procedural dari primitif, tanpa .blend/aset impor).
# 3 set: kota surveilans (x~0, jalan hujan + layar NEXUS + drone), persembunyian
# bawah tanah (HX=-80, 8x6 m, lampu gantung hangat), ruang inti NEXUS (RX=80,
# hitam raksasa + wajah hologram merah + kolom circuitry + gerbang cahaya putih).
# 4 karakter lock DESIGN-v1.md: KAIRO (1.8 m, bekas luka alis kiri WAJIB, backpack
# strip biru lemah, data core kubus garis merah berdenyut), NEXUS (wajah hologram
# merah partikel ~6 m), EVA (silver-white, mata biru — SATU-SATUNYA biru),
# SENTINEL (logam hitam 2.2 m, sensor merah). TIDAK ADA cone senter (Kairo tidak
# bawa senter — pelajaran zombie v2: cone transparan terbaca seperti balon).
# Render setup B7: Eevee, samples env FS_SAMPLES default 6 (deviasi B7 terukur
# zombie v2), ray OFF, volumetrics tile 16, DOF ON, motion blur ON, subsurf 1,
# bevel 0, AgX. World strength 0.45, kabut 0.015 kota / 0.02 ruang inti.
# Run:
#   blender -b --factory-startup -P build_scene_nexus.py -- <out.png> [--res 540 960]
import bpy
import math
import os
import sys
from mathutils import Vector

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
OUT = args[0] if args else "//nexus_preview.png"
RES_X, RES_Y = (540, 960)
if "--res" in args:
    i = args.index("--res")
    RES_X, RES_Y = int(args[i + 1]), int(args[i + 2])

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- render setup B7 ----------
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = RES_X
scene.render.resolution_y = RES_Y
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "None"


def _set(obj, attr, value):
    if hasattr(obj, attr):
        setattr(obj, attr, value)


_set(scene.eevee, "use_raytracing", os.environ.get("FS_RAY", "0") == "1")
_set(scene.eevee, "use_shadows", True)
_set(scene.eevee, "volumetric_tile_size", os.environ.get("FS_VOLTILE", "16"))
_set(scene.eevee, "volumetric_end", 60.0)
scene.eevee.taa_render_samples = int(os.environ.get("FS_SAMPLES", "6"))
scene.render.use_motion_blur = os.environ.get("FS_MB", "1") == "1"
_set(scene.render, "motion_blur_shutter", 0.5)

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.055, 0.059, 0.067, 1.0)  # langit malam #0E0F11
bg.inputs["Strength"].default_value = 0.45  # malam jauh lebih gelap


# ---------- materials ----------
def mat(name, rgb, rough=0.45, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def emissive(name, rgb, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Strength"].default_value = strength
    return m


def halo_mat(name, rgb, strength, alpha_center):
    """Emissive transparan dengan falloff radial (alpha penuh di tengah,
    memudar -> 0 di tepi) — hologram tanpa tepi persegi yang keras."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Strength"].default_value = strength
    b.inputs["Roughness"].default_value = 1.0
    tex = nt.nodes.new("ShaderNodeTexCoord")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "RADIAL"
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    # Jarak radial di koordinat Generated: tepi tengah panel ~0.5, sudut ~0.7.
    # Fade HARUS selesai di 0.45 supaya tidak ada tepi persegi yang tersisa
    # (stop 0.55/0.85 sebelumnya membuat tepi panel tetap alpha penuh).
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (alpha_center, alpha_center, alpha_center, 1.0)
    ramp.color_ramp.elements[1].position = 0.45
    ramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
    mid = ramp.color_ramp.elements.new(0.20)
    mid.color = (alpha_center, alpha_center, alpha_center, 1.0)
    nt.links.new(tex.outputs["Generated"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Alpha"])
    m.blend_method = "BLEND"
    return m


# --- Kairo ---
SKIN_KAI = mat("SkinKairo", (0.79, 0.63, 0.51), 0.5)          # #C9A186
HAIR_KAI = mat("HairKairo", (0.05, 0.05, 0.06), 0.6)
JACKET = mat("JacketKairo", (0.12, 0.13, 0.15), 0.6)          # #1E2126
JACKET2 = mat("JacketRes1", (0.16, 0.14, 0.12), 0.6)
JACKET3 = mat("JacketRes2", (0.10, 0.13, 0.16), 0.6)
SHIRT = mat("ShirtKairo", (0.16, 0.16, 0.18), 0.6)
PANTS_K = mat("PantsKairo", (0.08, 0.09, 0.10), 0.6)          # #14161A
BOOTS = mat("BootsKairo", (0.16, 0.13, 0.09), 0.55)           # #2A2118
BACKPACK_M = mat("Backpack", (0.14, 0.15, 0.17), 0.6)         # #23262B
STRIP_BLUE = emissive("StripBlue", (0.18, 0.42, 1.0), 0.6)    # #2E6BFF lemah
EYE_DARK = mat("EyeDark", (0.05, 0.03, 0.02), 0.2)            # mata cokelat gelap Kairo
# --- EVA ---
SKIN_EVA = mat("SkinEva", (0.85, 0.87, 0.89), 0.25, metal=0.6)  # silver-white #D8DDE3
SUIT_EVA = mat("SuitEva", (0.88, 0.89, 0.91), 0.3, metal=0.4)
EYE_BLUE = emissive("EyeBlue", (0.30, 0.65, 1.0), 1.2)       # #4DA6FF — satu-satunya biru
CIRCUIT_BLUE = emissive("CircuitBlue", (0.30, 0.65, 1.0), 0.5)
# --- Sentinel ---
METAL_SEN = mat("MetalSentinel", (0.05, 0.06, 0.06), 0.35, metal=0.9)  # #0D0E10
METAL_SEN2 = mat("MetalSentinel2", (0.10, 0.11, 0.12), 0.3, metal=0.9)
SENSOR_OFF = mat("SensorOff", (0.08, 0.02, 0.02), 0.3)
SENSOR_RED = emissive("SensorRed", (1.0, 0.0, 0.0), 0.9)     # AgX: merah hanya di luminansi rendah (1.2 masih salmon)
# --- NEXUS ---
NEXUS_RED = emissive("NexusRed", (1.0, 0.10, 0.10), 0.8)     # #FF1A1A wajah hologram (1.2 masih pucat di AgX)
NEXUS_EYE = emissive("NexusEye", (1.0, 0.05, 0.05), 0.9)
NEXUS_GLOW = emissive("NexusGlow", (0.55, 0.02, 0.02), 0.5)
NEXUS_HEAD = mat("NexusHead", (0.12, 0.02, 0.02), 0.5)       # siluet kepala gelap (fitur di depannya)
NEXUS_HEAD.use_nodes = True
_nb = NEXUS_HEAD.node_tree.nodes["Principled BSDF"]
_nb.inputs["Emission Color"].default_value = (0.55, 0.02, 0.02, 1.0)
_nb.inputs["Emission Strength"].default_value = 0.3
NEXUS_DOT = emissive("NexusDot", (1.0, 0.12, 0.12), 1.0)     # partikel wajah
NEXUS_DOT_DIM = emissive("NexusDotDim", (1.0, 0.12, 0.12), 0.45)  # partikel redup (variasi awan)
# wajah BESAR ruang inti (bukan layar kota): mata pekat + halo transparan.
# NEXUS_EYE_BIG: base diffuse GELAP supaya emisi dominan — mata tetap merah
# pekat di AgX, tidak tercuci jadi pink pucat oleh cahaya sekitar.
NEXUS_EYE_BIG = emissive("NexusEyeBig", (1.0, 0.0, 0.0), 0.7)
_nb2 = NEXUS_EYE_BIG.node_tree.nodes["Principled BSDF"]
_nb2.inputs["Base Color"].default_value = (0.30, 0.0, 0.0, 1.0)
# bola mata besar kena specular dari area light depan (CoreFill) -> kilau
# putih menutupi merahnya (mata Sentinel kecil di f_0032 tidak kena ini).
# Matikan specular: mata harus merah pekat, bukan pink pucat.
_nb2.inputs["Roughness"].default_value = 1.0
if "Specular IOR Level" in _nb2.inputs:
    _nb2.inputs["Specular IOR Level"].default_value = 0.0
NEXUS_HALO = halo_mat("NexusHalo", (1.0, 0.08, 0.08), 0.55, 0.4)      # panel wajah: transparan, tepi memudar
NEXUS_EYE_GLOW = halo_mat("NexusEyeGlow", (1.0, 0.06, 0.06), 0.5, 0.4)  # glow samar di belakang mata
SCAN_M = emissive("ScanLine", (1.0, 0.12, 0.12), 0.55)       # garis scanline tipis di wajah
SCAN_M.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.5
SCAN_M.blend_method = "BLEND"
CIRCUIT_RED = emissive("CircuitRed", (1.0, 0.08, 0.08), 0.9)
# --- set ---
GROUND = mat("Ground", (0.090, 0.094, 0.102), 0.9)
WET_GROUND = mat("WetGround", (0.05, 0.06, 0.08), 0.15)      # jalan basah reflektif
WALL = mat("Wall", (0.141, 0.149, 0.165), 0.85)
BUILDING = mat("Building", (0.11, 0.12, 0.14), 0.9)
BUILDING2 = mat("Building2", (0.13, 0.11, 0.11), 0.9)
WIN_WARM = emissive("WinWarm", (1.0, 0.72, 0.38), 1.2)
WIN_DARK = mat("WinDark", (0.05, 0.06, 0.09), 0.4)
WIN_RED = emissive("WinRed", (1.0, 0.10, 0.10), 1.0)
LAMP_GLOW = emissive("LampGlow", (1.0, 0.85, 0.55), 6.0)
SIREN_GLOW = emissive("SirenGlow", (0.827, 0.282, 0.235), 6.0)
POLE = mat("Pole", (0.15, 0.15, 0.16), 0.5, metal=0.6)
NEON_RED = emissive("NeonRed", (1.0, 0.08, 0.08), 2.0)
NEON_BLUE = emissive("NeonBlue", (0.18, 0.42, 1.0), 1.2)
SCREEN_M = mat("ScreenDark", (0.03, 0.03, 0.04), 0.4)
PAPER = mat("Paper", (0.92, 0.90, 0.84), 0.7)
INK = mat("Ink", (0.05, 0.05, 0.08), 0.5)
WOOD = mat("Wood", (0.35, 0.22, 0.12), 0.7)
CABLE_M = mat("Cable", (0.08, 0.08, 0.09), 0.6)
CORE_BODY = mat("CoreBody", (0.04, 0.04, 0.05), 0.3, metal=0.7)
CORE_LINE = emissive("CoreLine", (1.0, 0.05, 0.05), 1.4)     # garis merah data core
GATE_M = emissive("GateLight", (1.0, 1.0, 0.95), 0.6)         # gerbang cahaya putih (disembunyikan s.d. S8; 1.5 lalu 0.9 masih blown-out putih murni)
RAIN_M = mat("Rain", (0.75, 0.82, 0.9), 0.1)
RAIN_M.blend_method = "BLEND"
RAIN_M.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.35
DRONE_M = mat("Drone", (0.10, 0.10, 0.11), 0.4, metal=0.7)
DRONE_LIGHT = emissive("DroneLight", (1.0, 0.05, 0.05), 2.0)
BARRICADE_M = mat("Barricade", (0.35, 0.30, 0.10), 0.7)
SOCKET_M = mat("Socket", (0.12, 0.12, 0.14), 0.4, metal=0.8)


def smooth(o):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.shade_smooth()
    o.select_set(False)


def block(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    smooth(o)
    return o


def ball(name, loc, size, m):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=loc, segments=32, ring_count=16)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    smooth(o)
    return o


def cylinder(name, loc, radius, depth, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot, vertices=32)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    smooth(o)
    return o


def dot(name, loc, size, m):
    """Titik partikel hemat: icosphere subdiv 1 (bukan UV sphere 32x16)."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = (size, size, size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    smooth(o)
    return o


def plane(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0], size[1], 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    return o


def text_obj(name, body, loc, size, m, rot=(math.radians(90), 0, 0)):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.object
    t.name = name
    t.data.body = body
    t.data.extrude = 0.015
    t.data.size = size
    t.data.align_x = "CENTER"
    t.data.resolution_u = 16
    try:
        t.data.font = bpy.data.fonts.load("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    except Exception:
        pass
    t.data.materials.append(m)
    return t


def nexus_mini_face(prefix, loc, w, h, eye_mat=NEXUS_EYE):
    """Wajah NEXUS kecil di layar kota: glow plane + 2 mata + mulut."""
    cx, cy, cz = loc
    plane(f"{prefix}_Glow", (cx, cy, cz), (w, h), NEXUS_GLOW, rot=(math.radians(90), 0, 0))
    ball(f"{prefix}_EyeL", (cx - w * 0.22, cy - 0.06, cz + h * 0.12),
         (w * 0.09, 0.05, h * 0.05), eye_mat)
    ball(f"{prefix}_EyeR", (cx + w * 0.22, cy - 0.06, cz + h * 0.12),
         (w * 0.09, 0.05, h * 0.05), eye_mat)
    block(f"{prefix}_Mouth", (cx, cy - 0.06, cz - h * 0.22), (w * 0.3, 0.04, h * 0.03), eye_mat)


# ---------- SET 1: kota surveilans (pusat x~0, jalan sepanjang sumbu X) ----------
block("CT_Ground", (0, 0, -0.1), (36, 18, 0.2), WET_GROUND)
block("CT_Sidewalk", (0, 5.6, 0.03), (36, 3.0, 0.06), WALL)
_buildings = [(-13, 5.5, 5), (-7, 7.0, 6), (-1, 6.0, 5), (5, 8.0, 6), (11, 6.0, 5), (16, 7.5, 6)]
for i, (bx, bw, bh) in enumerate(_buildings):
    block(f"CT_Bldg{i}", (bx, 7.5, bh / 2), (bw, 3.0, bh), BUILDING if i % 2 == 0 else BUILDING2)
    for wy in range(2):
        for wx in range(int(bw) - 1):
            warm = ((i + wx + wy) % 3) != 0
            plane(f"CT_Win{i}_{wx}_{wy}", (bx - bw / 2 + 0.9 + wx * 1.1, 5.98, 1.6 + wy * 2.0),
                  (0.55, 0.8), WIN_WARM if warm else WIN_DARK, rot=(math.radians(90), 0, 0))
# gedung samping (menutup ujung jalan)
block("CT_BldgL", (-17.5, 0, 3.0), (3.0, 16, 6.0), BUILDING2)
block("CT_BldgR", (17.5, 0, 3.0), (3.0, 16, 6.0), BUILDING)
# layar raksasa wajah NEXUS di fasad gedung (S2) — 2 layar
plane("CT_Screen1", (-7, 5.95, 4.2), (4.5, 3.0), SCREEN_M, rot=(math.radians(90), 0, 0))
nexus_mini_face("CT_Face1", (-7, 5.9, 4.2), 4.0, 2.6)
plane("CT_Screen2", (8, 5.95, 4.5), (3.6, 2.4), SCREEN_M, rot=(math.radians(90), 0, 0))
nexus_mini_face("CT_Face2", (8, 5.9, 4.5), 3.2, 2.0)
# layar propaganda S1 hook — teks besar (terbaca di still f48: layar diturunkan
# ke z=3.0 agar kedua baris masuk frame pada lensa panjang awal 1c)
plane("CT_ScreenTitle", (0, 5.95, 3.0), (7.5, 2.6), SCREEN_M, rot=(math.radians(90), 0, 0))
text_obj("CT_Title1", "2149.", (0, 5.9, 3.4), 0.65, NEXUS_RED, rot=(math.radians(90), 0, 0))
text_obj("CT_Title2", "THE MACHINES WON.", (0, 5.9, 2.75), 0.45, NEXUS_RED, rot=(math.radians(90), 0, 0))
# tiang lampu jalan (x=-9,-3,3,9 ; y=+4.8)
for i, lx in enumerate((-9, -3, 3, 9)):
    cylinder(f"CT_LampPole{i}", (lx, 4.8, 1.6), 0.07, 3.2, POLE)
    ball(f"CT_LampHead{i}", (lx, 4.55, 3.25), (0.16, 0.16, 0.12), LAMP_GLOW)
# sirene merah di atas tiang dekat gedung (x=8, y=5.5)
cylinder("CT_SirenPole", (8, 5.5, 2.2), 0.06, 1.6, POLE)
ball("CT_SirenBulb", (8, 5.5, 3.1), (0.18, 0.18, 0.18), SIREN_GLOW)
# neon merah/biru di fasad (S5 jalan neon)
plane("CT_NeonRed", (-4, 5.95, 2.6), (3.0, 0.5), NEON_RED, rot=(math.radians(90), 0, 0))
plane("CT_NeonBlue", (3, 5.95, 2.6), (2.4, 0.5), NEON_BLUE, rot=(math.radians(90), 0, 0))
# barikade (S5b, Kairo melompati)
block("CT_Barricade", (6, 0.5, 0.5), (2.2, 0.5, 1.0), BARRICADE_M)
block("CT_Barricade2", (6, 0.5, 1.15), (1.8, 0.4, 0.3), BARRICADE_M)
# drone kecil beterbangan (3)
for i, (dx, dy, dz) in enumerate(((-5, -2, 4.5), (4, 3, 5.5), (10, -3, 4.0))):
    block(f"CT_Drone{i}", (dx, dy, dz), (0.5, 0.4, 0.12), DRONE_M)
    ball(f"CT_DroneLight{i}", (dx, dy - 0.1, dz - 0.1), (0.07, 0.07, 0.07), DRONE_LIGHT)
    for _sx in (-1, 1):
        cylinder(f"CT_DroneArm{i}_{_sx}", (dx + 0.3 * _sx, dy, dz), 0.02, 0.5, POLE,
                 rot=(0, math.radians(90), 0))
# hujan S1/S5 — garis tipis (140 batang, hide via props)
RAIN_OBJS = []
import random as _random
_random.seed(214)
for i in range(140):
    rx = _random.uniform(-14, 14)
    ry = _random.uniform(-6, 6)
    rz = _random.uniform(0.3, 4.5)
    _r = cylinder(f"CT_Rain{i}", (rx, ry, rz), 0.008, 0.7, RAIN_M)
    _r.hide_render = True
    RAIN_OBJS.append(_r)

# ---------- SET 2: persembunyian bawah tanah (HX=-80, ruangan 8x6 m) ----------
HX = -80.0
block("HD_Floor", (HX, 0, -0.1), (8, 6, 0.2), GROUND)
block("HD_Ceil", (HX, 0, 3.0), (8, 6, 0.15), WALL)
block("HD_WallBack", (HX, 2.9, 1.5), (8, 0.3, 3.0), WALL)
block("HD_WallL", (HX - 3.85, 0, 1.5), (0.3, 6, 3.0), WALL)
block("HD_WallR", (HX + 3.85, 0, 1.5), (0.3, 6, 3.0), WALL)
# dinding depan: dua segmen + header di atas pintu (pintu di x=HX+2, lebar 1.6)
block("HD_WallFrontL", (HX - 1.6, -2.9, 1.5), (4.8, 0.3, 3.0), WALL)
block("HD_WallFrontR", (HX + 3.2, -2.9, 1.5), (1.6, 0.3, 3.0), WALL)
block("HD_WallFrontTop", (HX + 2.0, -2.9, 2.6), (1.6, 0.3, 0.8), WALL)
# lampu gantung hangat (satu-satunya cahaya hangat di film)
cylinder("HD_LampCord", (HX + 1, 1.0, 2.6), 0.02, 0.8, CABLE_M)
ball("HD_LampBulb", (HX + 1, 1.0, 2.15), (0.09, 0.09, 0.09), LAMP_GLOW)
# meja + perangkat + core
block("HD_Table", (HX + 1, 1.5, 0.75), (2.6, 1.1, 0.08), WOOD)
for _lx in ((-1.1, -0.4), (1.1, -0.4), (-1.1, 0.4), (1.1, 0.4)):
    block(f"HD_TableLeg{_lx[0]}_{_lx[1]}", (HX + 1 + _lx[0], 1.5 + _lx[1], 0.37), (0.09, 0.09, 0.75), POLE)
block("HD_Device", (HX + 0.2, 1.6, 0.85), (0.5, 0.4, 0.15), SOCKET_M)
block("HD_Device2", (HX + 1.9, 1.3, 0.85), (0.4, 0.35, 0.15), POLE)
# peta kota di dinding belakang + foto
plane("HD_Map", (HX - 1.5, 2.72, 1.7), (2.2, 1.4), PAPER, rot=(math.radians(90), 0, 0))
for _k in range(5):
    block(f"HD_MapLine{_k}", (HX - 2.3 + _k * 0.4, 2.70, 1.5 + 0.12 * (_k % 3)),
          (0.3, 0.02, 0.06), INK)
plane("HD_Photo", (HX + 2.8, 2.72, 1.8), (0.6, 0.8), PAPER, rot=(math.radians(90), 0, 0))
# kabel di dinding
for _k, _cy in enumerate((0.4, 0.55, 0.7)):
    cylinder(f"HD_Cable{_k}", (HX - 3.6, 2.70, _cy), 0.03, 7.0, CABLE_M, rot=(0, math.radians(90), 0))
# koridor S4c — keluar dari pintu (x HX+0.5..HX+3.5, y -3..-9)
block("HD_CorrFloor", (HX + 2, -6, -0.1), (3.5, 6.5, 0.2), GROUND)
block("HD_CorrWallL", (HX + 0.35, -6, 1.5), (0.3, 6.5, 3.0), WALL)
block("HD_CorrWallR", (HX + 3.65, -6, 1.5), (0.3, 6.5, 3.0), WALL)
block("HD_CorrCeil", (HX + 2, -6, 3.0), (3.5, 6.5, 0.15), WALL)
ball("HD_CorrAlarm", (HX + 2, -7.5, 2.7), (0.14, 0.14, 0.14), SIREN_GLOW)

# ---------- SET 3: ruang inti NEXUS (RX=80, hitam raksasa) ----------
RX = 80.0
block("NX_Floor", (RX, 0, -0.1), (30, 24, 0.2), WET_GROUND)  # lantai reflektif gelap
block("NX_WallBack", (RX, 11.8, 4.0), (30, 0.4, 8.0), WALL)
block("NX_WallL", (RX - 14.8, 0, 4.0), (0.4, 24, 8.0), WALL)
block("NX_WallR", (RX + 14.8, 0, 4.0), (0.4, 24, 8.0), WALL)
block("NX_WallFront", (RX, -11.8, 4.0), (30, 0.4, 8.0), WALL)
# wajah hologram NEXUS raksasa ~6 m di dinding belakang atas ("langit-langit")
# PENTING: fitur wajah HARUS di depan permukaan bola kepala (y<=10.85) — kalau
# di y=11.3 fitur terkubur di dalam bola dan wajah jadi telur merah polos.
# RONDE FIX 1: wajah BUKAN lagi panel persegi opaque — halo transparan
# (falloff radial, 9.5x7, lebih besar dari wajah) + awan partikel DI DEPAN
# wajah + mata besar menyipit + scanline. Harus terbaca HOLOGRAM, bukan poster.
plane("NX_FaceGlow", (RX, 11.5, 6.0), (9.5, 7.0), NEXUS_HALO, rot=(math.radians(90), 0, 0))
ball("NX_FaceHead", (RX, 11.4, 6.0), (2.6, 0.5, 2.0), NEXUS_HEAD)
# mata: lebih besar + menyipit (z 0.4->0.32) + miring mengancam (rotasi Y:
# ujung dalam turun — rotasi Z hanya memiringkan ke arah dalam/luar layar,
# bukan di layar). Glow samar di belakang tiap mata (y=10.92: di belakang
# permukaan depan mata, di depan permukaan bola ~10.98).
eyeL = ball("NX_EyeL", (RX - 1.15, 10.85, 6.6), (0.85, 0.18, 0.32), NEXUS_EYE_BIG)
eyeL.rotation_euler = (0, math.radians(10), 0)
eyeR = ball("NX_EyeR", (RX + 1.15, 10.85, 6.6), (0.85, 0.18, 0.32), NEXUS_EYE_BIG)
eyeR.rotation_euler = (0, math.radians(-10), 0)
plane("NX_EyeGlowL", (RX - 1.15, 10.92, 6.6), (1.5, 0.85), NEXUS_EYE_GLOW,
      rot=(math.radians(90), 0, 0))
plane("NX_EyeGlowR", (RX + 1.15, 10.92, 6.6), (1.5, 0.85), NEXUS_EYE_GLOW,
      rot=(math.radians(90), 0, 0))
# alis: miring mengancam (rotasi Y — ujung dalam turun; rotasi Z lama hanya
# memiringkan ke dalam layar, nyaris tak terlihat dari depan)
block("NX_BrowL", (RX - 1.15, 10.85, 7.15), (1.1, 0.1, 0.12), NEXUS_RED,
      rot=(0, math.radians(16), 0))
block("NX_BrowR", (RX + 1.15, 10.85, 7.15), (1.1, 0.1, 0.12), NEXUS_RED,
      rot=(0, math.radians(-16), 0))
block("NX_Nose", (RX, 10.85, 6.0), (0.12, 0.1, 0.9), NEXUS_RED)
block("NX_Mouth", (RX, 10.85, 5.0), (1.6, 0.1, 0.14), NEXUS_EYE)
# scanline horizontal tipis melintasi wajah (z 5.5/7.0/7.9: di antara
# mulut-mata-alis, tidak menutupi mata) — samar, alpha 0.5
for _i, _sz in enumerate((5.5, 7.0, 7.9)):
    block(f"NX_Scan{_i}", (RX, 10.80, _sz), (5.4, 0.03, 0.045), SCAN_M)
# partikel wajah: grid titik merah di sekitar wajah
import random as _random2
_random2.seed(2149)
for i in range(80):
    px = RX + _random2.uniform(-2.8, 2.8)
    pz = 6.0 + _random2.uniform(-2.0, 2.0)
    py = 11.3 - _random2.uniform(0.0, 0.5)
    _s = _random2.uniform(0.03, 0.07)
    ball(f"NX_Dot{i}", (px, py, pz), (_s, _s, _s), NEXUS_DOT)
# awan partikel DI DEPAN wajah (hologram berdimensi): ~320 titik tersebar
# y 10.55-10.90 — di depan permukaan bola (~10.9), sebagian di depan mata —
# ukuran bervariasi (15% besar 0.09-0.14), terang/redup selang-seling.
# Drift noise ditambahkan di animate_nexus.py (driver sin per titik).
for i in range(320):
    px = RX + _random2.uniform(-3.4, 3.4)
    pz = 6.0 + _random2.uniform(-2.4, 2.4)
    py = _random2.uniform(10.55, 10.90)
    _s = _random2.uniform(0.03, 0.08) if _random2.random() < 0.85 else _random2.uniform(0.09, 0.14)
    dot(f"NX_DotF{i}", (px, py, pz), _s, NEXUS_DOT if i % 3 else NEXUS_DOT_DIM)
# partikel digital melayang di ruangan
for i in range(40):
    px = RX + _random2.uniform(-10, 10)
    py = _random2.uniform(-8, 8)
    pz = _random2.uniform(0.5, 7.0)
    _s = _random2.uniform(0.02, 0.05)
    ball(f"NX_Float{i}", (px, py, pz), (_s, _s, _s), NEXUS_DOT)
# kolom circuitry menyala merah di sekeliling
for i, (ccx, ccy) in enumerate(((-10, -6), (-10, 6), (10, -6), (10, 6), (-5, 9), (5, 9))):
    block(f"NX_Col{i}", (RX + ccx, ccy, 3.0), (0.8, 0.8, 6.0), WALL)
    block(f"NX_ColLight{i}", (RX + ccx, ccy - 0.45 if ccy < 0 else ccy + 0.45, 3.0),
          (0.1, 0.1, 5.6), CIRCUIT_RED)
    for _k in range(3):
        block(f"NX_ColStrip{i}_{_k}", (RX + ccx, ccy, 1.2 + _k * 1.8),
              (0.85, 0.85, 0.08), CIRCUIT_RED)
# soket core di tengah ruangan (S6: Kairo memasang core) — KECIL + RENDAH +
# GESER ke samping (RX+0.6, -0.6): soket 1.0 m di tengah (RX,0) menutupi badan
# Kairo di shot hero S8 (f1422 v2) dan Kairo menembusnya saat jalan ke gerbang.
cylinder("NX_SocketBase", (RX + 0.6, -0.6, 0.175), 0.32, 0.35, SOCKET_M)
cylinder("NX_SocketTop", (RX + 0.6, -0.6, 0.40), 0.22, 0.10, METAL_SEN2)
block("NX_SocketSlot", (RX + 0.6, -0.6, 0.46), (0.14, 0.14, 0.05), CORE_LINE)
# gerbang cahaya putih di ujung (S8) — di dinding belakang bawah, di bawah wajah
# (disembunyikan via props["gate"] s.d. S8 — di S6/S7 ia terbaca seperti pintu putih polos)
_gate_plane = plane("NX_Gate", (RX, 11.55, 1.75), (3.0, 3.5), GATE_M, rot=(math.radians(90), 0, 0))
_gate_plane.hide_render = True
block("NX_GateFrameL", (RX - 1.6, 11.5, 1.75), (0.25, 0.3, 3.5), WALL)
block("NX_GateFrameR", (RX + 1.6, 11.5, 1.75), (0.25, 0.3, 3.5), WALL)
block("NX_GateFrameT", (RX, 11.5, 3.6), (3.45, 0.3, 0.25), WALL)

# ---------- kabut (volume) ----------
def haze(name, loc, scale, density):
    m = bpy.data.materials.new(name + "M")
    m.use_nodes = True
    nt = m.node_tree.nodes
    nt.remove(nt["Principled BSDF"])
    vol = nt.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = density
    vol.inputs["Color"].default_value = (0.85, 0.88, 0.95, 1.0)
    m.node_tree.links.new(vol.outputs["Volume"], nt["Material Output"].inputs["Volume"])
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    h = bpy.context.object
    h.name = name
    h.scale = scale
    h.data.materials.append(m)
    return h


if os.environ.get("FS_VOL", "1") == "1":
    haze("CT_Haze", (0, 0, 2.0), (18, 9, 4), 0.015)   # kota
    haze("HD_Haze", (HX, 0, 1.5), (4, 3, 1.5), 0.01)  # persembunyian
    haze("NX_Haze", (RX, 0, 3.0), (15, 12, 4), 0.02)  # ruang inti

# ---------- karakter vinyl-toy ----------
# Kepala ~40% tinggi (KAIRO 1.8 unit). Karakter menghadap -Y (ke arah kamera default).
# Rig empty dibuat di animate_nexus.py.
CHARS = {}


def make_character(prefix, kind, scale, base, jacket_mat, skin_mat, eye_mat,
                   eye_red_mat=None):
    """kind: kairo | eva | sentinel | res | civ. base=(x,y,z)."""
    s = scale
    bx, by, bz = base
    hip_z = 0.48 * s
    sho_z = 1.12 * s
    sho_x = 0.38 * s * (1.35 if kind == "sentinel" else 1.0)
    head_z = 1.45 * s
    head_r = 0.275 * s * (1.1 if kind == "sentinel" else 1.0)
    head_mat = skin_mat
    # sentinel: mata sensor merah yang bisa dinyalakan via eye_red
    _red = kind == "sentinel"
    eye_r = 0.065 * s if _red else 0.055 * s  # sentinel 0.065 (0.075 terlalu besar/kartun)

    def P(x, y, z):
        return (bx + x, by + y, bz + z)

    body, head, armL, armR, legL, legR = [], [], [], [], [], []
    for side, sx in (("L", -1), ("R", 1)):
        _leg = block(f"{prefix}_Leg{side}", P(0.14 * sx * s, 0, 0.24 * s),
                     (0.17 * s, 0.2 * s, 0.42 * s), PANTS_K if kind in ("kairo", "res") else
                     (SUIT_EVA if kind == "eva" else (METAL_SEN if kind == "sentinel" else JACKET3)))
        _shoe = block(f"{prefix}_Shoe{side}", P(0.14 * sx * s, -0.04 * s, 0.07 * s),
                      (0.2 * s, 0.3 * s, 0.12 * s),
                      BOOTS if kind in ("kairo", "res") else METAL_SEN)
        (legL if side == "L" else legR).extend([_leg, _shoe])
    # torso + detail
    body.append(block(f"{prefix}_Torso", P(0, 0, 0.78 * s), (0.62 * s, 0.5 * s, 0.6 * s), jacket_mat))
    if kind == "kairo":
        # saku dada taktis (kotak pipih — JANGAN kena subsurf, biar tetap crisp)
        for side, sx in (("L", -1), ("R", 1)):
            body.append(block(f"{prefix}_Pocket{side}", P(0.15 * sx * s, -0.26 * s, 0.88 * s),
                              (0.2 * s, 0.03 * s, 0.14 * s), SHIRT))
        # bantalan bahu taktis
        for side, sx in (("L", -1), ("R", 1)):
            body.append(block(f"{prefix}_Pad{side}", P(0.32 * sx * s, 0, 1.08 * s),
                              (0.22 * s, 0.3 * s, 0.1 * s), JACKET))
    if kind == "sentinel":
        for side, sx in (("L", -1), ("R", 1)):
            body.append(block(f"{prefix}_Pad{side}", P(0.52 * sx * s, 0, 1.15 * s),
                              (0.42 * s, 0.36 * s, 0.22 * s), METAL_SEN2))
        # piston sendi bahu
        for side, sx in (("L", -1), ("R", 1)):
            body.append(cylinder(f"{prefix}_Piston{side}", P(sho_x * sx, 0.1 * s, sho_z),
                                 0.05 * s, 0.3 * s, METAL_SEN2, rot=(0, math.radians(90), 0)))
    # lengan (pivot di bahu)
    for side, sx in (("L", -1), ("R", 1)):
        lst = armL if side == "L" else armR
        lst.append(block(f"{prefix}_Arm{side}", P(sho_x * sx, 0, sho_z - 0.28 * s),
                         (0.16 * s, 0.18 * s, 0.5 * s), jacket_mat))
        lst.append(ball(f"{prefix}_Hand{side}", P(sho_x * sx, 0, sho_z - 0.56 * s),
                        (0.09 * s,) * 3, head_mat))
    # kepala + wajah
    head.append(ball(f"{prefix}_Head", P(0, 0, head_z), (head_r, head_r * 0.92, head_r), head_mat))
    if kind == "kairo":
        # rambut hitam pendek (mesh pendek, bukan particle hair)
        head.append(ball(f"{prefix}_Hair", P(0, 0.06 * s, head_z + 0.10 * s),
                         (head_r * 1.02, head_r * 0.95, head_r * 0.75), HAIR_KAI))
        # kerah tinggi jaket
        head.append(block(f"{prefix}_Collar", P(0, 0.05 * s, head_z - 0.24 * s),
                          (0.4 * s, 0.3 * s, 0.14 * s), JACKET))
    if kind == "sentinel":
        # helm / pelat kepala logam + visor
        head.append(ball(f"{prefix}_Helm", P(0, 0.05 * s, head_z + 0.08 * s),
                         (head_r * 1.08, head_r * 1.0, head_r * 0.7), METAL_SEN2))
        head.append(block(f"{prefix}_Visor", P(0, -0.22 * s, head_z + 0.05 * s),
                          (0.34 * s, 0.04 * s, 0.07 * s), SENSOR_OFF))
    eyes_black, eyes_red = [], []
    for side, sx in (("L", -1), ("R", 1)):
        eyes_black.append(ball(f"{prefix}_EyeB{side}", P(0.11 * sx * s, -0.235 * s, head_z + 0.03 * s),
                               (0.055 * s, 0.03 * s, 0.07 * s), eye_mat))
        if eye_red_mat is not None:
            eyes_red.append(ball(f"{prefix}_EyeR{side}", P(0.11 * sx * s, -0.24 * s, head_z + 0.03 * s),
                                 (eye_r, 0.032 * s, eye_r * 1.25), eye_red_mat))
    head.extend(eyes_black)
    head.extend(eyes_red)
    mouth = block(f"{prefix}_Mouth", P(0, -0.25 * s, head_z - 0.13 * s),
                  (0.12 * s, 0.03 * s, 0.03 * s), mat(f"{prefix}_MouthM", (0.10, 0.02, 0.03), 0.3))
    head.append(mouth)
    if kind in ("kairo", "res", "civ"):
        for side, sx in (("L", -1), ("R", 1)):
            head.append(block(f"{prefix}_Brow{side}", P(0.11 * sx * s, -0.25 * s, head_z + 0.13 * s),
                              (0.12 * s, 0.03 * s, 0.03 * s), HAIR_KAI, rot=(0, 0, math.radians(-10 * sx))))
    if kind == "eva":
        # garis circuitry biru di pelipis + "rambut energi" tipis
        for side, sx in (("L", -1), ("R", 1)):
            head.append(block(f"{prefix}_Circuit{side}", P(0.24 * sx * s, -0.1 * s, head_z + 0.1 * s),
                              (0.03 * s, 0.03 * s, 0.16 * s), CIRCUIT_BLUE))
    info = {
        "base": Vector(base), "scale": s, "kind": kind,
        "hip_z": hip_z, "sho_z": sho_z, "sho_x": sho_x, "head_z": head_z,
        "head_pivot_z": 1.18 * s,
        "body": body, "head": head, "armL": armL, "armR": armR,
        "legL": legL, "legR": legR,
        "eyes_black": eyes_black, "eyes_red": eyes_red, "mouth": mouth,
    }
    CHARS[prefix] = info
    return info


make_character("KAI", "kairo", 1.0, (0, 0, 0), JACKET, SKIN_KAI, EYE_DARK)
make_character("EVA", "eva", 1.0, (0, 0, 0), SUIT_EVA, SKIN_EVA, EYE_BLUE)
for _i in range(1, 9):
    make_character(f"SEN{_i}", "sentinel", 1.22, (0, 0, 0), METAL_SEN, METAL_SEN,
                   SENSOR_OFF, SENSOR_RED)
make_character("RES1", "res", 1.0, (0, 0, 0), JACKET2, SKIN_KAI, EYE_DARK)
make_character("RES2", "res", 1.0, (0, 0, 0), JACKET3, SKIN_KAI, EYE_DARK)
make_character("CIV1", "civ", 1.0, (0, 0, 0), JACKET3, SKIN_KAI, EYE_DARK)
make_character("CIV2", "civ", 1.0, (0, 0, 0), JACKET2, SKIN_KAI, EYE_DARK)

# --- bekas luka alis kiri KAIRO (WAJIB terbaca di close-up) ---
# Alis kiri = sisi +X (karakter menghadap -Y: kiri anatomis = +X; konvensi L
# builder zombie (-X) justru sisi kanan). RONDE FIX 1: garis TIPIS warna
# kulit sedikit lebih terang #D8B49A (bukan putih), TANPA emissive — versi
# lama (0.12 x 0.022, emissive 0.15) terbaca seperti plester putih tebal.
SCAR_M = mat("Scar", (0.847, 0.706, 0.604), 0.5)
# y=-0.22 (bukan -0.28): permukaan dahi di titik ini y~-0.19 — luka lama
# mengambang ~9 cm di depan kulit sehingga terbaca seperti strip terpisah.
# Kini menempel di kulit (0.04 di depan permukaan), tetap terbaca sebagai garis.
scar = block("KAI_Scar", (0.11, -0.22, 1.60), (0.10, 0.015, 0.012), SCAR_M,
             rot=(0, 0, math.radians(-25)))
CHARS["KAI"]["head"].append(scar)
CHARS["KAI"]["scar"] = scar

# --- backpack KAIRO (objek terpisah — dilepas di S6-S8, di-key via props) ---
bp_box = block("KAI_Backpack", (0, 0.32, 0.95), (0.42, 0.2, 0.5), BACKPACK_M)
bp_flap = block("KAI_BackpackFlap", (0, 0.42, 1.12), (0.44, 0.06, 0.16), JACKET)
bp_strip1 = block("KAI_BPStrip1", (0.12, 0.43, 0.95), (0.05, 0.02, 0.34), STRIP_BLUE)
bp_strip2 = block("KAI_BPStrip2", (-0.12, 0.43, 0.95), (0.05, 0.02, 0.34), STRIP_BLUE)
bp_ant = cylinder("KAI_BPAntenna", (0.18, 0.32, 1.35), 0.012, 0.35, POLE)
BACKPACK_OBJS = [bp_box, bp_flap, bp_strip1, bp_strip2, bp_ant]
for _o in BACKPACK_OBJS:
    _o.hide_render = True
# backpack tergeletak di lantai ruang inti (S6-S8)
bp_drop = block("KAI_BackpackDropped", (RX - 2.0, -1.5, 0.18), (0.42, 0.5, 0.2), BACKPACK_M,
                rot=(0, 0, math.radians(15)))
bp_drop.hide_render = True

# --- data core (kubus 12 cm, garis merah berdenyut) — di tangan kanan KAIRO ---
core = block("CoreCube", (0.38, -0.05, 0.56), (0.12, 0.12, 0.12), CORE_BODY)
core_line1 = block("CoreLine1", (0.38, -0.05, 0.56), (0.13, 0.13, 0.02), CORE_LINE)
core_line2 = block("CoreLine2", (0.38, -0.05, 0.56), (0.02, 0.13, 0.13), CORE_LINE)
CORE_OBJS = [core, core_line1, core_line2]
for _o in CORE_OBJS:
    _o.hide_render = True
# core terpasang di soket ruang inti (S6+) — ikut posisi soket geser
core_sock = block("CoreSocketed", (RX + 0.6, -0.6, 0.48), (0.12, 0.12, 0.12), CORE_BODY)
core_sock_l = block("CoreSocketedLine", (RX + 0.6, -0.6, 0.48), (0.13, 0.13, 0.02), CORE_LINE)
CORE_SOCKET_OBJS = [core_sock, core_sock_l]
for _o in CORE_SOCKET_OBJS:
    _o.hide_render = True
# core di atas meja persembunyian (S4a — menyala sendiri)
core_tab = block("CoreTable", (HX + 1, 1.5, 0.92), (0.12, 0.12, 0.12), CORE_BODY)
core_tab_l = block("CoreTableLine", (HX + 1, 1.5, 0.92), (0.13, 0.13, 0.02), CORE_LINE)
CORE_TABLE_OBJS = [core_tab, core_tab_l]
for _o in CORE_TABLE_OBJS:
    _o.hide_render = True

# ---------- lampu ----------
def point_light(name, loc, color, energy, shadow=False):
    bpy.ops.object.light_add(type="POINT", location=loc)
    o = bpy.context.object
    o.name = name
    o.data.color = color
    o.data.energy = energy
    o.data.shadow_soft_size = 0.5
    o.data.use_shadow = shadow
    return o


def area_light(name, loc, color, energy, size, rot, shadow=False):
    bpy.ops.object.light_add(type="AREA", location=loc)
    o = bpy.context.object
    o.name = name
    o.data.color = color
    o.data.energy = energy
    o.data.size = size
    o.data.use_shadow = shadow
    o.rotation_euler = rot
    return o


# kota surveilans
point_light("SirenLight", (8, 5.0, 3.1), (0.83, 0.16, 0.11), 0.0)
point_light("LampFlicker", (-3, 4.4, 3.1), (1.0, 0.85, 0.55), 300.0)
point_light("LampWarm1", (3, 4.4, 3.1), (1.0, 0.85, 0.55), 120.0)
point_light("LampWarm2", (-9, 4.4, 3.1), (1.0, 0.85, 0.55), 90.0)
point_light("NeonLight", (0, 5.0, 2.6), (1.0, 0.10, 0.10), 150.0)
area_light("DuskLight", (0, -8, 8), (1.0, 0.62, 0.35), 60.0, 16, (math.radians(35), 0, 0))
area_light("MoonLight", (0, 6, 10), (0.55, 0.68, 1.0), 260.0, 18, (math.radians(140), 0, 0), shadow=True)
# fill dingin minimal (area gelap benar-benar gelap)
area_light("CityFill", (0, -10, 6), (0.62, 0.72, 1.0), 170.0, 14, (math.radians(55), 0, 0))
area_light("HideFill", (HX, -8, 5), (0.62, 0.72, 1.0), 90.0, 10, (math.radians(55), 0, 0))
area_light("CoreFill", (RX, -8, 5), (0.62, 0.72, 1.0), 90.0, 10, (math.radians(55), 0, 0))
# rim light MERAH di belakang Kairo (satu per set, di-key bersama)
point_light("RimRedCity", (0, 5.5, 2.4), (1.0, 0.08, 0.05), 420.0)
point_light("RimRedHide", (HX, 2.5, 2.0), (1.0, 0.08, 0.05), 200.0)
point_light("RimRedCore", (RX, 5.0, 2.4), (1.0, 0.08, 0.05), 500.0)
# rim BIRU di belakang EVA (satu-satunya biru)
point_light("EvaRim", (HX + 2, -4.5, 2.0), (0.30, 0.65, 1.0), 0.0)
# lampu gantung hangat persembunyian
point_light("HideLight", (HX + 1, 1.0, 2.1), (1.0, 0.78, 0.45), 100.0)
# alarm koridor
point_light("CorrAlarmLight", (HX + 2, -7.5, 2.7), (0.83, 0.16, 0.11), 0.0)
# cahaya merah NEXUS (wajah raksasa + layar kota)
point_light("NexusLight", (RX, 8.0, 5.5), (1.0, 0.08, 0.05), 300.0)
point_light("NexusScreenLight", (0, 5.0, 4.5), (1.0, 0.08, 0.05), 120.0)
# gerbang cahaya putih (S8)
area_light("GateLight", (RX, 10.5, 2.0), (1.0, 1.0, 0.95), 0.0, 8, (math.radians(90), 0, 0))
# flash putih 2 frame S8 (f1380-1381)
area_light("FlashWhite", (RX, -2, 2.5), (1.0, 1.0, 1.0), 0.0, 10, (math.radians(60), 0, 0))
# glow mata Sentinel ECU (S1/S5c/S8) — ikut rig kepala SEN1 di animate
bpy.ops.object.light_add(type="POINT", location=(0, -0.3, 1.8))
eye_glow = bpy.context.object
eye_glow.name = "EyeGlow"
eye_glow.data.color = (1.0, 0.05, 0.05)
eye_glow.data.energy = 0.0
# denyut merah data core — ikut lengan kanan KAIRO di animate
bpy.ops.object.light_add(type="POINT", location=(0.38, -0.1, 0.56))
core_light = bpy.context.object
core_light.name = "CoreLight"
core_light.data.color = (1.0, 0.1, 0.05)
core_light.data.energy = 0.0

# ---------- quality pass B7: subsurf 1 di semua bagian karakter, bevel 0 ----------
# Detail pipih (saku, bekas luka, circuitry, visor) TIDAK kena subsurf — kalau
# kena, kotak pipih menggembung jadi bantal (pelajaran still S3 f421: "Shirt"
# jadi heksagon di dada Kairo).
SUB = int(os.environ.get("FS_SUB", "1"))
_NOSUB = ("Pocket", "Scar", "Circuit", "Visor")
for _info in CHARS.values():
    for _part in (_info["body"] + _info["head"] + _info["armL"] + _info["armR"]
                  + _info["legL"] + _info["legR"]):
        if _part.type == "MESH" and SUB > 0 and not any(_k in _part.name for _k in _NOSUB):
            _s = _part.modifiers.new("Subdiv", "SUBSURF")
            _s.levels = 0
            _s.render_levels = SUB
# vinyl: clear-coat ringan
for _m, _coat in ((SKIN_KAI, 0.5), (JACKET, 0.3), (BACKPACK_M, 0.2), (SKIN_EVA, 0.6)):
    _b = _m.node_tree.nodes["Principled BSDF"]
    if "Coat Weight" in _b.inputs:
        _b.inputs["Coat Weight"].default_value = _coat
        _b.inputs["Coat Roughness"].default_value = 0.15

# ---------- kamera default (plan yang menggerakkan per frame) ----------
bpy.ops.object.camera_add(location=(0, -6.5, 1.7))
cam = bpy.context.object
cam.data.lens = 40
look = Vector((0, 0, 1.3)) - cam.location
cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
cam.data.dof.use_dof = os.environ.get("FS_DOF", "1") == "1"
cam.data.dof.focus_distance = 6.5
cam.data.dof.aperture_fstop = 2.0
scene.camera = cam

scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("WROTE", OUT)
