# WORK_MEMORY — 비비 프로젝트 개발 기억

> 이 파일은 자동 관리됨. 직접 수정하지 말 것.
> 비비, 클코, Claude.ai 세 곳이 공유하는 개발 장기기억.

---

## [최근 3일]
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
