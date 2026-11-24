# Impeccable review — Lab 04 simulator UI

เอกสารนี้บันทึกการตรวจและปรับปรุง UI แบบ **scoped polish** หลังจากโค้ด Lab 04 ทำงานครบตาม B1–B8 แล้ว ไม่ได้ redesign และไม่แตะ logic ทางวิศวกรรม/การแปลงหน่วย/parser/กราฟข้อมูล

## ก่อนปรับปรุง (before)

หลักฐาน: `docs/impeccable-before-desktop.png` (OpenCode Browser, หน้า `/simulate` หลังรัน AC จริง, 800 CSS px)

คำสั่งและผลที่ใช้เป็นจุดเริ่ม:

```powershell
& '.opencode\skills\impeccable\scripts\impeccable.cmd' context --target templates/index.html
& '.opencode\skills\impeccable\scripts\impeccable.cmd' detect --json 'http://127.0.0.1:5050/?workspace=simulator'
```

ผล detector/gate ก่อนปรับปรุง:

- `straggler` (advisory): `p.course-badge` มีคำเดียวตกบรรทัดสุดท้าย
- `undersized-ui-text`: ข้อความฟังก์ชันบางส่วน (unit pill, caption, provenance, chart tick) มีขนาดต่ำกว่า 11 px หลัง scaling
- `flat-type-hierarchy` จากการสแกนไฟล์ template แบบ standalone (การสแกนนี้ไม่ resolve CSS ผ่าน `url_for()` จึงใช้เป็นสัญญาณร่วม ไม่ใช่ผลชี้ขาด)
- Lighthouse ก่อนปรับปรุง: Accessibility 1.00, Best Practices 1.00, SEO 0.75 — เหลือ `meta description` ที่ไม่มีใน `<head>`

หมายเหตุ: `detect --json --changed` ใช้ไม่ได้เพราะโฟลเดอร์นี้ไม่ใช่ git worktree ตอนรันคำสั่ง จึงสแกนไฟล์/URL แทน

## สิ่งที่แก้ (smallest safe changes)

อ่าน `reference/audit.md`, `reference/polish.md`, `reference/craft-floor.md` ตาม workflow ของ Impeccable แล้วแก้เฉพาะความสอดคล้องของระบบเดิม:

1. `templates/index.html`: เพิ่ม `<meta name="description">` สำหรับ SEO/Lighthouse
2. `static/style.css`:
   - ขยาย unit pill, chart tick/axis-label, model note, provenance line, figcaption ให้ ≥ 11 px (ผลจริง 11.52–13.12 px)
   - เพิ่ม `text-wrap: pretty` บน course badge, schematic caption และข้อความยาว
   - ทำให้ workspace tab, select, mode button และ submit button สูงอย่างน้อย 44 px และลด box-shadow ของปุ่มให้มี offset + blur ที่สอดคล้องกับโทนสีเดิม
   - เปลี่ยน status card และ provenance card ให้เป็น separator แทนการซ้อน card เพื่อลด `nested-cards` ที่ detector พบหลังรอบแรก
3. ไม่แก้ `app.py`, `spice_engine.py`, `charts.py`, `dc_bias.py` หรือ tests

## หลังปรับปรุง (after)

หลักฐาน:

- `docs/impeccable-after-desktop.png` — AC result เดิมหลัง restart server และ polish (800 CSS px)
- `docs/impeccable-after-mobile-390px.png` — 390 CSS px iframe emulation พร้อม AC result จริง

ผลตรวจจริง:

| การตรวจ | ผล |
|---|---|
| `impeccable detect --json 'http://127.0.0.1:5050/?workspace=simulator'` | `[]` |
| `impeccable detect --json 'http://127.0.0.1:5050/?workspace=bias'` | `[]` |
| Lighthouse simulator (OpenCode Browser) | Accessibility 1.00, Best Practices 1.00, SEO 1.00, failures `[]` |
| Desktop layout | `innerWidth=800`, `scrollWidth=785`, 2 charts, ไม่มี interactive target ต่ำกว่า 24 px |
| 390 px Emulation | `innerWidth=390`, `scrollWidth=375`, `Run status: SUCCESS`, 2 charts |
| ฟอนต์หลังแก้ | chart tick 12 px, unit 11.52 px, model note 13.12 px |

การคำนวณและผลจำลองยังเหมือนเดิม: SVG ยังสร้างจาก parsed ngspice output, ตาราง Lab 03 ยังเป็น analytical reference แยกต่างหาก และ error ภาษาไทย/การลบ stale result ยังผ่านชุดทดสอบเดิม

## AI ทำ / นักศึกษาตรวจ (สั้น ๆ)

1. AI อ่าน context/reference ของ Impeccable, รัน detector และเสนอการแก้แบบเฉพาะจุดใน CSS/meta เท่านั้น
2. AI เก็บภาพ before/after และ metrics จาก Chromium จริงผ่าน OpenCode Browser ไม่ได้สร้างภาพหรือตัวเลขขึ้นเอง
3. นักศึกษาตรวจว่าผล AC/TRAN, netlist, run status และ error state ไม่เปลี่ยนหลัง polish
4. นักศึกษารันชุดทดสอบจริงอีกครั้งหลังการแก้และตรวจหลักฐานก่อน commit
