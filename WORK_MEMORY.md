# WORK_MEMORY — 비비 프로젝트 개발 기억

> 이 파일은 자동 관리됨. 직접 수정하지 말 것.
> 비비, 클코, Claude.ai 세 곳이 공유하는 개발 장기기억.

---

## [최근 3일]
### 2026-04-15

#### 결정
- DB 스키마 변경 + timeline contact_id 복구 완료. 1) contacts 테이블 person_type VARCHAR(20) DEFAULT 미분류 컬럼 추가 2) 버그 기록 timeline 17건(16001522 번호) 삭제 → 313건 남음 3) backfill_contact_id.py 실행 → 199/313건 contact_id 복구(63.6%), 실패 1건(곽상일-미등록), 스킵 113건 4) normalize_name에 유니코드 제어문자(U+2068/U+2069 등) strip 추가로 CON-0312 김말자 동시감정 담당자2 추가 매칭 성공

#### 결정
- pipeline.py 검증 완료. 실제 payload 재전송 결과: [금윤미] bracket 추출→display_name=금윤미/CASE-20260415-금윤미(수정전 unknown), [채팅]나에게답장/[파일명]나에게답장→noise_skipped, 카카오페이→spam_skipped(contactName 있/없 둘 다). 버그 1건 발견+수정: bracket 추출 시 스팸이름도 name에 세팅해야 is_spam_sender()가 작동(수정전엔 spam name을 name에 미세팅→필터 무동작). 최종 로직: body에서 bracket 추출→name 무조건 세팅→process_message에서 is_spam_sender()처리.

#### 결정
- pipeline.py 4개 기능 추가: (1) rawMessage [닉네임] 추출 - sender_name 비어있을 때 re.match로 앞 대괄호 패턴 추출, SPAM_SENDERS 아닌 경우만 name으로 사용 (2) is_noise() - [.+] 나에게 답장 패턴 타임라인만 저장 분류/알림 스킵 (3) SPAM_SENDERS 상수 + is_spam_sender() - 카카오페이/토스 등 공식채널 완전 무시 (4) generate_case_id() - contact_id unknown 포함 시 name[:3] 또는 순번(001~)으로 재생성. 구문OK + 4개 시나리오 전부 통과.

#### 결정
- meeting-recorder server.py에 extract_call_info() 함수 추가. 통화녹음 파일명(통화_녹음_{상대방}_{YYMMDD}_{HHMMSS})에서 이름/번호 파싱. form 필드(phone_number, contact_name) 우선, 없으면 파일명 fallback. webhook sender/sender_name에 반영. 5/5 파싱 테스트 OK.

#### 결정
- contact_resolver.py 수정: resolve_contact 진입 시 matching_log confirmed 우선 조회 적용. _lookup_confirmed_match(nickname) 함수 추가 — sender_name 있고 phone 없을 때 matching_log에서 result=confirmed 최신 기록 조회 후 즉시 반환(score=100, basis=confirmed_match). 기존 exact/partial/fuzzy 로직은 그대로 유지. 테스트4개 전부 PASS. server.py 수정 불필요 확인.

#### 결정
- 작업D 완료: ViviApp 사진/서류 수신 → Upstage 자동 연결. meeting-recorder server.py의 /upload-photo, /upload-document 핸들러를 doc_pipeline.process_document 직접 호출로 교체. 모든 사진/서류를 Upstage OCR+분류+필드추출 후 document_parse_results DB 저장 + Telegram 📎 서류수신 알림 발송. 원시 알림 제거. Upstage 실패 시 기존 webhook 폴백 유지. UPSTAGE_API_KEY를 /root/meeting-recorder/.env에 추가. 실 API 호출 검증 완료(confidence=1, viviapp_photo/viviapp_document source로 DB 저장).

#### 현황
- ViviApp 통화녹음 업로드 정상 동작 확인. nginx /recording-upload → 5113/upload-recording 이미 설정됨. FileWatcherService 생존 확인(오늘 09:13/09:18/09:33 업로드 성공). 업로드 안 된다는 신고는 특정 시간대 일시적 현상으로 판단, 수정 없음.

#### 결정
- 작업C 수신 중복 알림 제거 + 발신 1층 처리 완료. bibi-gateway: kakao/sms/pc_kakao 원시 알림 제거(photo/call/meeting 유지). vivi-layer1 classifier.py: 발신 intent 추가(request_contact, quote_estimate, follow_up, reply_info). pipeline.py: 발신 urgency=low 고정, 발신 simple_reply 알림 생략. notify.py: 📤 발신 포맷 추가(case_id, intent 표시). 검증: 수신 1층만 알림, 발신 연락처요청 📤 알림, 발신 넵 알림 생략 모두 확인.

#### 결정
- Upstage API 엔드포인트 수정 완료. 올바른 URL: POST /v1/document-digitization (suffix 없음), output_formats=["text","markdown"] 파라미터 필수. 실전 검증: PDF 7페이지 OCR text_len=25254, mock=False, DB 저장 확인. 파이프라인 전체 정상 동작.

