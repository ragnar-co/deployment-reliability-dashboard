# TESTING — Deployment Reliability Dashboard

## Test Strategy
| Layer | ขอบเขต | เครื่องมือ |
|---|---|---|
| Unit | ฟังก์ชัน validate CSV, สูตรตัวชี้วัด | pytest |
| Integration | นำเข้าลง SQLite จริง (ไฟล์ชั่วคราว) แล้ว query | pytest + SQLite ชั่วคราว |
| E2E | ผ่าน HTTP (TestClient) ตั้งแต่อัปโหลดถึงอ่านหน้า/JSON ครอบคลุม CP-01…CP-06 | pytest + FastAPI TestClient |
| Security | XSS, SQL injection ผ่านพารามิเตอร์, ไฟล์ผิดประเภท | pytest |

ไม่ใช้ browser automation ใน MVP (ADR-002 เวลาจำกัด) E2E ทำที่ชั้น HTTP + การตรวจ HTML

คำสั่งรัน (ต้องผ่านก่อน push — BC-01): `python -m pytest -q` ในโปรเจกต์ที่ติดตั้ง `requirements-dev.txt` ต้องผ่านโดยไม่ต้องมีไฟล์ตัวอย่างจริง ด้วย fixture CSV ขนาดเล็กที่ commit ได้ (ข้อมูลสังเคราะห์ ไม่ใช่ข้อมูลจริง ดู FR-12)

