import httpx
import os
from typing import Optional

DART_API_KEY = os.getenv("DART_API_KEY", "")
DART_BASE = "https://opendart.fss.or.kr/api"


async def get_corp_code(company_name: str) -> Optional[str]:
    """회사명으로 DART corp_code 조회"""
    url = f"{DART_BASE}/corpCode.xml"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params={"crtfc_key": DART_API_KEY})
        resp.raise_for_status()

    # XML에서 회사명 매칭 (간단 파싱)
    import zipfile, io
    from xml.etree import ElementTree as ET

    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    xml_data = zf.read("CORPCODE.xml")
    root = ET.fromstring(xml_data)

    for item in root.findall("list"):
        name = item.findtext("corp_name", "")
        if company_name in name:
            return item.findtext("corp_code")
    return None


async def get_financial_summary(company_name: str) -> str:
    """
    최근 3년 재무제표 요약 (매출, 영업이익, 당기순이익, 부채비율)
    DART 재무정보 API 사용
    """
    if not DART_API_KEY:
        return "❌ DART_API_KEY가 설정되지 않았습니다. .env 파일에 키를 입력해주세요."

    corp_code = await get_corp_code(company_name)
    if not corp_code:
        return f"❌ '{company_name}'에 해당하는 기업을 DART에서 찾을 수 없습니다."

    results = []
    current_year = 2024

    async with httpx.AsyncClient(timeout=15) as client:
        for year in [current_year, current_year - 1, current_year - 2]:
            params = {
                "crtfc_key": DART_API_KEY,
                "corp_code": corp_code,
                "bsns_year": str(year),
                "reprt_code": "11011",  # 사업보고서
                "fs_div": "CFS",        # 연결재무제표
            }
            resp = await client.get(f"{DART_BASE}/fnlttSinglAcntAll.json", params=params)
            data = resp.json()

            if data.get("status") != "000":
                results.append(f"  {year}년: 데이터 없음")
                continue

            items = {
                item["account_nm"]: item.get("thstrm_amount", "0")
                for item in data.get("list", [])
            }

            def fmt(val: str) -> str:
                try:
                    return f"{int(val.replace(',', '')) / 1_0000_0000:.0f}억원"
                except:
                    return val or "-"

            revenue = fmt(items.get("매출액", items.get("수익(매출액)", "0")))
            op_income = fmt(items.get("영업이익", "0"))
            net_income = fmt(items.get("당기순이익", "0"))
            results.append(
                f"  {year}년 | 매출: {revenue} | 영업이익: {op_income} | 순이익: {net_income}"
            )

    output = f"📊 [{company_name}] 재무제표 요약 (연결기준)\n"
    output += "\n".join(results)
    output += "\n\n※ 출처: DART 전자공시시스템"
    return output


async def get_company_trends(company_name: str) -> str:
    """
    DART 최근 공시(IR, 신사업, 주요경영사항 등) 기반 트렌드 분석
    """
    if not DART_API_KEY:
        return "❌ DART_API_KEY가 설정되지 않았습니다. .env 파일에 키를 입력해주세요."

    corp_code = await get_corp_code(company_name)
    if not corp_code:
        return f"❌ '{company_name}'에 해당하는 기업을 DART에서 찾을 수 없습니다."

    async with httpx.AsyncClient(timeout=15) as client:
        params = {
            "crtfc_key": DART_API_KEY,
            "corp_code": corp_code,
            "bgn_de": "20240101",
            "end_de": "20251231",
            "pblntf_ty": "B",  # 주요사항보고
            "page_count": 10,
        }
        resp = await client.get(f"{DART_BASE}/list.json", params=params)
        data = resp.json()

    filings = data.get("list", [])
    if not filings:
        return f"📭 [{company_name}] 최근 주요 공시를 찾을 수 없습니다."

    output = f"📈 [{company_name}] 최근 공시/트렌드\n\n"
    for f in filings[:8]:
        output += f"  • [{f.get('rcept_dt', '')}] {f.get('report_nm', '')}\n"

    output += "\n💡 주요 키워드는 위 공시 제목을 바탕으로 Claude가 분석합니다."
    output += "\n※ 출처: DART 전자공시시스템"
    return output
