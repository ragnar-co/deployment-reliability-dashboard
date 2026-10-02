# CHANGELOG

รูปแบบตาม Keep a Changelog; เวอร์ชันยังเป็น 0.x (ก่อน production hardening)

## Unreleased
- Deploy บน Coolify (TASKS.md T-12) — ผู้ใช้จะ deploy เอง; DEPLOYMENT.md เป็น concept ที่ยังไม่ได้ทดลอง
- Push ไป repository ของบริษัท (T-11) — ปัจจุบัน push ไปที่ repository ที่ผู้ใช้ระบุแล้ว (ดู `DELIVERY.md` ที่ root)
- Phase 2: AI investigation draft (extension point ใน ARCHITECTURE.md)

## Version History
### 0.1.2 — 2026-10-02
- Fixed: กด refresh หลังอัปโหลดสำเร็จทำให้ส่งไฟล์ซ้ำและขึ้น "This exact file was already imported" — เปลี่ยนเป็น Post/Redirect/Get (`POST /upload` สำเร็จ = 303 ไป `/`)

### 0.1.1 — 2026-10-02 (`dd49df4`)
- Changed: ค่าเฉลี่ยระยะเวลาของ deployment ที่สำเร็จแสดงทศนิยม 2 ตำแหน่ง (half-up) — ชุดข้อมูล valid ได้ 325.11 วินาที
- Added: ผลนำเข้าแสดงจำนวน successful และ failed; API คืน `successful_deployments`
- Added: README ระบุว่าแดชบอร์ดไม่ใช่การยืนยัน root cause
- Added: `test_data/` พร้อม test ของไฟล์ valid/invalid (รวม 67 test)
- Changed: PLAN.md/CONTEXT.md ปรับให้ตรงขอบเขตปัจจุบัน (รวม Coolify)

### 0.1.0 — 2026-10-02 (`6a98878`)
- Added: นำเข้า CSV แบบ atomic, validate ทั้งไฟล์, ตรวจไฟล์ซ้ำด้วย SHA-256 และ `deployment_id` ซ้ำ
- Added: แดชบอร์ด (จำนวน, success rate, เวลาเฉลี่ย แยกบริการ), ตัวกรองบริการ/environment, รายการ failed deployment, pagination
- Added: ขีดจำกัดไฟล์ 10 MiB พร้อมการเตือนใน UI
- Added: `/health`, structured log พร้อม `correlation_id`, Dockerfile (non-root, volume `/data`)
- Added: เอกสาร `ddd-web-app` ชุดแรก