## Test Cases
| ID | Case | Type | Covers |
|---|---|---|---|
| TST-001 | นำเข้า fixture CSV ถูกต้อง ตัวเลขรวมตรงค่าคาดหวังที่คำนวณด้วยมือ | Integration | FR-01, AC-01, AC-04 |
| TST-002 | สูตรรายบริการ (success rate, เวลาเฉลี่ยเฉพาะ success) และการเรียงจากต่ำสุด | Unit/Integration | FR-06, AC-05 |
| TST-003 | ตัวกรองบริการเปลี่ยนตัวเลขและรายการ | Integration | FR-07, AC-06 |
| TST-004 | รายการล้มเหลวเรียงใหม่สุดก่อนและมี error ต้นฉบับ | Integration | FR-08, AC-07 |
| TST-005 | ปฏิเสธ (หลายแบบในไฟล์เดียวหลายไฟล์): คอลัมน์ขาด / status ไม่ถูกต้อง / วันที่ไม่ถูกต้อง / duration ≤ 0 / `deployment_id` ซ้ำในไฟล์ / error_message ไม่สอดคล้อง / ไฟล์ว่าง → ไม่มีข้อมูลบางส่วน | Integration | FR-02, FR-03, AC-02 |
| TST-006 | อัปโหลดไฟล์เดิมซ้ำ → `DUPLICATE_FILE` 409 | Integration | FR-04, AC-03 |
| TST-007 | ไฟล์ใหม่ที่มี `deployment_id` เดิม → `DUPLICATE_DEPLOYMENT` 409 และไม่เหลือแถวใหม่ (rollback) | Integration | FR-04, AC-03 |
| TST-008 | ไม่มีโค้ดอ่าน CSV เพื่อคำนวณตัวเลขหลังนำเข้า: ลบไฟล์ CSV แล้วตัวเลขยังคืนค่าได้ | Integration | FR-09, AC-08 |
| TST-009 | `GET /health` = 200 | Contract | FR-10, AC-09 |
| TST-010 | (P1) ตัวกรอง environment | Integration | FR-11, AC-10 |
| TST-011 | ไฟล์ตัวอย่างจริง (เมื่อมีในเครื่อง ไม่ใช่เงื่อนไขบังคับของ AC-11) นำเข้าได้ 36,527 แถว ค่ารวมตรง G-01 และ `release-validator` เป็นอันดับแรก | E2E | AC-04, AC-05, AC-11 |
| TST-012 | `<script>` ในทุกฟิลด์ที่แสดง (`error_message`, `service_name`, `environment`, `deployment_id`) และในค่า `service` ของ query ไม่ถูก render เป็น HTML | Security | SC-02 |
| TST-013 | ค่า `service` ที่มี `'` หรือ `;` ไม่ทำให้ query ผิดพลาด | Security | TC-06 |
| TST-014 | ไฟล์ไม่ใช่ UTF-8 ถูกปฏิเสธ | Security | SC-03 |
| TST-015 | log เป็น JSON มี `correlation_id`; ใช้ค่า `X-Request-ID` เมื่อส่งมา | Integration | ARCHITECTURE Observability |
| TST-016 | Pagination: 250 แถวล้มเหลวได้ 3 หน้า (100/100/50), `page` เกินหรือไม่ถูกต้องไม่ error, `limit`/`offset` ไม่ถูกต้องบน API = 422 `INVALID_PARAMETER` | Integration | API_SPEC `/api/failures`, UI_SPEC |
| TST-017 | Empty state: ฐานข้อมูลว่างแสดง "No data yet" และ API คืน `total = 0` | Integration | UI_SPEC |
| TST-018 | คอลัมน์เกิน, header ตัวพิมพ์ใหญ่, ชื่อคอลัมน์ซ้ำ → `INVALID_FILE`; BOM + CRLF ถูกรับ; `deployment_id` ซ้ำภายในไฟล์ → 422 `VALIDATION_FAILED` ระบุหมายเลขแถวแบบ 1-based; ลำดับการตรวจตาม API_SPEC | Integration | LC-01, API_SPEC |
| TST-019 | Container รันเป็น non-root และเขียน `/data` ได้ (ทำมือ/สคริปต์ docker) | System | SC-04, TC-08 |
| TST-020 | ไฟล์ = 10 MiB พอดีผ่านด่านขนาด; 10 MiB + 1 ไบต์ → `FILE_TOO_LARGE` 413 ทั้ง `/upload` (กล่อง error บนหน้า) และ `/api/import`; ไม่มีข้อมูลบางส่วน; ตั้ง `MAX_UPLOAD_BYTES` ต่ำลงแล้วค่าที่แสดงในข้อความและหน้าเว็บเปลี่ยนตาม | Integration | SC-03, TC-07, NFR-03 |
| TST-022 | หน้าเว็บมีข้อมูลขีดจำกัดสำหรับ client (เช่น `data-max-bytes`) ตรงกับ `MAX_UPLOAD_BYTES`; มีองค์ประกอบเตือน `role="alert"` ซ่อนอยู่เมื่อเริ่มต้น และมี fallback ฝั่ง server เมื่อ JavaScript ปิด (ทดสอบผ่าน HTML ส่วนพฤติกรรมเลือกไฟล์ใหญ่ตรวจมือ) | Integration + manual | UI_SPEC, NFR-03 |
| TST-021 | ตัวกรอง `service` ที่ไม่มีอยู่ = 200 ว่าง; dropdown ยังแสดงบริการทั้งหมดเมื่อเลือกบริการหนึ่ง | Integration | API_SPEC, UI_SPEC |

### E2E scenarios (CP trace)
| Scenario | CP-ID | ขั้นตอน | Delivery |
|---|---|---|---|
| E2E-01 | CP-01 | `POST /upload` ไฟล์ถูกต้อง → หน้ามีข้อความสำเร็จและทุกบริการ | UI |
| E2E-02 | CP-02 | `GET /?service=<s>` → ตัวเลขและแถวล้มเหลวเฉพาะบริการ พร้อม error | UI |
| E2E-03 | CP-03 | `GET /` → บริการแรกในตารางคือ success rate ต่ำสุด | UI |
| E2E-04 | CP-04 | `POST /upload` ไฟล์ผิดกติกา (รวม `deployment_id` ซ้ำในไฟล์ → 422) → กล่อง error; จำนวนแถวไม่เปลี่ยน | UI |
| E2E-05 | CP-05 | อัปโหลดซ้ำ/`deployment_id` ซ้ำผ่าน `POST /api/import` → 409 ไม่มีข้อมูลซ้ำ | system |
| E2E-06 | CP-06 | หลัง deploy บน Coolify (ใช้ fixture ไม่ใช่ข้อมูลจริงถ้าไม่จำเป็น): นำเข้า → redeploy → ตัวเลขเดิมยังอยู่ (ทำมือ บันทึกผลใน Sign-off) | system |