#### 결정
- 통화녹음 STT → 1층 파이프라인 연결 완료. meeting-recorder/server.py의 _send_webhook 호출에 sender(전화번호), sender_name(이름) 필드 추가. 기존 bibi-gateway → message_jobs → layer1 worker 경로 활용. 검증: layer1_messages에 channel=call, contact_id=CON-0319(연락처 resolve), intent=new_inquiry, urgency=immediate, has_embedding=t 저장 확인

#### 결정
- 작업B Upstage Document AI 1층 파이프라인 구축 완료. bibi-gateway(5114)에 POST /document-parse 라우트 추가 (기존 /webhook/bibi-incoming, /notify 무변경). 생성 파일: upstage_client.py(mock모드+실전전환), doc_pipeline.py(MinIO→Upstage→DB→텔레그램). DB: document_parse_results 테이블 생성(vector(768), JSONB, 인덱스 3개). MinIO vivi-documents 버킷 사용. API 키(UPSTAGE_API_KEY) /root/.env에 자리 만들어둠 — 키 입력 시 즉시 실전 전환.

#### 결정
- 1층 3단계 완료: ko-sroberta(jhgan/ko-sroberta-multitask 768dim) 임베딩+pgvector HNSW 인덱스로 케이스 매칭 구현. case_matcher.py 생성. threshold=0.70, lookback=30일. embedding 컬럼 layer1_messages에 추가. 검증: 교통사고상담 vs 교통사고진행확인 cosine_sim=0.6858로 신규케이스(threshold 미달), 다른발신자=다른케이스. _new_case_id가 결정론적(contact_id+날짜)이라 threshold 미달도 같은 케이스 ID 배정됨. 실데이터 쌓이면 threshold 튜닝 예정.

#### 결정
- 1층 4단계 완료: notify.py 생성(분류결과 텔레그램 알림), bibi-gateway에 /notify 라우트 추가(기존 send_telegram 경유), pipeline.py 알림 연결. 알림 생략 조건: direction=outgoing 또는 urgency=low+intent=simple_reply. 검증: 신규상담→notification_sent, 단순응답 넵→생략, 발신→생략. DB저장은 모든 케이스 정상. 3단계(ko-sroberta 케이스매칭) 미구현 상태.

#### 결정
- 1층 2단계 완료: contact.py(contact-resolver 5111 연동, 실제 응답필드 contactId/displayName/isNew 맞춤), classifier.py(Kiwi 형태소+키워드 규칙, Gemini 폴백 구조 완성, 키 없으면 비활성), urgency.py(채널/의도/키워드 기반 4단계), pipeline.py 전체 파이프라인 연결. 테스트 5개 전부 통과: new_inquiry/document_submit/progress_check/simple_reply=정확, phone채널=immediate 정확. 규칙 분류 신뢰도 0.7~0.9 달성.

#### 결정
- 0층 모니터링 작업B+C 완료. B: /root/vivi_env/daily_report.py 생성, 매일 KST 09:00(UTC 00:00) 크론, 채널별 감지 건수+평일 0건 경고→bibi-gateway 웹훅→텔레그램. C: /root/vivi_env/e2e_test.py 생성, 매일 KST 06:00(UTC 21:00) 크론, 합성 메시지→파이프라인 검증→테스트 데이터 삭제→Bot API 직접 텔레그램 알림

#### 결정
- 1층 이해(Comprehension) 텍스트 입구 1단계 뼈대 구축 완료. /root/vivi-layer1/ 생성: config.py, pipeline.py, db.py, worker.py. DB 테이블 3개 생성: layer1_messages(기존 messages는 Honcho 시스템 충돌로 이름 변경), layer1_classification_logs, message_jobs. bibi-gateway/server.py에 enqueue_message() 추가(기존 텔레그램 알림 유지). Hermes venv에 psycopg 설치. vivi-layer1 systemd 서비스 등록 및 기동. 검증: 웹훅 수신→message_jobs(status=done)→layer1_messages 저장 전 흐름 정상.

#### 결정
- ViviApp 대면 상담 자동 감지 파이프라인 완성. VAD(Silero v5)+화자인식(ECAPA-TDNN) → 사용자(sim=0.519)+타인(sim=0.106) 감지 → 자동 녹음 → 서버 업로드 SUCCESS. 파일: auto_meet_1776181160676.wav(1.83MB) 수신 확인. 핵심 수정: MIC AudioSource 통일, 임베딩 등록 후 서비스 재시작 필요, MEETING_DETECT_WINDOW_SEC=60, VAD_MIN_THRESHOLD=0.03.

