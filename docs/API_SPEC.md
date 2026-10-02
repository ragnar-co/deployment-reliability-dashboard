# API_SPEC — Deployment Reliability Dashboard

## Endpoint List
มี **6 operations** (ไม่มี endpoint metrics: ตัวชี้วัดมาจาก log ตาม ARCHITECTURE.md) ทุกตัวไม่มี authentication (SECURITY.md) `required_role` = `internal_user`

| Method | Path | auth_required | required_role | คำอธิบาย | error_codes |
|---|---|---|---|---|---|
| GET | `/` | false | `internal_user` | หน้า Dashboard (HTML); query: `service`, `environment` (P1), `page` (≥ 1, ค่าที่น้อยกว่า 1 หรือไม่ใช่ตัวเลขถือเป็น 1) | – |
| POST | `/upload` | false | `internal_user` | นำเข้า CSV จากฟอร์ม **ตอบ 303 redirect เสมอ** (ทั้งสำเร็จและถูกปฏิเสธ) ไป `/?notice=<token>` (Post/Redirect/Get เพื่อให้กด refresh ไม่ส่งไฟล์ซ้ำ) ข้อความผล/เหตุผลที่ถูกปฏิเสธเก็บในหน่วยความจำของแอป อ่านได้ **ครั้งเดียว** (หมดอายุ 120 วินาที, สูงสุด 200 รายการ) ดังนั้น refresh แล้วข้อความหาย token ที่ไม่รู้จักถูกเมิน รหัสข้อผิดพลาดและ HTTP status ตามตาราง Error Codes ใช้กับ `/api/import` เท่านั้น ส่วนหน้าเว็บแสดงข้อความเหตุผลเดียวกัน | `INVALID_FILE`, `VALIDATION_FAILED`, `DUPLICATE_FILE`, `DUPLICATE_DEPLOYMENT`, `FILE_TOO_LARGE`, `IMPORT_BUSY` |
| POST | `/api/import` | false | `internal_user` | นำเข้า CSV ตอบ JSON | เหมือน `/upload` ยกเว้นไม่มีการเรนเดอร์ HTML |
| GET | `/api/services` | false | `internal_user` | ตัวเลขรวมและแยกตามบริการ | `INVALID_PARAMETER` |
| GET | `/api/failures` | false | `internal_user` | รายการ failed deployment | `INVALID_PARAMETER` |
| GET | `/health` | false | ไม่มี (เปิดให้เรียกได้โดยไม่ต้องมีตัวตน; ไม่ใช่ `internal_user`) | health check สำหรับ Coolify | – |

ไม่มี endpoint ใดคืนข้อมูลนอกเหนือจาก `deployments` และ `import_batches` (DATA_MODEL.md)

## Request and Response Schema

### `POST /upload`, `POST /api/import` — Request
`multipart/form-data`

| field | type | allowed_values | nullable | required |
|---|---|---|---|---|
| `file` | file (UTF-8 CSV) | ต้องมี 7 คอลัมน์: `deployment_id`, `service_name`, `status`, `duration_seconds`, `error_message`, `deployment_date`, `environment` | false | true |

**รูปแบบไฟล์ (เจ้าของ):**
- UTF-8, ตัด BOM ถ้ามี; ตัวคั่น `,` ตามมาตรฐาน CSV (RFC 4180: เครื่องหมายคำพูดและขึ้นบรรทัดใหม่ได้ทั้ง LF/CRLF)
- Header ต้องมี **ครบ 7 คอลัมน์เป๊ะ** ชื่อเป็นตัวพิมพ์เล็กตามนี้ ลำดับใดก็ได้ **คอลัมน์เกินหรือชื่อซ้ำ = ปฏิเสธทั้งไฟล์** ด้วย `INVALID_FILE` (LC-01)
- ตัดช่องว่างหัวท้ายของทุกค่าก่อนตรวจ; `status` เป็นตัวพิมพ์เล็กเท่านั้น (`Success` ไม่ผ่าน)
- หมายเลขแถวใน error = **เลขบรรทัดของข้อมูลแบบ 1-based โดยนับ header เป็นบรรทัด 1** (แถวข้อมูลแรก = Row 2) รูปแบบข้อความ `Row N: <เหตุผล>` เรียงตามลำดับในไฟล์ และคืนเฉพาะ 20 รายการแรก

