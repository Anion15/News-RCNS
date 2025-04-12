#  News-RCNS

뉴스 요약, 감정 태그, 반대 의견 자동 생성 시스템  
**Emotion Tagging and Contrasting News Summarization System**


---

##  설치 및 실행 방법

### 1. Docker 설치
운영체제에 따라 아래 링크에서 Docker를 설치합니다:
- [Windows용 Docker](https://docs.docker.com/desktop/install/windows-install/)
- [macOS용 Docker](https://docs.docker.com/desktop/install/mac-install/)
- [Linux용 Docker](https://docs.docker.com/engine/install/)

### 2. Docker 이미지 다운로드
터미널 또는 명령 프롬프트(cmd)에서 아래 명령어를 입력하여 도커 이미지를 다운로드합니다.
(도커 이미지는 6.1GB로 다운로드시 시간이 소요될 수 있습니다.)
```bash
docker pull anion15/news-rcns:latest
```
> **도커 이미지 페이지 :**[Docker-overview](https://hub.docker.com/r/anion15/news-rcns)

### 3. Ollama 설치

1. Ollama 공식 웹사이트에서 다운로드: [https://ollama.com](https://ollama.com)
2. 설치 후, 터미널(cmd 또는 터미널)에서 아래 명령어로 모델을 다운로드:
```bash
ollama pull exaone3.5:2.4b
```

3. 모델을 준비한 후, 다음 명령어로 Ollama 서버를 실행:
```bash
net start com.docker.service
```
위 명령어를 입력하고 'docker desktop'을 실행하세요.
```bash
ollama serve
```
>  이미 포트(기본: 11434)를 사용하는 프로세스가 있다면 `taskkill /PID [번호] /F` 명령어로 종료해야 합니다.
>> 만약에 사용 중인 프로세스를 종료해도 계속 활성화된다면 `ollama run exaone3.5:2.4b` 하여도 됩니다.

---

## 4. Docker 컨테이너 실행

운영체제별로 아래 명령어 중 하나를 새 터미널에서 실행하세요.

### 공통 실행 명령어 (windows, macOS)
```powershell/bash
docker run -p 5000:5000 -e OLLAMA_HOST=http://host.docker.internal:11434 anion15/news-rcns
```

### Linux 전용 (터미널에서 실행)
Linux에서는 `host.docker.internal`이 작동하지 않을 수 있으므로 다음처럼 사용해야 합니다:
```bash
docker run -p 5000:5000 -e OLLAMA_HOST=http://[자신의 로컬 IP주소]:11434 anion15/news-rcns
```
> 예: `OLLAMA_HOST=http://192.168.0.10:11434`

---

## 접속 방법

웹 브라우저를 열고 아래 주소로 접속:
```
https://127.0.0.1:5000
```

외부망 연결이 추가로 필요하시면 ngrok을 이용하거나 Cloudflare Tunnel을 이용하면 됩니다.


---
## 설치 완료 -> 실행하기
<img src="https://github.com/user-attachments/assets/e962a415-ee58-4cda-b2f9-f71c03bfa86a" width="60%" height="50%" title="px(픽셀) 크기 설정" alt="RubberDuck"></img>
- 만약에 설치를 다 하였지만 다시 실행시키고 싶으실땐 아래 순서에 따라 실행해주세요.
1. 새 명령 프롬프트를 관리자 권한으로 생성한다.
2. `net start com.docker.service`
3. 'docker desktop'앱 실행
4. `ollama run exaone3.5:2.4b`
5. 새 명령 프롬프트를 관리자 권한으로 생성한다.
6. `docker run -p 5000:5000 -e OLLAMA_HOST=http://host.docker.internal:11434 anion15/news-rcns`
7. https://127.0.0.1:5000/

---


## 추가 저장 파일 구조 (자동)
| 파일명 | 설명 |
|--------|------|
| `title.txt` | 뉴스 제목 |
| `summary.txt` | 뉴스 요약 내용 |
| `tag.txt` | 감정 태그 (긍정/부정/중립) |
| `opinion.txt` | 기존 의견 요약 |
| `newopinion.txt` | 다른 의견 요약 |
| `img.txt` | 대표 이미지 링크 |

---

- 개발자: [Anion15](https://github.com/Anion15)
