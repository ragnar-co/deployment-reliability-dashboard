# AGENTS.md — Deployment Reliability Dashboard

กฎสำหรับ AI coding agent (Claude Code/Codex) ที่แก้โค้ดในโปรเจกต์นี้ เอกสารนี้ไม่ซ้ำเนื้อหาของเอกสารอื่น: ชี้ไปยังเจ้าของข้อเท็จจริงแต่ละข้อ

## Project Overview
เว็บแอปภายในที่นำเข้า CSV ประวัติ deployment ลง SQLite และแสดงตัวชี้วัดความน่าเชื่อถือแยกบริการ ขอบเขตดู SCOPE.md ข้อกำหนดดู PRD.md และ CONSTRAINTS.md เป็นเครื่องมือช่วยจัดลำดับการตรวจสอบ ไม่ใช่การยืนยัน root cause

## Tech Stack
Python 3.12, FastAPI, Jinja2, SQLite3 (stdlib `sqlite3`), pytest ตัวเลือกและเหตุผลอยู่ใน ARCHITECTURE.md (Tech Stack Decisions) และ ADR.md เวอร์ชันของ dependency pin ใน `requirements.txt` / `requirements-dev.txt` ห้ามเพิ่ม dependency โดยไม่แก้ ARCHITECTURE.md

## Coding Conventions
- **Naming:** Python `snake_case` (ฟังก์ชัน/ตัวแปร), `PascalCase` (class), `UPPER_SNAKE_CASE` (ค่าคงที่); ชื่อตาราง/คอลัมน์ตาม DATA_MODEL.md ทุกตัว; รหัสข้อผิดพลาดตาม `application_error_code` ใน API_SPEC.md
- **File structure:** `app/` (โค้ด: `main.py` routes, `importer.py` validate+import, `metrics.py` query, `db.py` schema, `errors.py`, `config.py`, `logging_setup.py`, `templates/`), `tests/`, `docs/`, `Dockerfile`
- **ภาษาของ comment:** อังกฤษ ในโค้ด; เอกสารใน `docs/` เขียนเนื้อหาบรรยายเป็นไทย identifier เป็นอังกฤษ
- ตัวเลขบนแดชบอร์ดทุกค่าอ่านจาก SQLite หลังนำเข้า (CONSTRAINTS.md TC-05)

## Forbidden Patterns
- ห้ามคำนวณตัวเลขจากไฟล์ CSV ดิบหลังขั้นตอนนำเข้า
- ห้ามต่อสตริงเป็น SQL; ใช้ parameter เสมอ (TC-06)
- ห้ามบันทึกข้อมูลบางส่วน: การนำเข้าต้องผ่าน transaction เดียว (TC-04)
- ห้ามเขียนทับ `deployment_id` ที่มีอยู่ (FR-04)
- ห้าม render ค่าจาก CSV แบบ `|safe` หรือปิด autoescape (SC-02)
- ห้าม hard-code ค่าที่ต้อง calibrate (ขีดจำกัดขนาดไฟล์, SLO, retention): ใช้ config หรือ `null` พร้อมเจ้าของ
- ห้าม commit `*.db`, ไฟล์ CSV ข้อมูลจริง, `.env`, credential, URL ภายในบริษัท (LC-03)
- ห้ามเพิ่มคอลัมน์ใน CSV/ตาราง หรือเปลี่ยนสูตรตัวชี้วัด โดยไม่แก้ DATA_MODEL.md / PRD.md ก่อน
- ห้ามเปลี่ยน `docs/` ฝั่งเดียวโดยให้โค้ดไม่ตรง (หรือกลับกัน)
- ห้ามอ่าน/ส่งข้อมูล CSV ไปบริการภายนอก (รวมถึง AI endpoint) ใน Phase 1

## Testing Requirements
- คำสั่ง: `python -m pytest -q` ต้องผ่านก่อน commit/push (BC-01) รายละเอียดชั้น test ดู TESTING.md
- ทุกการเปลี่ยนพฤติกรรมต้องมี test; แก้บั๊กต้องเพิ่ม test ที่ล้มก่อนแก้
- **เกณฑ์ coverage รวมที่บล็อก CI (เจ้าของ: เอกสารนี้):** `null` — เจ้าของการ calibrate: Engineering Lead ยังไม่มี CI อัตโนมัติ จึงไม่มีกลไกบล็อก ขณะที่เป็น `null` coverage เป็นแนวทาง ไม่ใช่เงื่อนไขผ่าน
- **วิธีวัด/บังคับ:** วัดด้วย `pytest --cov=app` (ต้องติดตั้ง `pytest-cov`); เมื่อมี CI (Phase 3) ให้ตั้งเกณฑ์ที่นี่ที่เดียวแล้วให้ job CI อ่านจากค่านี้ ส่วนเป้าหมายรายชั้นอยู่ที่ TESTING.md

## PDPA Rules
- ข้อมูลนำเข้าเป็น `non_personal` ทั้งหมด (DATA_MODEL.md Data Classification) ห้ามรับหรือเก็บคอลัมน์เพิ่ม; ไฟล์ที่มีคอลัมน์เกินถูกปฏิเสธ (LC-01)
- ถ้าพบข้อมูลส่วนบุคคลในไฟล์ (เช่น ชื่อคนใน `error_message`) ให้หยุด รายงาน และทำตาม SECURITY.md Incident Response Plan ห้ามแก้ข้อมูลเงียบๆ
- ห้ามเขียนเนื้อหาแถวข้อมูลหรือข้อความ error ลง log (TRACKING_PLAN.md)
- ก่อนเพิ่มฟิลด์ที่อาจเป็นข้อมูลส่วนบุคคล ต้องอัปเดต DATA_MODEL.md และทบทวน PDPA (LC-02)
