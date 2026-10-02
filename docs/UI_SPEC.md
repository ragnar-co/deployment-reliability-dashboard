# UI_SPEC — Deployment Reliability Dashboard

## Page Inventory
มี **1 หน้า** (server-rendered) และ endpoint ฟอร์ม 1 รายการ

| Route | Page | Method | คำอธิบาย |
|---|---|---|---|
| `/` | Dashboard | GET | แสดงส่วน Import, ตัวกรองบริการ, ตัวเลขรวม, ตารางแยกบริการ, รายการ failed deployment; query: `service`, `environment` (P1), `page` (ดู API_SPEC.md) |
| `/upload` | (ไม่มีหน้าของตัวเอง) | POST | รับฟอร์มอัปโหลด CSV ตอบ redirect 303 ไป `/?notice=…` เสมอ ไม่ว่าสำเร็จหรือถูกปฏิเสธ หน้า `/` แสดงข้อความผลนำเข้าหรือกล่อง error **หนึ่งครั้ง** แล้วหายเมื่อกด refresh (กด refresh ไม่ส่งไฟล์ซ้ำ) |

## User Flow Diagrams
```mermaid
flowchart TD
  A[เปิด Dashboard] --> B{มีข้อมูล?}
  B -- ไม่ --> C[ข้อความ 'No data yet' + ฟอร์มอัปโหลด]
  B -- ใช่ --> D[ตัวเลขรวม + ตารางแยกบริการ เรียงจาก success rate ต่ำสุด]
  C --> E[เลือกไฟล์ CSV + อัปโหลด]
  D --> E
  E --> F{validation ผ่าน?}
  F -- ผ่าน --> G[ข้อความสำเร็จ + ข้อมูลทุกบริการ]
  F -- ไม่ผ่าน --> H[กล่อง error ระบุแถวและเหตุผล + 'nothing was saved']
  D --> I[เลือกบริการ]
  I --> J[ตัวเลขและรายการล้มเหลวของบริการนั้น + error ต้นฉบับ]
```

### Critical Path Trace
เฉพาะ CP-ID ที่ PERSONAS.md กำหนด `Delivery = UI` (CP-05 และ CP-06 เป็น `system` ไม่ปรากฏที่นี่)

| CP-ID | Route | ขั้นตอนบน UI |
|---|---|---|
| CP-01 | `/upload` → `/` | เลือกไฟล์ถูกต้อง → อัปโหลด → เห็นข้อความสำเร็จและข้อมูลทุกบริการ |
| CP-02 | `/` (`?service=`) | เลือกบริการจาก dropdown → ตัวเลขและรายการล้มเหลวเหลือเฉพาะบริการนั้น พร้อมข้อความ error |
| CP-03 | `/` | ตารางแยกบริการเรียงจาก success rate ต่ำสุด; แถวแรกคือจุดเริ่มตรวจสอบ |
| CP-04 | `/upload` | ไฟล์ผิดกติกา หรือไฟล์เกิน 10 MB → กล่อง error (role=alert) ระบุแถวและเหตุผล (หรือข้อความขนาดไฟล์) ข้อมูลเดิมไม่เปลี่ยน |

