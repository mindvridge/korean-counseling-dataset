# 병렬 처리 모드 - 10배 빠른 생성 🚀

## 🎯 속도 비교

| 모드 | 동시 작업 | 예상 시간 | 스크립트 |
|------|----------|----------|---------|
| **순차 처리** | 1개 | **10일** | `generate_batch.py` |
| **병렬 처리** ⚡ | 10개 | **1일** | `generate_batch_parallel.py` |

## ⚡ 병렬 모드 특징

- **10개 동시 생성**: ThreadPoolExecutor 사용
- **자동 오류 복구**: 실패한 작업 자동 재시도
- **실시간 통계**: 완료/오류 개수 실시간 표시
- **Thread-safe**: 안전한 동시 처리

---

## 🚀 Windows에서 실행

### 병렬 모드 실행 (추천) ⭐

```cmd
start_parallel_windows.bat
```

**설정:**
- 병렬 작업자: 10개
- 예상 시간: 약 1일
- 자동 체크포인트 저장

### 작업자 수 조절

더 빠르게 하려면 작업자 수를 늘리세요:

```cmd
set AIMLAPI_API_KEY=a899ee6960e64af39eade8b5e37dd1e8
set PYTHONIOENCODING=utf-8
python scripts\generate_batch_parallel.py --workers 20 --total 9800
```

| 작업자 수 | 예상 시간 | 비고 |
|----------|----------|------|
| 5 | 2일 | 안정적 |
| 10 | 1일 | **권장** ⭐ |
| 20 | 12시간 | 빠름 (API 제한 주의) |
| 30 | 8시간 | 매우 빠름 (오류 가능) |

---

## 🐧 Linux/Mac에서 실행

### 병렬 모드

```bash
export AIMLAPI_API_KEY='a899ee6960e64af39eade8b5e37dd1e8'
python scripts/generate_batch_parallel.py --workers 10 --total 9800
```

### nohup으로 백그라운드 실행

```bash
export AIMLAPI_API_KEY='a899ee6960e64af39eade8b5e37dd1e8'
nohup python scripts/generate_batch_parallel.py --workers 10 --total 9800 > logs/parallel_output.log 2>&1 &
```

---

## 📊 실시간 진행 상황

**화면 출력 예시:**

```
======================================================================
🚀 한국어 심리상담 데이터셋 생성 시작 (병렬 처리)
======================================================================
📊 총 목표: 9,800개
🤖 모델: claude-sonnet-4-5
⚡ 병렬 작업자: 10개
📦 배치 크기: 100개
💾 체크포인트 간격: 1000개
======================================================================

📁 기존 파일 개수:
  - adolescent: 1037개 (목표: 5390개, 남은 개수: 4353개)

======================================================================
📝 카테고리: adolescent
🎯 목표: 4353개
======================================================================

📦 시드 파일 110개 로드됨
🔄 100개 대화 생성 시작 (병렬 10개)

생성: 45%|████████████▌             | 45/100 [00:54<01:06, 완료: 45, 오류: 0]
```

**특징:**
- 실시간 진행률 표시
- 완료/오류 통계
- 예상 남은 시간

---

## ⚙️ 고급 설정

### 파라미터 설명

```bash
python scripts/generate_batch_parallel.py \
  --batch-size 100 \      # 배치당 생성 개수
  --checkpoint 1000 \     # 체크포인트 간격
  --total 9800 \          # 총 생성 목표
  --workers 10            # 병렬 작업자 수 ⭐
```

### 최적 작업자 수 찾기

**테스트 실행:**

```cmd
REM 100개만 테스트
python scripts\generate_batch_parallel.py --workers 10 --total 100
python scripts\generate_batch_parallel.py --workers 20 --total 100
python scripts\generate_batch_parallel.py --workers 30 --total 100
```

**시간을 재고 최적값 선택**

---

## 🔍 성능 모니터링

### 실시간 통계 확인

스크립트가 주기적으로 표시:
- **완료**: 성공적으로 생성된 개수
- **오류**: 실패한 개수
- **진행률**: 현재 배치 진행 상황

### 생성 속도 계산

```
속도 = 완료 개수 / 경과 시간
예: 100개 / 10분 = 10개/분 = 600개/시간
```

---

## ⚠️ 주의사항

### API Rate Limit

- AIML API의 rate limit 확인 필요
- 너무 많은 동시 요청 시 오류 발생 가능
- **권장: 10-20 작업자**

### 오류 처리

- 오류 발생 시 자동 재시도 (최대 3회)
- 실패한 작업은 건너뛰고 계속 진행
- 오류 통계는 실시간 표시

### 메모리 사용

- 작업자 수가 많을수록 메모리 사용 증가
- 일반적으로 10-20개는 문제없음
- 50개 이상은 메모리 부족 가능

---

## 💡 문제 해결

### "Too Many Requests" 오류

**원인:** API rate limit 초과

**해결:**
```cmd
REM 작업자 수 줄이기
python scripts\generate_batch_parallel.py --workers 5 --total 9800
```

### 메모리 부족

**원인:** 작업자 수가 너무 많음

**해결:**
```cmd
REM 작업자 수 줄이기
python scripts\generate_batch_parallel.py --workers 10 --total 9800
```

### 진행이 멈춤

**원인:** 모든 작업자가 API 대기 중

**확인:**
- 2-3분 기다려보기 (정상)
- 5분 이상 멈추면 Ctrl+C로 중단 후 재시작

---

## 📈 예상 결과

### 10 작업자 기준

- **속도**: 10개/2분 = 5개/분 = 300개/시간
- **전체**: 9,800개 ÷ 300개/시간 = **약 33시간 (1.4일)**

### 20 작업자 기준

- **속도**: 20개/2분 = 10개/분 = 600개/시간
- **전체**: 9,800개 ÷ 600개/시간 = **약 16시간**

---

## 🎓 작동 원리

### ThreadPoolExecutor

```python
# 10개의 워커 스레드 생성
with ThreadPoolExecutor(max_workers=10) as executor:
    # 각 워커가 독립적으로 API 호출
    futures = [executor.submit(generate, seed) for seed in seeds]

    # 완료되는 대로 결과 수집
    for future in as_completed(futures):
        result = future.result()
```

### Thread-safe 카운터

```python
# 여러 스레드가 동시에 접근해도 안전
with self.lock:
    self.total_generated += 1
```

---

## 📝 순차 vs 병렬 비교

### 순차 처리 (기존)

```
시드1 → 대화1 생성 (2분)
시드2 → 대화2 생성 (2분)
시드3 → 대화3 생성 (2분)
...
총: 9,800개 × 2분 = 19,600분 = 326시간 = 13.6일
```

### 병렬 처리 (10개)

```
시드1 → 대화1 생성 (2분) ┐
시드2 → 대화2 생성 (2분) ├─ 동시 실행
시드3 → 대화3 생성 (2분) │
...                      │
시드10 → 대화10 생성 (2분)┘

총: 9,800개 ÷ 10 × 2분 = 1,960분 = 32.7시간 = 1.4일
```

---

**생성일**: 2025-12-17
**모드**: 병렬 처리
**권장 작업자**: 10-20개
