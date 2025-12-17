# Windows 환경 실행 가이드

## 🖥️ Windows에서 데이터셋 생성하기

### ⚠️ 중요 사항

Windows 환경에서는 UTF-8 인코딩 문제로 일부 조정이 필요합니다.
Python 스크립트가 자동으로 인코딩을 처리하도록 수정되었습니다.

---

## 🚀 빠른 시작

### 방법 1: 배치 파일 실행 (추천)

**CMD에서 실행:**
```cmd
start_generation_windows.bat
```

**특징:**
- ✅ 자동으로 UTF-8 인코딩 설정
- ✅ 백그라운드에서 실행
- ✅ 로그 파일에 저장: `logs\generation_output.log`

### 방법 2: 직접 Python 실행

**CMD에서:**
```cmd
chcp 65001
set AIMLAPI_API_KEY=a899ee6960e64af39eade8b5e37dd1e8
set PYTHONIOENCODING=utf-8
python scripts\generate_batch.py --batch-size 100 --checkpoint 1000 --total 9800
```

**PowerShell에서:**
```powershell
$env:AIMLAPI_API_KEY = "a899ee6960e64af39eade8b5e37dd1e8"
$env:PYTHONIOENCODING = "utf-8"
python scripts\generate_batch.py --batch-size 100 --checkpoint 1000 --total 9800
```

---

## 📊 진행 상황 확인

### 방법 1: 배치 파일 사용

```cmd
check_progress_windows.bat
```

### 방법 2: 실시간 로그 보기

**PowerShell에서:**
```powershell
Get-Content logs\generation_output.log -Wait
```

**CMD에서 (최근 로그만):**
```cmd
type logs\generation_output.log
```

### 방법 3: 파일 개수 확인

```cmd
dir /b data\raw\adolescent\conv_*.json | find /c /v ""
dir /b data\raw\adult\conv_*.json | find /c /v ""
dir /b data\raw\crisis\conv_*.json | find /c /v ""
```

---

## 🛑 작업 중단

### 프로세스 찾기

```cmd
tasklist | findstr python
```

### 프로세스 종료

**특정 PID 종료:**
```cmd
taskkill /PID <PID번호> /F
```

**모든 Python 프로세스 종료:**
```cmd
taskkill /IM python.exe /F
```

---

## 🔧 인코딩 문제 해결

### 문제: UnicodeEncodeError 발생

**원인:** Windows의 기본 인코딩(cp949)이 한글/이모지를 처리하지 못함

**해결책 1:** 스크립트 자동 처리 (이미 적용됨)
- `generate_batch.py`가 자동으로 UTF-8 설정

**해결책 2:** CMD 인코딩 변경
```cmd
chcp 65001
```

**해결책 3:** 환경변수 설정
```cmd
set PYTHONIOENCODING=utf-8
```

### 문제: 한글이 깨져서 보임

**해결책:** PowerShell 사용
```powershell
Get-Content logs\generation_output.log -Encoding UTF8 -Wait
```

---

## 📁 생성된 파일

### Windows용 스크립트
- `start_generation_windows.bat` - 생성 시작
- `check_progress_windows.bat` - 진행 상황 확인

### Linux/Mac용 스크립트 (Windows에서 사용 불가)
- `start_generation.sh`
- `start_with_monitor.sh`
- `check_progress.sh`
- `stop_generation.sh`

---

## 💡 유용한 명령어

### 디스크 사용량 확인
```cmd
dir /s data\raw
```

### 로그에서 오류 찾기
```cmd
findstr /i "error 오류 실패" logs\generation_output.log
```

### Python 버전 확인
```cmd
python --version
```

### 필요한 패키지 설치
```cmd
pip install requests tqdm
```

---

## ⏱️ 예상 소요 시간

- **전체 개수:** 9,800개
- **예상 시간:** 약 10일
- **속도:** 약 1.8분/대화

---

## 🔐 보안 팁

API 키를 환경변수로 관리하려면:

**PowerShell에서:**
```powershell
[System.Environment]::SetEnvironmentVariable('AIMLAPI_API_KEY', 'a899ee6960e64af39eade8b5e37dd1e8', 'User')
```

이후 재부팅하면 영구적으로 설정됩니다.

---

## 📝 문제 해결

### 스크립트가 실행되지 않음

1. Python 설치 확인:
   ```cmd
   python --version
   ```

2. 필요한 패키지 설치:
   ```cmd
   pip install requests tqdm
   ```

3. 경로 확인:
   ```cmd
   cd
   ```
   현재 디렉토리가 프로젝트 루트인지 확인

### 로그 파일이 생성되지 않음

```cmd
mkdir logs
```

### 권한 오류

관리자 권한으로 CMD 실행:
- CMD를 우클릭 → "관리자 권한으로 실행"

---

## 🆚 Linux vs Windows 차이점

| 항목 | Linux | Windows |
|------|-------|---------|
| 스크립트 | `.sh` | `.bat` |
| 경로 구분자 | `/` | `\` |
| 인코딩 | UTF-8 (기본) | cp949 (기본) |
| 실시간 로그 | `tail -f` | `Get-Content -Wait` |
| 백그라운드 | `nohup` | `start /B` |

---

**생성일:** 2025-12-17
**업데이트:** Windows 지원 추가
**문의:** 인코딩 문제 발생 시 PowerShell 사용 권장