## Component Hierarchy
```
Dashboard (/)
├─ Masthead              ชื่อแอป + ImportForm (ไฟล์, ปุ่ม Upload, ข้อความ "CSV, max 10 MB")
├─ UploadSizeWarning     เตือนทันทีที่เลือกไฟล์ใหญ่เกินขีดจำกัด (role=alert) และปิดปุ่ม Upload
├─ StatusMessage         สำเร็จ (role=status) / ปฏิเสธ (role=alert, รายการเหตุผล)
├─ Lead                  ประโยคนำ: "Check <service> first" (บริการอันดับ 1 ของมุมมองปัจจุบัน) พร้อม success rate และจำนวนที่ล้มเหลว;
│                        เมื่อเลือกบริการ = ชื่อบริการ + success rate; ไม่มีข้อมูลตรงตัวกรอง = ข้อความบอกให้ล้างตัวกรอง;
│                        มีหมายเหตุเสมอว่าเป็นการจัดลำดับ ไม่ได้ระบุสาเหตุ
├─ Figures               แถบตัวเลขรวม (dl): Deployments · Successful · Failed · Success rate · Avg successful duration (s)
├─ ServiceFilter         <select> บริการ + environment (รายการเลือกมาจากฐานข้อมูลทั้งหมด ไม่ผูกกับ filter ที่เลือกอยู่; ส่งฟอร์มเมื่อเปลี่ยน)
├─ ServiceTable          # (อันดับ) · Service · แถบสัดส่วน · Success rate · Failed · Deployments · Avg successful duration (s)
└─ FailureTable          Deployment · Service · Env · Date · Duration (s) · Error message  (+ Pagination)
```
แถบสัดส่วนในแถวของ ServiceTable: ส่วนเขียว = deployment สำเร็จ ส่วนแดง = ล้มเหลว ความยาวตามสัดส่วนจริง เป็นเพียงภาพเสริม (`aria-hidden`) ค่าตัวเลข % พิมพ์อยู่ในเซลล์ถัดไปเสมอ จึงไม่ใช้สีเป็นสัญญาณเดียว แอนิเมชันเดียวของหน้าคือแถบขยายเมื่อโหลด และปิดเมื่อผู้ใช้ตั้ง `prefers-reduced-motion`; หมายเลขอันดับเป็นข้อมูลจริง (ลำดับจาก success rate ต่ำสุด) ไม่ใช่ตัวตกแต่ง
```

## State Management Plan
ไม่มี state ฝั่ง client สถานะอยู่ใน URL และฐานข้อมูล:
- `service` (query) ว่าง = ทุกบริการ; ค่าที่ไม่มีอยู่แสดงผลศูนย์แถว ไม่ error
- `page` (query) หน้าของรายการล้มเหลว ขนาดหน้า = 100 แถว (`offset = (page − 1) × 100`); `page` ที่ไม่ใช่ตัวเลขหรือ < 1 ถือเป็น 1; เกินหน้าสุดท้ายแสดงรายการว่างพร้อมลิงก์ Prev; ควบคุมด้วยลิงก์ Prev/Next และข้อความ "Page N / M"
- ผลนำเข้าอยู่ในการตอบกลับของ POST เท่านั้น (ไม่มี session)
- ตัวเลขทุกค่าอ่านจาก SQLite ต่อ request (TC-05)

## Responsive Breakpoints
| Breakpoint | ความกว้าง | พฤติกรรม |
|---|---|---|
| mobile | < 900px | แถบตัวเลข 2 คอลัมน์; ตารางเลื่อนแนวนอนในกรอบของตัวเอง ไม่ให้หน้าล้นจอ |
| desktop | ≥ 900px | แถบตัวเลข 5 ช่องในแถวเดียว; ตารางเต็มความกว้าง (max 1120px) |

## Design Tokens
| Token | Light | Dark | หมายเหตุ |
|---|---|---|---|
| `--paper` | #F2F4F3 | #101619 | พื้นหลังหน้า |
| `--surface` | #FFFFFF | #172026 | พื้นตาราง/แถบตัวเลข |
| `--ink` | #17232B | #E4EAED | ข้อความ |
| `--muted` | #54626B | #9AA8B1 | ข้อความรอง |
| `--line` | #D5DCDF | #2A363D | เส้นแบ่ง |
| `--alarm` | #B3261E | #F28B82 | ส่วนที่ล้มเหลว; success rate < 85% |
| `--warn` | #8A5200 | #E3A63C | 85% ≤ rate < 90% |
| `--good` | #1B6E5F | #5CC2AE | ส่วนที่สำเร็จ; rate ≥ 90% |
| `--accent` | #1F4E79 | #7FB2E5 | ลิงก์/พื้นปุ่ม |
| `--on-accent` | #FFFFFF | #0E1A22 | ข้อความบนปุ่ม |

**การเตือนขนาดไฟล์ (NFR-03, TC-07):** ฟอร์มมี `data-max-bytes` ตามค่า `MAX_UPLOAD_BYTES` (ไม่ hard-code 10 MB ใน JavaScript) เมื่อผู้ใช้เลือกไฟล์ที่ `file.size` เกิน JavaScript ต้องแสดงข้อความ `File is X.X MB; the maximum is 10 MB. Nothing was uploaded.` ในกล่อง `role="alert"` ทันที และปิดปุ่ม Upload ไว้จนกว่าจะเลือกไฟล์ใหม่ที่ไม่เกิน ถ้า JavaScript ปิดอยู่หรือถูกเลี่ยง server ปฏิเสธด้วย `FILE_TOO_LARGE` 413 และแสดงข้อความ `File exceeds the maximum of 10 MB.` ในกล่อง error ของหน้า (ไม่มีขนาดจริง เพราะ server หยุดอ่านทันที; CP-04 ครอบคลุมเส้นทางนี้) ตัวเลข "10 MB" ในข้อความมาจากค่าตั้งค่า ไม่ใช่ข้อความตายตัว

ข้อความหลักของ UI (เจ้าของ copy): ว่าง = "No data yet. Upload a deployment-history CSV to begin."; สำเร็จ = "Imported N deployments (S successful, F failed)."; ปฏิเสธ = "Import rejected — nothing was saved." ตามด้วยรายการเหตุผล; ค่า null ของ rate/duration แสดง "–"; ปุ่ม "Upload"
โหมดสว่าง/มืดเลือกตาม `prefers-color-scheme` ของเบราว์เซอร์ (ไม่มีปุ่มสลับ)

Contrast ที่คำนวณแล้ว (ข้อความเทียบกับ `--surface`; ข้อความปุ่มเทียบกับ `--accent`): สว่าง ink 16.01, muted 6.29, alarm 6.54, warn 6.39, good 6.10, accent 8.66, ปุ่ม 8.66; มืด ink 13.60, muted 6.77, alarm 6.92, warn 7.70, good 7.70, accent 7.40, ปุ่ม 7.90 — ทุกค่า ≥ 4.5:1 (แถบเขียว/แดงเป็นภาพเสริม ไม่ได้อาศัยความต่างระหว่างสองสีเพราะมีตัวเลข %)

Typography: system font stack (ไม่โหลดฟอนต์ภายนอก) ขนาดฐาน 15px; หัวข้อนำหนักตัวหนาและชิดแน่น; ตัวเลขใช้ tabular-nums; รหัส deployment และข้อความ error ใช้ monospace เพราะเป็นข้อมูลจาก log จริง

เกณฑ์สี 85% และ 90% เป็น **ค่าสอนสำหรับตัวอย่าง (illustrative)** ไม่ใช่มาตรฐานอุตสาหกรรม ใช้เป็นค่าคงที่ในโค้ดเพียงเพื่อแสดงผลของ MVP โดยไม่กระทบตัวเลข; ค่าที่ calibrate แล้ว = `null` เจ้าของ Engineering Lead (ความเสี่ยงกับ Phase 3 เมื่อเกณฑ์จริงต่างจากนี้)

## Accessibility Guidelines
- เป้าหมาย: **WCAG 2.1 ระดับ AA**
- Contrast: ข้อความปกติ ≥ **4.5:1**; ข้อความใหญ่และองค์ประกอบ UI ≥ **3:1** ทั้งธีมสว่างและมืด
- ห้ามใช้สีอย่างเดียวบอกสถานะ: แสดงตัวเลข % ควบคู่เสมอ
- Form มี `<label>`; ข้อความสำเร็จ `role="status"`, ข้อผิดพลาด `role="alert"`; ตารางใช้ `<th>` และ `<thead>`
- ใช้งานด้วยคีย์บอร์ดได้ทั้งหมด; dropdown มี `<noscript>` ปุ่ม Apply สำรอง

## i18n & Content Strategy
- Locale ที่รองรับ: `en` (ค่าเริ่มต้น) — fallback: `en`
- ข้อความ UI เป็นภาษาอังกฤษ เพราะผู้ใช้เป็นทีม DevOps ที่คุ้นศัพท์เทคนิค ข้อความ error จากข้อมูลแสดงตามต้นฉบับโดยไม่แปล
- ไม่รองรับหลาย locale ใน MVP; `th` เป็นตัวเลือก Phase 3 (fallback: `en`)
- วันที่แสดง ISO `YYYY-MM-DD`; ระยะเวลาแสดงเป็นวินาที
