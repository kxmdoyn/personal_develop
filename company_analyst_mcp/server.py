import asyncio
import os
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

load_dotenv()

from tools.dart_tool import get_financial_summary, get_company_trends, get_corp_code
from tools.news_tool import get_recent_news, get_competitor_analysis
from tools.applicant_tool import generate_interview_questions, analyze_applicant_fit

app = Server("company-analyst")

COMPANY_NAME_HINT = """
DART에 등록된 상장 법인명을 사용해야 합니다.
- 자회사/브랜드명은 지주사로 변환: 하나은행→하나금융지주, 신한은행→신한지주, KB국민은행→KB금융, 우리은행→우리금융지주, IBK기업은행→IBK기업은행(그대로), 하이닉스→SK하이닉스, KT→KT(그대로)
- 그룹명은 대표 상장사로: SK→SK(주), LG→LG(주), 삼성→삼성전자(또는 삼성물산)
- 확실하지 않으면 공식 상장사명 그대로 입력 (예: LG CNS, SK텔레콤, 카카오, 네이버)
"""


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_financial_summary",
            description=f"기업의 최근 3년 재무제표 요약 (영업수익/영업이익/순이익/자산). DART 공식 API 사용.\n{COMPANY_NAME_HINT}",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "DART 등록 상장법인명 (예: 하나금융지주, KB금융, 삼성전자, LG CNS, SK텔레콤)",
                    }
                },
                "required": ["company_name"],
            },
        ),
        types.Tool(
            name="get_recent_news",
            description="구글 뉴스 RSS로 기업 관련 최신 뉴스 가져오기",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "검색할 기업명 (브랜드명 그대로 가능: 하나은행, 카카오, 네이버 등)",
                    },
                    "days": {
                        "type": "integer",
                        "description": "최근 몇 일 뉴스 (기본값: 30)",
                        "default": 30,
                    },
                },
                "required": ["company_name"],
            },
        ),
        types.Tool(
            name="get_company_trends",
            description=f"DART 공시 기반 기업 트렌드 및 주요 경영사항 분석.\n{COMPANY_NAME_HINT}",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "DART 등록 상장법인명",
                    }
                },
                "required": ["company_name"],
            },
        ),
        types.Tool(
            name="get_competitor_analysis",
            description="구글 뉴스 + 네이버 금융 기반 경쟁사 분석",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "분석할 기업명",
                    }
                },
                "required": ["company_name"],
            },
        ),
        types.Tool(
            name="generate_interview_questions",
            description="기업 특화 면접 예상 질문 생성. profile.txt의 내 스펙 자동 참조.",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "지원할 기업명",
                    },
                    "job_type": {
                        "type": "string",
                        "description": "직군 (예: AI개발, 데이터분석, 기획). 비워도 됨.",
                        "default": "",
                    },
                },
                "required": ["company_name"],
            },
        ),
        types.Tool(
            name="analyze_applicant_fit",
            description="채용공고(JD)와 내 프로필 매칭 분석. 강점/약점/지원전략 제공.",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "지원할 기업명",
                    },
                    "job_description": {
                        "type": "string",
                        "description": "채용공고 전문 텍스트",
                    },
                },
                "required": ["company_name", "job_description"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "get_financial_summary":
            result = await get_financial_summary(arguments["company_name"])
        elif name == "get_recent_news":
            result = await get_recent_news(arguments["company_name"], days=arguments.get("days", 30))
        elif name == "get_company_trends":
            result = await get_company_trends(arguments["company_name"])
        elif name == "get_competitor_analysis":
            result = await get_competitor_analysis(arguments["company_name"])
        elif name == "generate_interview_questions":
            result = generate_interview_questions(arguments["company_name"], job_type=arguments.get("job_type", ""))
        elif name == "analyze_applicant_fit":
            result = analyze_applicant_fit(arguments["company_name"], job_description=arguments["job_description"])
        else:
            result = f"❌ 알 수 없는 tool: {name}"
    except Exception as e:
        result = f"❌ 오류 발생: {str(e)}"

    return [types.TextContent(type="text", text=result)]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())