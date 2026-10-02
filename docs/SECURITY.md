# SECURITY — Deployment Reliability Dashboard

## Authentication and Authorization
Authentication ≠ authorization ≠ session: MVP **ไม่มีทั้งสามอย่าง** (non-goal, SC-01) ใครก็ตามที่เข้าถึงแอปได้ทางเครือข่ายใช้งานได้เต็ม จึงต้องจำกัดการเข้าถึงที่ชั้น Coolify/เครือข่ายภายในบริษัท และห้ามเปิดสาธารณะ นี่คือความเสี่ยงที่ยอมรับชั่วคราวของ Phase 1 บันทึกใน DEPLOYMENT.md เป็นขั้นตอนบังคับ

### Roles (เจ้าของ enum `role`)
| role | ความหมาย |
|---|---|
| `internal_user` | ผู้ใช้ที่เข้าถึงแอปได้ผ่านเครือข่ายภายใน ทำได้ทุก endpoint |

### Permissions Matrix
| Endpoint (API_SPEC.md) | `internal_user` |
|---|---|
| `GET /` , `GET /api/services`, `GET /api/failures` | อนุญาต |
| `POST /upload`, `POST /api/import` | อนุญาต |
| `GET /health` | อนุญาต (ไม่ต้องมีตัวตน) |

Phase 3 ต้องเพิ่มบทบาทที่แยกสิทธิ์นำเข้ากับสิทธิ์อ่าน ก่อนเปิดให้ผู้ใช้กว้างขึ้น

การยืนยันว่า "จำกัดเครือข่ายแล้ว" เป็นเงื่อนไขของ T-12 (TASKS.md Definition of Done): ต้องลองเข้าจากเครือข่ายภายนอกแล้วถูกปฏิเสธ

## PDPA Compliance Checklist
| Item | สถานะ |
|---|---|
| ข้อมูลส่วนบุคคลในชุดข้อมูล | ไม่มี (DATA_MODEL.md Data Classification: ทุกฟิลด์ `non_personal`) |
| Consent flow | ไม่จำเป็น เพราะไม่เก็บข้อมูลส่วนบุคคล |
| Data subject rights (เข้าถึง/ลบ/แก้ไข) | ไม่มีข้อมูลเจ้าของข้อมูลให้ใช้สิทธิ์ |
| Audit log | ไม่มีใน MVP (ดู Audit Logging Requirements) |
| เงื่อนไขทบทวน | ถ้า export จริงมีชื่อผู้ deploy หรือตัวระบุบุคคล ต้องทบทวน PDPA, อัปเดต DATA_MODEL.md ก่อนรับคอลัมน์ใหม่ (LC-02) |

## Threat Model
| ID | OWASP Top 10 | ภัยคุกคามในแอปนี้ | มาตรการ |
|---|---|---|---|
| THR-01 | A01 Broken Access Control | ไม่มี auth: ผู้ไม่ประสงค์ดีบนเครือข่ายอัปโหลด/อ่านข้อมูลได้ | จำกัดเครือข่ายที่ Coolify (SC-01); Phase 3 เพิ่ม auth |
| THR-02 | A02 Cryptographic Failures | ข้อมูลภายในถูกดักระหว่างทาง | TLS ที่ Coolify proxy (ดู Encryption Strategy) |
| THR-03 | A03 Injection (SQL) | ค่า `service` จาก query ถูกใช้ใน SQL | Query ทุกตัว parameterized (TC-06) |
| THR-04 | A03 Injection (XSS) | ทุกฟิลด์จาก CSV ที่ถูกแสดงมี HTML/JS (`error_message`, `service_name`, `environment`, `deployment_id`) รวมถึง `service` จาก query ที่ถูกสะท้อนใน dropdown | Jinja2 autoescape; test ทุกฟิลด์ด้วย `<script>` (SC-02, TST-012) |
| THR-05 | A04 Insecure Design | ไฟล์ใหญ่/รูปแบบผิดทำให้ทรัพยากรหมด | จำกัดขนาด 10 MiB (TC-07) บังคับที่ server และอ่านแบบตัดทันทีเมื่อเกิน; ตรวจ UTF-8 และคอลัมน์ก่อนบันทึก |
| THR-06 | A05 Security Misconfiguration | Container รันเป็น root; `*.db` ถูก commit | non-root user (SC-04); `.gitignore` (LC-03) |
| THR-07 | A06 Vulnerable Components | dependency มีช่องโหว่ | pin เวอร์ชันใน requirements; ตรวจก่อน release (ไม่มีเครื่องมือสแกนใน MVP) |
| THR-08 | A07 Identification/Authentication Failures | ไม่มี authentication | ยอมรับความเสี่ยงชั่วคราว (ข้างบน) |
| THR-09 | A08 Software/Data Integrity | CSV ที่ถูกแก้ไขแล้วนำเข้า | checksum กันซ้ำ; ไม่ใช่การรับรองความถูกต้องของต้นทาง |
| THR-10 | A09 Logging/Monitoring Failures | ไม่รู้ว่าใครนำเข้าอะไร | log ผลนำเข้าพร้อม `batch_id` (ARCHITECTURE.md Observability) |
| THR-11 | A10 SSRF | แอปไม่เรียก URL ภายนอกตามค่าผู้ใช้ | ไม่มีความเสี่ยงใน MVP; ต้องทบทวนเมื่อเชื่อม AI endpoint (Phase 2) |

