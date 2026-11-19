# nexus-render-farm

Render farm GitHub Actions untuk film **NEXUS ZERO Episode 1 "Iteration 214"**
(60 dtk, 24 fps, 1440 frame, 9:16 utama + 16:9).

- `pipeline-nexus/` — pipeline final Tahap 1 (build_scene_nexus.py,
  plan_nexus.py, animate_nexus.py, plan.json 1440 baris). md5 identik dengan
  `~/workspace/shorts/nexus-zero/pipeline/`.
- `.github/workflows/render-nexus-test.yml` — tes 120 frame (S1 f0–59 + S7
  f1200–1259), 20 job paralel x 6 frame, Eevee 540x960, FS_SAMPLES=6
  (deviasi B7 terukur, sama seperti zombie v2).

Repo PUBLIK supaya menit Actions gratis. Full run (Tahap 3) tugas terpisah
setelah tes lolos.
