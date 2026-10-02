# Deployment Reliability Dashboard

นำเข้าประวัติ deployment (CSV) เก็บใน SQLite แล้วแสดงจำนวน, success rate และเวลาเฉลี่ยของ deployment ที่สำเร็จแยกตามบริการ พร้อมรายการที่ล้มเหลวและข้อความ error

เอกสารเต็ม: [`docs/README.md`](docs/README.md) (Quick Start, ข้อกำหนด, การ deploy บน Coolify)

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q
uvicorn app.main:app --port 8000   # http://127.0.0.1:8000
```
