# ADR — Architecture Decision Records

## Decision Log
เจ้าของ enum `adr_status`: `Proposed`, `Accepted`, `Deprecated`, `Superseded`

### ADR-001 — ใช้ SQLite3 แทน DuckDB/PostgreSQL
- **Status:** Accepted
- **Context:** โจทย์อนุญาต SQLite3 หรือ DuckDB; ข้อมูลตัวอย่างราว 36,527 แถว ใช้งาน instance เดียว (TC-01, TC-02)
- **Alternatives:** DuckDB (columnar, ไม่จำเป็นกับขนาดนี้); PostgreSQL (ต้องมี service เพิ่มบน Coolify)
- **Decision:** SQLite3 ผ่าน `sqlite3` ของ Python
- **Consequences:** (+) ไม่มี service เพิ่ม ตั้งค่าน้อย; (−) เขียนได้ทีละ transaction จึงห้ามหลาย instance; ต้องมี persistent volume (TC-08)

### ADR-002 — Server-rendered FastAPI + Jinja2
- **Status:** Accepted
- **Context:** หน้าเดียว ไม่มีความต้องการ interactivity ซับซ้อน เวลา 120 นาที
- **Alternatives:** SPA (React); Django
- **Decision:** FastAPI + Jinja2 พร้อม JSON API เฉพาะที่ช่วยตรวจสอบ/ทดสอบ
- **Consequences:** (+) ไม่มี build step ฝั่ง client; (−) ถ้าต้องการ UI โต้ตอบมากใน Phase 3 อาจต้องทบทวน

### ADR-003 — นำเข้าแบบ validate ทั้งไฟล์ แล้วเขียนใน transaction เดียว
- **Status:** Accepted
- **Context:** ข้อมูลบางส่วนทำให้ตัวเลขแดชบอร์ดผิดโดยไม่มีใครรู้ (PN-04)
- **Alternatives:** ข้ามแถวผิดแล้วนำเข้าที่เหลือ; นำเข้าทีละแถว
- **Decision:** ปฏิเสธทั้งไฟล์เมื่อมีแถวผิด; `deployment_id` เป็น global unique ไม่เขียนทับ; ตรวจไฟล์ซ้ำด้วย SHA-256
- **Consequences:** (+) ข้อมูลที่เห็นเชื่อถือได้; (−) ผู้ใช้ต้องแก้ไฟล์ต้นทางแล้วอัปโหลดใหม่

### ADR-004 — Deploy ด้วย Dockerfile บน Coolify แบบ instance เดียว (`recreate`)
- **Status:** Accepted
- **Context:** SQLite เขียนได้ทีละ process; ต้อง deploy ผ่าน Coolify (BC-01)
- **Alternatives:** Nixpacks; rolling update หลาย instance
- **Decision:** Dockerfile + persistent volume + replica = 1
- **Consequences:** (+) ควบคุม non-root และ volume ได้; (−) มีช่วงหยุดสั้นขณะ redeploy (ดู DEPLOYMENT.md Zero-downtime Deployment)

## Template
```
### ADR-NNN — <ชื่อสั้น>
- Status: Proposed | Accepted | Deprecated | Superseded
- Context / Alternatives / Decision / Consequences
```

## Index
| ADR | Title | Status |
|---|---|---|
| ADR-001 | SQLite3 | Accepted |
| ADR-002 | FastAPI + Jinja2 | Accepted |
| ADR-003 | Atomic import | Accepted |
| ADR-004 | Coolify + Dockerfile, instance เดียว | Accepted |
