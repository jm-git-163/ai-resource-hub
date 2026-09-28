# 🚀 AI 크리에이터 리소스 허브

AI 콘텐츠 제작에 필요한 모든 리소스를 자동 수집하고, 한글 설명과 함께 검색·필터·즐겨찾기 기능을 제공하는 웹 대시보드입니다.

## 🌐 사이트 바로가기

**👉 [https://jm-git-163.github.io/ai-resource-hub/](https://jm-git-163.github.io/ai-resource-hub/)**

## ✨ 주요 기능

| 기능 | 설명 |
|---|---|
| 📊 **10개 카테고리** | 트렌드, 프롬프트, 스킬, 워크플로, 오픈소스, 디자인, 영상, 에셋, 공모전, 리서치 |
| 🔍 **실시간 검색** | 제목, 설명(한글/영문), 태그로 즉시 검색 |
| 🏷️ **필터** | 카테고리별, 플랫폼별 (GitHub, HuggingFace, arXiv, HackerNews) |
| ⭐ **즐겨찾기** | 마음에 드는 리소스 저장 (브라우저 로컬 저장) |
| 🌿 **신선도 관리** | 자동 점수 계산, 오래된 자료 자동 폐기 |
| 🔄 **자동 업데이트** | GitHub Actions로 매주 자동 수집 |
| 🌙 **다크/라이트 모드** | 토글 전환, 설정 저장 |

## 📁 프로젝트 구조

```
ai-resource-hub/
├── index.html              # 메인 대시보드
├── css/style.css           # 스타일시트
├── js/app.js               # 앱 로직
├── data/resources.json     # 수집된 리소스 데이터
├── scripts/
│   ├── collector.py        # 리소스 자동 수집기
│   └── freshness_manager.py # 신선도 관리
└── .github/workflows/
    └── auto-collect.yml    # 주간 자동 수집
```

## 🔧 수동 데이터 업데이트

```bash
# 리소스 수집
python scripts/collector.py

# 신선도 관리 (오래된 자료 정리)
python scripts/freshness_manager.py
```

## 📈 수집 대상

| 플랫폼 | 수집 내용 |
|---|---|
| **GitHub** | AI 에이전트, 프롬프트, LLM 도구, 워크플로, 디자인 시스템, 무료 에셋 등 |
| **HuggingFace** | 트렌딩 모델 (텍스트·이미지·음성), 인기 Spaces |
| **arXiv** | 최신 AI 논문 (LLM, Diffusion, Agent) |
| **HackerNews** | AI 관련 뉴스 및 토론 |
| **큐레이션** | 무료 폰트, SFX, 음악, 사진, 아이콘, 공모전, 디자인 영감 사이트 |

## 🔐 Google 로그인 설정 (선택)

Firebase Google 인증을 활성화하려면:

1. [Firebase Console](https://console.firebase.google.com)에서 프로젝트 생성
2. Authentication → Google 로그인 활성화
3. Authorized Domain에 `jm-git-163.github.io` 추가
4. `js/app.js`에 `firebaseConfig` 값 입력

## 📜 라이선스

MIT License