**หมายเหตุ CSRF:** แอปไม่มี session/cookie จึงไม่มีสิทธิ์ที่ถูกขโมยผ่าน CSRF แต่ `POST /upload` ถูกยิงข้ามไซต์ได้ถ้าผู้โจมตีเข้าถึงเครือข่ายเดียวกัน จึงพึ่งการจำกัดเครือข่าย (SC-01) เช่นเดียวกับภัยอื่น

## Encryption Strategy
- **In transit:** TLS ที่ Coolify reverse proxy; แอปรับ HTTP ภายในเครือข่ายคอนเทนเนอร์เท่านั้น
- **At rest:** ไฟล์ SQLite บน volume; การเข้ารหัสระดับดิสก์/volume เป็นความรับผิดชอบของโครงสร้างพื้นฐาน Coolify ไม่ได้เข้ารหัสในแอป เหตุผล: ข้อมูลเป็น `internal` ไม่ใช่ข้อมูลส่วนบุคคล (DATA_MODEL.md); สถานะการเข้ารหัสของ volume ต้องยืนยันโดย DevOps ของบริษัท = `null` (owner: DevOps Operator)
- **Secrets:** ไม่มีใน MVP; อนาคตเก็บใน Coolify environment variables (SC-05)

## Audit Logging Requirements
MVP ไม่มี audit log เพราะไม่มีตัวตนผู้ใช้ให้บันทึก มีเพียง application log ตาม ARCHITECTURE.md Observability ระยะเวลาเก็บ log และ audit log: `null` — ค่าอยู่ที่ DATA_MODEL.md § Data Retention Policy (เจ้าของ Engineering Lead) ไม่ซ้ำที่นี่ Phase 3 ต้องบันทึก: ใคร, นำเข้าไฟล์ใด (sha256), เมื่อใด, ผล

## Incident Response Plan
เนื่องจากไม่มีข้อมูลส่วนบุคคล การแจ้งเหตุละเมิดต่อสำนักงานตาม PDPA (กรอบ 72 ชั่วโมง) จึงไม่เกิดขึ้นตามปกติ หากตรวจพบว่ามีข้อมูลส่วนบุคคลอยู่ในไฟล์ที่นำเข้า ให้ถือเป็นเหตุ:

1. หยุดการใช้งาน (หยุด container บน Coolify)
2. ระบุ batch จาก `import_batches` และขอบเขตข้อมูล
3. สำรองและลบ batch/ไฟล์ฐานข้อมูลที่ปนเปื้อนตามที่ DPO/เจ้าของข้อมูลกำหนด
4. แจ้งผู้รับผิดชอบด้านข้อมูลส่วนบุคคลของบริษัทเพื่อประเมินหน้าที่แจ้งเหตุภายใน 72 ชั่วโมง
5. อัปเดต DATA_MODEL.md และ CONSTRAINTS.md ก่อนเปิดใช้ใหม่

ระดับความรุนแรงของเหตุ (`incident_severity`) นิยามที่ RUNBOOK.md (เจ้าของ enum) ขั้นตอนปฏิบัติการอยู่ใน RUNBOOK.md Incident Response
