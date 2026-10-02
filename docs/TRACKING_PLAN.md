# TRACKING_PLAN — Deployment Reliability Dashboard

เอกสารนี้เป็นเจ้าของ enum `event_name` (product analytics) **MVP ไม่เก็บ analytics ใดๆ** จึงไม่มีค่าใน `event_name` นี่คือการตัดสินใจที่ตั้งใจ ไม่ใช่เอกสารที่ยังเขียนไม่เสร็จ: ผู้ใช้เป็นทีม DevOps ภายใน และไม่มีโจทย์ใดต้องวัดพฤติกรรมผู้ใช้ (PRD.md Goals ใช้เกณฑ์ที่ตรวจด้วย test ไม่ใช่ตัวชี้วัดการใช้งาน)

## Event Inventory
| event_name (analytics) | สถานะ |
|---|---|
| (ไม่มี) | ไม่ติดตามเหตุการณ์ผู้ใช้ใน Phase 1 |

ถ้า Phase 3 ต้องการวัดการใช้งาน (เช่น จำนวนการนำเข้า) ต้องเพิ่มรายการที่นี่ก่อน และทบทวน Consent & PDPA Gating ด้านล่าง

**แยกจาก application log:** แอปเขียน log แบบ structured เพื่อการปฏิบัติการ (ARCHITECTURE.md Observability) ซึ่งไม่ใช่ analytics และไม่ใช่ค่าของ `event_name` ชื่อเหตุการณ์ใน log (snake_case) คือ `request`, `import_accepted`, `import_rejected`

## Event Schema & Properties
ไม่มี analytics event จึงไม่มี schema สำหรับ analytics ส่วน schema ของ log (เจ้าของ ARCHITECTURE.md Observability อ้างถึงที่นี่เพื่อไม่ให้ซ้ำ):

| log event | ฟิลด์เพิ่มเติม (นอกเหนือจาก `ts`, `level`, `correlation_id`, `event`) |
|---|---|
| `request` | `method`, `path`, `status`, `ms` |
| `import_accepted` | `batch_id`, `rows` |
| `import_rejected` | `code` (ค่าของ `application_error_code`), `error_count` |

ห้ามใส่เนื้อหาแถวข้อมูลหรือข้อความ error ของ CSV ลงใน log (SECURITY.md Audit Logging Requirements)

## Identity & Session Rules
- ไม่มีตัวตนผู้ใช้ ไม่มี session ไม่มี cookie (SECURITY.md Authentication and Authorization)
- ไม่มี anonymous ID สำหรับ analytics; `correlation_id` เป็นตัวระบุต่อ request เพื่อไล่ log เท่านั้น ไม่ผูกกับบุคคลและไม่ถูกเก็บข้ามคำขอ

## Consent & PDPA Gating
ไม่เก็บข้อมูลส่วนบุคคลและไม่มี tracking ต่อบุคคล จึงไม่ต้องมี consent banner (DATA_MODEL.md Data Classification: ทุกฟิลด์ `non_personal`) เงื่อนไขทบทวน: ก่อนเพิ่ม analytics event, cookie หรือตัวระบุผู้ใช้ใดๆ ต้องอัปเดตเอกสารนี้ SECURITY.md และ DATA_MODEL.md แล้วประเมิน PDPA ใหม่

## Tracking QA Checklist
- [ ] `event_name` ไม่มีค่า และไม่มีโค้ดส่ง analytics ออกนอกแอป
- [ ] ไม่มี cookie ถูกตั้งโดยแอป
- [ ] log ไม่มีเนื้อหาแถวข้อมูล/ข้อความ error (TST-015 และการตรวจ log `import_rejected`)
- [ ] ทุก log มี `correlation_id` (TST-015)
