# Validation — Lab 03 BJT DC Bias + Lab 04 CE Amplifier Simulator

เอกสารนี้บันทึก **ค่าอ้างอิงที่คำนวณมืออย่างอิสระ** และ **ผลที่อ่านจากหน้าเว็บจริง**
ตามตาราง A1–A5 ของใบงาน โดยไม่ใช้ค่าจากโค้ดเป็นคำตอบอ้างอิง

เงื่อนไขร่วมทุกกรณี: VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V
เกณฑ์: |ΔIC| ≤ 0.01 mA และ |ΔVCE| ≤ 0.02 V เทียบกับค่าอ้างอิงที่ยังไม่ปัดเศษ
หน่วยบนฟอร์ม: ตัวต้านทานเป็น kΩ (1000 kΩ = 1 MΩ), แรงดันเป็น V

## 1. ค่าอ้างอิงอิสระ (คำนวณมือจากสมการในใบงาน)

### A1 · Voltage Divider Bias (โหมดเดิมของ Lab 2)

R1 = 100 kΩ, R2 = 22 kΩ, RE = 1 kΩ

| ขั้น | สมการ | ค่า |
|---|---|---|
| VTH | 12 × 22 / (100 + 22) | 2.1639 V |
| RTH | 100 × 22 / (100 + 22) | 18.0328 kΩ |
| IB | (2.1639 − 0.70) / (18.0328 + 101 × 1) kΩ | 12.299 µA |
| IC | 100 × 12.299 µA | **1.2299 mA** |
| IE | 101 × 12.299 µA | 1.2422 mA |
| VE | 1.2422 mA × 1 kΩ | 1.2422 V |
| VC | 12 − 1.2299 mA × 2.2 kΩ | 9.2943 V |
| VCE | 9.2943 − 1.2422 | **8.0521 V** |

### A2 · Fixed Bias

RB = 1 MΩ = 1000 kΩ (Emitter ต่อลงกราวด์ตรง ๆ, VE = 0)

| ขั้น | สมการ | ค่า |
|---|---|---|
| IB | (12 − 0.70) / 1 000 000 Ω | 11.300 µA |
| IC | 100 × 11.300 µA | **1.1300 mA** |
| IE | 101 × 11.300 µA | 1.1413 mA |
| VE | 0 (ไม่มี RE) | 0 V |
| VB | 0 + 0.70 | 0.70 V |
| VC | 12 − 1.1300 mA × 2.2 kΩ | 9.5140 V |
| VCE | 9.5140 − 0 | **9.5140 V** |

### A3 · Emitter Bias

RB = 1 MΩ, RE = 1 kΩ

| ขั้น | สมการ | ค่า |
|---|---|---|
| IB | (12 − 0.70) / [1 000 000 + 101 × 1000] Ω | 10.2634 µA |
| IC | 100 × 10.2634 µA | **1.02634 mA** |
| IE | 101 × 10.2634 µA | 1.03660 mA |
| VE | 1.03660 mA × 1 kΩ | 1.0366 V |
| VB | 1.0366 + 0.70 | 1.7366 V |
| VC | 12 − 1.02634 mA × 2.2 kΩ | 9.74205 V |
| VCE | 9.74205 − 1.0366 | **8.70545 V** |

### A4 · Emitter Bias, เปลี่ยนเฉพาะ RE เป็น 2 kΩ

| ขั้น | สมการ | ค่า |
|---|---|---|
| IB | (12 − 0.70) / [1 000 000 + 101 × 2000] Ω | 9.4010 µA |
| IC | 100 × 9.4010 µA | **0.94010 mA** |
| IE | 101 × 9.4010 µA | 0.94950 mA |
| VE | 0.94950 mA × 2 kΩ | 1.8990 V |
| VC | 12 − 0.94010 mA × 2.2 kΩ | 9.93178 V |
| VCE | 9.93178 − 1.8990 | **8.03278 V** |

