# README — Deployment Reliability Dashboard

## Project Name and Description

**Deployment Reliability Dashboard** — เว็บแอปภายในที่นำเข้าประวัติ deployment จาก CSV เก็บลง SQLite แล้วแสดงจำนวน deployment, อัตราสำเร็จ และเวลาเฉลี่ยของ deployment ที่สำเร็จแยกตามบริการ พร้อมรายการที่ล้มเหลวและข้อความ error เพื่อชี้ว่าควรเริ่มตรวจบริการใดก่อน

> **สถานะ (2026-10-02):** implement แล้ว T-01…T-10 และ T-13; ทำตาม Quick Start ได้จริง `python -m pytest -q` ผ่าน 72 test; Docker image ตรวจแล้วในเครื่อง (non-root, volume, health) T-12 (Coolify) ผู้ใช้จะ deploy เอง: DEPLOYMENT.md เป็น concept ที่ยังไม่ได้ทดลองบน Coolify

> **หมายเหตุ:** แดชบอร์ดนี้เป็นเครื่องมือช่วยจัดลำดับว่าควรตรวจบริการใดก่อน **ไม่ใช่การยืนยัน root cause** ข้อมูลใน CSV (วัน, ระยะเวลา, ข้อความ error) ไม่พอจะสรุปสาเหตุที่แท้จริงได้

## Quick Start
1. `python3.12 -m venv .venv && source .venv/bin/activate` → ได้ prompt ที่มี `(.venv)`
2. `pip install -r requirements-dev.txt` → ติดตั้งสำเร็จไม่มี error
3. `python -m pytest -q` → ทุก test ผ่านด้วย fixture CSV สังเคราะห์ (ไม่ต้องมีไฟล์ตัวอย่างจริง; TST-011 รันเฉพาะเมื่อมีไฟล์จริง)
4. `uvicorn app.main:app --port 8000` → log แสดง `Uvicorn running on http://127.0.0.1:8000`
5. เปิด `http://127.0.0.1:8000/health` → ได้ `{"status":"ok"}`
6. เปิด `http://127.0.0.1:8000/` → เห็น "No data yet" และฟอร์มอัปโหลด
7. อัปโหลด fixture CSV → เห็นตัวเลขตรงค่าคาดหวังของ fixture; **ถ้ามีไฟล์ตัวอย่างจริง** อัปโหลดแล้วต้องเห็น 36,527 deployments, success rate 92.1% และบริการแรกคือ `release-validator`

## Prerequisites
- Python 3.12
- pip (มากับ Python 3.12)
- Docker (ถ้าจะ build image ตาม DEPLOYMENT.md)
- ไฟล์ CSV ที่มี 7 คอลัมน์ตาม API_SPEC.md (Request and Response Schema) (ไฟล์ตัวอย่าง `theBeth_deployments_mock.csv` ไม่ถูก commit; ใช้ fixture สังเคราะห์สำหรับ test)
- Python packages: `fastapi`, `uvicorn`, `jinja2`, `python-multipart` (runtime) และ `pytest`, `httpx` (dev) pin เวอร์ชันใน `requirements*.txt` แล้ว (fastapi 0.142.2, uvicorn 0.54.0, jinja2 3.1.6, python-multipart 0.0.32, pytest 9.1.1, httpx 0.28.1)
- (สำหรับ deploy) Docker image build ได้, Coolify instance และ repo ของบริษัท ดู DEPLOYMENT.md

## Installation
1. Clone: `git clone https://github.com/ragnar-co/deployment-reliability-dashboard.git` แล้วติดตั้งตาม Quick Start ขั้น 1–2
2. ตัวแปรสภาพแวดล้อม (นิยามที่ DEPLOYMENT.md Environment Variables): `DB_PATH` ค่าเริ่มต้น `data/dashboard.db`; `MAX_UPLOAD_BYTES` ค่าเริ่มต้น `10485760` (10 MiB)
3. Container (ตรวจแล้วในเครื่อง ยังไม่ได้ทดลองบน Coolify): `docker build -t deployment-reliability-dashboard .` แล้ว `docker run -d --name drd -p 8000:8000 -v drd-data:/data deployment-reliability-dashboard` ต้อง mount volume ที่ `/data`

## Usage
- **Import CSV:** หน้า `/` → Choose File → Upload (ครั้งละหนึ่งไฟล์) หรือ `curl -F file=@test_data/deployments_valid.csv http://127.0.0.1:8000/api/import` ไฟล์ valid ที่ให้มาได้ 1,000 แถว (851 success, 149 failed, 85.10%, 325.11 วินาที) ไฟล์ invalid ถูกปฏิเสธทั้งไฟล์พร้อมเหตุผลระบุแถวและไม่มีข้อมูลค้าง ข้อความผลลัพธ์/error แสดงครั้งเดียว (refresh แล้วหาย) ไฟล์ซ้ำถูกปฏิเสธและบอกว่านำเข้าไปแล้วเมื่อไร ไฟล์เกิน 10 MB ถูกเตือนก่อนอัปโหลด รายละเอียดที่ API_SPEC.md
- เลือกบริการจาก dropdown เพื่อดูเฉพาะบริการนั้น (P1: กรอง environment ได้ด้วย)
- API: `POST /api/import`, `GET /api/services`, `GET /api/failures`, `GET /health` ดู API_SPEC.md

## Architecture Overview
โครงสร้างโค้ด: `app/` (main.py routes, importer.py, metrics.py, db.py, flash.py, templates/), `tests/` (72 test, `tests/fixtures/small.csv` สังเคราะห์), `test_data/` (ไฟล์ valid/invalid), `docs/` (20 ไฟล์), `Dockerfile` ·
FastAPI + Jinja2 instance เดียว, SQLite บน persistent volume, deploy ด้วย Dockerfile บน Coolify ดู ARCHITECTURE.md; การ deploy ดู DEPLOYMENT.md; กฎสำหรับ AI agent ที่ลงมือแก้โค้ดอยู่ที่ AGENTS.md (ข้อกำหนดโดยรวมที่ CONSTRAINTS.md); ขั้นตอนปฏิบัติการอยู่ที่ RUNBOOK.md

เอกสารทั้งชุด: PERSONAS → CONSTRAINTS → VPD → SCOPE → PRD → GLOSSARY → ARCHITECTURE → ADR → DATA_MODEL → UI_SPEC → TRACKING_PLAN → SECURITY → API_SPEC → AGENTS → TASKS → DEPLOYMENT → TESTING → CHANGELOG → RUNBOOK → README (ครบ 20 ไฟล์ตาม blueprint)

## Contributing
- เปลี่ยน data contract หรือสูตรตัวชี้วัดต้องแก้ DATA_MODEL.md/PRD.md ก่อนแก้โค้ด
- ห้าม commit credential, `*.db`, ไฟล์ CSV ข้อมูลจริง
- รัน `python -m pytest -q` ให้ผ่านก่อน push

## License
`null` — เจ้าของ: ผู้ใช้ (บริษัทกำหนดสัญญาอนุญาต)
