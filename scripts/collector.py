import urllib.request
import urllib.parse
import urllib.error
import json
import ssl
import os
import sys
import time
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

CATEGORIES = {
    "trend":     {"icon": "📈", "name_kr": "트렌드",      "name_en": "Trends",       "guide": "왜 지금 중요하고 한국은 어느 단계인가"},
    "prompt":    {"icon": "💬", "name_kr": "프롬프트",    "name_en": "Prompts",      "guide": "어떤 모델에서 어디에 쓰나, 결과 예시"},
    "skill":     {"icon": "🤖", "name_kr": "스킬",       "name_en": "Skills",       "guide": "쉽게 말하면 무슨 일을 대신해주나"},
    "workflow":  {"icon": "🔄", "name_kr": "워크플로",    "name_en": "Workflows",    "guide": "몇 단계를 몇 단계로 줄여주나"},
    "opensource":{"icon": "🛠️", "name_kr": "오픈소스",   "name_en": "Open Source",  "guide": "설치할 가치가 있나, Demo 먼저 볼 수 있나"},
    "design":    {"icon": "🎨", "name_kr": "디자인",     "name_en": "Design",       "guide": "레이아웃·타이포·모션 중 무엇을 배울까"},
    "video":     {"icon": "🎬", "name_kr": "영상",       "name_en": "Video",        "guide": "훅·카메라·편집·사운드 중 무엇이 좋은가"},
    "asset":     {"icon": "📦", "name_kr": "무료 에셋",   "name_en": "Free Assets",  "guide": "상업 사용 가능한가"},
    "contest":   {"icon": "🏆", "name_kr": "공모전",     "name_en": "Contests",     "guide": "내가 참가 가능한가, 왜 추천하나"},
    "research":  {"icon": "📄", "name_kr": "리서치",     "name_en": "Research",     "guide": "비전공자인 내가 어디에 적용할 수 있나"}
}

def request_json(url, headers=None):
    if headers is None:
        headers = {}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            if response.status == 200:
                return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"    ❌ 오류 발생 ({url}): {e}")
    return None

def request_xml(url):
    try:
        with urllib.request.urlopen(url, context=ssl_context) as response:
            if response.status == 200:
                return ET.fromstring(response.read().decode('utf-8'))
    except Exception as e:
        print(f"    ❌ 오류 발생 ({url}): {e}")
    return None