**ทำนายก่อนรัน A4:** IC ต้อง **ลดลง** จาก A3 เพราะ RE อยู่ในตัวส่วนของ IB
(RB + (β+1)RE) เมื่อ RE เพิ่มจาก 1 kΩ เป็น 2 kΩ ตัวส่วนเพิ่ม IB จึงลด
และ IC = β·IB ลดตาม (ทำนาย 1.0263 → 0.9401 mA)

### A5 · อินพุตผิด

Fixed Bias, RB = 0 → ต้องแสดงข้อความให้แก้ RB, หน้าเว็บไม่ล้ม,
และต้องไม่แสดงผลรอบก่อนเป็นผลของรอบนี้

## 2. ผลที่อ่านจากหน้าเว็บจริง (รอบเดียว ไม่มีการแก้โค้ดระหว่างตรวจ)

| ID | วิธีตรวจ | อินพุต | ค่าคาดหมาย | ผลที่เห็น | สถานะ | หลักฐาน |
|---|---|---|---|---|---|---|
| A1 | OpenCode Browser | Divider · R1 100, R2 22, RE 1 kΩ | IC 1.2299 mA · VCE 8.0521 V | IC **1.230 mA** · VCE **8.052 V** (VB 1.942, VE 1.242, VC 9.294, IB 12.299 µA, IE 1.242 mA) | **PASS** | Snapshot + `docs/browser-a1-divider.jpeg` |
| A2 | OpenCode Browser | Fixed · RB 1000 kΩ | IC 1.1300 mA · VCE 9.5140 V | IC **1.130 mA** · VCE **9.514 V** (VB 0.700, VE 0.000, IB 11.300 µA, IE 1.141 mA) · ฟอร์มไม่มีช่อง RE | **PASS** | Snapshot; ช่อง RE ไม่ปรากฏจริง |
| A3 | OpenCode Browser | Emitter · RB 1000 kΩ, RE 1 kΩ | IC 1.02634 mA · VCE 8.70545 V | IC **1.026 mA** · VCE **8.705 V** (VB 1.737, VE 1.037, IB 10.263 µA, IE 1.037 mA) · มีช่อง RE | **PASS** | Snapshot |
| A4 | OpenCode Browser | Emitter · เหมือน A3 แต่ RE 2 kΩ | IC 0.94010 mA · VCE 8.03278 V (IC ลดจาก A3) | IC **0.940 mA** · VCE **8.033 V** (VE 1.899, VB 2.599) · โหมดยังเป็น Emitter | **PASS** | Snapshot; ค่าที่ส่งจริง `re=2`, `mode=emitter` |
| A5 | OpenCode Browser | Fixed · RB 0 | มีข้อความให้แก้ RB, ไม่มีผลลัพธ์, ไม่ล้ม | ข้อความ **"RB ต้องมากกว่าศูนย์ (kΩ)"**, `Input rejected`, ไม่มีตารางผลลัพธ์, หน้าเว็บปกติ | **PASS** | Snapshot + `docs/browser-a5-fixed-rb0.jpeg` |

ทุกรอบอ่านค่าจากหน้าผลลัพธ์ที่เพิ่งแสดงหลังส่งฟอร์ม ไม่ได้ใช้ผลรอบก่อน
และไม่มีการแก้ไฟล์โปรแกรมก่อนส่งรายงานรอบแรก จึงไม่มีรอบ "ก่อน–หลัง"

### วิธีตรวจ

- **Playwright MCP: NOT RUN** — เครื่องนี้ไม่มี `node`/`npx` ใน PATH
  (`node --version` / `npx --version` เรียกไม่พบ) จึงเปิด MCP server ไม่ได้
- **ใช้แทน:** OpenCode Browser tool ในตัวแอป (Chromium ของ OpenCode Desktop)
  เปิด `http://127.0.0.1:5050/` เลือกโหมดด้วย `<select name="mode">` + ปุ่ม
  `Load form`, กรอกช่องด้วย `fill_form`, กด `Calculate DC Bias` แล้วอ่าน
  Snapshot/ข้อความจริงจากหน้าเว็บ
