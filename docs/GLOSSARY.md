# GLOSSARY — Deployment Reliability Dashboard

## Term Definitions
| Term | Definition | Owning role |
|---|---|---|
| Deployment | หนึ่งครั้งของการ deploy บริการหนึ่งไปยัง environment หนึ่ง ตามที่บันทึกในไฟล์ export | DevOps Operator |
| Service | ชื่อบริการที่ถูก deploy (`service_name`) | DevOps Operator |
| Success rate | สัดส่วน deployment ที่สำเร็จ ตามนิยามใน PRD.md (Functional Requirements) | Engineering Lead |
| Average successful duration | ค่าเฉลี่ยระยะเวลาของ deployment ที่สำเร็จ หน่วยวินาที ตามนิยามใน PRD.md | Engineering Lead |
| Failed deployment | deployment ที่ผลลัพธ์เป็นล้มเหลว พร้อมข้อความ error ต้นฉบับ | DevOps Operator |
| Error message | ข้อความข้อผิดพลาดต้นฉบับของ failed deployment | DevOps Operator |
| Import | การนำเข้าไฟล์ CSV หนึ่งไฟล์เข้าฐานข้อมูล ซึ่งสำเร็จทั้งไฟล์หรือไม่บันทึกเลย | DevOps Operator |
| Import batch | บันทึกของการนำเข้าที่สำเร็จหนึ่งครั้ง (ชื่อไฟล์, checksum, จำนวนแถว) | DevOps Operator |
| Checksum | ค่า SHA-256 ของเนื้อไฟล์ ใช้ตรวจไฟล์ซ้ำ | DevOps Operator |
| Dashboard | หน้าเดียวที่แสดงตัวชี้วัดรวม ตารางแยกบริการ และรายการล้มเหลว | Engineering Lead |
| Service filter | ตัวเลือกจำกัดมุมมองให้เหลือบริการเดียว ค่าเริ่มต้นคือทุกบริการ | DevOps Operator |
| Environment | ปลายทางที่ deploy ตามคอลัมน์ `environment` ใน CSV เป็นข้อความอิสระที่ต้องไม่ว่าง (ไม่ใช่ enum ของระบบ ต่างจากแถว `environment` ใน Enumeration Registry ซึ่งหมายถึงสภาพแวดล้อมที่รันตัวแอป) | DevOps Operator |
| CP-ID | รหัส critical path ที่ PERSONAS.md เป็นเจ้าของ | DevOps Operator |
| Investigation draft | ร่างข้อเสนอตรวจสอบที่ AI สร้าง (Phase 2 ไม่อยู่ใน MVP) เป็นตัวช่วย ไม่ใช่ root cause ที่ยืนยันแล้ว | Engineering Lead |

## Term-to-Entity Mapping
Reconcile แล้วกับ DATA_MODEL.md, API_SPEC.md และ UI_SPEC.md (2026-10-02)

| Term | Entity (DATA_MODEL) | Resource (API_SPEC) | Page (UI_SPEC) |
|---|---|---|---|
| Deployment, Failed deployment, Error message, Service, Environment | `deployments` | `GET /api/failures`, `GET /api/services` | Dashboard |
| Import, Import batch, Checksum | `import_batches` | `POST /api/import`, `POST /upload` | Dashboard (ส่วน Import) |
| Success rate, Average successful duration | (คำนวณ ไม่เก็บ) | `GET /api/services` | Dashboard |
| Investigation draft | (Phase 2 ยังไม่มี) | (Phase 2) | (Phase 2) |

## Disputed Terms
| Term | ความหมายที่ขัดแย้ง | Resolution |
|---|---|---|
| "Duration" | เวลา deploy ในไฟล์ (วินาที) กับระยะเวลาแสดงผลแบบมนุษย์อ่าน | หน่วยที่เก็บและแสดงเป็นหลักคือวินาที (`duration_seconds`) การแสดงแบบอ่านง่ายไม่เปลี่ยนค่าที่เก็บ |
| "Success rate" | อัตราของทุก deployment กับอัตราของเฉพาะที่เสร็จสิ้น | ใช้อัตราจาก deployment ทั้งหมดใน filter (PRD.md) |

## Glossary Change Log
| Date | Change | By |
|---|---|---|
| 2026-10-02 | สร้างเอกสารครั้งแรก; reconcile Term-to-Entity Mapping | Documentation author |
| 2026-10-02 | เพิ่มเจ้าของ enum `event_name` (TRACKING_PLAN.md) และ `incident_severity` (RUNBOOK.md) เมื่อเอกสารครบ 20 ไฟล์ | Documentation author |

## Enumeration Registry
ดัชนีเท่านั้น ห้ามมีค่าของ enum ค่าอยู่ที่เอกสารเจ้าของ

| Enum | Owner document | หมายเหตุ |
|---|---|---|
| requirement_priority | SCOPE.md | |
| work_item_status | TASKS.md | |
| pdpa_classification | DATA_MODEL.md | |
| confidentiality_class | DATA_MODEL.md | |
| environment | ARCHITECTURE.md | สภาพแวดล้อมที่รันแอป ไม่ใช่คอลัมน์ CSV |
| application_error_code | API_SPEC.md | |
| role | SECURITY.md | |
| deployment_strategy | DEPLOYMENT.md | |
| deployment_status | DATA_MODEL.md | enum ของโดเมน: ผลลัพธ์ของ deployment |
| import_batch_status | DATA_MODEL.md | enum ของโดเมน |
| adr_status | ADR.md | |
| event_name | TRACKING_PLAN.md | ไม่มีค่าใน Phase 1 (ไม่มี analytics) |
| incident_severity | RUNBOOK.md | |