def fetch_github():
    print("\n📈 [1/5] GitHub 데이터 수집 시작...")
    resources = []
    headers = {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'AI-Resource-Hub/2.0',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token:
        headers['Authorization'] = f'Bearer {github_token}'
        
    queries = {
        "trend": [
            "artificial intelligence stars:>5000 pushed:>2025-06-01",
            "generative AI stars:>1000 pushed:>2025-06-01"
        ],
        "prompt": [
            "awesome prompts stars:>500",
            "topic:prompt-engineering stars:>100",
            "chatgpt prompts stars:>200",
            "stable diffusion prompts stars:>50",
            "system prompt stars:>100"
        ],
        "skill": [
            "topic:ai-agents stars:>100",
            "mcp server stars:>50",
            "cursor rules stars:>30",
            "AGENTS.md",
            "ai coding assistant stars:>100",
            "claude skill stars:>20"
        ],
        "workflow": [
            "comfyui workflow stars:>50",
            "topic:ai-workflow stars:>50",
            "n8n workflow stars:>50",
            "content creation automation stars:>30",
            "video production ai stars:>30"
        ],
        "opensource": [
            "topic:open-source-llm stars:>200",
            "topic:stable-diffusion stars:>500",
            "topic:local-llm stars:>100",
            "text to speech open source stars:>100",
            "ai video generation stars:>100"
        ],
        "design": [
            "awesome design resources stars:>200",
            "ui design resources stars:>100",
            "design system stars:>500",
            "figma plugin ai stars:>30"
        ],
        "video": [
            "video editing ai stars:>50",
            "youtube tools stars:>100",
            "subtitle generator stars:>50",
            "ai video stars:>100"
        ],
        "asset": [
            "free fonts stars:>100",
            "free sound effects stars:>30",
            "free stock photos stars:>50",
            "free icons stars:>200",
            "free templates stars:>50"
        ],
        "contest": [
            "ai competition stars:>50",
            "kaggle solutions stars:>100"
        ],
        "research": [
            "papers with code stars:>200",
            "awesome machine learning stars:>500",
            "ai research papers stars:>100"
        ]
    }
    
    for category, qs in queries.items():
        for q in qs:
            print(f"  ⏳ [{category.upper()}] {q}...")
            encoded_q = urllib.parse.quote(q)
            url = f"https://api.github.com/search/repositories?q={encoded_q}&per_page=30&sort=stars&order=desc"
            data = request_json(url, headers)
            if data and 'items' in data:
                count = 0
                for item in data['items']:
                    resources.append({
                        "id": f"github-{item['id']}",
                        "title": item['name'],
                        "description": item['description'] or "",
                        "url": item['html_url'],
                        "platform": "github",
                        "category": category,
                        "stars": item['stargazers_count'],
                        "tags": item['topics'] if 'topics' in item else [],
                        "language": item['language'] or "",
                        "updated_at": item['pushed_at'][:10] if item.get('pushed_at') else "",
                        "author": item['owner']['login'],
                        "license": item['license']['name'] if item.get('license') else "",
                        "demo_url": item['homepage'] or ""
                    })
                    count += 1
                print(f"  ✅ {count}개 수집")
            time.sleep(7)
            
    return resources

def fetch_huggingface():
    print("\n🤗 [2/5] HuggingFace 데이터 수집 시작...")
    resources = []
    
    endpoints = [
        {"url": "https://huggingface.co/api/models?filter=text-generation&sort=trendingScore&direction=-1&limit=20", "cat": "opensource", "type": "model"},
        {"url": "https://huggingface.co/api/models?filter=text-to-image&sort=trendingScore&direction=-1&limit=15", "cat": "opensource", "type": "model"},
        {"url": "https://huggingface.co/api/models?filter=text-to-speech&sort=trendingScore&direction=-1&limit=10", "cat": "asset", "type": "model"},
        {"url": "https://huggingface.co/api/spaces?sort=trendingScore&direction=-1&limit=20", "cat": "opensource", "type": "space"}
    ]
    
    for ep in endpoints:
        print(f"  ⏳ HuggingFace {ep['type']} ({ep['cat']}) 수집...")
        data = request_json(ep["url"])
        if data:
            count = 0
            for item in data:
                item_id = item.get('_id', item.get('id'))
                repo_id = item.get('id', '')
                stars = item.get('likes', 0)
                
                url = f"https://huggingface.co/spaces/{repo_id}" if ep["type"] == "space" else f"https://huggingface.co/{repo_id}"
                demo_url = url if ep["type"] == "space" else ""
                
                resources.append({
                    "id": f"hf-{item_id}",
                    "title": repo_id,
                    "description": "",
                    "url": url,
                    "platform": "huggingface",
                    "category": ep["cat"],
                    "stars": stars,
                    "tags": item.get('tags', []),
                    "language": "",
                    "updated_at": item.get('lastModified', '')[:10] if item.get('lastModified') else "",
                    "author": repo_id.split('/')[0] if '/' in repo_id else "",
                    "license": "",
                    "demo_url": demo_url
                })
                count += 1
            print(f"  ✅ {count}개 수집")
        time.sleep(2)
        
    return resources

def fetch_arxiv():
    print("\n📄 [3/5] arXiv 논문 수집 시작...")
    resources = []
    
    queries = [
        ("cat:cs.AI+AND+abs:large+language+model", 15),
        ("cat:cs.CV+AND+abs:diffusion+model", 10),
        ("cat:cs.AI+AND+abs:agent", 10)
    ]
    
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    
    for q, limit in queries:
        print(f"  ⏳ arXiv 검색: {q}...")
        url = f"http://export.arxiv.org/api/query?search_query={q}&start=0&max_results={limit}&sortBy=lastUpdatedDate&sortOrder=descending"
        root = request_xml(url)
        if root is not None:
            count = 0
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
                entry_id = entry.find('atom:id', ns).text
                published = entry.find('atom:published', ns).text[:10] if entry.find('atom:published', ns) is not None else ""
                
                authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
                author_str = authors[0] + (" et al." if len(authors) > 1 else "")
                
                tags = [cat.get('term') for cat in entry.findall('atom:category', ns)]
                
                resources.append({
                    "id": f"arxiv-{entry_id.split('/')[-1]}",
                    "title": title,
                    "description": summary,
                    "url": entry_id,
                    "platform": "arxiv",
                    "category": "research",
                    "stars": 0,
                    "tags": tags,
                    "language": "",
                    "updated_at": published,
                    "author": author_str,
                    "license": "",
                    "demo_url": ""
                })
                count += 1
            print(f"  ✅ {count}개 수집")
        time.sleep(3)
        
    return resources

def fetch_hackernews():
    print("\n📰 [4/5] HackerNews AI 뉴스 수집 시작...")
    resources = []
    
    keywords = ['AI', 'GPT', 'LLM', 'machine learning', 'deep learning', 'neural', 'generative', 'diffusion', 'transformer', 'open source', 'claude', 'gemini', 'openai', 'anthropic', 'llama', 'stable diffusion']
    
    print("  ⏳ Top Stories 가져오는 중...")
    top_ids = request_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    if top_ids:
        count = 0
        for item_id in top_ids[:50]:
            item = request_json(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json")
            if item and item.get('title'):
                title = item['title']
                if any(kw.lower() in title.lower() for kw in keywords):
                    resources.append({
                        "id": f"hn-{item_id}",
                        "title": title,
                        "description": "",
                        "url": item.get('url', f"https://news.ycombinator.com/item?id={item_id}"),
                        "platform": "hackernews",
                        "category": "trend",
                        "stars": item.get('score', 0),
                        "tags": ["news"],
                        "language": "",
                        "updated_at": datetime.fromtimestamp(item.get('time', 0), tz=timezone.utc).strftime('%Y-%m-%d'),
                        "author": item.get('by', ''),
                        "license": "",
                        "demo_url": ""
                    })
                    count += 1
                    if count >= 20:
                        break
            time.sleep(0.2)
        print(f"  ✅ AI 관련 뉴스 {count}개 수집")
        
    return resources

def get_curated_resources():
    print("\n📦 [5/5] 큐레이션 데이터 추가 중...")
    resources = []
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    curated = [
        # ASSET - Free Fonts
        {"category": "asset", "title": "Google Fonts", "url": "https://fonts.google.com", "description": "구글 무료 폰트 라이브러리. 1600+ 오픈소스 폰트. 상업적 사용 가능.", "description_kr": "✅ 상업 사용 가능 | 1600+ 무료 폰트, 웹폰트 지원", "stars": 99999, "tags": ["font", "free", "commercial"], "license": "OFL/Apache 2.0"},
        {"category": "asset", "title": "눈누 (Noonnu)", "url": "https://noonnu.cc", "description": "한글 무료 폰트 모음. 라이선스별 필터링 가능.", "description_kr": "✅ 상업 사용 가능 | 한글 전용 무료 폰트 모음, 라이선스 확인 편리", "stars": 99998, "tags": ["font", "korean", "free"], "license": "Various"},
        {"category": "asset", "title": "Font Squirrel", "url": "https://www.fontsquirrel.com", "description": "100% free for commercial use fonts.", "description_kr": "✅ 상업 사용 가능 | 영문 무료 폰트, 상업용 보장", "stars": 50000, "tags": ["font", "free", "commercial"], "license": "Free"},

        # ASSET - Free SFX/Music
        {"category": "asset", "title": "Freesound", "url": "https://freesound.org", "description": "Collaborative database of Creative Commons licensed sounds.", "description_kr": "⚠️ CC 라이선스 확인 필요 | 40만+ 무료 효과음, 커뮤니티 기반", "stars": 90000, "tags": ["sfx", "sound", "free", "cc"], "license": "CC"},
        {"category": "asset", "title": "Pixabay Music", "url": "https://pixabay.com/music", "description": "Free music for videos, films, and games.", "description_kr": "✅ 상업 사용 가능 | 무료 배경음악, 영상 제작용", "stars": 85000, "tags": ["music", "bgm", "free"], "license": "Pixabay License"},
        {"category": "asset", "title": "Mixkit", "url": "https://mixkit.co", "description": "Free assets for video creation - music, SFX, video templates.", "description_kr": "✅ 상업 사용 가능 | 무료 음악+효과음+영상 템플릿 올인원", "stars": 80000, "tags": ["music", "sfx", "video", "template"], "license": "Free"},
        {"category": "asset", "title": "BBC Sound Effects", "url": "https://sound-effects.bbcrewind.co.uk", "description": "BBC의 16,000+ 무료 효과음 아카이브.", "description_kr": "⚠️ 비상업(개인/교육)만 가능 | BBC 고품질 16,000+ 효과음", "stars": 70000, "tags": ["sfx", "bbc", "archive"], "license": "RemArc"},

        # ASSET - Free Stock
        {"category": "asset", "title": "Unsplash", "url": "https://unsplash.com", "description": "Beautiful free images & pictures.", "description_kr": "✅ 상업 사용 가능 | 고품질 무료 사진, 출처 표기 불필요", "stars": 95000, "tags": ["photo", "stock", "free"], "license": "Unsplash License"},
        {"category": "asset", "title": "Pexels", "url": "https://www.pexels.com", "description": "Free stock photos, royalty free images & videos.", "description_kr": "✅ 상업 사용 가능 | 무료 사진+영상 소스, 출처 표기 불필요", "stars": 94000, "tags": ["photo", "video", "stock", "free"], "license": "Pexels License"},
        {"category": "asset", "title": "Pixabay", "url": "https://pixabay.com", "description": "Over 4.5 million free stock photos, videos, music, and illustrations.", "description_kr": "✅ 상업 사용 가능 | 사진+영상+음악+일러스트 통합 무료 소스", "stars": 93000, "tags": ["photo", "video", "music", "illustration"], "license": "Pixabay License"},

        # ASSET - Free Icons/Illustrations
        {"category": "asset", "title": "Heroicons", "url": "https://heroicons.com", "description": "Beautiful hand-crafted SVG icons by the makers of Tailwind CSS.", "description_kr": "✅ 상업 사용 가능 | Tailwind 팀 제작 SVG 아이콘", "stars": 88000, "tags": ["icon", "svg", "free"], "license": "MIT"},
        {"category": "asset", "title": "Lucide Icons", "url": "https://lucide.dev", "description": "Beautiful & consistent icons. Open source.", "description_kr": "✅ 상업 사용 가능 | 오픈소스 아이콘 세트, 다양한 프레임워크 지원", "stars": 87000, "tags": ["icon", "svg", "free"], "license": "ISC"},
        {"category": "asset", "title": "unDraw", "url": "https://undraw.co", "description": "Open-source illustrations for any idea.", "description_kr": "✅ 상업 사용 가능 | 커스텀 컬러 일러스트, 출처 불필요", "stars": 86000, "tags": ["illustration", "svg", "free"], "license": "Free"},

        # DESIGN - Inspiration
        {"category": "design", "title": "Behance", "url": "https://www.behance.net", "description": "Showcase & discover creative work.", "description_kr": "레이아웃·타이포 | 포트폴리오 기반 디자인 영감, Adobe 연동", "stars": 99000, "tags": ["portfolio", "design", "inspiration"], "license": "N/A"},
        {"category": "design", "title": "Dribbble", "url": "https://dribbble.com", "description": "Discover the world's top designers & creatives.", "description_kr": "UI·모션 | UI/UX 디자인 트렌드, 드리블 샷 레퍼런스", "stars": 98000, "tags": ["ui", "design", "inspiration"], "license": "N/A"},
        {"category": "design", "title": "Awwwards", "url": "https://www.awwwards.com", "description": "The awards of design, creativity and innovation on the internet.", "description_kr": "모션·인터랙션 | 세계 최고 웹 디자인 수상작 모음", "stars": 97000, "tags": ["web", "design", "award"], "license": "N/A"},
        {"category": "design", "title": "Pinterest - AI Art", "url": "https://www.pinterest.com/search/pins/?q=AI%20art%20design", "description": "AI art and design inspiration boards.", "description_kr": "레이아웃·컨셉 | AI 아트 무드보드, 비주얼 레퍼런스 수집", "stars": 96000, "tags": ["moodboard", "ai-art", "reference"], "license": "N/A"},
        {"category": "design", "title": "Mobbin", "url": "https://mobbin.com", "description": "Save hours of UI & UX research with our library of 300,000+ app screenshots.", "description_kr": "UI·레이아웃 | 30만+ 실제 앱 UI 스크린샷, 패턴 검색", "stars": 95000, "tags": ["ui", "mobile", "reference"], "license": "Free tier"},

        # VIDEO - Resources
        {"category": "video", "title": "Pexels Videos", "url": "https://www.pexels.com/videos", "description": "Free stock videos & footage.", "description_kr": "✅ 상업 가능 | 무료 영상 소스, 4K 지원", "stars": 90000, "tags": ["video", "stock", "free"], "license": "Pexels License"},
        {"category": "video", "title": "Coverr", "url": "https://coverr.co", "description": "Beautiful free stock video footage.", "description_kr": "✅ 상업 가능 | 고품질 무료 배경 영상, 웹사이트용", "stars": 85000, "tags": ["video", "stock", "free"], "license": "Free"},
        {"category": "video", "title": "Artlist", "url": "https://artlist.io", "description": "Royalty-free music & SFX for video creators.", "description_kr": "⚠️ 유료 (무료 체험) | 영상 크리에이터 인기 1위 음악/SFX 구독", "stars": 80000, "tags": ["music", "sfx", "video"], "license": "Paid"},

        # CONTEST
        {"category": "contest", "title": "Kaggle Competitions", "url": "https://www.kaggle.com/competitions", "description": "Data science & ML competitions.", "description_kr": "🌍 누구나 참가 | ML/AI 대회, 상금+포트폴리오+취업 연계", "stars": 99000, "tags": ["competition", "ml", "data-science"], "license": "N/A"},
        {"category": "contest", "title": "AI Hub 공모전", "url": "https://aihub.or.kr", "description": "한국 AI Hub - AI 관련 공모전 및 데이터셋.", "description_kr": "🇰🇷 국내 | 한국 정부 AI 공모전, 한국어 데이터셋 제공", "stars": 95000, "tags": ["competition", "korean", "government"], "license": "N/A"},
        {"category": "contest", "title": "DACON", "url": "https://dacon.io", "description": "한국 AI 경진대회 플랫폼.", "description_kr": "🇰🇷 국내 | 한국판 Kaggle, 기업 연계 AI 대회", "stars": 94000, "tags": ["competition", "korean", "ai"], "license": "N/A"},
        {"category": "contest", "title": "Devpost", "url": "https://devpost.com", "description": "Online hackathons & software competitions.", "description_kr": "🌍 누구나 참가 | 글로벌 해커톤 플랫폼, AI 트랙 다수", "stars": 90000, "tags": ["hackathon", "competition"], "license": "N/A"},
        {"category": "contest", "title": "공모전 대외활동 올콘", "url": "https://all-con.co.kr", "description": "국내 공모전·대외활동 종합 플랫폼.", "description_kr": "🇰🇷 국내 | 디자인·영상·AI 공모전 통합 검색", "stars": 88000, "tags": ["competition", "korean", "design"], "license": "N/A"}
    ]
    
    for i, item in enumerate(curated):
        resources.append({
            "id": f"curated-{i}",
            "title": item["title"],
            "description": item["description"],
            "description_kr": item["description_kr"],
            "url": item["url"],
            "platform": "curated",
            "category": item["category"],
            "stars": item["stars"],
            "tags": item["tags"],
            "language": "",
            "updated_at": today,
            "author": "curated",
            "license": item["license"],
            "demo_url": ""
        })
        
    print(f"  ✅ 큐레이션 데이터 {len(curated)}개 추가 완료")
    return resources

def generate_korean_desc(resource):
    category = resource.get('category', 'opensource')
    cat_info = CATEGORIES.get(category, CATEGORIES['opensource'])
    title = resource.get('title', '').lower()
    desc = resource.get('description', '').lower()
    text = title + ' ' + desc
    
    if category == 'trend':
        parts = []
        if any(w in text for w in ['gpt', 'llm', 'language model']): parts.append('LLM 분야')
        if any(w in text for w in ['image', 'vision', 'diffusion']): parts.append('이미지 AI')
        if any(w in text for w in ['video']): parts.append('영상 AI')
        if any(w in text for w in ['agent', 'autonomous']): parts.append('AI 에이전트')
        if any(w in text for w in ['open source', 'free']): parts.append('오픈소스')
        focus = ', '.join(parts[:2]) if parts else 'AI'
        return f"🔥 {focus} 트렌드 | 주목해야 할 변화"
    
    elif category == 'prompt':
        models = []
        if any(w in text for w in ['chatgpt', 'gpt']): models.append('GPT')
        if any(w in text for w in ['claude']): models.append('Claude')
        if any(w in text for w in ['midjourney']): models.append('Midjourney')
        if any(w in text for w in ['stable diffusion', 'sdxl', 'flux']): models.append('SD/Flux')
        if any(w in text for w in ['gemini']): models.append('Gemini')
        model_str = '+'.join(models[:2]) if models else '범용'
        use = '이미지 생성' if any(w in text for w in ['image', 'art', 'draw']) else '텍스트/코딩' if any(w in text for w in ['code', 'coding']) else '다목적'
        return f"🎯 {model_str} | {use}용 프롬프트"
    
    elif category == 'skill':
        jobs = []
        if any(w in text for w in ['code', 'coding', 'develop']): jobs.append('코딩 자동화')
        if any(w in text for w in ['agent']): jobs.append('작업 자율 실행')
        if any(w in text for w in ['mcp', 'server', 'tool']): jobs.append('외부 도구 연결')
        if any(w in text for w in ['cursor', 'copilot']): jobs.append('IDE 코딩 보조')
        if any(w in text for w in ['search', 'browse', 'web']): jobs.append('웹 검색/탐색')
        if any(w in text for w in ['file', 'document']): jobs.append('파일/문서 처리')
        job_str = ', '.join(jobs[:2]) if jobs else 'AI 작업 지원'
        return f"🔧 대신 해주는 일: {job_str}"
    
    elif category == 'workflow':
        steps = []
        if any(w in text for w in ['comfyui', 'node']): steps.append('노드 기반')
        if any(w in text for w in ['n8n', 'zapier', 'make']): steps.append('노코드 자동화')
        if any(w in text for w in ['video', 'edit']): steps.append('영상 제작')
        if any(w in text for w in ['image', 'art']): steps.append('이미지 생성')
        if any(w in text for w in ['pipeline', 'chain']): steps.append('파이프라인')
        step_str = ', '.join(steps[:2]) if steps else '작업 자동화'
        return f"⚡ {step_str} | 복잡한 과정을 단순화"
    
    elif category == 'opensource':
        has_demo = any(w in text for w in ['demo', 'playground', 'try', 'online', 'web', 'space'])
        demo_str = '🌐 데모 가능' if has_demo else '💻 설치 필요'
        kind = '언어 모델' if any(w in text for w in ['llm', 'language model', 'text-generation']) else '이미지 생성' if any(w in text for w in ['image', 'diffusion', 'text-to-image']) else '음성 합성' if any(w in text for w in ['tts', 'speech', 'voice']) else '영상 생성' if any(w in text for w in ['video']) else 'AI 도구'
        return f"{demo_str} | {kind}"
    
    elif category == 'design':
        aspects = []
        if any(w in text for w in ['layout', 'grid', 'responsive']): aspects.append('레이아웃')
        if any(w in text for w in ['typography', 'font', 'type']): aspects.append('타이포그래피')
        if any(w in text for w in ['motion', 'animation', 'transition']): aspects.append('모션')
        if any(w in text for w in ['ui', 'interface', 'ux']): aspects.append('UI/UX')
        if any(w in text for w in ['color', 'palette']): aspects.append('컬러')
        if any(w in text for w in ['icon', 'illustration']): aspects.append('아이콘/일러스트')
        aspect_str = '·'.join(aspects[:2]) if aspects else '디자인 전반'
        return f"🎨 배울 점: {aspect_str}"
    
    elif category == 'video':
        elements = []
        if any(w in text for w in ['hook', 'thumbnail', 'click']): elements.append('훅/썸네일')
        if any(w in text for w in ['camera', 'shoot', 'film']): elements.append('촬영')
        if any(w in text for w in ['edit', 'cut', 'montage', 'premiere', 'davinci']): elements.append('편집')
        if any(w in text for w in ['sound', 'music', 'audio', 'sfx']): elements.append('사운드')
        if any(w in text for w in ['subtitle', 'caption']): elements.append('자막')
        if any(w in text for w in ['ai', 'generate']): elements.append('AI 생성')
        elem_str = '·'.join(elements[:2]) if elements else '영상 제작'
        return f"🎬 핵심: {elem_str}"
    
    elif category == 'asset':
        license_info = resource.get('license', '').lower()
        if any(w in license_info for w in ['mit', 'apache', 'free', 'cc0', 'unlicense', 'isc', 'pixabay', 'unsplash', 'pexels', 'ofl']):
            commercial = '✅ 상업 사용 가능'
        elif any(w in license_info for w in ['cc-by-nc', 'non-commercial', 'personal', 'remarc']):
            commercial = '⚠️ 비상업만 가능'
        elif any(w in license_info for w in ['cc-by', 'cc']):
            commercial = '⚠️ 출처 표기 필요'
        elif any(w in license_info for w in ['paid', 'premium']):
            commercial = '💰 유료'
        else:
            commercial = '⚠️ 라이선스 확인 필요'
        
        kind = '폰트' if any(w in text for w in ['font', '폰트']) else '효과음/음악' if any(w in text for w in ['sound', 'music', 'sfx', 'audio', '음악', '효과음']) else '사진/이미지' if any(w in text for w in ['photo', 'image', 'stock', 'picture']) else '아이콘' if any(w in text for w in ['icon']) else '일러스트' if any(w in text for w in ['illustrat']) else '템플릿' if any(w in text for w in ['template']) else '에셋'
        return f"{commercial} | {kind}"
    
    elif category == 'contest':
        return resource.get('description_kr', '🏆 AI/디자인 공모전')
    
    elif category == 'research':
        apps = []
        if any(w in text for w in ['vision', 'image', 'visual']): apps.append('이미지/비전 분야')
        if any(w in text for w in ['language', 'text', 'nlp']): apps.append('텍스트/NLP 분야')
        if any(w in text for w in ['agent']): apps.append('AI 에이전트')
        if any(w in text for w in ['efficient', 'fast', 'small']): apps.append('경량화/최적화')
        if any(w in text for w in ['benchmark', 'evaluation']): apps.append('성능 평가')
        app_str = ', '.join(apps[:2]) if apps else 'AI 연구'
        return f"📄 적용 분야: {app_str}"
    
    return f"[{cat_info['name_kr']}] 관련 리소스"

def main():
    print("🚀 AI 리소스 수집기 v2.0 시작")
    print("=" * 50)
    
    all_resources = []
    
    # 1. GitHub
    all_resources.extend(fetch_github())
    
    # 2. HuggingFace
    all_resources.extend(fetch_huggingface())
    
    # 3. arXiv
    all_resources.extend(fetch_arxiv())
    
    # 4. HackerNews
    all_resources.extend(fetch_hackernews())
    
    # 5. Curated resources
    all_resources.extend(get_curated_resources())
    
    # 6. Deduplicate by URL
    seen_urls = set()
    deduped_resources = []
    for r in all_resources:
        if r['url'] not in seen_urls:
            seen_urls.add(r['url'])
            deduped_resources.append(r)
            
    # 7. Generate Korean descriptions for non-curated
    for r in deduped_resources:
        if 'description_kr' not in r:
            r['description_kr'] = generate_korean_desc(r)
            
    # 8. Save JSON
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "resources.json")
    
    output_data = {
        "last_updated": datetime.now().isoformat(),
        "categories": CATEGORIES,
        "resources": deduped_resources
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ 파일 저장 오류: {e}")
        return

    # 9. Print summary stats
    print("\n" + "=" * 50)
    print("📊 수집 결과 요약:")
    
    stats = {k: 0 for k in CATEGORIES.keys()}
    for r in deduped_resources:
        cat = r.get('category')
        if cat in stats:
            stats[cat] += 1
            
    total = sum(stats.values())
    
    for k, v in stats.items():
        icon = CATEGORIES[k]["icon"]
        name = CATEGORIES[k]["name_kr"]
        # align name length for display
        print(f"  {icon} {name:<6}: {v:>4}개")
        
    print("  " + "─" * 17)
    print(f"  총 합계:     {total:>4}개\n")
    print(f"🎉 저장 완료: {output_file}")

if __name__ == "__main__":
    main()