- ใช้พอร์ต **5050** เพราะพอร์ต 5000 มี Flask ของ Lab 02 ค้างอยู่ก่อนแล้ว

## 3. เส้นทางข้อมูลของ RE (A3 → A4)

`templates/index.html` ช่อง `name="re"` → `app.py` `POST /calculate`
อ่าน `request.form` เฉพาะ field ของโหมด (`FIELDS["emitter"]`) →
`kohm_to_ohm(form["re"], "RE")` แปลง kΩ เป็น Ω ครั้งเดียวที่ขอบ HTTP →
`calculate_emitter_bias(..., re=2000, ...)` →
`IB = (VCC − VBE) / (RB + (β+1)·RE)` → `IC = β·IB` →
dict `{ic, vce, ...}` → template แสดง `IC` เป็น mA และ `VCE` เป็น V
ดังนั้นการเปลี่ยน RE ย่อมเปลี่ยน IB, IC และ VCE ตามที่เห็นใน A4

## 4. Automated tests (regression ของ Lab 02)

```powershell
# จากรากของ repository นี้
python -m unittest discover -s tests -v
# หรือจาก root ของ repo รวม: python -m unittest discover -s lab03/tests -t lab03 -v
```

ผลจริง: **24 tests, OK** — ชุดทดสอบเดิมของ Lab 02 ยังผ่านทั้งหมด
(Divider ไม่เสีย) ไม่ได้เพิ่ม unittest ใหม่ตามขอบเขตใบงาน

## 5. AI ช่วยอะไร และนักศึกษาตรวจอะไร

| ส่วน | AI (OpenCode) ทำ | นักศึกษาตรวจ |
|---|---|---|
| `dc_bias.py` | เขียน `calculate_fixed_bias`, `calculate_emitter_bias`, แยก `_operating_point` / `_region` | เทียบสมการกับ Engineering Electronics, ตรวจว่าตัวส่วนมี (β+1)RE เฉพาะโหมดที่มี RE, ตรวจหน่วย Ω/A |
| `app.py` | เลือกฟังก์ชันด้วย `if/elif` ตาม `mode`, แปลงหน่วย, ตรวจอินพุตตามโหมด | ตรวจว่าโหมดไม่รู้จักไม่ถูกเดาเป็น Divider, ตรวจว่าแปลงหน่วยที่จุดเดียว |
| `templates/index.html` | เพิ่ม select โหมด, ช่องตามโหมด, schematic ตามโหมด | ตรวจว่าช่อง RE หายใน Fixed, ผล/error ระบุโหมด, A5 ไม่โชว์ผลเก่า |
| Validation | รัน A1–A5 ผ่าน Browser และบันทึกผล | คำนวณมือ A2–A4 ก่อนรัน, ยืนยันค่าที่เห็นและสถานะ |

## 6. หมายเหตุ

- ผลนอก Forward-Active เป็นเพียงค่าจากสมการ ไม่ใช่ผลจำลองที่แม่นยำ
- ตัวเลขบนหน้าเว็บปัด 3 ตำแหน่ง การตรวจละเอียดใช้ค่าอ้างอิงก่อนปัดเศษ
- ค่าอ้างอิงในตาราง A3/A4 คำนวณใหม่จากสมการใบงาน ไม่ได้คัดลอกจากเอาต์พุตโปรแกรม

---

## 7. Lab 04 — BJT CE Amplifier Simulator (B1–B8)

### สภาพแวดล้อมจริงที่ใช้ตรวจ

- Flask 3.1.3 ใน `.venv` (Python 3.10.11), server `http://127.0.0.1:5050/`
- ngspice **41** (`ngspice_con.exe`) ที่
  `C:\Users\B6806477\AppData\Local\ngspice-conda\app\Library\bin\ngspice_con.exe`
  ถูกส่งผ่านตัวแปร `NGSPICE_BINARY`