#### 결정
- 1층 입구 4개 확정: 텍스트(카톡/문자) + 서류/이미지(사진/PDF) + 음성(통화/대면녹음) + 외부자료(판례/법령/통계)
- Upstage Document AI + CLOVA OCR 1층에 포함 (서류 이해도 1층 역할)
- 리턴제로 STT도 1층에 포함 (음성 이해도 1층 역할)
- 외부자료(판례 17만건 등) 분류/임베딩/태깅도 1층 역할

#### 인사이트
- 1층 분류 체계는 딥리서치로 뽑을 수 없음. 대표님 실무 분류 체계(발신자 유형, 서류 유형, 의도, 긴급도 기준)가 설계의 핵심
- 발신자 유형이 의도 분류보다 선행해야 함: 같은 "서류 보내드립니다"도 고객/보험사/병원에 따라 의미가 다름
- 발신자 유형 누락 발견: 설계사, 보호자도 연락 옴. SOUL.md 때처럼 ACTA 인터뷰로 전체 분류 체계 뽑아내기로 결정
- 서류 분류가 방대함 (피듀피, 소득자료, 보험계약정보 등) → 대분류로 시작하고 실전에서 세분류 추가하는 방식 채택 (비비 철학: 확실한 건 자동, 애매한 건 1번 확인, 학습해서 확대)
#### 결정
- 1층(이해) 구현 도구 최종 확정: 텍스트 이해(kiwipiepy + Gemini Flash-Lite + ko-sroberta) + 서류/이미지 이해(Upstage Document AI + CLOVA OCR 백업) + 저장검색(pgvector + SKIP LOCKED) + 파이프라인(psycopg3, pydantic-settings, structlog, tenacity, httpx)
- Upstage Document AI를 1층에 포함: 사진/PDF 서류 분류+OCR도 "이해"의 범위. 카톡으로 진단서 사진 오면 뭔 서류인지 판별하는 것이 1층 역할
- Kiwi 규칙 분류 + SKIP LOCKED + Upstage 전부 처음부터 구현 (대표님 방침: 난이도/비용 비슷하면 미리 다 만들어둔다)

#### 인사이트
- 딥리서치 결과를 "지금 불필요"로 잘라내는 것은 확장성 설계 무시. 대표님 철학: 기억 인프라 5개 깔 때와 같은 논리로, 나중에 바꿔끼우는 삽질이 더 비싸다
#### 결정
- 트랙A 대면감지 전체 파이프라인 완성: VAD(prob=0.733) + 화자인식(사용자 sim=0.519, 타인 sim=0.106) + 대면판정 + 자동녹음 + 서버업로드(1.83MB) end-to-end 성공
- 1층 오케스트레이터: Plain Python 확정 (n8n 복원 안 함, LangGraph는 Phase 2)
- 1층 분류: Kiwi 규칙엔진 불필요 — LLM(Gemini Flash-Lite) 전량 처리해도 월 $0.11, 규칙엔진 만드는 삽질 비용이 더 큼
- PostgreSQL SKIP LOCKED 작업큐 불필요 — 일 50-200건 규모에서 동기 처리로 충분
- 기억 인프라 5개(pgvector+Qdrant+Neo4j+Graphiti+Honcho) Docker 유지 확정 — 1층에서는 pgvector만 연결하되 나머지는 대기 상태 유지
- WORK_MEMORY 프로젝트 지시 보완: 매 응답 시 드래프트 기록 + 대화 종료 시 최종 체크 규칙 추가

#### 인사이트
- 통합 메신저 아이디어: 고객별 전 채널(카톡/문자/전화) 타임라인 통합 뷰. 0층 감지 + 1층 분류 + PostgreSQL 저장이 완성되면 UI만 씌우면 됨. 플로팅 오버레이 카드의 풀버전
- 클코 WORK_MEMORY 보고 규칙이 CLAUDE.md에 누락되어 있었음 — 보고했다는 보고만 하고 실제 파일 수정은 안 한 케이스

#### 현황
- Gmail 폴링 파이프라인 수리 완료: 제목 패턴 WORK_MEMORY|로 통일, 병합 후 자동 git push 추가
- 드래프트 수거 → WORK_MEMORY.md 병합 → 압축 → git push 자동화 확인

#### 결정
- 1층 분류체계 인터뷰 완료. 핵심 구조 확정:

발신자 유형 9개: 고객, 고객보호자, 보험사담당자, 설계사, 업무관련자, 회사식구, 가족, 지인(타손사포함), 광고/일회성

판단 순서: 급한가? → 누구지? → 무슨 건이지?

긴급도 기준(대표님 실제 패턴): 전화=급함의 신호, 서류 있으면 먼저 챙김, 내일 일정인데 준비 안 됨, 고객이 현장(병원 등)에서 막힘. FM의 "즉시 답장"이 아니라 상황 기반 판단.

케이스 구조: 고객(큰 폴더) > 사고(하위 폴더). 한 고객 여러 건 가능하나 보통 진행 중 1건.

