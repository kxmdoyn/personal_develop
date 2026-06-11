# 🏢 Company Analyst MCP

취준용 기업분석 MCP 서버입니다.  
DART 공식 API + 구글 뉴스 RSS로 재무제표, 뉴스, 트렌드, 경쟁사, 면접 질문을 분석합니다.

---

## 📁 구조

```
company_analyst_mcp/
├── server.py              # MCP 서버 메인
├── tools/
│   ├── dart_tool.py       # 재무제표 요약 + 트렌드 (DART API)
│   ├── news_tool.py       # 뉴스 크롤링 + 경쟁사 (구글 뉴스 RSS)
│   └── applicant_tool.py  # 지원자 분석 + 면접 질문
├── profile.txt            # ← 내 스펙 입력 (필수!)
├── .env                   # ← DART API 키 입력 (Git 제외)
├── .gitignore
└── requirements.txt
```

---

## ⚙️ 설치 방법

### 1. Python 3.11 설치 (pyenv 사용)

```bash
brew install pyenv
pyenv install 3.11.9
```

### 2. 가상환경 생성 및 패키지 설치

```bash
cd company_analyst_mcp
pyenv local 3.11.9
~/.pyenv/versions/3.11.9/bin/python3 -m venv --without-pip venv
source venv/bin/activate
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
pip install -r requirements.txt
```

### 3. DART API 키 설정

`.env` 파일에 발급받은 키 입력:

```
DART_API_KEY=발급받은키입력
```

> DART API 발급: https://opendart.fss.or.kr → 마이페이지 → OpenAPI 신청

### 4. 내 프로필 작성

`profile.txt`를 열어서 학력/경험/기술스택 입력  
(면접 질문 생성, JD 분석 시 자동 참조)

---

## 🔌 Claude Desktop 연결

`~/Library/Application Support/Claude/claude_desktop_config.json` 열어서 추가:

```json
{
  "mcpServers": {
    "company-analyst": {
      "command": "/절대경로/company_analyst_mcp/venv/bin/python",
      "args": ["/절대경로/company_analyst_mcp/server.py"],
      "env": {
        "DART_API_KEY": "발급받은키입력"
      }
    }
  }
}
```

> ⚠️ `/절대경로/` → 실제 경로로 변경  
> 예: `/Users/kxmdoyn/workspace/doyeon/company_analyst_mcp`

저장 후 **Claude Desktop 재시작 (Cmd+Q 후 재실행)**

---

## 💬 사용 예시

```
하나은행 재무제표 요약해줘
SKT 최근 뉴스 보여줘
카카오 요즘 트렌드 어때?
삼성전자 경쟁사 분석해줘
하나은행 AI개발 직군 면접 질문 만들어줘
이 JD 분석해줘: [채용공고 붙여넣기]
```

---

## 🛠️ Tool 목록

| Tool                           | 설명                   | DART 키 필요 |
| ------------------------------ | ---------------------- | :----------: |
| `get_financial_summary`        | 최근 3년 재무제표 요약 |      ✅      |
| `get_recent_news`              | 구글 뉴스 RSS 크롤링   |      ❌      |
| `get_company_trends`           | 공시 기반 트렌드 분석  |      ✅      |
| `get_competitor_analysis`      | 경쟁사 비교            |      ❌      |
| `generate_interview_questions` | 면접 예상 질문 생성    |      ❌      |
| `analyze_applicant_fit`        | JD + 프로필 매칭 분석  |      ❌      |

---

## 🔄 회사명 자동 매핑

브랜드명/자회사명으로 물어봐도 자동으로 DART 상장법인명으로 변환됩니다.

| 입력       | 자동 변환    |
| ---------- | ------------ |
| 하나은행   | 하나금융지주 |
| 신한은행   | 신한지주     |
| KB국민은행 | KB금융       |
| 우리은행   | 우리금융지주 |
| LG CNS     | LG씨엔에스   |
| 하이닉스   | SK하이닉스   |
