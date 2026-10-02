# RUNBOOK — Deployment Reliability Dashboard

เอกสารนี้เป็นเจ้าของ enum `incident_severity` และเป็นที่ที่ alert ของ SLO ใน ARCHITECTURE.md ถูกยืนยัน ค่าที่ยังไม่มีใครวัดเป็น `null` พร้อมเจ้าของ

## Daily Operations
| งาน | วิธี | ความถี่ |
|---|---|---|
| ตรวจสุขภาพ | `GET /health` ต้อง 200 `{"status":"ok"}` (Coolify เรียกให้อัตโนมัติ) | ต่อเนื่อง / ตรวจมือเมื่อสงสัย |
| นำเข้าข้อมูลใหม่ | อัปโหลด CSV ที่หน้า `/` อ่านข้อความผลลัพธ์ ถ้าถูกปฏิเสธให้แก้ไฟล์ต้นทางตามเหตุผลที่ระบุ | เมื่อมี export ใหม่ |
| ดู log | Coolify → Logs; ค้นหา `correlation_id` หรือ `event` (`import_rejected`) | เมื่อมีปัญหา |
| สำรองข้อมูล | ดู Backup and Recovery | ก่อน redeploy ที่เปลี่ยน schema |

ผู้รับผิดชอบ: DevOps Operator

## Monitoring and Alerts
เกณฑ์ตัวเลขของทุก alert เป็น `null` เพราะ SLO ยังไม่ถูกวัด (ARCHITECTURE.md Observability & SLOs) เจ้าของการ calibrate: Engineering Lead ช่องทางแจ้งเตือน (ปลายทาง) = `null` เจ้าของ: DevOps Operator

| Alert | มาจาก SLO | เงื่อนไข | ระดับ (`incident_severity`) | การดำเนินการ |
|---|---|---|---|---|
| AL-01 Health check ล้มเหลว | SLO-01 | `/health` ไม่ใช่ 200 ต่อเนื่องเกิน `null` | `critical` | ทำตาม Troubleshooting: "health ล่ม" |
| AL-02 หน้า Dashboard ช้า | SLO-02 | เวลาตอบเกิน `null` | `minor` | ตรวจขนาดฐานข้อมูลและ log `ms` ของ `request` |
| AL-03 การนำเข้าช้า | SLO-03 | เวลานำเข้าเกิน `null` | `minor` | ตรวจ `IMPORT_BUSY` ซ้ำๆ และขนาดไฟล์ |
| AL-04 การนำเข้าถูกปฏิเสธซ้ำๆ | (ไม่มี SLO) | `import_rejected` เกิน `null` ครั้งต่อช่วง | `minor` | ดูรหัส `code` ใน log แล้วดู Troubleshooting |

### Severity (เจ้าของ enum `incident_severity`)
| ค่า | ความหมาย |
|---|---|
| `critical` | แอปใช้งานไม่ได้ หรือข้อมูลเสียหาย/สูญหาย หรือพบข้อมูลส่วนบุคคลในข้อมูลนำเข้า |
| `major` | ฟังก์ชันหลักใช้ไม่ได้บางส่วน (เช่น นำเข้าไม่ได้ แต่ดูข้อมูลได้) |
| `minor` | ช้าหรือไม่สะดวก แต่ทำงานได้ |

