import httpx
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET


async def get_recent_news(company_name: str, days: int = 30) -> str:
    """구글 뉴스 RSS로 최신 뉴스 가져오기"""
    url = "https://news.google.com/rss/search"
    params = {
        "q": company_name,
        "hl": "ko",
        "gl": "KR",
        "ceid": "KR:ko",
    }

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
    except Exception as e:
        return f"❌ 뉴스 가져오기 실패: {e}"

    try:
        root = ET.fromstring(resp.text)
    except Exception as e:
        return f"❌ 뉴스 파싱 실패: {e}"

    items = root.findall(".//item")
    if not items:
        return f"📭 [{company_name}] 최근 뉴스를 찾을 수 없습니다."

    cutoff = datetime.now() - timedelta(days=days)
    output = f"📰 [{company_name}] 최근 {days}일 주요 뉴스\n\n"
    count = 0

    for item in items[:15]:
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date = item.findtext("pubDate", "").strip()
        source = item.findtext("source", "").strip()

        if not title:
            continue

        # 날짜 파싱
        date_str = ""
        try:
            dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
            if dt < cutoff:
                continue
            date_str = dt.strftime("%Y.%m.%d")
        except Exception:
            date_str = pub_date[:16] if pub_date else ""

        output += f"  • {title}\n"
        if source or date_str:
            output += f"    [{source}] {date_str}\n"
        if link:
            output += f"    {link}\n"
        output += "\n"
        count += 1
        if count >= 10:
            break

    if count == 0:
        return f"📭 [{company_name}] 최근 {days}일 뉴스가 없습니다."

    output += "※ 출처: Google 뉴스"
    return output


async def get_competitor_analysis(company_name: str) -> str:
    """구글 뉴스 RSS로 경쟁사 관련 뉴스 + 네이버 금융 종목 정보"""
    # 경쟁사 뉴스 검색
    competitor_query = f"{company_name} 경쟁사 OR 업계 OR 시장점유율"
    url = "https://news.google.com/rss/search"
    params = {
        "q": competitor_query,
        "hl": "ko",
        "gl": "KR",
        "ceid": "KR:ko",
    }

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, params=params)
            root = ET.fromstring(resp.text)
        items = root.findall(".//item")
    except Exception:
        items = []

    output = f"🏢 [{company_name}] 경쟁사 분석\n\n"

    # 네이버 금융 자동완성으로 종목코드 시도
    try:
        from bs4 import BeautifulSoup
        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }
        async with httpx.AsyncClient(timeout=10, headers=HEADERS, follow_redirects=True) as client:
            resp2 = await client.get(
                "https://finance.naver.com/search/searchList.naver",
                params={"query": company_name}
            )
            soup = BeautifulSoup(resp2.text, "html.parser")
            link = soup.select_one("td.tit a")
            if link and "code=" in link.get("href", ""):
                code = link["href"].split("code=")[-1].split("&")[0]
                # 기업 정보
                resp3 = await client.get(f"https://finance.naver.com/item/coinfo.naver?code={code}")
                soup3 = BeautifulSoup(resp3.text, "html.parser")
                industry_el = soup3.select_one("em.industry")
                summary_el = soup3.select_one("div.summary_info p")
                if industry_el:
                    output += f"  업종: {industry_el.get_text(strip=True)}\n"
                if summary_el:
                    output += f"  개요: {summary_el.get_text(strip=True)[:200]}...\n"
                output += "\n"
    except Exception:
        pass

    # 경쟁사 관련 뉴스
    if items:
        output += "  📰 경쟁사 관련 최신 뉴스\n\n"
        for item in items[:6]:
            title = item.findtext("title", "").strip()
            source = item.findtext("source", "").strip()
            pub_date = item.findtext("pubDate", "")[:16]
            if title:
                output += f"  • {title}\n"
                output += f"    [{source}] {pub_date}\n\n"
    else:
        output += "  경쟁사 뉴스를 찾을 수 없습니다.\n"

    output += "💡 Tip: 'KB금융 vs 하나금융지주 비교해줘'처럼 추가 요청 가능\n"
    output += "※ 출처: Google 뉴스 / 네이버 금융"
    return output