사고 유형: 생상(개인보험-후유장해/진단금/기타/면책), TA(대인1/대인2/자손자상, 단독or병합, 산재병합), 일반배상, 산재, 국가배상(가끔)

서류 유형 대분류: 의료기록류(초진기록지/구급일지/영상판독지/조직검사/수술기록지/입퇴원확인서/의사오더지/간호기록지), 진단소견류(진단서/후유장해진단서/소견서/의료자문회신서/향후치료비추정서), 사고행정류(교통사고사실확인원/사고경위서), 보험법률류(지급내역서/보정서/의뢰서/의견서/손해사정서/보험증권/자동차보험증권/단체보험증권/배상보험증권/판결문/금감원자료/금감원분쟁조정결과), 비용소득류(진료비내역서/진료비영수증/소득관련자료/재직증명서/급여명세서), 참고자료(맥브라이드/장해분류표/호프만계수/통계소득/도시일용임금/소송가기준/위자료기준/판례/의학용어사전)

초기 상담 흐름: 연락수신 → 경로 파악 → 사고내용 파악 → 서류요청 (백프로)

#### 인사이트
- 대표님이 전화 내용을 자주 까먹음 → 비비가 통화 요약 + 약속사항을 자동 추적하면 "또 안내하는" 문제 해결
- 가급적 메시지로 로그 남기려는 습관 → 비비가 전화 내용도 자동 로그화하면 이 부담 제거
- 의견서는 고객 서류가 아니라 대표님이 보험사에 보내는 업무 양식
- 변호사법 위반 항상 조심해야 함 → 비비 3층 판단에서 경계선 알림 기능 필요

## 결정
- ViviNotificationListener(NotificationListenerService)가 갤럭시 배터리 최적화에 의해 반복적으로 죽는 문제 발생
- SMS/카톡 수신 감지를 AccessibilityService로 전환 완료 (2026-04-15)
- AccessibilityService는 시스템이 보호하므로 배터리 최적화에 죽지 않음

## 이슈
- AccessibilityService로 SMS 알림 감지 시 발신자 번호 파싱 버그 발견
- 실제 발신번호 대신 삼성 메시지 앱 내부 ID(예: 16001522)가 찍힘
- 로그 확인 후 수정 필요 (event.getText(), getParcelableData() 등 어떤 값이 오는지 먼저 확인)

## 현재 0층 감지 구조 (업데이트)
- 카톡 발신: KakaoOutgoingService (AccessibilityService) — 변경 없음
- 카톡 수신: AccessibilityService로 전환 (NotificationListener에서 변경)
- 문자 수신: AccessibilityService로 전환 (NotificationListener에서 변경)
- 문자 발신: SmsOutgoingObserver — 변경 없음
- 통화녹음/대면녹음/사진: 기존 유지

#### 결정
- 1층 텍스트 입구 작업지시서 완성: 4단계 구현 (뼈대→분류→케이스매칭→알림업그레이드)
- 1단계(뼈대) 클코 지시 시작: 프로젝트 구조 + DB 테이블 + message_jobs 큐 + worker.py + bibi-gateway 연결

#### 현황  
- Gmail 폴링 파이프라인 수리 완료 (제목 패턴 WORK_MEMORY| + git push 자동화 + 1분 폴링)
- 문자 발신 감지 AccessibilityService 전환 완료 (ContentObserver→AccessibilityService 내 ContentObserver 등록으로 안정성 확보)
- 0층 안정성 개선 3건 완료 (중복 등록 방지, 메모리 누수, debounce 500ms)
- 헬스체크 강화 완료 (Gmail OAuth + 마지막 수거 시각 + git 상태 + 텔레그램 알림, 매시 정각)

#### 결정
- 0층 모니터링 체계 3종 구축 완료:
  1. Uptime Kuma(Docker 3001): 전 서비스 10개 1분 간격 감시 + 다운 시 텔레그램 즉시 알림. nginx 프록시: stayz90.com/status/
  2. 일일 감지 리포트: 매일 KST 09:00 채널별 감지 건수 + 0건 경고. 첫 실행 결과 4/14 기준 총 112건 정상
  3. E2E 파이프라인 테스트: 매일 KST 06:00 합성 메시지 → 전체 파이프라인 검증 → 성공/실패 텔레그램 알림

- 1층 1단계(뼈대) + 2단계(분류) 완료. 4단계(알림 업그레이드) 진행 중.
  - messages 테이블명 충돌 → layer1_messages / layer1_classification_logs로 변경
  - Kiwi 규칙 기반 의도 분류 5/5 정확 확인
  - Gemini 폴백은 API 키 발급 후 .env에 넣으면 자동 활성화

#### 인사이트
- 버그는 영원히 안 사라짐 — "빨리 알고 빨리 고치는 체계"가 답
- Uptime Kuma 비밀번호 변경 필요 (초기값 Vivi2026!)

