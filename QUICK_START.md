# 빠른 시작 가이드

## 🎯 목적에 따른 실행 방법

### 방법 1: 진행 상황을 보면서 실행 (추천)

**터미널에서 실행:**
```bash
cd /home/user/korean-counseling-dataset
./start_with_monitor.sh
```

**특징:**
- ✅ 실시간으로 진행 상황 확인 가능
- ✅ Ctrl+C로 화면에서 나가도 백그라운드 계속 실행
- ✅ 로그는 `logs/generation_output.log`에 자동 저장
- 📺 화면에서 대화 생성 과정을 직접 볼 수 있음

**화면에서 나가기:**
```
Ctrl+C (백그라운드 작업은 계속됨)
```

**나간 후 다시 보기:**
```bash
tail -f logs/generation_output.log
```

---

### 방법 2: 조용히 백그라운드에서만 실행

**터미널에서 실행:**
```bash
cd /home/user/korean-counseling-dataset
./start_generation.sh
```

**특징:**
- ✅ 화면에 아무것도 표시 안 함
- ✅ 바로 터미널로 돌아옴
- ✅ 완전히 백그라운드에서만 실행

**진행 상황 확인:**
```bash
./check_progress.sh
```

---

## 📊 진행 상황 확인 방법

### 1. 실시간 로그 보기
```bash
tail -f logs/generation_output.log
```
- 생성 중인 대화를 실시간으로 확인
- Ctrl+C로 종료

### 2. 요약 정보 보기
```bash
./check_progress.sh
```
- 프로세스 상태
- 카테고리별 파일 개수
- 최근 로그 20줄

### 3. 파일 개수만 확인
```bash
find data/raw -name "conv_*.json" | wc -l
```

---

## 🛑 작업 중단

```bash
./stop_generation.sh
```

중단 후 재시작하면 **자동으로 이어서** 생성합니다!

---

## 💡 상황별 추천

| 상황 | 추천 방법 |
|------|-----------|
| 처음 실행하는데 진행 상황 보고 싶음 | `./start_with_monitor.sh` ✅ |
| 그냥 백그라운드에서만 돌리고 싶음 | `./start_generation.sh` |
| 이미 실행 중인데 진행 상황 보고 싶음 | `tail -f logs/generation_output.log` |
| 간단히 요약만 보고 싶음 | `./check_progress.sh` |
| 작업 중단하고 싶음 | `./stop_generation.sh` |

---

## ⚙️ 예상 소요 시간

- **전체 개수**: 9,800개
- **현재 상태**: 1,889개 완료 (19.3%)
- **남은 개수**: 7,911개
- **예상 시간**: 약 10일
- **체크포인트**: 1,000개마다 자동 저장

---

## 📁 파일 위치

- **로그**: `logs/generation_output.log`
- **PID**: `logs/generation.pid`
- **생성 데이터**: `data/raw/{adolescent,adult,crisis}/conv_*.json`
- **체크포인트**: `logs/checkpoint_*.json`

---

## ❓ 문제 해결

### "Permission denied" 오류
```bash
chmod +x start_with_monitor.sh start_generation.sh check_progress.sh stop_generation.sh
```

### 프로세스가 실행 중인지 확인
```bash
ps aux | grep generate_batch.py
```

### 로그에 오류가 있는지 확인
```bash
grep -i "error\|오류" logs/generation_output.log
```

---

**생성일**: 2025-12-17
**업데이트**: 실시간 모니터링 스크립트 추가
