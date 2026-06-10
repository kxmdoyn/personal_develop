import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Optional


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


async def get_recent_news(company_name: str, days: int = 30) -> str:
    """
    네이버 뉴스에서 최근 뉴스 크롤링
    """
    query = company_name
    url = "https://search.naver.com/search.naver"
    params = {
        "where": "news",
        "query": query,
        "sort": "1",   # 최신순
        "ds": (datetime.now() - timedelta(days=days)).strftime("%Y.%m.%d"),
        "de": datetime.now().strftime("%Y.%m.%d"),
    }

    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.select("div.news_wrap.api_ani_send")

    if not articles:
        return f"📭 [{company_name}] 최근 {days}일 뉴스를 찾을 수 없습니다."

    output = f"📰 [{company_name}] 최근 {days}일 주요 뉴스\n\n"
    seen = set()

    for article in articles[:10]:
        title_el = article.select_one("a.news_tit")
        press_el = article.select_one("a.info.press")
        date_el = article.select_one("span.info")
        desc_el = article.select_one("div.dsc_wrap")

        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        if title in seen:
            continue
        seen.add(title)

        press = press_el.get_text(strip=True) if press_el else ""
        date = date_el.get_text(strip=True) if date_el else ""
        desc = desc_el.get_text(strip=True)[:80] if desc_el else ""
        link = title_el.get("href", "")

        output += f"  • {title}\n"
        if press or date:
            output += f"    [{press}] {date}\n"
        if desc:
            output += f"    {desc}...\n"
        output += f"    {link}\n\n"

    output += "※ 출처: 네이버 뉴스"
    return output


async def get_competitor_analysis(company_name: str) -> str:
    """
    네이버 금융에서 동종업계 경쟁사 정보 크롤링
    """
    # 네이버 금융 검색으로 종목코드 먼저 찾기
    search_url = "https://finance.naver.com/search/searchList.naver"
    params = {"query": company_name}

    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:
        resp = await client.get(search_url, params=params)
        soup = BeautifulSoup(resp.text, "html.parser")

    # 첫 번째 종목 결과
    stock_link = soup.select_one("td.tit a")
    if not stock_link:
        return f"❌ '{company_name}' 종목을 네이버 금융에서 찾을 수 없습니다. 정확한 회사명을 입력해주세요."

    href = stock_link.get("href", "")
    # /item/main.naver?code=005930 형식에서 코드 추출
    code = ""
    if "code=" in href:
        code = href.split("code=")[-1].split("&")[0]

    if not code:
        return f"❌ '{company_name}' 종목코드를 찾을 수 없습니다."

    # 동종업계 비교 페이지
    compare_url = f"https://finance.naver.com/item/coinfo.naver?code={code}"
    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:
        resp = await client.get(compare_url)
        soup = BeautifulSoup(resp.text, "html.parser")

    # 업종 정보
    industry_el = soup.select_one("em.industry")
    industry = industry_el.get_text(strip=True) if industry_el else "정보 없음"

    # 기업 개요
    summary_el = soup.select_one("div.summary_info p")
    summary = summary_el.get_text(strip=True)[:200] if summary_el else ""

    output = f"🏢 [{company_name}] 경쟁사 분석\n\n"
    output += f"  업종: {industry}\n"
    if summary:
        output += f"  개요: {summary}...\n\n"

    # 동종업종 페이지에서 경쟁사 목록
    sector_url = f"https://finance.naver.com/sise/sectorDetail.naver?sectorcode={code[:3]}"
    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:
        resp2 = await client.get(
            f"https://finance.naver.com/item/main.naver?code={code}",
        )
        soup2 = BeautifulSoup(resp2.text, "html.parser")

    # 동일 업종 상위 기업
    peers = soup2.select("table.tb_type1 tr")
    if peers:
        output += "  📊 주요 재무지표\n"
        for row in peers[1:5]:
            cols = row.select("td")
            if len(cols) >= 3:
                name = cols[0].get_text(strip=True)
                if name:
                    output += f"  • {name}\n"

    output += "\n💡 Tip: '경쟁사 A vs B 비교해줘'라고 추가로 요청하면 심층 비교 가능\n"
    output += "※ 출처: 네이버 금융"
    return output