#### 결정
- 1층 이해(Comprehension) 레이어 4단계 전부 완료:
  1. 뼈대 (큐 + worker) ✅
  2. 분류 (Kiwi 규칙 기반 intent/urgency) ✅
  3. 케이스 매칭 (ko-sroberta 768dim + pgvector HNSW) ✅
  4. 알림 업그레이드 (smart notification — low/simple_reply 생략) ✅
- 전체 파이프라인: 메시지 수신 → 의도/긴급도 분류 → 임베딩+케이스 매칭 → 스마트 텔레그램 알림. API 호출 없이 로컬 처리.
- ko-sroberta cosine threshold 0.70 설정. 같은 발신자+같은 날이면 contactId 기반으로 동일 케이스 귀결 (임베딩은 보조 수단).
- 테이블: layer1_messages, layer1_classification_logs (messages 테이블명 충돌 방지)

#### 인사이트
- 실데이터에서 "네네~" → simple_reply/low 정확 분류 확인 — Kiwi 규칙 기반이 실전에서 작동
- 유사도 threshold 튜닝은 실제 오분류 사례 축적 후 조정 예정

#### 결정
- 작업A 완료: 통화녹음(meeting-recorder) → 1층 파이프라인 연결. server.py에 sender/sender_name 2줄 추가. 기존 STT 로직 무변경.
  - 검증: layer1_messages 저장 ✅, 연락처 resolve ✅, 의도분류(new_inquiry) ✅, 긴급도(immediate) ✅, 임베딩 ✅
- 작업B 완료: Upstage Document AI 서류 파이프라인 구축.
  - upstage_client.py + doc_pipeline.py 생성
  - document_parse_results 테이블 (vector(768), JSONB, 인덱스 3개)
  - POST /document-parse 엔드포인트 추가
  - API 키(.env에 UPSTAGE_API_KEY) 넣으면 mock→실전 즉시 전환
  - Upstage 무료 크레딧 $10 확보 완료
- 작업C(중복알림 제거 + 발신 분류) 진행 중

#### 인사이트
- 통화녹음 1층 연결은 기존 웹훅 경로를 그대로 활용해서 2줄로 해결 — 새 경로 만들 필요 없었음
- Upstage Document AI: Parse $0.01/page + Extract $0.03/page + Classify 무료(베타). $10 크레딧이면 250페이지 처리 가능

#### 결정
- 작업C 완료: 수신 중복알림 제거 + 발신 1층 처리
  - bibi-gateway: kakao/sms/pc_kakao 원시 알림 제거 (photo/call/meeting은 유지)
  - 발신 intent 4개 추가: request_contact, quote_estimate, follow_up, reply_info
  - 발신 urgency=low 고정, reply_simple은 알림 생략
  - 📤 발신 알림 포맷: 채널/상대방/케이스/intent/내용
  - 검증 4건 전부 통과

- 1층 이해(Comprehension) 레이어 전체 완성:
  - 텍스트(카톡/문자): 수신 분류 + 발신 분류 + 스마트알림 ✅
  - 통화녹음: STT → 1층 자동 연결 ✅  
  - 서류/사진: Upstage Document AI 연동 ✅ (API키 실전 전환 완료)
  - 중복알림 해결: 텍스트는 1층 알림만, 파일류는 원시 유지 ✅

#### 인사이트
- 1층은 "비비의 귀"에서 "비비의 이해력"으로 진화 — 단순 감지(0층)와 이해(1층)가 분리되어 각자 역할이 명확해짐

#### 이슈
- 1층 연락처 매칭 문제: 카톡 [금윤미]가 unknown으로 표시. contacts에 동일 이름 있음에도 매칭 실패
  - 원인 추정: 1층 worker가 전화번호 기반 resolve만 하고, 카톡 닉네임 → displayName 매칭을 안 하고 있을 가능성
  - 0층 재설계(4/11)의 매칭로그 구조가 1층에 연결 안 됐을 수 있음
  - 확인 필요: pipeline.py의 연락처 resolve 로직에서 닉네임 매칭 코드 유무

- 1층 분류 품질 부족: "주치의 자문 이야?" → 기타/일반문의로 분류. 손해사정 도메인 키워드(주치의자문, 동의, 감정, 자문료, 소견서 등) 미반영
  - Kiwi 규칙에 도메인 키워드 추가 필요 (대표님 도메인 지식 필요)

#### 결정
- 사진/서류 자동 Upstage 연결: 모든 사진 필터 없이 전부 Upstage에 보내기로 결정 (대표님 지시). 작업D 지시서 작성 완료

#### 결정
- 작업D 완료: 사진/서류 자동 Upstage 연결
  - /upload-photo, /upload-document 모두 Upstage OCR → DB → 📎 텔레그램 자동 처리
  - Upstage 실패 시 기존 원시 webhook 폴백 (알림 누락 방지)
  - meeting-recorder .env에 UPSTAGE_API_KEY 추가