**ลำดับการตรวจ (หยุดที่ข้อแรกที่ล้มเหลว):**
1. ขนาดไฟล์เกินขีดจำกัดที่ตั้งไว้ → `FILE_TOO_LARGE`
2. ไม่ใช่ UTF-8, header ผิด, ไม่มีแถวข้อมูล → `INVALID_FILE`
3. SHA-256 ตรงกับ batch เดิม → `DUPLICATE_FILE`
4. กติการะดับแถว (รวม `deployment_id` ซ้ำภายในไฟล์เดียวกัน) → `VALIDATION_FAILED`
5. `deployment_id` ที่มีอยู่แล้วในฐานข้อมูล → `DUPLICATE_DEPLOYMENT`
6. ฐานข้อมูลถูกล็อกโดยการนำเข้าอื่น → `IMPORT_BUSY`

กติการะดับแถว (เจ้าของ: PRD.md FR-02 / CONSTRAINTS.md TC-03) ผิดข้อใดข้อหนึ่ง = ปฏิเสธทั้งไฟล์

### `POST /api/import` — Response 200
| field | type | allowed_values | nullable | required |
|---|---|---|---|---|
| `batch_id` | integer | ≥ 1 | false | true |
| `rows` | integer | ≥ 1 | false | true |
| `successful_deployments` | integer | 0…rows (จำนวนแถวที่ `status = success`) | false | true |
| `failed_deployments` | integer | 0…rows (จำนวนแถวที่ `status = failed` ไม่ใช่จำนวนการนำเข้าที่ล้มเหลว) | false | true |

### Error Response (ทุก endpoint JSON)
| field | type | allowed_values | nullable | required |
|---|---|---|---|---|
| `code` | string | ค่าของ `application_error_code` | false | true |
| `errors` | array of string | ข้อความ ระบุแถว (สูงสุด 20 รายการ) | false | true |

### `GET /api/services`
Query: `service` (string, optional, ว่าง = ทุกบริการ), `environment` (string, optional, P1/F-10)

