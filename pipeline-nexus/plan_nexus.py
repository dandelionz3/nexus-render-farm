#!/usr/bin/env python3
# plan_nexus.py — generator plan.json NEXUS ZERO Episode 1 "Iteration 214".
# Satu baris per frame (f 0..1439). Per frame: rig tiap karakter, intensitas
# lampu, kamera (x,y,z,target,focus,lens,roll Dutch), flag.
# Murni Python (tanpa bpy). Pola: plan_zombie_v2.py.
#   python3 plan_nexus.py [plan.json]
import json
import math
import os
import sys

N = 1440
HX = -80.0  # offset persembunyian bawah tanah (sama dengan build_scene_nexus.py)
RX = 80.0   # offset ruang inti NEXUS
FLASH = 1380  # flash putih 2 frame: 1380-1381 (S8)
ALL_CHARS = ["KAI", "EVA"] + [f"SEN{i}" for i in range(1, 9)] + ["RES1", "RES2", "CIV1", "CIV2"]


def clamp(x, a, b):
    return max(a, min(b, x))


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def seg_t(f, a, b):
    return clamp((f - a) / max(1, b - a), 0.0, 1.0)


def shake(f, amp, freq=1.7):
    return amp * (math.sin(f * 0.9 * freq) * 0.6 + math.sin(f * 2.3 * freq + 1.3) * 0.4)


def walk_cycle(phase, amp, arm_amp=None):
    if arm_amp is None:
        arm_amp = amp * 0.8
    return {
        "legL": amp * math.sin(phase),
        "legR": -amp * math.sin(phase),
        "armL": -arm_amp * math.sin(phase),
        "armR": arm_amp * math.sin(phase),
        "bob": 0.045 * abs(math.cos(phase)),
    }


def char(x=0, y=0, z=0, rot=0, lean=0, squash=1.0, crouch=0.0, pitch=0.0,
         head_tilt=0, head_turn=0, armL=0, armR=0, legL=0, legR=0,
         eye_red=False, vis=True, mouthW=1.0, mouthH=1.0):
    return {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3), "rot": round(rot, 2),
            "lean": round(lean, 2), "squash": round(squash, 3), "crouch": round(crouch, 3),
            "pitch": round(pitch, 2), "head_tilt": round(head_tilt, 2),
            "head_turn": round(head_turn, 2), "armL": round(armL, 2), "armR": round(armR, 2),
            "legL": round(legL, 2), "legR": round(legR, 2),
            "eye_red": bool(eye_red), "vis": bool(vis),
            "mouthW": round(mouthW, 2), "mouthH": round(mouthH, 2)}


def hidden():
    return char(vis=False)


def cam(x, y, z, tx, ty, tz, focus, lens, roll=0.0):
    return {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3),
            "tx": round(tx, 3), "ty": round(ty, 3), "tz": round(tz, 3),
            "focus": round(focus, 2), "lens": round(lens, 1),
            "roll": round(roll, 2)}


def lights(siren=0, lamp=300, dusk=60, moon=260, flash=0, hide=0, nexus=120,
           gate=0, rim=0, eye=0, core=0, eva=0, corr=0, neon=150, fill=90):
    return {"siren": round(siren, 1), "lamp": round(lamp, 1), "dusk": round(dusk, 1),
            "moon": round(moon, 1), "flash": round(flash, 1), "hide": round(hide, 1),
            "nexus": round(nexus, 1), "gate": round(gate, 1), "rim": round(rim, 1),
            "eye": round(eye, 1), "core": round(core, 1), "eva": round(eva, 1),
            "corr": round(corr, 1), "neon": round(neon, 1), "fill": round(fill, 1)}


def sentinel_patrol(x, y, f, phase0=0.0, rot=90, speed=0.5):
    """Sentinel: langkah berat kaku, kepala menoleh dengan jeda mekanik."""
    ph = phase0 + f * 0.06 * speed
    step = 14 * math.sin(ph)
    # kepala menoleh stepwise (jedak mekanik): tahan 12 frame, pindah 8 frame
    turn = 18 * math.sin(math.floor(f / 20) * 1.1)
    return char(x, y, 0.02 * abs(math.cos(ph)), rot=rot, lean=3,
                head_tilt=2, head_turn=turn,
                armL=6, armR=-6, legL=step, legR=-step, eye_red=True)