- 1층 이해(Comprehension) 레이어 전 채널 완성:
  - 카톡/문자 수신+발신: Kiwi 분류 + 케이스매칭 + 스마트알림 ✅
  - PC카톡 발신: 동일 ✅
  - 통화녹음: STT → 1층 자동 ✅
  - 대면녹음: STT → 1층 자동 ✅
  - 사진/서류: Upstage OCR → DB → 알림 자동 ✅
  - 원시 알림: 전 채널 제거 완료 (1층 알림으로 대체)

#### 이슈 (미해결, 다음 작업)
- 연락처 매칭: 카톡 닉네임 [금윤미]가 contacts에 있는데도 unknown 표시. 1층 resolve가 닉네임 매칭 안 하고 있을 가능성
- 분류 품질: 손해사정 도메인 키워드 미반영. "주치의 자문" → 기타로 분류. Kiwi 규칙 튜닝 필요 (대표님 도메인 지식 필요)

#### 결정
- 1층 품질개선 3개 작업 병렬 완료 (2026-04-15):

작업A (pipeline.py):
  - rawMessage [닉네임] 추출 → sender_name 비어있을 때 fallback
  - 스팸 필터: 카카오페이/카카오뱅크/토스 등 공식채널 완전 무시 (저장/분류/알림 전부 스킵)
  - "나에게 답장" 노이즈 필터: 타임라인만 저장, 분류/알림 스킵
  - CASE ID unknown 방어: contactId앞8자 → name앞3자 → 순번(001~)

작업B (contact_resolver.py):
  - resolve_contact 진입 시 matching_log confirmed 우선 조회
  - 대표님이 텔레그램에서 확인한 닉네임-연락처 매핑 자동 적용 (score 100)
  - confirmed 없으면 기존 exact/partial/fuzzy 로직 그대로

작업C (meeting-recorder/server.py):
  - extract_call_info() 함수 추가: 통화녹음 파일명에서 이름/번호 파싱
  - form 필드 우선, 없으면 파일명 fallback
  - webhook payload sender/sender_name에 파싱 결과 반영

#### 이슈 (미해결)
- 분류 품질 (지인+고객 톤 구분): 규칙 기반으로 못 푸는 문제. 4층(기억) 이상에서 관계 맥락으로 해결 필요
- 실전 검증 대기: 다음 카톡/통화녹음에서 unknown → 이름 전환 확인 필요

#### 결정
- 1층 품질 개선 3작업 병렬 완료 (2026-04-15):

  작업A (pipeline.py):
  - rawMessage [닉네임] 추출 → resolve_contact 연결 완료. sender_name 비어있을 때 대괄호 패턴 파싱
  - 스팸 필터: 카카오페이/카카오뱅크/토스 등 공식채널 완전 무시
  - "나에게 답장" 노이즈: 타임라인 저장만, 분류/알림 스킵
  - CASE ID unknown 방어: 미매칭 시 이름 또는 순번으로 생성

  작업B (contact_resolver.py):
  - matching_log confirmed 우선 참조 추가. 대표님이 텔레그램에서 확인한 닉네임-연락처 매핑 자동 적용 (score 100)
  - 기존 exact/partial/fuzzy 로직은 유지 (confirmed 없을 때 폴백)

  작업C (meeting-recorder/server.py):
  - extract_call_info() 함수 추가. 통화녹음 파일명에서 이름/번호 파싱
  - form 필드 우선, 없으면 파일명 fallback
  - webhook payload의 sender/sender_name에 파싱 결과 전달

- 실제 payload 기반 검증 6건 전부 PASS
- 과정에서 발견한 버그(스팸 이름 빈문자열 처리) 즉시 수정

#### 이슈 (다음 작업)
- DB 스키마 재배치 필요: timeline에 분류결과(category)/긴급도(urgency) 컬럼 없음. 1층 결과 저장 구조 논의 중
- 분류 품질: 도메인 키워드 튜닝 필요 (지인+고객 캐주얼 톤 구분은 규칙 기반 한계, 4층 이상에서 해결)
#### 결정
- 1층 품질 개선 3건 완료 (작업A+B+C 병렬 실행):

  작업A (pipeline.py):
  - rawMessage에서 [닉네임] 추출 → resolve_contact에 name 전달
  - 스팸 필터: 카카오페이/카카오뱅크/토스 등 공식채널 완전 무시
  - "나에게 답장" 노이즈 → 타임라인만 저장, 분류/알림 스킵
  - CASE ID unknown 방어: 미매칭 시 이름 또는 순번 사용

  작업B (contact_resolver.py):
  - matching_log confirmed 결과 우선 참조 (score 100 즉시 반환)
  - 한 번 확인된 닉네임은 다시 묻지 않음

  작업C (meeting-recorder/server.py):
  - extract_call_info() 함수 추가: 통화녹음 파일명에서 이름/번호 파싱
  - form 필드 우선, 없으면 파일명 fallback
  - webhook payload의 sender/sender_name에 결과 반영

