# SCOPE — Deployment Reliability Dashboard

## MVP Feature List
| ID | Feature | Priority | Traces to |
|---|---|---|---|
| F-01 | อัปโหลด CSV ครั้งละหนึ่งไฟล์ | P0 | UC-01, VP-03 |
| F-02 | Validate ทั้งไฟล์ก่อนบันทึก และบันทึกแบบ atomic ลง SQLite | P0 | UC-01, VP-03 |
| F-03 | ตรวจไฟล์ซ้ำด้วย SHA-256 และปฏิเสธ `deployment_id` ที่มีอยู่แล้ว | P0 | UC-01, VP-03 |
| F-04 | แสดงจำนวน deployment, สำเร็จ, ล้มเหลว และ success rate รวม | P0 | UC-02, VP-01 |
| F-05 | ตารางแยกบริการ: จำนวน deployment, success rate, เวลาเฉลี่ยของ success เรียงจาก success rate ต่ำสุด | P0 | UC-02, UC-05, VP-01 |
| F-06 | ตัวกรองบริการ (ค่าเริ่มต้น = ทุกบริการ) | P0 | UC-03, VP-02 |
| F-07 | รายการ failed deployment (บริการ, environment, วันที่, ระยะเวลา, error) เรียงใหม่สุดก่อน | P0 | UC-04, VP-02 |
| F-08 | Test/validation อัตโนมัติที่รันซ้ำได้ (FR-12) | P0 | BC-01 |
| F-09 | Deploy ผ่าน Coolify (Dockerfile + persistent volume + health check) | P0 | CP-06, BC-01 |

**Priority scale (เจ้าของ):** P0 = บังคับสำหรับ MVP, P1 = ควรมีถ้าเวลาเหลือ, P2 = เลื่อนไป phase ถัดไป

| ID | Feature | Priority | Traces to |
|---|---|---|---|
| F-10 | ตัวกรอง environment | P1 | UC-03 |

ตัวกรอง environment เป็นส่วนเสริมที่ไม่บังคับ (F-06 ที่บังคับคือบริการ) ทำเฉพาะถ้าเวลาเหลือ

## Out-of-Scope Items
| Item | Rationale | Phase |
|---|---|---|
| AI investigation draft (Bonus) | ไม่ให้หน่วงเวลา MVP; ต้องรอ endpoint/โควตาจากบริษัท | Phase 2 |
| Authentication / RBAC | non-goal ของ phase นี้; ลดความเสี่ยงด้วยการจำกัดเครือข่าย (SC-01) | Phase 3 |
| Root-cause determination อัตโนมัติ | ข้อมูล CSV ไม่พอสรุป root cause | never |
| Rollback / remediation อัตโนมัติ | เกินหน้าที่ของแดชบอร์ดซึ่งอ่านอย่างเดียว | never |
| Integration กับ CI/CD หรือ log provider | แหล่งข้อมูลคือ CSV เท่านั้น | Phase 3 |
| หลาย instance / managed database | ใช้ SQLite instance เดียว | Phase 3 |
| Timestamp ละเอียด, commit SHA, ownership, ลิงก์ log | CSV ปัจจุบันไม่มีฟิลด์เหล่านี้ | Phase 3 |

## Phase Roadmap
ผู้ถือหน้าต่างเวลาของ phase ที่นี่ที่เดียว เอกสารอื่นอ้างด้วยชื่อ phase

| Phase | Window | Content |
|---|---|---|
| Phase 1 — MVP | 120 นาทีนับจากเริ่มงาน | F-01…F-09 |
| Phase 2 — AI Investigation | `null` — owner: ผู้ใช้ (กำหนดเมื่ออนุมัติ bonus) | ร่างข้อเสนอตรวจสอบจาก failed deployments พร้อมอ้าง `deployment_id` |
| Phase 3 — Production hardening | `null` — owner: Engineering Lead | auth, integration, ข้อมูลเพิ่ม |

## External Dependencies
| Dependency | Owner | Blocks |
|---|---|---|
| GitHub repo บริษัท (`<COMPANY_REPO_URL>`) และสิทธิ์ push | ผู้ใช้ | Phase 1 (handoff) |
| Coolify instance + การเชื่อม Git source | DevOps ของบริษัท | Phase 1 (F-09) |
| AI endpoint และโควตาที่บริษัทจัดให้ | ผู้ใช้ | Phase 2 |
