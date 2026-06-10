# 🏢 Company Analyst MCP

취준용 기업분석 MCP 서버입니다.  
DART 공식 API + 네이버 뉴스 크롤링으로 재무제표, 뉴스, 트렌드, 경쟁사, 면접 질문을 분석합니다.

---

## 📁 구조

```
company_analyst_mcp/
├── server.py              # MCP 서버 메인
├── tools/
│   ├── dart_tool.py       # 재무제표 요약 + 트렌드 (DART API)
│   ├── news_tool.py       # 뉴스 크롤링 + 경쟁사 (네이버)
│   └── applicant_tool.py  # 지원자 분석 + 면접 질문
├── profile.txt            # ← 내 스펙 입력 (필수!)
├── .env                   # ← DART API 키 입력
└── requirements.txt
```

---

## ⚙️ 설치 방법

### 1. 패키지 설치

```bash
cd company_analyst_mcp
pip install -r requirements.txt
```

### 2. DART API 키 설정

`.env` 파일 열어서 발급받은 키 입력:

```
DART_API_KEY=발급받은키입력
```

> DART API 발급: https://opendart.fss.or.kr → 마이페이지 → OpenAPI 신청

### 3. 내 프로필 작성

`profile.txt`를 열어서 내 스펙/경험 입력  
(면접 질문 생성, 지원자 분석 시 자동으로 참조됩니다)

---

## 🔌 Claude Desktop 연결

`~/Library/Application Support/Claude/claude_desktop_config.json` 파일을 열고 아래 내용 추가:

```json
{
  "mcpServers": {
    "company-analyst": {
      "command": "python",
      "args": ["/절대경로/company_analyst_mcp/server.py"],
      "env": {
        "DART_API_KEY": "발급받은키입력"
      }
    }
  }
}
```

> ⚠️ `/절대경로/` 부분을 실제 경로로 바꿔주세요.  
> 예: `/Users/doyeon/projects/company_analyst_mcp/server.py`

설정 후 **Claude Desktop 재시작**하면 연결 완료!

---

## 💬 사용 예시

Claude Desktop에서 이렇게 말하면 됩니다:

```
"하나은행 재무제표 요약해줘"
"SKT 최근 뉴스 보여줘"
"카카오 요즘 트렌드 어때?"
"삼성전자 경쟁사 분석해줘"
"하나은행 AI개발 직군 면접 질문 만들어줘"
"이 JD 분석해줘: [채용공고 붙여넣기]"
```

---

## 🛠️ Tool 목록

| Tool | 설명 | DART 키 필요 |
|------|------|:---:|
| `get_financial_summary` | 최근 3년 재무제표 요약 | ✅ |
| `get_recent_news` | 네이버 뉴스 크롤링 | ❌ |
| `get_company_trends` | 공시 기반 트렌드 분석 | ✅ |
| `get_competitor_analysis` | 경쟁사 비교 (네이버 금융) | ❌ |
| `generate_interview_questions` | 면접 예상 질문 생성 | ❌ |
| `analyze_applicant_fit` | JD + 프로필 매칭 분석 | ❌ |
