# 서버 독립 실행 가이드

## 📌 개요

Claude Code 세션과 무관하게 서버에서 독립적으로 데이터셋 생성 작업을 실행하는 방법입니다.

## 🚀 빠른 시작

### 1. 실행

```bash
cd /home/user/korean-counseling-dataset
./start_generation.sh
```

실행 후 터미널을 닫거나 Claude Code 세션을 종료해도 계속 실행됩니다.

### 2. 진행 상황 확인

```bash
./check_progress.sh
```

또는 실시간 로그 보기:

```bash
tail -f logs/generation_output.log
```

### 3. 중단

```bash
./stop_generation.sh
```

## 📋 제공되는 스크립트

### start_generation.sh
- **기능**: 백그라운드에서 데이터셋 생성 시작
- **특징**: nohup 사용하여 세션 독립 실행
- **로그**: `logs/generation_output.log`
- **PID**: `logs/generation.pid`

### check_progress.sh
- **기능**: 현재 진행 상황 확인
- **출력**:
  - 프로세스 실행 여부
  - 카테고리별 생성 파일 개수
  - 최근 로그 (20줄)

### stop_generation.sh
- **기능**: 실행 중인 프로세스 중단
- **처리**: 정상 종료 시도 → 강제 종료 시도
- **정리**: PID 파일 자동 삭제

## 🔍 수동 명령어

### 프로세스 확인

```bash
# PID 파일에서 프로세스 ID 확인
cat logs/generation.pid

# 프로세스 실행 여부 확인
ps -p $(cat logs/generation.pid)

# 전체 Python 프로세스 확인
ps aux | grep generate_batch.py
```

### 로그 모니터링

```bash
# 실시간 로그 (Ctrl+C로 종료)
tail -f logs/generation_output.log

# 마지막 100줄 보기
tail -n 100 logs/generation_output.log

# 오류 메시지만 보기
grep -i "error\|오류\|실패" logs/generation_output.log
```

### 파일 개수 확인

```bash
# 전체 개수
find data/raw -name "conv_*.json" | wc -l

# 카테고리별 개수
ls -1 data/raw/adolescent/conv_*.json | wc -l
ls -1 data/raw/adult/conv_*.json | wc -l
ls -1 data/raw/crisis/conv_*.json | wc -l
```

### 프로세스 종료

```bash
# 정상 종료
kill $(cat logs/generation.pid)

# 강제 종료
kill -9 $(cat logs/generation.pid)

# PID 파일 삭제
rm logs/generation.pid
```

## 🔄 재시작

중단된 작업을 재시작하면 기존 파일을 건너뛰고 이어서 생성합니다:

```bash
./start_generation.sh
```

스크립트는 자동으로:
- 기존 파일 개수 확인
- 목표 개수에서 차감
- 남은 개수만 생성

## 💡 추가 옵션

### 다른 방법 1: screen 사용

```bash
# screen 세션 시작
screen -S dataset-generation

# 작업 실행
cd /home/user/korean-counseling-dataset
export AIMLAPI_API_KEY='a899ee6960e64af39eade8b5e37dd1e8'
python scripts/generate_batch.py --batch-size 100 --checkpoint 1000 --total 9800

# Detach: Ctrl+A, D

# 재연결
screen -r dataset-generation

# 종료
screen -X -S dataset-generation quit
```

### 다른 방법 2: tmux 사용

```bash
# tmux 세션 시작
tmux new -s dataset-generation

# 작업 실행
cd /home/user/korean-counseling-dataset
export AIMLAPI_API_KEY='a899ee6960e64af39eade8b5e37dd1e8'
python scripts/generate_batch.py --batch-size 100 --checkpoint 1000 --total 9800

# Detach: Ctrl+B, D

# 재연결
tmux attach -t dataset-generation

# 종료
tmux kill-session -t dataset-generation
```

## 📊 예상 소요 시간

- **속도**: 약 1.8분/대화
- **총 개수**: 9,800개
- **예상 시간**: 약 10일
- **체크포인트**: 1,000개마다 자동 저장

## ⚠️ 주의사항

1. **API 키**: `start_generation.sh`에 하드코딩되어 있음 (보안 주의)
2. **네트워크**: 서버가 인터넷에 연결되어 있어야 함
3. **디스크**: 약 100MB 이상의 여유 공간 필요
4. **중복 실행**: 동일한 스크립트를 중복 실행하지 마세요
5. **백업**: 정기적으로 Git commit & push 권장

## 🔐 보안 권장사항

API 키를 환경변수로 관리하려면:

```bash
# .env 파일 생성 (git에서 제외됨)
echo "AIMLAPI_API_KEY=a899ee6960e64af39eade8b5e37dd1e8" > .env

# 스크립트에서 로드
source .env
python scripts/generate_batch.py --batch-size 100 --checkpoint 1000 --total 9800
```

## 📝 문제 해결

### 프로세스가 시작되지 않음
```bash
# Python 경로 확인
which python
python --version

# 스크립트 권한 확인
ls -l start_generation.sh
```

### 로그가 생성되지 않음
```bash
# 로그 디렉토리 확인
ls -ld logs/

# 권한 확인
chmod 755 logs/
```

### API 오류 발생
- 로그에서 오류 메시지 확인: `tail -f logs/generation_output.log`
- API 키 유효성 확인
- 네트워크 연결 확인

---

**생성일**: 2025-12-17
**버전**: 1.0
**관련 스크립트**: `scripts/generate_batch.py`