Contract test ครบทุก operation ใน API_SPEC.md: `GET /` (TST-003, TST-016, TST-017 หน้าเว็บ), `POST /upload` (TST-005/006), `POST /api/import` (TST-001/005/006), `GET /api/services` (TST-002), `GET /api/failures` (TST-004), `GET /health` (TST-009)

## Coverage Requirements
- เกณฑ์ coverage รวมที่บล็อก CI เป็นของ `AGENTS.md` (Testing Requirements) ซึ่งยังไม่มีค่า: **`null`** (เจ้าของ: Engineering Lead) จึงไม่มีการบล็อก CI ด้วย coverage ใน Phase 1 เอกสารนี้ไม่กำหนดตัวเลขทดแทน
- วิธีวัด: `pytest --cov=app` (ต้องติดตั้ง `pytest-cov` ถ้าจะวัด) เป็นแนวทาง

| Layer | เป้าหมาย | ผลต่อ CI |
|---|---|---|
| Unit | `null` | guidance |
| Integration | `null` | guidance |
| E2E | ครอบคลุม CP-ID ทั้ง 6 ข้อ | guidance (ตรวจโดย review ก่อน push; ไม่มี CI อัตโนมัติ) |

### Verification Log (2026-10-02)
- `python -m pytest -q`: 67 passed (รวม TST-011 กับไฟล์ตัวอย่างจริง: 36,527 แถว, 92.10%, 187.80 วินาที, 24 บริการ, `release-validator` 79.29%)
- ไฟล์ `test_data/deployments_valid.csv` ให้ 851 success / 149 failed / 85.10% / 325.11 วินาที และ `deployments_invalid.csv` ถูกปฏิเสธโดยไม่มีข้อมูลค้าง (test_checklist_data.py)
- TST-019 (ทำมือ): image build ได้; `id -un` = `app`; นำเข้าไฟล์ตัวอย่างลง `/data` ได้; restart คอนเทนเนอร์แล้วยังมี 36,527 แถว; Docker health = `healthy` (นี่คือการจำลอง CP-06 ด้วย Docker volume ในเครื่อง ไม่ใช่บน Coolify E2E-06 ยังต้องทำบน Coolify)
- TST-022 ส่วนพฤติกรรมเลือกไฟล์ใหญ่ในเบราว์เซอร์: **ยังไม่ได้ตรวจ**

## Security Test Results
ช่องบันทึกผล — ยังไม่ได้รันจนกว่าจะ implement
| Check | อ้างอิง | ผล | วันที่ |
|---|---|---|---|
| XSS ทุกฟิลด์ (TST-012) | A03 | ผ่าน | 2026-10-02 |
| SQL injection (TST-013) | A03 | ผ่าน | 2026-10-02 |
| Upload validation (TST-014, TST-018, TST-020) | A04 | ผ่าน | 2026-10-02 |
| Pen test | – | นอกขอบเขต Phase 1 (เพราะไม่มี auth ต้องจำกัดที่เครือข่าย) | – |

## Performance Test Results
Benchmark ผูกกับ NFR ใน PRD.md; ค่าเป้าหมายยังไม่ calibrate
| Benchmark | Traces to | Target | ผล |
|---|---|---|---|
| เวลาตอบหน้า Dashboard (ข้อมูลระดับไฟล์ตัวอย่าง) | NFR-01 | `null` (Engineering Lead) | ยังไม่วัด |
| เวลานำเข้าไฟล์ตัวอย่าง | NFR-02 | `null` (DevOps Operator) | วัดครั้งเดียวบนเครื่องพัฒนา: ≈ 0.22 วินาที (36,527 แถว) ไม่ใช่เป้าหมาย |

## UAT Sign-off
| Role | ตรวจ | ลงนาม |
|---|---|---|
| DevOps Operator | CP-01, CP-02, CP-04, CP-05, CP-06 | ยังไม่ลงนาม |
| Engineering Lead | CP-03 และตัวเลขตรง G-01 | ยังไม่ลงนาม |

เกณฑ์ผ่าน: ทุก P0 ใน PRD.md ผ่าน, ชุด test ผ่าน, `/health` = 200 บน Coolify