- 검증: 실제 payload 6건 replay 테스트 전부 PASS
- 과정 중 버그 1건 수정: bracket 추출 시 스팸 이름 처리 순서 오류

#### 인사이트
- 클코 테스트 시 가짜 payload 직접 만들지 말 것. 실제 로그에서 원본 replay가 진짜 테스트 (삽질방지 교훈 추가)

#### 논의 중
- DB 스키마 재배치 필요: timeline에 category/urgency 컬럼 없음, contacts에 kakaoNickname 누락 가능, unknown 케이스 정리 필요
- 1층 분류 품질: 지인+고객 관계에서 업무/잡담 구분은 규칙으로 한계. 4층(기억) 이상에서 맥락 기반으로 잡아야 할 영역

#### 결정
- 1층 분류 방향 확정:
  - 키워드 분류 폐기: 실제 데이터 84%가 구어체("ㅇ","엉","그려")라 키워드 매칭 불가능. Kiwi 코드는 비활성화(삭제 아님, 2~3층 재활용)
  - person_type 4개(고객/담당자/업무관계인/미분류): 이벤트 기반 확정만. 키워드 매칭 안 함
  - 확정 이벤트: 수임계약서 서명→고객, 병원서류 수신(보낸사람=대상자)→고객, 명함 OCR→담당자
  - 보험계약조회/소득정보 링크 발신→미분류 시에만 고객 (지인에게도 보낼 수 있어서 확정 이벤트에서 제외 검토)
  - 키워드 학습 자동화: 분류 확정 데이터가 쌓이면 3~6개월 주기 크론잡으로 독점 키워드 자동 추출 → 분류 정확도 점진적 개선

- 핵심 인사이트: 1층은 "누구인지"만 정확히. 메시지 내용 이해는 2~3층에서 대화 흐름째로 처리
  - 같은 "자문" 키워드도 고객/담당자 양쪽에서 사용 → 단일 메시지 키워드 분류 불가능 확인
  - 사람별 묶기(contact_id 연결)가 person_type보다 선행 과제

- timeline contact_id 복구: 330건 중 199건 매칭 성공(실질 96.6%), 1건 실패(미등록), 130건 스킵(시스템/스팸)

#### 이슈 (다음 작업)
- cases 테이블 0건: 케이스 생성/연결이 안 되고 있음. 상담중/진행중/종결 관리의 전제조건
- ViviApp 통화녹음 업로드 시 READ_CALL_LOG로 전화번호를 form 필드에 같이 보내도록 수정 필요 (매칭 정확도 향상)
- 테스트 payload는 직접 만들지 말고 실제 로그에서 원본 replay할 것 (삽질방지)

### 2026-04-14

#### 결정
- meeting-recorder/server.py에 _save_speech_metrics 추가: 리턴제로 utterances(start_at ms + duration ms)에서 말속도(WPM), 침묵간격(avg/max/count) 추출 → signal_metrics 저장. process_call() 내 format_transcript 직후 호출. meeting-recorder 서비스 재시작 완료

#### 결정
- signal_metrics 테이블 생성 + signal_analyzer.py 크론 등록(매일 KST 09:30). transcribe_calls.py 말속도/침묵 추출은 파일 미존재로 보류. timeline 컬럼: tenant_id/timestamp/source/direction/raw_message (contact_id 전부 NULL, tenant_id 기준 분석). 분석 결과: response_time_sec 21건, contact_frequency 10건, message_length 3건 signal_metrics 저장

#### 결정
- 환율 크론 등록: ecos_collector.py 매일 UTC 00:00(KST 09:00) 실행. update_work_memory.py 카테고리 현황/이슈 추가 → 총 6개(결정/인사이트/논의중/보류/현황/이슈)

#### 결정
- 0층 생활형 API 현황 확인: 날씨(vivi_env/weather.py)+미세먼지(air_quality.py) 크론 등록완료(3시간마다+KST06:00). 환율은 ecos_collector.py 구현됨 but 크론 미등록. 공휴일 매월1일. systemctl 서비스 없음, 전부 크론 기반.

#### 결정
- WORK_MEMORY 보고 규칙 간소화: 로컬+VPS CLAUDE.md 동기화 완료. 긴 규칙 → 핵심 4줄로 압축

#### 결정
- WORK_MEMORY 보고 규칙 추가 완료: 로컬 CLAUDE.md + VPS CLAUDE.md 양쪽에 보고 규칙 동기화. 조회·확인 포함 모든 작업 종료 시 기록 의무화, 카테고리 4종(결정/현황/이슈/인사이트) 정의

#### 결정
- 기억 공유 3트랙(A/B/C) 완료: 비비 자체 갱신 루프 + 안전성 강화 + Gmail 폴링 5분 최적화

#### 결정
- update_work_memory.py 설치 완료 및 테스트