## Troubleshooting Guide
| อาการ | ตรวจ | แก้ |
|---|---|---|
| `/health` = 503 `unavailable` | log ของคอนเทนเนอร์; ตรวจว่า `/data` ถูก mount และเป็นของ user `app` | แก้สิทธิ์ volume ให้ user `app` เขียนได้ (DEPLOYMENT.md Container contract) แล้ว redeploy |
| ข้อมูลหายหลัง redeploy | ตรวจว่ามี Persistent Storage mount ที่ `/data` | เพิ่ม mount แล้วนำเข้าใหม่จากไฟล์ต้นฉบับ หรือกู้จากไฟล์สำรอง |
| อัปโหลดแล้วได้ 413 / error จาก proxy | ขนาดไฟล์เทียบ 10 MiB (`MAX_UPLOAD_BYTES`); ขีดจำกัดของ Coolify/proxy | แยกไฟล์ให้เล็กลง หรือปรับขีดจำกัดของ proxy (ต้องไม่ต่ำกว่า 10 MiB: LB-4) |
| 422 `VALIDATION_FAILED` / `INVALID_FILE` | อ่านรายการเหตุผล (ระบุหมายเลขแถว 1-based นับ header เป็นบรรทัด 1) | แก้ไฟล์ต้นทางแล้วอัปโหลดใหม่ ไม่มีข้อมูลค้างจากการนำเข้าที่ถูกปฏิเสธ |
| 409 `DUPLICATE_FILE` | ไฟล์นี้เคยนำเข้าแล้ว (checksum ตรง) | ไม่ต้องทำอะไร ข้อมูลอยู่ครบแล้ว |
| 409 `DUPLICATE_DEPLOYMENT` | มี `deployment_id` ซ้ำกับข้อมูลเดิม | ใช้ id ที่ไม่ซ้ำ หรือถ้าต้องแก้ข้อมูลเดิม ดู "แก้ import ที่ผิด" ใน Backup and Recovery |
| 503 `IMPORT_BUSY` | มีการนำเข้าอื่นกำลังเขียน | รอสักครู่แล้วลองใหม่ |
| หน้าเปิดได้แต่ "No data yet" | ฐานข้อมูลว่างหรือชี้ผิดไฟล์ (`DB_PATH`) | ตรวจ `DB_PATH` และ volume |
| ตัวกรองบริการไม่พบบริการ | ชื่อบริการสะกดตรงกับในไฟล์หรือไม่ | เลือกจาก dropdown |

## Backup and Recovery
- **สำรอง:** `sqlite3 /data/dashboard.db ".backup /data/backup-<YYYYMMDD>.db"` ในคอนเทนเนอร์ (ไฟล์สำรองอยู่บน volume เดียวกัน จึงไม่ป้องกันความเสียหายของ volume เอง: การคัดลอกออกนอก volume = `null` เจ้าของ DevOps Operator)
- **กู้:** หยุดคอนเทนเนอร์ → แทนที่ `dashboard.db` ด้วยไฟล์สำรอง → เริ่มใหม่ → ตรวจ `/health` และตัวเลขรวม
- **แก้ import ที่ผิด:** แอปไม่มีฟีเจอร์ลบ ใช้ขั้นตอนใน DEPLOYMENT.md Rollback Procedure (กู้ไฟล์สำรอง หรือลบ `dashboard.db` แล้วนำเข้าใหม่จากไฟล์ต้นฉบับ)
- **RTO / RPO:** `null` — เจ้าของ: Engineering Lead (ข้อมูลสร้างซ้ำได้จากไฟล์ export ต้นฉบับ จึงควรเก็บไฟล์ CSV ต้นฉบับไว้นอกแอป)

## Incident Response
1. ระบุระดับตามตาราง Severity
2. `critical`: แจ้ง DevOps Operator และ Engineering Lead ทันที (ช่องทาง = `null` ตามข้างบน) หยุดการนำเข้าจนกว่าจะสอบสวนเสร็จ
3. เก็บหลักฐาน: log ที่มี `correlation_id`, `batch_id` ของการนำเข้าที่เกี่ยวข้อง (`import_batches`), เวลา
4. แก้ไขตาม Troubleshooting หรือกู้จากไฟล์สำรอง
5. ถ้าพบข้อมูลส่วนบุคคลในข้อมูลนำเข้า: ถือเป็น `critical` และทำตาม SECURITY.md Incident Response Plan (รวมการประเมินแจ้งเหตุตาม PDPA ภายใน 72 ชั่วโมง)
6. หลังเหตุ: บันทึกสาเหตุและอัปเดตเอกสารนี้หรือ CHANGELOG.md ถ้ามีการเปลี่ยนพฤติกรรม

ข้อมูลใน CSV ไม่พอสรุป root cause ของ deployment ที่ล้มเหลว (ดู CONTEXT): ใช้แดชบอร์ดเพื่อเลือกจุดเริ่มสืบสวนเท่านั้น

## Scaling Procedures
**ไม่ scale** ใน Phase 1: รัน 1 instance (replica = 1) เพราะ SQLite เขียนได้ทีละ process (TC-02, ADR-004) ห้ามเพิ่ม replica หรือใช้ rolling update การ scale up/down ของ resource ต่อคอนเทนเนอร์ (CPU/RAM) ไม่มีเกณฑ์ที่ calibrate: `null` เจ้าของ DevOps Operator ถ้าต้องการหลาย instance ต้องย้ายฐานข้อมูลก่อน (Phase 3)
