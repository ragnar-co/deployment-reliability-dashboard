# TASKS — Deployment Reliability Dashboard

ค่า `estimated_effort` เป็นงบเวลาที่ตั้งให้ลงตัวกับกรอบ 120 นาทีของโจทย์ ไม่ใช่ค่าที่วัดจริง: ถือเป็นค่าสอนจนกว่าจะบันทึกเวลาจริง เจ้าของการ calibrate: DevOps Operator

**ความเสี่ยงของแผนเวลา:** T-01…T-12 รวม 120 นาทีพอดี **ไม่มีเวลาเผื่อ** และ T-13 (P1) อยู่นอกงบ ทำเฉพาะเมื่อ T-12 เสร็จก่อนกำหนด T-11 และ T-12 ขึ้นกับ repo URL/สิทธิ์ push และ Coolify ที่ต้องมีพร้อมก่อนเริ่มนับ 120 นาที (SCOPE.md External Dependencies) ถ้าสองอย่างนี้ยังไม่พร้อม ให้ส่งมอบถึง T-10 ก่อนแล้วบันทึกว่า BC-01 ยังไม่ครบเพราะ dependency ภายนอก

## Task Breakdown
เจ้าของ enum `work_item_status`: `todo`, `in_progress`, `done`, `blocked`

| ID | Description | Feature / P0 | status |
|---|---|---|---|
| T-01 | สร้างโครงโปรเจกต์ (`app/`, `tests/`, requirements, `.gitignore`) | F-08 | done |
| T-02 | สร้าง schema SQLite ตาม DATA_MODEL.md | F-02 | done |
| T-03 | ตัว validate CSV ทั้งไฟล์ตามกติกา TC-03 | F-02 | done |
| T-04 | นำเข้าแบบ atomic + import batch + checksum + ตรวจ `deployment_id` ซ้ำ | F-01, F-02, F-03 | done |
| T-05 | Query ตัวเลขรวม/แยกบริการ/รายการล้มเหลว (parameterized) | F-04, F-05, F-06, F-07 | done |
| T-06 | Endpoint ตาม API_SPEC.md รวม `/health` | F-01, F-06, F-09 | done |
| T-07 | หน้า Dashboard ตาม UI_SPEC.md | F-04…F-07 | done |
| T-08 | Test ตาม TESTING.md รวมการตรวจกับค่าอ้างอิงของไฟล์ตัวอย่าง | F-08 | done |
| T-09 | Dockerfile (non-root, volume, health check) | F-09 | done |
| T-10 | README และ smoke test จากขั้นตอนที่เขียน | F-08 | done |
| T-11 | Push ไป `<COMPANY_REPO_URL>` (push แล้วที่ repo ที่ผู้ใช้ระบุ; ถ้าต้องส่ง repo ของบริษัทต้องเปลี่ยน remote) | F-09 | done |
| T-12 | Deploy บน Coolify ตาม DEPLOYMENT.md | F-09 | blocked |
| T-13 | (P1) ตัวกรอง environment | F-10 | done |

T-12 `blocked`: ผู้ใช้ deploy บน Coolify เอง (2026-10-02) เอกสารเป็น concept ไว้ก่อน (DEPLOYMENT.md) ส่วน T-11 push เสร็จแล้ว (SCOPE.md External Dependencies)

## Task Sequence and Dependencies
| ID | depends_on[] |
|---|---|
| T-01 | – |
| T-02 | T-01 |
| T-03 | T-01 |
| T-04 | T-02, T-03 |
| T-05 | T-02 |
| T-06 | T-04, T-05 |
| T-07 | T-06 |
| T-08 | T-04, T-05, T-06, T-07 |
| T-09 | T-06 |
| T-10 | T-08, T-09 |
| T-11 | T-08, T-10 |
| T-12 | T-09, T-11 |
| T-13 | T-07 |

## Definition of Done
| ID | definition_of_done |
|---|---|
| T-01 | แอปเริ่มทำงานในเครื่องได้ |
| T-02 | ฐานข้อมูลสร้างตารางและ index ครบตามเอกสาร |
| T-03 | ทุกกรณี AC-02 ถูกปฏิเสธพร้อมหมายเลขแถว |
| T-04 | บังคับขีดจำกัด 10 MiB ที่ server (TST-020); fixture นำเข้าได้ครบ; ไฟล์ผิดไม่เหลือข้อมูล; ไฟล์ซ้ำถูกปฏิเสธ; ถ้ามีไฟล์ตัวอย่างจริงต้องนำเข้าได้ 36,527 แถว |
| T-05 | ตัวเลขตรงกับค่าคาดหวังของ fixture ทุกบริการ; ถ้ามีไฟล์ตัวอย่างจริงต้องตรง G-01 |
| T-06 | ทุก operation ใน API_SPEC.md ตอบตามสคีมา และ log เป็น JSON พร้อม `correlation_id` (TST-015) |
| T-07 | CP-01…CP-04 ทำได้บนหน้าเดียว รวมการเตือนเมื่อเลือกไฟล์เกิน 10 MB (TST-022) |
| T-08 | `python -m pytest -q` ผ่านทั้งหมดโดยไม่ต้องมีไฟล์ตัวอย่างจริง ด้วย fixture CSV ขนาดเล็กที่ค่าคาดหวังคำนวณด้วยมือ; ถ้ามีไฟล์ตัวอย่างจริงต้องตรง G-01 ด้วย (FR-12, AC-11) |
| T-09 | Image build ได้, รันเป็น non-root และเขียน `/data` ได้ (TST-019), `/health` ผ่าน |
| T-10 | ผู้อื่นทำตาม README แล้วรันได้; README ระบุรายการ dependency ที่ใช้จริง |
| T-11 | บันทึก commit SHA และการยืนยันจาก remote; ตรวจว่า `git ls-files` ไม่มี `*.db`, CSV ข้อมูลจริง, `.env` (LC-03) |
| T-12 | Launch Blockers ใน DEPLOYMENT.md ปิดครบ; URL เปิดได้, `/health` 200; เข้าจากเครือข่ายภายนอกแล้วถูกปฏิเสธ (SC-01); ข้อมูลอยู่หลัง redeploy (CP-06); บันทึกเวลาช่วงหยุดของ `recreate` |
| T-13 | AC-10 ผ่าน |

## Assignments and Estimates
ผู้รับผิดชอบทั้งหมด: ผู้ใช้ร่วมกับ AI coding agent (Claude Code/Codex)

| ID | estimated_effort (นาที) | หมายเหตุ |
|---|---|---|
| T-01 | 10 | |
| T-02 | 5 | |
| T-03 | 10 | |
| T-04 | 10 | |
| T-05 | 15 | |
| T-06 | 10 | |
| T-07 | 15 | |
| T-08 | 15 | |
| T-09 | 5 | |
| T-10 | 10 | |
| T-11 | 5 | |
| T-12 | 10 | |
| T-13 | 5 | ทำถ้าเหลือเวลา |
