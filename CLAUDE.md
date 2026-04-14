# /root/docs 작업 규칙

## 작업 완료 시 필수 절차

작업이 완료되면 반드시 아래 스크립트로 WORK_MEMORY를 갱신하고 GitHub에 push한다.

```bash
cd /root/docs
python3 update_work_memory.py --category "카테고리" --content "내용"
```

카테고리 종류: `결정`, `완료`, `이슈`, `메모`

push 실패(non-fast-forward) 시:
```bash
git pull --rebase origin main && git push origin main
```

## GitHub 토큰

Remote URL에 토큰이 포함되어 있음. 토큰 갱신 시:
```bash
git remote set-url origin https://x-access-token:[NEW_TOKEN]@github.com/stayz-hue/vivi-memory.git
```

## 파일 구조

- WORK_MEMORY.md — 비비의 작업 기억 (Claude.ai와 공유)
- compress_memory.py — 오래된 항목 압축 (매일 UTC 15:00 자동 실행)
- gmail_memory_receiver.py — Gmail 드래프트 폴링 (*/5 분마다 자동 실행)
- update_work_memory.py — WORK_MEMORY 갱신 + git push 헬퍼

---

## WORK_MEMORY 보고 규칙 (필수)

모든 작업 종료 시 update_work_memory.py를 실행하고 git push한다. 예외 없음.

### "작업"의 정의
코드 수정, 파일 생성, 서비스 재시작만이 작업이 아니다.
조회·확인·점검·진단도 작업이다.
대표님이나 Claude.ai가 결과를 볼 수 있어야 하므로, 확인한 내용도 반드시 기록한다.

조회 작업 예시:
- crontab -l
- systemctl status [서비스명]
- docker ps / docker logs
- cat / head / tail / grep으로 파일 내용 확인
- ps aux, netstat, df, free 등 시스템 상태 확인
- curl로 API 응답 확인
- DB 쿼리로 데이터 조회

### 카테고리 기준
| 상황 | --category |
|------|-----------|
| 뭔가 변경/생성/삭제했을 때 | 결정 |
| 조회/확인/점검만 했을 때 | 현황 |
| 문제/에러/이상 발견했을 때 | 이슈 |
| 아이디어/개선점 떠올랐을 때 | 인사이트 |

### 실행 명령어
python3 /root/docs/update_work_memory.py --category [카테고리] --content [내용] && cd /root/docs && git add -A && git push

### 금지사항
- "변경 없으니 보고 안 함" ← 이 판단 금지. 변경 없어도 보고한다.
- content에 명령어 결과를 그대로 복붙하지 말고, 핵심만 요약해서 적는다.
- 한 세션에서 여러 작업을 했으면 각각 따로 보고하지 말고, 마지막에 한 번에 모아서 보고한다.
