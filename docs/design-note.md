# Design Note — Lab 03 BJT DC Bias Web App (three bias circuits)

## 1. เป้าหมาย

ต่อยอดเว็บ Flask ของ Lab 02 ให้เลือกวงจรไบอัสได้สามแบบ แล้วคำนวณ DC
Operating Point ด้วยสมการ Forward-Active เดียวกัน และแสดงผลบน Browser
พร้อม validation และ warning เมื่อแบบจำลองใช้ไม่ได้

โหมดที่รองรับ:

| โหมด | อินพุตเพิ่ม | ตำแหน่งอุปกรณ์ |
|---|---|---|
| Voltage Divider Bias | R1, R2, RE | R1 จาก VCC ไป Base, R2 จาก Base ลงกราวด์, RE จาก Emitter ลงกราวด์ |
| Fixed Bias | RB | RB จาก VCC ไป Base, Emitter ต่อลงกราวด์ตรง ๆ |
| Emitter Bias (แหล่งจ่ายเดียว) | RB, RE | RB จาก VCC ไป Base, RE จาก Emitter ลงกราวด์ |

ขอบเขต: DC Operating Point เท่านั้น ไม่มี SPICE, DC Load Line, AC/Transient
หรือ bypass capacitor

## 2. Data Flow

```
Browser: select mode + form POST
        │  mode, vcc, (r1, r2 | rb), rc, (re), beta, vbe
        ▼
app.py  POST /calculate
        │  เลือก field ตามโหมด → แปลง kΩ → Ω ครั้งเดียว → dispatch if/elif
        ▼
dc_bias.py
        │  calculate_dc_bias / calculate_fixed_bias / calculate_emitter_bias
        │  dict: vth, rth, ib, ic, ie, vb, ve, vc, vce, region, warning
        ▼
templates/index.html + static/style.css
        │  แสดงโหมด ผลลัพธ์ หน่วย สถานะ และ warning
        ▼
Browser
```

เหตุผลที่แยกไฟล์:

- `dc_bias.py` เป็น pure engineering logic ไม่ import Flask/HTML ทดสอบได้ตรง ๆ
- `app.py` ดูแล HTTP, การเลือกฟังก์ชัน และการแปลงหน่วย
- `templates/` แสดงผลเท่านั้น ไม่เก็บสมการ
- `tests/` คือชุดทดสอบเดิมของ Lab 02 (regression ว่า Divider ไม่เสีย)

## 3. สมการ (Forward-Active Approximation)

ทุกโหมด: `IC = β·IB`, `IE = (β+1)·IB`, `VB = VE + VBE`,
`VC = VCC − IC·RC`, `VCE = VC − VE`

**Fixed Bias**

```
IB = (VCC − VBE) / RB
VE = 0
VCE = VC
```

**Emitter Bias**

```
IB = (VCC − VBE) / (RB + (β+1)·RE)
VE = IE·RE
```

**Voltage Divider Bias** (เหมือน Lab 02)

```
VTH = VCC·R2 / (R1 + R2)
RTH = R1·R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β+1)·RE)
VE  = IE·RE
```

## 4. สมมติฐานและหน่วย

- ทรานซิสเตอร์อยู่ใน Forward-Active Region, β และ VBE คงที่
- ตัวต้านทานเป็นอุดมคติ, ไม่คิด Early effect หรืออุณหภูมิ
- อินพุต: VCC/VBE เป็น V, RB/R1/R2/RC/RE เป็น kΩ (1000 kΩ = 1 MΩ)
- แปลง kΩ → Ω ที่ `app.py` ก่อนเรียก `dc_bias.py`; ผลลัพธ์ SI (V, A)
  แล้ว template แสดง V, mA และ µA

## 5. การเลือกฟังก์ชันและการตรวจสอบ

`app.py` เก็บ `MODES`, `MODE_LABELS`, `FIELDS` และ `DEFAULTS` ต่อโหมด
`POST /calculate` รับ `mode` แล้ว

- `divider` → `calculate_dc_bias(...)`, แปลง R1, R2, RC, RE
- `fixed` → `calculate_fixed_bias(...)`, แปลง RB, RC (ไม่แตะ RE)
- `emitter` → `calculate_emitter_bias(...)`, แปลง RB, RC, RE
- โหมดอื่น → ข้อความ error ภาษาไทย ไม่เดาเป็น Divider

ถ้าไม่ส่ง `mode` มา (ฟอร์มเก่าของ Lab 02) จะถือเป็น `divider` เพื่อให้ผลเดิม
และเทสต์เดิมยังใช้ได้

| เงื่อนไข | สถานะ | การแสดงผล |
|---|---|---|
| `IB ≤ 0` (Divider: `VTH ≤ VBE` ด้วย) | Cutoff | warning ว่าแบบจำลองใช้ไม่ได้ |
| `VCE < 0.2 V` | Saturation | warning ว่าแบบจำลองไม่น่าเชื่อถือ |
| อื่น ๆ | Forward Active | แสดงผลปกติ |

อินพุตผิด (ค่าว่าง, ไม่ใช่ตัวเลข, ค่าไม่จำกัด, R ≤ 0, β ≤ 0, VBE < 0)
ถูกปฏิเสธด้วย `ValueError` และแสดงข้อความภาษาไทยบนหน้าเดิมโดยไม่ล้ม
ฟอร์มแสดงเฉพาะช่องของโหมดที่เลือก (เปลี่ยนโหมดด้วยปุ่ม `Load form`,
ไม่ต้องใช้ JavaScript) และผลลัพธ์/error ระบุชื่อโหมดเสมอ

## 6. เอกสารอ้างอิง

- ทางเลือกและเหตุผล: `docs/brainstorm.md` §6
- ผลตรวจ A1–A5 และค่าอ้างอิสระ: `docs/validation.md`
- Design ฉบับเต็ม: `docs/superpowers/specs/2026-11-17-lab03-bjt-bias-design.md`
- แผนพัฒนา: `docs/superpowers/plans/2026-11-17-lab03-bjt-bias-modes.md`
- ใบงาน: `docs/lab03-assignment.html`