- BJT model ที่ใช้จริง: **LAB_NPN** — Gummel-Poon NPN แบบทั่วไปสำหรับการสอน
  (**ไม่ใช่ part number เชิงพาณิชย์**) พารามิเตอร์ทั้งหมดพิมพ์อยู่ใน netlist
  ที่แบ่งปันในหน้าเว็บ จึงทำซ้ำได้
- หน่วยบนฟอร์ม: R เป็น kΩ, C เป็น µF, VCC เป็น V, source เป็น mV peak,
  frequency เป็น kHz, duration เป็น ms — แอปแปลงเป็น SI ก่อนส่งเข้า ngspice
- วิธีตรวจ browser: **OpenCode Browser tool (Chromium จริง)** ใช้
  `navigate → snapshot → fill → evaluate(requestSubmit) → read DOM → screenshot`
  เนื่องจาก `browser.click` ค้างที่ `DOM.getNodeForLocation` แม้ปุ่มอยู่ใน viewport
  และ `elementFromPoint` ชี้ที่ปุ่ม การส่งฟอร์มจึงทำผ่าน `requestSubmit()` บนฟอร์มจริง
  ของหน้าเว็บ ไม่ใช่การจำลองผลใน JavaScript
- **Playwright MCP: NOT RUN** — เครื่องนี้ไม่มี `node`/`npx` ใน PATH จึงเปิด MCP
  server ไม่ได้ ผลด้านล่างเป็น OpenCode Browser ตามข้อ fallback ของใบงาน ไม่ได้
  อ้างว่าเป็นผล Playwright MCP
- ไม่ได้แก้โค้ดระหว่างรอบ B1–B8 ที่บันทึกไว้ในตารางนี้

### ผล B1–B8

