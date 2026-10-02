# Deployment Reliability Dashboard

เว็บแอปภายในสำหรับทีม DevOps: นำเข้าประวัติ deployment จากไฟล์ CSV เก็บลง SQLite แล้วแสดงจำนวน deployment, อัตราสำเร็จ และเวลาเฉลี่ยของ deployment ที่สำเร็จ **แยกตามบริการ** พร้อมรายการ deployment ที่ล้มเหลวและข้อความ error เลือกดูเฉพาะบริการได้ เพื่อบอกว่าควรเริ่มตรวจบริการไหนก่อน

> **ข้อควรเข้าใจ:** แดชบอร์ดนี้เป็นเครื่องมือช่วย **จัดลำดับการตรวจสอบ** ไม่ใช่การยืนยัน root cause ข้อมูลใน CSV (วัน, ระยะเวลา, ข้อความ error) ไม่พอจะสรุปสาเหตุที่แท้จริงได้

## Prerequisites
- Python 3.12 (ทดสอบบน 3.13 ได้เช่นกัน) และ pip
- Docker (เฉพาะถ้าจะรันเป็น container)
- ไฟล์ CSV ที่มี 7 คอลัมน์: `deployment_id`, `service_name`, `status`, `duration_seconds`, `error_message`, `deployment_date`, `environment`

## Install
```bash
git clone https://github.com/ragnar-co/deployment-reliability-dashboard.git
cd deployment-reliability-dashboard
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```
Dependency ถูก pin เวอร์ชันไว้ใน `requirements.txt` / `requirements-dev.txt`

## Run
```bash
uvicorn app.main:app --port 8000
```
เปิด http://127.0.0.1:8000 (ตรวจสุขภาพ: http://127.0.0.1:8000/health ต้องได้ `{"status":"ok"}`) ฐานข้อมูลถูกสร้างเองที่ `data/dashboard.db` (ไม่ถูก commit)

| ตัวแปรสภาพแวดล้อม | ค่าเริ่มต้น | ความหมาย |
|---|---|---|
| `DB_PATH` | `data/dashboard.db` | ตำแหน่งไฟล์ SQLite |
| `MAX_UPLOAD_BYTES` | `10485760` (10 MiB) | ขนาดไฟล์อัปโหลดสูงสุด หน้าเว็บเตือนก่อนอัปโหลดถ้าเกิน |

## Test
```bash
python -m pytest -q
```
ต้องผ่านทั้งหมด (72 test) โดยไม่ต้องมีไฟล์ข้อมูลจริง test ที่ใช้ไฟล์ตัวอย่างจริง `theBeth_deployments_mock.csv` จะถูกข้ามเมื่อไม่มีไฟล์นั้น (ไฟล์ไม่ถูก commit)

## Import CSV
**ผ่านหน้าเว็บ:** เปิดหน้าแรก → **Choose File** → เลือก `.csv` → **Upload** (ครั้งละหนึ่งไฟล์) สำเร็จจะเห็น "Imported N deployments (S successful, F failed)." ครั้งเดียว ถ้ากด refresh ข้อความจะหายและไฟล์ไม่ถูกส่งซ้ำ

**ผ่าน API:**
```bash
curl -F file=@test_data/deployments_valid.csv http://127.0.0.1:8000/api/import
# {"batch_id":1,"rows":1000,"successful_deployments":851,"failed_deployments":149}
```

**ลองกับไฟล์ที่ให้มา:**
| ไฟล์ | ผลที่คาดหวัง |
|---|---|
| `test_data/deployments_valid.csv` | นำเข้า 1,000 แถว: 851 success, 149 failed, success rate 85.10%, เวลาเฉลี่ย 325.11 วินาที |
| `test_data/deployments_invalid.csv` | ถูกปฏิเสธทั้งไฟล์ พร้อมเหตุผลระบุหมายเลขแถว (เช่น `Row 2: duration_seconds must be a positive integer, got '0'`) และไม่มีข้อมูลบางส่วนถูกบันทึก |

**กติกาการนำเข้า:** ตรวจทั้งไฟล์ก่อนบันทึก และบันทึกใน transaction เดียว (ผิดแถวเดียว = ไม่บันทึกเลย) · ไฟล์เดิมซ้ำ (checksum ตรงกัน) ถูกปฏิเสธและแจ้งว่านำเข้าไปแล้วเมื่อไร · `deployment_id` ที่มีอยู่แล้วจะไม่ถูกเขียนทับ · คอลัมน์เกินหรือขาดถูกปฏิเสธ · ไฟล์เกิน 10 MB ถูกปฏิเสธ รายละเอียดทั้งหมดอยู่ใน `docs/API_SPEC.md`

## ใช้แดชบอร์ด
- ประโยคบนสุดบอกบริการที่อัตราสำเร็จต่ำสุด ("Check … first") ตารางเรียงจากต่ำสุด พร้อมแถบสัดส่วนสำเร็จ/ล้มเหลว
- เลือก **Service** (และ **Environment**) เพื่อให้ตัวเลข ตาราง และรายการที่ล้มเหลวเปลี่ยนตามกัน
- รายการ failed deployment เรียงใหม่สุดก่อน แสดงข้อความ error ต้นฉบับ และแบ่งหน้าละ 100 แถว

## Docker
```bash
docker build -t deployment-reliability-dashboard .
docker run -d --name drd -p 8000:8000 -v drd-data:/data deployment-reliability-dashboard
```
รันเป็น user ที่ไม่ใช่ root, เก็บฐานข้อมูลที่ `/data` (ต้อง mount volume ไม่เช่นนั้นข้อมูลหายเมื่อสร้างคอนเทนเนอร์ใหม่) และมี health check ที่ `/health` **ยังไม่มีระบบยืนยันตัวตน** จึงต้องจำกัดการเข้าถึงที่ชั้นเครือข่าย การ deploy บน Coolify ยังเป็นแนวคิดที่ยังไม่ได้ทดลอง ดู `docs/DEPLOYMENT.md`

## โครงสร้างโปรเจกต์
```
app/            โค้ด (main.py routes, importer.py validate+import, metrics.py, db.py, templates/)
tests/          test อัตโนมัติ + tests/fixtures/small.csv (ข้อมูลสังเคราะห์)
test_data/      ไฟล์ valid / invalid สำหรับลองและตรวจ
docs/           เอกสาร ddd-web-app ครบ 20 ไฟล์ (เริ่มที่ docs/README.md)
Dockerfile      image สำหรับ container / Coolify
DELIVERY.md     บันทึกการส่งมอบ
```

## เอกสาร
เริ่มที่ [`docs/README.md`](docs/README.md) · ขอบเขต [`docs/SCOPE.md`](docs/SCOPE.md) · สถาปัตยกรรม [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · API [`docs/API_SPEC.md`](docs/API_SPEC.md) · การ deploy [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) · การปฏิบัติการ [`docs/RUNBOOK.md`](docs/RUNBOOK.md) · กฎสำหรับ AI agent [`docs/AGENTS.md`](docs/AGENTS.md)

## ข้อห้าม
ห้าม commit ข้อมูลจริง, `*.db`, `.env`, credential หรือ URL ภายในบริษัท (ดู `.gitignore`)