#### 결정
- 기억 인프라 5개 설치 완료: pgvector(v0.6.0) + Qdrant(6333) + Neo4j(7474/7687) + Graphiti(8000) + Honcho(8100)
- Zep → Graphiti 변경 (Zep 셀프호스팅 deprecated)
- Honcho self-hosted 선택 (데이터 주권 원칙)
- API Haiku 월 ~3,000원 구조 확정 (비용 최적화는 나중에)
- WORK_MEMORY 기억 공유 시스템 도입

#### 논의 중
- Cloud Scheduled Task vs API 비용 최적화 — 지금은 API, 사용자 늘면 재검토
- Claude.ai에서 비비 스킬 직접 호출 — 텔레그램으로 비비한테 시키면 됨, 별도 구현 불필요

#### 인사이트
- 에이전트 접근성 병목 = 기술이 아니라 UX ("사용법을 가르치지 않는 것이 최고의 UX")
- "앱의 시대 → 에이전트의 시대" — 배민/카카오T는 비비가 쓰는 도구가 됨
- 비비에게 4개의 뇌: 기억하는 뇌(Qdrant), 추론 뇌(Neo4j), 장기기억 뇌(Graphiti), 꿈 꾸는 뇌(Honcho)

#### 보류
- 비비Law 무료 미끼 전략 (DB 수백만건 축적 후 재검토)
- 비용 최적화 Cloud Scheduled Task 구조 (API 비용 아파질 때)

---





#### 결정
- WORK_MEMORY 기억 공유 시스템 파이프라인 테스트 성공 (이 메시지가 보이면 정상)

#### 인사이트
- Claude.ai → Gmail → VPS → WORK_MEMORY.md 자동 파이프라인 검증 완료
#### 결정
- WORK_MEMORY 기억 공유 시스템 구현 완료 (테스트)
- Gmail 파이프라인은 초안(draft) 기반으로 변경

#### 논의 중
- Claude.ai Gmail MCP에 send 기능 없음 → draft 기반 우회



#### 결정
- WORK_MEMORY 기억 공유 시스템 Gmail 드래프트 파이프라인 테스트

#### 인사이트
- 이 메시지가 WORK_MEMORY.md에 반영되면 Claude.ai → VPS 자동 파이프라인 성공

#### 결정
- 기억 인프라 5개 설치 완료: pgvector + Qdrant + Neo4j + Graphiti(Zep 대체) + Honcho(self-hosted)
- WORK_MEMORY 기억 공유 시스템 구축: nginx 웹노출 + Gmail 드래프트 파이프라인 + 시간 압축
- 비비/클코/Claude.ai 3곳 기억 공유 완성
- API 비용 구조: Haiku 월 ~3,000원, 비용 최적화는 나중에
- 메모리 28개→18개 정리, 중복 제거 (전략 인사이트는 WORK_MEMORY로 이관)

#### 논의 중
- Cloud Scheduled Task로 Max 플랜 활용 가능하나, 월 3천원이라 지금은 불필요
- Claude.ai에서 비비 스킬 호출 — 텔레그램으로 직접 시키면 됨
- 기억 통 크기: 7일 상세 / 7~14일 한 줄 / 14일+ 최소 (확정)

#### 인사이트
- 비비 4개의 뇌: 기억하는 뇌(Qdrant), 추론 뇌(Neo4j), 장기기억 뇌(Graphiti), 꿈 꾸는 뇌(Honcho)
- Zep 셀프호스팅 deprecated → 핵심 엔진 Graphiti만 분리 설치로 해결
- Gmail MCP는 발송 불가, 드래프트만 가능 → 오히려 더 깔끔 (받은편지함 안 더러워짐)
- 가급적 API 호출 없이 규칙 기반 구현 원칙 확정

#### 보류
- Anthropic API 월 상한 설정 ($10 limit, $5 alert)
- 비비Law 무료 미끼 전략 (DB 축적 후 재검토)

























































































## [1~2주 전]

- 2026-04-13: Supabase→PostgreSQL 이관 완료, 법제처 판례 API 연동 + 전체 수집 시작, 0층 API 110개 정리
- 2026-04-12: 0층 감지 분리 완료 (n8n 36노드→5노드), ViviApp 통일, MinIO 설치, 8개 시나리오 검증 통과
- 2026-04-11: 레이어 모델 v2 확정 (6층), 시트 8개→4개(25필드), Claude API 신규만(월5~10건)
- 2026-04-10: 마스터플랜 v7 최종, 삽질방지헌법 v7 추가, RAM 티어별 도구 분석

---































































































## [1개월+]

- 2026-04-07~09: 유캔싸인 통합, PC카톡 감지, Contact Identity Resolution, v7 비비 헌법 방향(규칙→성향)
- 2026-04-04~06: SOUL.md 완성, Hermes Agent 설치, 케이스 시트 23컬럼, 통화녹음 STT 파이프라인
- 2026-04-03: 메모리 프레임워크 5개 비교 (Honcho 1순위 추천), Hermes 1차 조사