def ped_walk(x, y, f, phase0, rot, amp=22):
    ph = phase0 + f * 0.11
    c = walk_cycle(ph, amp)
    return char(x, y, c["bob"], rot=rot, lean=4, head_tilt=0, head_turn=0,
                armL=c["armL"], armR=c["armR"], legL=c["legL"], legR=c["legR"])


rows = []
for f in range(N):
    chars = {}
    props = {"core_in_hand": False, "core_table": False, "core_socket": False,
             "backpack": False, "backpack_dropped": False, "rain": False,
             "gate": False}  # gerbang cahaya putih — hanya S8
    flash_white = False

    # ================= S1 HOOK (0-71) =================
    if f < 72:
        props["backpack"] = True
        props["rain"] = True
        if f < 24:
            # 1a: ECU mata Sentinel, Dutch 10, statis — gelap -> mata merah menyala
            chars["SEN1"] = char(0, 1.5, 0, rot=0, lean=0, head_tilt=0, eye_red=True)
            chars_cam = cam(0.25, -0.5, 1.8, 0, 1.45, 1.78, 1.95, 80, roll=10)
            eye = 600 * smooth(seg_t(f, 0, 23))
            li = lights(siren=0, lamp=0, dusk=0, moon=40, eye=eye, rim=60, fill=40, neon=0, nexus=0)
        elif f < 48:
            # 1b: punch-in cepat ke mata, shake halus
            t = smooth(seg_t(f, 24, 47))
            chars["SEN1"] = char(0, 1.5, 0, rot=0, lean=0, head_tilt=0, eye_red=True)
            chars_cam = cam(0.2 + shake(f, 0.02), lerp(-0.5, -0.15, t), 1.79 + shake(f + 5, 0.01),
                            0, 1.45, 1.78, lerp(1.95, 1.6, t), lerp(80, 95, t), roll=10)
            li = lights(siren=0, lamp=0, dusk=0, moon=40, eye=600, rim=60, fill=40, neon=0, nexus=0)
        else:
            # 1c: cut wide jalan hujan, Dutch 10 — Kairo lari KE ARAH kamera
            # (start lebih dekat: sh_y 2.2 bukan 3.5 — di f48 Kairo sudah ~55% tinggi frame)
            t = seg_t(f, 48, 71)
            sh_y = lerp(2.2, -2.0, t)
            ph = f * 0.55
            c = walk_cycle(ph, 40)
            chars["KAI"] = char(0, sh_y, c["bob"], rot=0, lean=12, head_tilt=-4,
                                armL=c["armL"], armR=c["armR"], legL=c["legL"], legR=c["legR"])
            chars["SEN1"] = char(0.8, sh_y + 3.5, 0, rot=0, lean=4, eye_red=True,
                                 legL=10 * math.sin(f * 0.3), legR=-10 * math.sin(f * 0.3))
            chars["SEN2"] = char(-1.6, sh_y + 4.2, 0, rot=0, lean=4, eye_red=True,
                                 legL=10 * math.sin(f * 0.3 + 1), legR=-10 * math.sin(f * 0.3 + 1))
            cx, cy, cz = 0, lerp(-4.6, -3.2, smooth(t)), lerp(1.4, 1.3, smooth(t))
            chars_cam = cam(cx + shake(f, 0.06), cy, cz + shake(f + 9, 0.03),
                            0, sh_y, 1.55, abs(cy - sh_y), lerp(85, 55, smooth(t)), roll=10)
            flick = 450 if (f // 5) % 2 == 0 else 40
            sir = 900 if (f // 4) % 2 == 0 else 60
            li = lights(siren=sir, lamp=flick, dusk=0, moon=260, eye=300, rim=420, neon=150)
        for _p in ("EVA", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
        if f < 48:
            for _p in ("KAI", "SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                       "EVA", "RES1", "RES2", "CIV1", "CIV2"):
                chars[_p] = hidden()
    # ================= S2 ANCAMAN (72-287) =================
    elif f < 288:
        if f < 145:
            # 2a: aerial tinggi, turun pelan — kota surveilans malam (72-144, f144 aerial)
            t = seg_t(f, 72, 144)
            for i in range(1, 7):
                chars[f"SEN{i}"] = sentinel_patrol(lerp(-9 + i * 3, -6 + i * 3, t), 1.0 + (i % 2),
                                                   f, phase0=i * 2.0, rot=90)
            chars["CIV1"] = ped_walk(lerp(-4, 2, t), 2.5, f, 1.0, rot=90, amp=18)
            chars["CIV2"] = ped_walk(lerp(-2, 4, t), -1.5, f, 3.0, rot=90, amp=18)
            chars_cam = cam(0, lerp(-7, -4.5, smooth(t)), lerp(12, 7.5, smooth(t)),
                            0, 2, 0, 10, 40)
            li = lights(siren=200, lamp=300, dusk=60, moon=260, nexus=300, rim=0, fill=90)
        elif f < 216:
            # 2b: tracking jalanan — 6 Sentinel berpatroli, manusia digiring
            t = seg_t(f, 145, 215)
            sen_x = lerp(-9, 3, t)
            for i in range(1, 7):
                chars[f"SEN{i}"] = sentinel_patrol(sen_x - 1.5 + (i - 1) * 2.2, 1.0 + (i % 2) * 0.8,
                                                   f, phase0=i * 2.0, rot=90)
            chars["CIV1"] = ped_walk(sen_x + 10, 2.2, f, 1.0, rot=90, amp=18)
            chars["CIV2"] = ped_walk(sen_x + 11.5, -1.0, f, 3.0, rot=90, amp=18)
            chars["RES1"] = ped_walk(sen_x + 9, 0.2, f, 5.0, rot=90, amp=18)
            chars_cam = cam(sen_x - 2 + shake(f, 0.03), -4.5, 1.7,
                            sen_x + 2, 1.0, 1.3, 6.5, 48)
            li = lights(siren=300 + 200 * math.sin(f * 0.2), lamp=320, dusk=0, moon=260,
                        nexus=300, rim=0, fill=90)
        else:
            # 2c: slow push-in ke layar NEXUS
            t = seg_t(f, 216, 287)
            for i in range(1, 7):
                chars[f"SEN{i}"] = sentinel_patrol(lerp(3 + i * 2.0, 6 + i * 2.0, t), 1.0,
                                                   f, phase0=i * 2.0, rot=90)
            chars_cam = cam(-7, lerp(-4, 2.5, smooth(t)), lerp(2.0, 4.0, smooth(t)),
                            -7, 5.9, 4.2, lerp(6.5, 3.5, smooth(t)), lerp(50, 65, t))
            li = lights(siren=150, lamp=200, dusk=0, moon=200, nexus=500, rim=0, fill=70)
        for _p in ("KAI", "EVA", "SEN7", "SEN8", "RES2"):
            chars[_p] = hidden()
        if f < 145:
            chars["RES1"] = hidden()
        if f >= 216:
            for _p in ("CIV1", "CIV2", "RES1"):
                chars[_p] = hidden()
    # ================= S3 KAIRO (288-599) =================
    elif f < 600:
        props["backpack"] = True
        props["core_in_hand"] = True
        if f < 360:
            # 3a: wide persembunyian, statis
            chars["KAI"] = char(HX + 1, 0.6, 0, rot=0, lean=5, head_tilt=4,
                                armL=10, armR=35, legL=0, legR=0)
            chars["RES1"] = char(HX - 1, 1.8, 0, rot=140, lean=6, head_tilt=8, armL=5, armR=5)
            chars["RES2"] = char(HX + 2.5, 2.2, 0, rot=200, lean=6, head_tilt=8, armL=5, armR=5)
            chars["CIV1"] = char(HX - 2, 0.5, 0, rot=60, lean=4, head_tilt=6, armL=5, armR=5)
            chars_cam = cam(HX - 2, -2.5, 1.7, HX + 1, 1.0, 1.2, 4.0, 40)
            li = lights(moon=40, hide=100, rim=120, fill=35, nexus=0, neon=0, lamp=0, dusk=0)
        elif f < 480:
            # 3b: slow dolly-in ke wajah Kairo — core berdenyut, bekas luka terbaca
            t = seg_t(f, 360, 479)
            core_pulse = 60 + 50 * math.sin(f * 0.35)
            chars["KAI"] = char(HX + 1, 0.6, 0, rot=0, lean=lerp(5, 8, smooth(t)),
                                head_tilt=lerp(4, -2, smooth(t)), head_turn=lerp(0, -8, smooth(t)),
                                armL=10, armR=lerp(35, 55, smooth(t)), legL=0, legR=0)
            chars["RES1"] = char(HX - 1, 1.8, 0, rot=140, lean=6, head_tilt=8, armL=5, armR=5)
            chars["RES2"] = char(HX + 2.5, 2.2, 0, rot=200, lean=6, head_tilt=8, armL=5, armR=5)
            chars["CIV1"] = char(HX - 2, 0.5, 0, rot=60, lean=4, head_tilt=6, armL=5, armR=5)
            chars_cam = cam(lerp(HX - 0.5, HX + 0.4, smooth(t)), lerp(-2.2, -0.9, smooth(t)),
                            lerp(1.6, 1.55, smooth(t)),
                            HX + 1, 0.6, 1.45, lerp(3.0, 1.6, smooth(t)), lerp(46, 62, t))
            li = lights(moon=40, hide=100, rim=200, fill=35, core=core_pulse,
                        nexus=0, neon=0, lamp=0, dusk=0)
        else:
            # 3c: ambang pintu — EVA muncul, mata biru satu-satunya biru
            t = seg_t(f, 480, 599)
            chars["KAI"] = char(HX + 1, 0.6, 0, rot=lerp(0, 45, smooth(seg_t(f, 480, 520))),
                                lean=5, head_tilt=4, head_turn=lerp(0, 35, smooth(seg_t(f, 480, 520))),
                                armL=10, armR=35, legL=0, legR=0)
            chars["EVA"] = char(HX + 2, -2.6, 0, rot=180, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars["RES1"] = char(HX - 1, 1.8, 0, rot=140, lean=6, head_tilt=8, armL=5, armR=5)
            chars["RES2"] = char(HX + 2.5, 2.2, 0, rot=200, lean=6, head_tilt=8, armL=5, armR=5)
            chars["CIV1"] = char(HX - 2, 0.5, 0, rot=60, lean=4, head_tilt=6, armL=5, armR=5)
            chars_cam = cam(lerp(HX + 0.5, HX + 0.8, smooth(t)), lerp(0.8, 0.2, smooth(t)),
                            1.6, HX + 2, -2.6, 1.5, lerp(3.5, 3.0, smooth(t)), 52)
            li = lights(moon=40, hide=100, rim=120, fill=35, eva=500, core=60,
                        nexus=0, neon=0, lamp=0, dusk=0)
        for _p in ("SEN1", "SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8", "CIV2"):
            chars[_p] = hidden()
        if f < 480:
            chars["EVA"] = hidden()
    # ================= S4 CORE MENUNGGU (600-863) =================
    elif f < 864:
        if f < 672:
            # 4a: dolly-in ke core di meja — core menyala SENDIRI
            t = seg_t(f, 600, 671)
            props["core_table"] = True
            props["backpack"] = True
            core_pulse = 80 + 120 * (0.5 + 0.5 * math.sin(f * 0.5))
            chars["KAI"] = char(HX + 1, 0.2, 0, rot=0, lean=lerp(5, 14, smooth(t)),
                                head_tilt=lerp(4, 18, smooth(t)),
                                armL=10, armR=lerp(35, 60, smooth(t)), legL=0, legR=0)
            chars["RES1"] = char(HX - 1, 1.8, 0, rot=140, lean=6, head_tilt=8, armL=5, armR=5)
            chars_cam = cam(lerp(HX + 0.5, HX + 0.8, smooth(t)), lerp(-1.8, -0.4, smooth(t)),
                            lerp(1.6, 1.3, smooth(t)),
                            HX + 1, 1.5, 0.95, lerp(3.2, 1.6, smooth(t)), lerp(48, 62, t))
            li = lights(moon=40, hide=100, rim=150, fill=35, core=core_pulse,
                        nexus=0, neon=0, lamp=0, dusk=0)
            for _p in ("EVA", "SEN1", "SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                       "RES2", "CIV1", "CIV2"):
                chars[_p] = hidden()
        elif f < 768:
            # 4b: wajah EVA, close-up — mata biru berkedip pelan
            t = seg_t(f, 672, 767)
            props["core_table"] = True
            blink = 1.0 if (f % 72) < 66 else 0.7  # kedip via squash ringan
            chars["EVA"] = char(HX + 1.5, 0.5, 0, rot=0, lean=2, head_tilt=lerp(6, 0, smooth(t)),
                                head_turn=lerp(10, 0, smooth(t)), armL=5, armR=5,
                                squash=blink)
            chars["KAI"] = char(HX + 0.5, -0.8, 0, rot=25, lean=5, head_tilt=4,
                                head_turn=30, armL=10, armR=20, legL=0, legR=0)
            chars_cam = cam(lerp(HX + 1.2, HX + 1.3, smooth(t)), lerp(-1.8, -1.4, smooth(t)),
                            1.6, HX + 1.5, 0.5, 1.45, lerp(2.8, 2.2, smooth(t)), 62)
            li = lights(moon=40, hide=100, rim=100, fill=35, eva=400, core=120,
                        nexus=0, neon=0, lamp=0, dusk=0)
            for _p in ("SEN1", "SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                       "RES1", "RES2", "CIV1", "CIV2"):
                chars[_p] = hidden()
        else:
            # 4c: tracking koridor, shake naik — alarm merah, Sentinel masuk
            t = seg_t(f, 768, 863)
            props["backpack"] = True
            sen_y = lerp(-8.5, -4.5, smooth(t))
            chars["SEN1"] = sentinel_patrol(HX + 2, sen_y, f, phase0=0, rot=180, speed=0.8)
            chars["KAI"] = char(HX + 2, -2.2, 0, rot=180, lean=6, head_tilt=4,
                                head_turn=0, armL=10, armR=25, legL=0, legR=0)
            chars["EVA"] = char(HX + 1.2, -2.4, 0, rot=180, lean=2, head_tilt=4,
                                armL=5, armR=5)
            chars_cam = cam(HX + 2 + shake(f, 0.05 + 0.06 * t), lerp(-4.2, -3.6, smooth(t)),
                            1.6 + shake(f + 3, 0.03),
                            HX + 2, sen_y, 1.4, lerp(4.0, 3.0, smooth(t)), 50)
            alarm = 900 if (f // 6) % 2 == 0 else 80
            li = lights(moon=40, hide=100, rim=100, fill=35, corr=alarm, eye=400,
                        nexus=0, neon=0, lamp=0, dusk=0, siren=alarm)
            for _p in ("SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                       "RES1", "RES2", "CIV1", "CIV2"):
                chars[_p] = hidden()
    # ================= S5 KEJARAN (864-1055) =================
    elif f < 1056:
        props["backpack"] = True
        props["rain"] = True
        props["core_in_hand"] = True
        if f < 936:
            # 5a: tracking cepat, Dutch 9, shake — Kairo + 2 resistance lari
            t = seg_t(f, 864, 935)
            sh_x = lerp(-10, 2, t)
            ph = f * 0.6
            c = walk_cycle(ph, 42)
            chars["KAI"] = char(sh_x, 0, c["bob"], rot=90, lean=13, head_tilt=-4,
                                armL=c["armL"], armR=c["armR"], legL=c["legL"], legR=c["legR"])
            chars["RES1"] = char(sh_x - 1.2, 1.4, walk_cycle(ph + 1.5, 40)["bob"], rot=90, lean=12,
                                 armL=walk_cycle(ph + 1.5, 40)["armL"], armR=walk_cycle(ph + 1.5, 40)["armR"],
                                 legL=walk_cycle(ph + 1.5, 40)["legL"], legR=walk_cycle(ph + 1.5, 40)["legR"])
            chars["RES2"] = char(sh_x - 2.0, -1.6, walk_cycle(ph + 3.0, 40)["bob"], rot=90, lean=12,
                                 armL=walk_cycle(ph + 3.0, 40)["armL"], armR=walk_cycle(ph + 3.0, 40)["armR"],
                                 legL=walk_cycle(ph + 3.0, 40)["legL"], legR=walk_cycle(ph + 3.0, 40)["legR"])
            for i in range(1, 5):
                chars[f"SEN{i}"] = sentinel_patrol(sh_x - 3.5 - i * 1.2, (i % 2) * 1.6 - 0.8,
                                                   f, phase0=i * 1.7, rot=90, speed=1.0)
            chars_cam = cam(sh_x + 1.0 + shake(f, 0.09), -4.5 + shake(f + 5, 0.05),
                            1.6 + shake(f + 11, 0.04),
                            sh_x, 0, 1.2, 5.5, 48, roll=9)
            li = lights(siren=700 + 300 * math.sin(f * 0.4), lamp=300, dusk=0, moon=260,
                        eye=400, rim=420, neon=250)
        elif f < 1008:
            # 5b: low-angle — Kairo melompati barikade
            t = seg_t(f, 936, 1007)
            sh_x = lerp(2, 10, t)
            jump = math.sin(math.pi * clamp(seg_t(f, 960, 990), 0, 1)) if 960 <= f <= 990 else 0.0
            ph = f * 0.6
            c = walk_cycle(ph, 42)
            chars["KAI"] = char(sh_x, 0.5, c["bob"] + 0.55 * jump, rot=90, lean=14,
                                armL=c["armL"], armR=c["armR"], legL=c["legL"], legR=c["legR"])
            chars["RES1"] = char(sh_x - 1.5, 1.6, walk_cycle(ph + 1.5, 40)["bob"], rot=90, lean=12,
                                 armL=walk_cycle(ph + 1.5, 40)["armL"], armR=walk_cycle(ph + 1.5, 40)["armR"],
                                 legL=walk_cycle(ph + 1.5, 40)["legL"], legR=walk_cycle(ph + 1.5, 40)["legR"])
            for i in range(1, 5):
                chars[f"SEN{i}"] = sentinel_patrol(sh_x - 4.5 - i * 1.2, (i % 2) * 1.6 - 0.8,
                                                   f, phase0=i * 1.7, rot=90, speed=1.0)
            chars_cam = cam(8.5, -3.5, 0.8, sh_x, 0.5, 1.0, 4.5, 50)
            li = lights(siren=700, lamp=300, dusk=0, moon=260, eye=400, rim=420, neon=250)
        else:
            # 5c: ECU mata Sentinel mengejar — sensor merah mengunci
            t = seg_t(f, 1008, 1055)
            chars["SEN1"] = char(0, 1.5, 0, rot=0, lean=0, head_tilt=lerp(0, 4, smooth(t)), eye_red=True)
            chars_cam = cam(0.2, lerp(-0.6, -0.4, smooth(t)), 1.8,
                            0, 1.45, 1.78, lerp(2.0, 1.7, smooth(t)), lerp(75, 85, t))
            li = lights(siren=500, lamp=100, dusk=0, moon=60, eye=900, rim=100, fill=40, neon=0)
        for _p in ("EVA", "CIV1", "CIV2"):
            chars[_p] = hidden()
        if f < 936:
            chars["SEN5"] = hidden(); chars["SEN6"] = hidden()
            chars["SEN7"] = hidden(); chars["SEN8"] = hidden()
        elif f < 1008:
            chars["SEN5"] = hidden(); chars["SEN6"] = hidden()
            chars["SEN7"] = hidden(); chars["SEN8"] = hidden()
            chars["RES2"] = hidden()
        else:
            for _p in ("KAI", "SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                       "RES1", "RES2"):
                chars[_p] = hidden()
    # ================= S6 RUANG INTI (1056-1199) =================
    elif f < 1200:
        props["backpack_dropped"] = True  # backpack dilepas, tergeletak di lantai
        if f < 1120:
            # 6a: low-angle reveal — Kairo memasang core ke soket
            t = seg_t(f, 1056, 1119)
            install = smooth(seg_t(f, 1080, 1110))
            props["core_in_hand"] = f < 1100
            props["core_socket"] = f >= 1100
            chars["KAI"] = char(RX, lerp(-1.2, -0.8, smooth(t)), 0, rot=180,
                                lean=lerp(4, 16, smooth(t)), crouch=lerp(0.0, 0.5, smooth(seg_t(f, 1056, 1080))),
                                head_tilt=lerp(0, 20, smooth(t)),
                                armL=10, armR=lerp(20, 70, install), legL=0, legR=0)
            chars_cam = cam(lerp(RX - 2.5, RX - 2.0, smooth(t)), lerp(-4.5, -4.0, smooth(t)),
                            lerp(0.9, 1.1, smooth(t)),
                            RX, 0, 1.2, 4.5, 45)
            li = lights(moon=80, nexus=lerp(300, 600, smooth(t)), rim=400, fill=90,
                        core=80 if f < 1100 else 200, gate=0, neon=0, lamp=0, dusk=0)
        else:
            # 6b: tilt-up ke wajah NEXUS — partikel terbentuk, mata menyala
            t = seg_t(f, 1120, 1199)
            props["core_socket"] = True
            chars["KAI"] = char(RX, -0.8, 0, rot=180, lean=6, crouch=0.2,
                                head_tilt=lerp(20, -14, smooth(t)),
                                armL=10, armR=lerp(70, 15, smooth(t)), legL=0, legR=0)
            chars_cam = cam(RX - 1.0, -5.0, 1.2,
                            RX, lerp(0, 11.4, smooth(t)), lerp(1.2, 6.0, smooth(t)),
                            lerp(5.0, 11.0, smooth(t)), lerp(45, 55, t))
            li = lights(moon=80, nexus=lerp(600, 900, smooth(t)), rim=400, fill=90,
                        core=200, gate=0, neon=0, lamp=0, dusk=0)
        for _p in ("EVA", "SEN1", "SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
    # ================= S7 REVELATION (1200-1319) =================
    elif f < 1320:
        props["backpack_dropped"] = True
        props["core_socket"] = True
        if f < 1260:
            # 7a: dolly-in ke wajah Kairo — membeku, mata membesar, bekas luka jelas
            t = seg_t(f, 1200, 1259)
            chars["KAI"] = char(RX, -1.0, 0, rot=0, lean=lerp(4, 8, smooth(t)),
                                head_tilt=lerp(0, -4, smooth(t)), head_turn=0,
                                armL=5, armR=5, legL=0, legR=0, mouthH=1.3)
            chars_cam = cam(RX, lerp(-3.8, -2.2, smooth(t)), lerp(1.6, 1.55, smooth(t)),
                            RX, -1.0, 1.45, lerp(2.8, 1.3, smooth(t)), lerp(50, 70, t))
            li = lights(moon=80, nexus=lerp(700, 900, smooth(t)), rim=500, fill=90,
                        core=150, gate=0, neon=0, lamp=0, dusk=0)
        else:
            # 7b: montase kilat 3 cut — siluet 213 Kairo sebelumnya, jatuh satu per satu
            cut = (f - 1260) // 20  # 0, 1, 2
            if cut == 0:
                chars["KAI"] = char(RX - 4, 3, 0, rot=30, lean=10, crouch=0.7,
                                    head_tilt=16, armL=15, armR=15)
                chars_cam = cam(RX - 4, -1.0, 1.0, RX - 4, 3, 1.0, 4.2, 55)
            elif cut == 1:
                chars["KAI"] = char(RX + 4, 4, 0, rot=-25, lean=14, crouch=0.85,
                                    head_tilt=20, armL=20, armR=10)
                chars_cam = cam(RX + 4, 0.5, 1.1, RX + 4, 4, 1.1, 4.2, 55)
            else:
                chars["KAI"] = char(RX, 6, 0, rot=0, lean=0, pitch=-80,
                                    head_tilt=0, armL=30, armR=30)
                chars_cam = cam(RX + 1, 2.0, 1.2, RX, 6, 0.5, 4.5, 50)
            li = lights(moon=80, nexus=900, rim=600, fill=90, core=150,
                        gate=0, neon=0, lamp=0, dusk=0)
        for _p in ("EVA", "SEN1", "SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
    # ================= S8 CLIFFHANGER (1320-1439) =================
    else:
        props["backpack_dropped"] = True
        props["core_socket"] = True
        props["gate"] = True  # gerbang cahaya putih tampil mulai S8
        if f < 1380:
            # 8a: ECU mata Kairo — senyum tipis
            t = seg_t(f, 1320, 1379)
            smile = smooth(seg_t(f, 1360, 1379))
            chars["KAI"] = char(RX, -1.0, 0, rot=0, lean=6, head_tilt=lerp(0, -6, smooth(t)),
                                head_turn=0, armL=5, armR=5, legL=0, legR=0,
                                mouthW=lerp(1.0, 1.7, smile), mouthH=lerp(1.0, 0.6, smile))
            chars_cam = cam(lerp(RX + 0.2, RX + 0.1, smooth(t)), lerp(-2.4, -2.0, smooth(t)),
                            lerp(1.55, 1.52, smooth(t)),
                            RX, -1.0, 1.48, lerp(1.5, 1.1, smooth(t)), lerp(70, 80, t))
            li = lights(moon=80, nexus=800, rim=500, fill=80, core=150, gate=0,
                        neon=0, lamp=0, dusk=0)
        elif f < 1382:
            # 8b: flash putih 2 frame (f1380-1381)
            flash_white = True
            chars["KAI"] = char(RX, -1.0, 0, rot=0, lean=6, head_tilt=-6,
                                armL=5, armR=5, mouthW=1.7, mouthH=0.6)
            chars_cam = cam(RX + 0.1, -2.0, 1.52, RX, -1.0, 1.48, 1.1, 80)
            li = lights(moon=80, nexus=800, rim=500, fill=80, core=150, gate=0,
                        flash=2500, neon=0, lamp=0, dusk=0)
        elif f < 1404:
            # transisi: Kairo berbalik (rot 0 -> 180), kamera menahan lalu mulai mundur
            # (mundur sampai y=-5.0 supaya cut ke 8c — kamera sudah di belakang —
            # tidak terasa melompat)
            t = seg_t(f, 1382, 1403)
            chars["KAI"] = char(RX, -1.0, 0, rot=lerp(0, 180, smooth(t)), lean=6,
                                head_tilt=0, armL=5, armR=5, mouthW=1.7, mouthH=0.6)
            chars_cam = cam(RX + 0.1, lerp(-2.0, -5.0, smooth(t)), lerp(1.52, 1.4, smooth(t)),
                            RX, -1.0, 1.4, lerp(1.1, 2.5, smooth(t)), lerp(80, 60, t))
            li = lights(moon=80, nexus=800, rim=500, fill=80, core=150,
                        gate=lerp(0, 300, smooth(t)), neon=0, lamp=0, dusk=0)
        else:
            # 8c: pull-back lambat -> low-angle hero — Kairo berjalan KE ARAH 2 Sentinel
            # RONDE FIX 1: KAIRO DI TENGAH (x=RX, bukan RX-1.5) + kamera tepat di
            # belakangnya (x RX+0.6 = 3/4 ringan, bidik ke Kairo) — Kairo ~50%
            # tinggi frame, KEDUA Sentinel utuh mengapit gerbang. Soket sudah
            # digeser ke samping + direndahkan di build, tidak lagi di tengah
            # jalan. Gerbang diredupkan (gate 200->500, GATE_M 0.9).
            t = seg_t(f, 1404, 1439)
            kai_y = lerp(-1.0, 3.5, smooth(t))
            ph = f * 0.35
            c = walk_cycle(ph, 26)
            chars["KAI"] = char(RX, kai_y, c["bob"], rot=180, lean=8, head_tilt=0,
                                armL=c["armL"], armR=c["armR"], legL=c["legL"], legR=c["legR"],
                                mouthW=1.4, mouthH=0.7)
            chars["SEN1"] = char(RX - 2, 6, 0, rot=180, lean=3, head_tilt=0, eye_red=True,
                                 armL=6, armR=-6, legL=0, legR=0)
            chars["SEN2"] = char(RX + 2, 6, 0, rot=180, lean=3, head_tilt=0, eye_red=True,
                                 armL=6, armR=-6, legL=0, legR=0)
            chars_cam = cam(RX + 0.6, kai_y - 5.0, lerp(1.1, 1.0, smooth(t)),
                            RX, kai_y + 0.6, 1.35,
                            5.6, lerp(52, 46, t))
            li = lights(moon=80, nexus=900, rim=600, fill=150, core=150,
                        gate=lerp(150, 350, smooth(t)), eye=lerp(300, 700, smooth(t)),
                        neon=0, lamp=0, dusk=0)
        for _p in ("EVA", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
        if f < 1404:
            chars["SEN1"] = hidden()
            chars["SEN2"] = hidden()

    # pastikan SEMUA karakter ada di tiap baris (0 frame kosong)
    for _p in ALL_CHARS:
        if _p not in chars:
            chars[_p] = hidden()

    rows.append({"f": f, "t": round(f / 24.0, 4), "chars": chars, "lights": li,
                 "cam": chars_cam, "props": props, "flash_white": flash_white})


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "plan.json")
    with open(out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
    print(f"WROTE {out}: {len(rows)} rows")
    # self-checks
    assert len(rows) == N
    assert rows[0]["f"] == 0 and rows[-1]["f"] == N - 1
    flashes = [r["f"] for r in rows if r["flash_white"]]
    assert flashes == [FLASH, FLASH + 1], f"flash frames: {flashes}"
    empty_rows = [r["f"] for r in rows if not r["chars"]]
    assert not empty_rows, f"frame kosong: {empty_rows}"
    missing = [(r["f"], [p for p in ALL_CHARS if p not in r["chars"]])
               for r in rows if any(p not in r["chars"] for p in ALL_CHARS)]
    assert not missing, f"karakter hilang: {missing[:5]}"
    print(f"CHECK OK: flash frames {flashes}, semua {len(rows)} baris punya "
          f"{len(ALL_CHARS)} karakter, 0 frame kosong")


if __name__ == "__main__":
    main()
