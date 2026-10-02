# CONSTRAINTS — Deployment Reliability Dashboard

> ค่าที่ยังไม่มีใครวัดเขียนเป็น `null` พร้อมผู้รับผิดชอบการ calibrate ข้อความ "ต้อง/ห้าม/ควร" ใช้ตามความหมายของ ISO house style (ต้อง = บังคับ, ควร = แนะนำ)

## Legal and Compliance Constraints

| ID | Constraint | วิธีตรวจ |
|---|---|---|
| LC-01 | ข้อมูลนำเข้าต้องไม่มีข้อมูลส่วนบุคคล สคีมา CSV มี 7 คอลัมน์ที่กำหนดไว้เท่านั้น ไฟล์ที่มีคอลัมน์อื่นถูกปฏิเสธทั้งไฟล์ (`INVALID_FILE`) | DATA_MODEL เก็บ 7 field จาก CSV เท่านั้น (ตาราง `deployments` มี 8 คอลัมน์ โดยเพิ่ม `batch_id` ซึ่งระบบสร้างเอง) |
| LC-02 | หาก export จริงในอนาคตมีข้อมูลส่วนบุคคล (เช่น ชื่อผู้ deploy) ต้องทบทวน PDPA ก่อนเพิ่มคอลัมน์ | มี ADR/CHANGELOG บันทึกการเปลี่ยน data contract ก่อน implement |
| LC-03 | ห้ามมี credential จริง, URL ภายในบริษัท หรือข้อมูลที่นำเข้า อยู่ใน commit | `git ls-files` ไม่พบ `*.db`, CSV ข้อมูลจริง, `.env` |

## Technical Constraints

| ID | Constraint | วิธีตรวจ |
|---|---|---|
| TC-01 | ใช้ SQLite3 เป็นฐานข้อมูลเดียว (ไม่ใช้ DuckDB) | ARCHITECTURE ระบุ SQLite; ไม่มี dependency ฐานข้อมูลอื่น |
| TC-02 | รองรับ instance เดียว ไม่รองรับหลาย instance หรือ bulk import พร้อมกัน | DEPLOYMENT ตั้ง replica = 1 |
| TC-03 | Data contract: `deployment_id` ไม่ซ้ำ; `status` เป็น `success` หรือ `failed` เท่านั้น; `duration_seconds` เป็นจำนวนเต็มบวก; `deployment_date` เป็น ISO `YYYY-MM-DD`; `error_message` ว่างเมื่อ success และบังคับเมื่อ failed | test การนำเข้าไม่ถูกต้องทุกกรณีผ่าน |
| TC-04 | การนำเข้าต้อง atomic: validation ล้มเหลว = ไม่มีแถวใดถูกบันทึก | test ยืนยันจำนวนแถวไม่เปลี่ยนหลังถูกปฏิเสธ |
| TC-05 | ตัวเลขบนแดชบอร์ดต้องอ่านจาก SQLite เท่านั้น ห้ามคำนวณจาก CSV ดิบหลังนำเข้า | review โค้ด + test |
| TC-06 | Query ที่รับค่า filter ต้อง parameterized | review โค้ด |
| TC-07 | ขนาดไฟล์อัปโหลดสูงสุด `MAX_UPLOAD_BYTES` = **10 MiB (10,485,760 ไบต์)** (ผู้ใช้กำหนดเมื่อ 2026-10-02; ไฟล์ตัวอย่างประมาณ 2.1 MB) ไฟล์ที่ใหญ่กว่าถูกปฏิเสธและ UI ต้องเตือนผู้ใช้ (UI_SPEC.md Component Hierarchy: UploadSizeWarning) | TST-020; ค่าเป็นของ DevOps Operator ปรับได้ผ่าน environment variable |
| TC-08 | ฐานข้อมูลต้องอยู่บน persistent volume บน Coolify | CP-06 ผ่าน |

## Security Constraints

| ID | Constraint | วิธีตรวจ |
|---|---|---|
| SC-01 | ไม่มี authentication/authorization ใน phase นี้ (non-goal) จึงต้องจำกัดการเข้าถึงที่ชั้น Coolify/เครือข่ายภายใน ห้ามเปิดสาธารณะ | DEPLOYMENT ระบุการจำกัดการเข้าถึง; ความเสี่ยงบันทึกใน SECURITY |
| SC-02 | ข้อความ error จากข้อมูลต้องถูก escape เมื่อแสดงผลเพื่อกัน XSS | test ใส่ `<script>` แล้วไม่ถูก render เป็น HTML |
| SC-03 | ตรวจการเข้ารหัสและรูปแบบไฟล์ก่อนประมวลผล และตรวจขนาดไม่เกิน `MAX_UPLOAD_BYTES` (TC-07) ทั้งฝั่ง client (เตือนก่อนส่ง) และฝั่ง server (บังคับจริง) | TST-014 และ TST-020 |
| SC-04 | Container ต้องไม่รันเป็น root | Dockerfile ใช้ non-root user |
| SC-05 | Secrets (ถ้ามีในอนาคต) เก็บใน Coolify environment variables เท่านั้น | ไม่มี secret ใน repo |

## Business Constraints

| ID | Constraint | วิธีตรวจ |
|---|---|---|
| BC-01 | ต้องมี Test หรือ Validation ผ่าน, push ไป repo บริษัท และ deploy ผ่าน Coolify จนเปิดใช้งานได้ ภายใน 120 นาที | บันทึกเวลาเริ่มและ commit SHA ที่ push |
| BC-02 | ใช้ Claude Code/Codex และ token ที่มีอยู่ ไม่เติมเพิ่ม | ไม่มีการซื้อ/เติม token |
| BC-03 | เลือก blueprint เพียงหนึ่งตัว: `ddd-web-app` | เอกสารทั้งชุดมาจาก blueprint นี้ |
| BC-04 | เอกสารขั้นต่ำต้องครบครบทั้ง 20 ไฟล์ตาม `meta.generation_order` ของ `ddd-web-app` ที่ README.md ระบุ | ตรวจรายการไฟล์ใน `docs/` |
| BC-05 | Bonus AI workflow ต้องไม่ทำให้ MVP ล่าช้า ถือเป็น extension point เท่านั้น | SCOPE ระบุ out of scope พร้อม phase |

## Integration Constraints

| ID | Constraint | วิธีตรวจ |
|---|---|---|
| IC-01 | Source ต้อง push ไป GitHub repo บริษัท URL และสิทธิ์ push ยังไม่ได้รับ: ใช้ placeholder `<COMPANY_REPO_URL>` จนกว่าจะได้รับ | owner: ผู้ใช้ ให้ก่อนขั้นตอน handoff |
| IC-02 | Deploy ผ่าน Coolify โดยใช้ Dockerfile และ volume สำหรับ SQLite; instance และ credential เป็นของบริษัท | DEPLOYMENT มีขั้นตอนครบ; ไม่มี credential ในเอกสาร |
| IC-03 | Bonus AI ใช้ endpoint และโควตาที่บริษัทจัดให้ รายละเอียด (endpoint, โควตา) = `null` จนกว่าจะอนุญาตให้ทำ | owner: ผู้ใช้ |
| IC-04 | แหล่งข้อมูลคือไฟล์ CSV เท่านั้น ไม่มี integration กับ CI/CD หรือ log provider | SCOPE ระบุ out of scope |