เมื่อระบุ `service` ทั้ง `overall` และ `services[]` ถูกกรองเหลือบริการนั้น (รายการตัวเลือกใน dropdown มาจากฐานข้อมูลโดยตรง ไม่ผูกกับ endpoint นี้) `service` ที่ไม่มีอยู่ = 200 พร้อม `total = 0` และ `services = []` ไม่ใช่ error การเรียงของ `services[]`: `success_rate` น้อยไปมาก → `failures` มากไปน้อย → `service_name` ตามตัวอักษร การปัดเศษ = half-up (ไม่ใช่ banker's rounding)

| field | type | allowed_values | nullable | required |
|---|---|---|---|---|
| `overall.total` | integer | ≥ 0 | false | true |
| `overall.successes` | integer | ≥ 0 | false | true |
| `overall.failures` | integer | ≥ 0 | false | true |
| `overall.success_rate` | number | 0–100 ปัด 2 ตำแหน่ง | true (เมื่อ total = 0) | true |
| `overall.avg_success_seconds` | number | > 0 ปัด 2 ตำแหน่ง (half-up) | true (เมื่อไม่มี success) | true |
| `services[]` | array of object | ฟิลด์: `service_name`, `total`, `successes`, `failures`, `success_rate`, `avg_success_seconds` (ชนิดเดียวกับ overall) เรียงจาก `success_rate` ต่ำสุด | false | true |

### `GET /api/failures`
Query: `service` (string, optional), `environment` (string, optional, P1/F-10), `limit` (integer, 1–1000, default 100), `offset` (integer, ≥ 0, default 0) — ค่าที่อยู่นอกช่วงหรือไม่ใช่จำนวนเต็ม = `INVALID_PARAMETER` 422 หน้าเว็บแปลง `page` เป็น `offset = (page − 1) × 100`, `limit = 100`

| field | type | allowed_values | nullable | required |
|---|---|---|---|---|
| `total` | integer | ≥ 0 | false | true |
| `items[].deployment_id` | string | – | false | true |
| `items[].service_name` | string | – | false | true |
| `items[].environment` | string | – | false | true |
| `items[].deployment_date` | string | `YYYY-MM-DD` | false | true |
| `items[].duration_seconds` | integer | > 0 | false | true |
| `items[].error_message` | string | ข้อความต้นฉบับ ไม่ว่าง | false | true |

เรียงใหม่สุดก่อน: `deployment_date` มากไปน้อย แล้ว `deployment_id` มากไปน้อย โดยเทียบเป็น **ข้อความ** (ไม่แปลงเป็นตัวเลข)

### `GET /health`
Response 200: `status` (string, `ok`, ไม่ nullable, required) เมื่อเปิดฐานข้อมูลไม่ได้ = 503 พร้อม `status = unavailable`

## Authentication
ไม่มี (SECURITY.md Authentication and Authorization) ทุก endpoint ต้องปกป้องด้วยเครือข่าย

## Error Codes
เจ้าของ enum `application_error_code`

| code | HTTP | เมื่อใด |
|---|---|---|
| `INVALID_FILE` | 422 | ไม่ใช่ UTF-8, คอลัมน์ขาด หรือไม่มีแถวข้อมูล |
| `VALIDATION_FAILED` | 422 | แถวใดแถวหนึ่งผิดกติกา (status/วันที่/duration/error_message) |
| `DUPLICATE_FILE` | 409 | checksum SHA-256 ตรงกับ batch ที่เคยนำเข้า ข้อความ: `This file was already imported on <YYYY-MM-DD> (batch #<id>, <rows> deployments). Nothing was changed.` เพื่อบอกผู้ใช้ว่าข้อมูลอยู่ครบแล้วและไม่ต้องทำอะไร |
| `DUPLICATE_DEPLOYMENT` | 409 | `deployment_id` มีอยู่แล้ว หรือซ้ำกันในไฟล์ |
| `FILE_TOO_LARGE` | 413 | ไฟล์ใหญ่กว่า `MAX_UPLOAD_BYTES` (ค่าเริ่มต้น 10 MiB (10,485,760 ไบต์), TC-07) แอปต้องหยุดอ่านเมื่อเกินขีดจำกัด ไม่ต้องรับไฟล์ทั้งก้อนเข้าหน่วยความจำ ข้อความจาก server: `File exceeds the maximum of 10 MB.` (server หยุดอ่านเมื่อเกิน จึงไม่ทราบขนาดจริง; ข้อความที่มีขนาดจริง `File is X.X MB; ...` แสดงโดย client ตาม UI_SPEC.md) |
| `INVALID_PARAMETER` | 422 | `limit`/`offset`/`page` ไม่ถูกต้องบน `/api/*` |
| `IMPORT_BUSY` | 503 | มีการนำเข้าอื่นถือการล็อกเขียนของ SQLite ลองใหม่ภายหลัง ไม่มีข้อมูลบางส่วน |

ทุกกรณี error ไม่มีการเขียนข้อมูลบางส่วน (TC-04) `/upload` แสดงข้อความเดียวกันบนหน้า Dashboard

## Rate Limiting
`null` — ไม่มีการ calibrate; เจ้าของ: DevOps Operator ความเสี่ยงบันทึกใน SECURITY.md THR-05

## Versioning Strategy
ยังไม่มี prefix เวอร์ชัน: `/api/*` เป็นเวอร์ชันเดียวสำหรับ Phase 1 การเปลี่ยนที่ทำให้ client เดิมพังต้องบันทึกใน PRD.md/API_SPEC.md ก่อน และเพิ่ม `/api/v2` ภายหลัง