| Case | Method | Input | Expected / Reference | Observed (อ่านจากหน้าเว็บจริง) | Evidence | Status |
|---|---|---|---|---|---|---|
| B1 · Regression | OpenCode Browser, ส่งฟอร์ม Lab 3 ทีละโหมด | Divider: VCC 12, R1 100, R2 22, RC 2.2, RE 1 kΩ, β 100, VBE 0.70; Fixed/Emitter: RB 1000 kΩ | Divider IC 1.2299 mA / VCE 8.0521 V; Fixed 1.1300 mA / 9.5140 V; Emitter 1.0263 mA / 8.7055 V (จาก `docs/validation.md` §1) | Divider **IC 1.230 mA, VCE 8.052 V** (VB 1.942, VE 1.242); Fixed **IC 1.130 mA, VCE 9.514 V**; Emitter **IC 1.026 mA, VCE 8.705 V** (VB 1.737, VE 1.037) ทุกอันระบุ `Mode:` ตรงโหมด | Snapshot ข้อความจริง + `docs/browser-b1-emitter.png` | **PASS** |
| B2 · DC SPICE | OpenCode Browser, `/simulate` → DC → requestSubmit | CE reference: VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ, RL 10 kΩ, Cin/Cout 10 µF | ต้องเห็น VB/VE/VC/VCE/IC จาก ngspice พร้อม model และ run status ไม่ใช่ค่าสมการ Lab 3 | `Run status: SUCCESS`, `ngspice 41 · model LAB_NPN · DC`; **VB 1.9454 V, VE 1.2857 V, VC 9.1980 V, VBE 0.6597 V, VCE 7.9123 V, IB 12.1229 µA, IC 1.2743 mA, IE 1.2864 mA** ตาราง Lab 3 อยู่แยกภายใต้หัวข้อ “Lab 3 analytical reference — not SPICE” | `docs/browser-b2-dc.png`; log จริง: `v(base)=1.945436e+00`, `v(emitter)=1.285739e+00`, `v(collector)=9.198032e+00`, `@q1[ib]=1.212290e-05`, `@q1[ic]=1.274278e-03` | **PASS** |
| B3 · Change RE | เปลี่ยนเฉพาะ RE แล้วรัน DC ซ้ำ | เดิม RE 1 kΩ → เปลี่ยนเป็น **2 kΩ** (browser `fill`) | operating point ต้องเปลี่ยนตาม ngspice ไม่ใช่ค่าค้าง | IC **1.2743 → 0.6944 mA**, VB **1.9454 → 2.0456 V**, VE **1.2857 → 1.4019 V**, VC **9.1980 → 10.4723 V**, VCE **7.9123 → 9.0704 V** | `docs/browser-b3-re2-dc.png` และข้อความก่อน/หลังที่อ่านจาก DOM | **PASS** |
| B4 · AC | OpenCode Browser, `/simulate` → AC → requestSubmit | sweep 1 Hz–10 MHz, source 10 mV @ 1 kHz | Bode plot แกน frequency/gain/phase พร้อมหน่วย และค่าจาก run จริง | `Run status: SUCCESS`; **141 points**, peak **4.86 dB**, gain @ 1e+03 Hz **4.86 dB**, phase **−179.9°**, lower −3 dB **1.31 Hz**, upper **4.24e+06 Hz**; 2 SVG, trace ละ 141 จุด; แกน `Frequency (Hz, log scale)`, `Gain (dB)`, `Phase (degrees)` | `docs/browser-b4-ac.png`; DOM: `polyline.trace` 2 เส้น × 141 จุด | **PASS** |
| B5 · Transient | OpenCode Browser, `/simulate` → TRAN → requestSubmit | Amplitude **10 mV peak**, frequency **1 kHz**, duration 5 ms | เห็น Vin/Vout ตามเวลา มีแกน time/voltage และสัญญาณกลับเฟส | `Run status: SUCCESS`; **258 points**, Vin p-p **19.993 mV**, Vout p-p **0.035 V**, phase relation **inverted (near 180 deg)**; แกน `Time (s)` / `Voltage (V)`; trace ละ 258 จุด | `docs/browser-b5-tran-10mv-1khz.png` | **PASS** |
| B6 · Change Source | `fill` amplitude/frequency แล้วรัน TRAN ซ้ำ | 10 mV @ 1 kHz → **20 mV @ 2 kHz** | waveform ต้องเปลี่ยน ไม่ใช่กราฟ hard-code | netlist รอบใหม่คือ `SIN(0 0.02 2000)`; points **258 → 508**, Vin p-p **19.993 → 39.985 mV**, Vout p-p **0.035 → 0.070 V**; พิกัด trace ตัวอย่างเปลี่ยนจาก `66.00,45.11` เป็น `66.00,46.20` | `docs/browser-b6-tran-20mv-2khz.png` + netlist/trace ที่อ่านจาก DOM | **PASS** |
| B7 · Invalid / Fail | เคยรันสำเร็จแล้ว `fill` RE=0 แล้วส่งใหม่ | RE **0** (หน่วย kΩ) | error ภาษาไทย, ไม่ค้างผลสำเร็จ, ไม่แสดง netlist/กราฟรอบก่อน | ข้อความ **“RE ต้องมากกว่าศูนย์”**, `Run rejected`, `No stale or previous results are shown.`; ไม่มี `Run status: SUCCESS`, ไม่มีตาราง “DC operating point from ngspice”, ไม่มี netlist | `docs/browser-b7-invalid-re.png` | **PASS** |
| B8 · UI | เปิดผล AC ใน viewport 800×609 และใน iframe กว้าง 390 CSS px | desktop + phone-width (390 px) แล้วสลับ workspace/analysis | กราฟ/หน่วย/ปุ่มอ่านได้ ไม่ตัดเนื้อหาสำคัญ | desktop `innerWidth=800, scrollWidth=785`; 390 px `innerWidth=390, scrollWidth=375` (ไม่มี horizontal overflow); ทั้งสองเห็น 2 SVG, แกนพร้อมหน่วย และปุ่ม `Run ngspice AC` | `docs/browser-b8-desktop.png`, `docs/browser-b8-mobile-390px.png` | **PASS** (desktop) / **PASS** (390 px iframe emulation); native window resize **NOT RUN** |

