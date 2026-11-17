# AGENTS.md — Lab 03 conventions

## Stack

- Python 3.12 (ขั้นต่ำ 3.10), Flask 3.1.3
- Test runner: `unittest` จาก standard library เท่านั้น (ห้ามเพิ่ม pytest)

## Commands

```powershell
# จากรากของ repository (โฟลเดอร์ที่มี app.py)
python -m unittest discover -s tests -v
python -m flask --app app run --port 5050

# จาก root ของ repo รวม gitlab/
python -m unittest discover -s lab03/tests -t lab03 -v
```

## Rules

- `dc_bias.py` ต้องเป็น pure engineering logic: ห้าม import Flask หรือรู้จัก HTML/HTTP
  และต้องไม่รับ/คืนค่าที่ขึ้นกับหน่วย kΩ (รับ SI: V, A, Ω)
- `app.py` รับ HTTP, เลือกฟังก์ชันตาม `mode`, แปลงหน่วย kΩ → Ω, แล้ว render template
- โหมดที่รองรับมีสามค่าเท่านั้น: `divider`, `fixed`, `emitter`
  โหมดอื่นต้องแจ้ง error ห้าม fallback เป็น Divider
- ถ้าไม่ส่ง `mode` มา ให้ถือเป็น `divider` (ความเข้ากันได้กับฟอร์ม Lab 02)
- ผลลัพธ์ทุกโหมดต้องเป็น dict คีย์เดียวกัน:
  `vth, rth, ib, ic, ie, vb, ve, vc, vce, region, warning`
  (`vth`/`rth` เป็น `None` ในโหมดที่ไม่ใช้)
- Template ต้องไม่ฝังผลลัพธ์หรือสมการฟิสิกส์เป็นค่าคงที่ และต้องแสดงชื่อโหมด
  ของผลลัพธ์/error ทุกครั้ง
- UI เป็นภาษาอังกฤษตาม mockup; ข้อความ error/warning เป็นภาษาไทย;
  identifier ในโค้ดเป็นภาษาอังกฤษ
- ห้ามแก้ไฟล์ Lab 1 (`electrical.py`, `test_electrical.py`) หรือโฟลเดอร์ `lab02/`
- ห้าม commit `.venv/`, `.env`, `__pycache__/`
- ห้ามอ้างว่า test ผ่านหรือ Browser ผ่านโดยไม่ได้รันจริง