### หลักฐานว่ากราฟไม่ใช่ mock data

- ทุกกราฟสร้างจาก parsed output ของ ngspice รอบปัจจุบันเท่านั้น (`charts.py`
  ได้ polyline จาก list ใน `spice_engine.run_analysis` ไม่มีการอ่านค่าคงที่)
- B4: AC trace มี 141 จุดตรงตาม `Points` ใน summary ที่ parser อ่านจาก log
- B5/B6: เมื่อเปลี่ยน source netlist เปลี่ยนจาก `SIN(0 0.01 1000)` เป็น
  `SIN(0 0.02 2000)` และจำนวนจุด/ค่าพิกัด/peak-to-peak เปลี่ยนตาม
- B7: เมื่อ validation ปฏิเสธ input หน้าเว็บไม่แสดง success/netlist/ตารางเก่า
  จึงไม่มีการสลับผลสำเร็จปลอม

### ข้อจำกัดที่ยังต้องบอกตามความจริง

- **LAB_NPN** เป็นโมเดลสอน ไม่ใช่ทรานซิสเตอร์จริง ดังนั้นค่ากระแส/AC gain
  ไม่ควรเทียบกับ 2N3904 หรือ device อื่นโดยตรง
-  phase ใน `.ac` ถูกแปลงจาก `vp()` ของ ngspice (RAD) เป็นองศาก่อน plot
  และแสดงหน่วย `Phase (degrees)` อย่างชัดเจน
- B8 ใช้ iframe 390 CSS px เพื่อบังคับ media query แบบมือถือ เพราะ
  `window.resizeTo(390, 844)` ถูก browser tool เพิกเฉย (`innerWidth` คง 800)
  จึงยังไม่ได้ทดสอบการย่อหน้าต่าง Chromium จริง
- `browser.click` ของ OpenCode Browser tool ล้มเหลวด้วย
  `DOM.getNodeForLocation`; ปุ่มยังอยู่ใน DOM และ `elementFromPoint` ชี้ถูกต้อง
  จึงใช้ `requestSubmit()` บนฟอร์มจริงแทน และบันทึกวิธีนี้ไว้ข้างบน

### Automated tests และคำสั่งทำซ้ำ

```powershell
$env:NGSPICE_BINARY = 'C:\Users\B6806477\AppData\Local\ngspice-conda\app\Library\bin\ngspice_con.exe'
C:\Users\B6806477\Desktop\Lab-3\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

ผลจริงรอบล่าสุด: **Ran 50 tests ... OK** (รวม 12 tests เดิม Lab 3,
tests ของ `spice_engine.py`, และ web simulator tests; มี integration test
ที่รัน ngspice จริง 3 analysis เมื่อพบ engine)

### AI ช่วยอะไร / นักศึกษาตรวจอะไร (Lab 04)

| ส่วน | AI (OpenCode) ทำ | นักศึกษาตรวจ |
|---|---|---|
| `spice_engine.py` | เขียน validation SI, netlist `.op/.ac/.tran`, `subprocess.run([...], shell=False)`, parser และ error ภาษาไทย | ตรวจว่าข้อความ input ไม่หลุดเข้า netlist, timeout/nonzero/empty/parse fail ไม่โชว์ผลเก่า, ตรวจ log จริง `/simulate` |
| `charts.py` + template | สร้าง SVG จาก parsed data พร้อมแกน/หน่วย และแยกตาราง Lab 3 reference | ตรวจว่าเปลี่ยน amplitude/frequency แล้ว trace เปลี่ยนจริง (B6) และ phase มีหน่วยองศา |
| README/validation | รวมคำสั่งติดตั้ง ngspice แบบพกพา, `NGSPICE_BINARY`, ผล B1–B8 และข้อจำกัด | ทดสอบรัน server/ngspice ซ้ำ, เทียบค่า DC กับ log, ยืนยันว่า Playwright MCP ไม่ได้รันจึงไม่รายงานเป็น PASS |

