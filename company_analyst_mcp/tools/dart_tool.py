import httpx
import os
import zipfile
import io
from typing import Optional
from xml.etree import ElementTree as ET

DART_API_KEY = os.getenv("DART_API_KEY", "")
DART_BASE = "https://opendart.fss.or.kr/api"

_CORP_CODE_CACHE: dict = {}
_CORP_LIST_CACHE: list = []

# 영문/약칭 → DART 등록 법인명 변환 테이블
ALIAS_MAP = {
    "lg cns": "LG씨엔에스",
    "lgcns": "LG씨엔에스",
    "sk하이닉스": "SK하이닉스",
    "하이닉스": "SK하이닉스",
    "kb국민은행": "KB금융",
    "국민은행": "KB금융",
    "신한은행": "신한지주",
    "우리은행": "우리금융지주",
    "농협은행": "NH농협금융지주",
    "하나은행": "하나금융지주",
    "기업은행": "IBK기업은행",
    "삼성그룹": "삼성전자",
    "sk그룹": "SK(주)",
    "lg그룹": "LG(주)",
    "롯데그룹": "롯데지주",
}

# 재무데이터 없는 구법인 → 현재 지주사 매핑
LEGACY_CODE_MAP = {
    "00130897": "00547583",  # 구 하나은행 → 하나금융지주
    "00158909": "00547583",  # 구 하나은행 → 하나금융지주
}

NOISE = ("기업인수목적", "스팩", "SPAC", "호기업", "호스팩")


async def _load_corp_list() -> list:
    global _CORP_LIST_CACHE
    if _CORP_LIST_CACHE:
        return _CORP_LIST_CACHE
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{DART_BASE}/corpCode.xml", params={"crtfc_key": DART_API_KEY})
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        root = ET.fromstring(zf.read("CORPCODE.xml"))
        _CORP_LIST_CACHE = [
            {
                "name": item.findtext("corp_name", ""),
                "code": item.findtext("corp_code", ""),
                "stock": item.findtext("stock_code", "").strip(),
            }
            for item in root.findall("list")
        ]
    except Exception:
        pass
    return _CORP_LIST_CACHE


def _normalize(name: str) -> str:
    """소문자 + 공백 제거"""
    return name.lower().replace(" ", "").replace("(주)", "").replace("주식회사", "").strip()


async def _find_corp_code(company_name: str) -> Optional[str]:
    """전체 법인 목록에서 검색"""
    corps = await _load_corp_list()
    norm_query = _normalize(company_name)

    # 1순위: 완전 일치 (노이즈 제외)
    for c in corps:
        if _normalize(c["name"]) == norm_query and not any(n in c["name"] for n in NOISE):
            code = c["code"]
            return LEGACY_CODE_MAP.get(code, code)

    # 2순위: 포함 일치, 상장사 우선, 이름 짧은 것
    candidates = [
        c for c in corps
        if norm_query in _normalize(c["name"]) and not any(n in c["name"] for n in NOISE)
    ]
    listed = sorted([c for c in candidates if c["stock"]], key=lambda x: len(x["name"]))
    if listed:
        code = listed[0]["code"]
        return LEGACY_CODE_MAP.get(code, code)

    unlisted = sorted(candidates, key=lambda x: len(x["name"]))
    if unlisted:
        code = unlisted[0]["code"]
        return LEGACY_CODE_MAP.get(code, code)

    return None


async def get_corp_code(company_name: str) -> Optional[str]:
    """회사명 → corp_code. alias 변환 + 자동 매핑 포함"""
    # alias 변환
    normalized = ALIAS_MAP.get(company_name.lower().strip(), company_name)

    if normalized in _CORP_CODE_CACHE:
        return _CORP_CODE_CACHE[normalized]

    code = await _find_corp_code(normalized)
    if code:
        _CORP_CODE_CACHE[normalized] = code
        _CORP_CODE_CACHE[company_name] = code
        return code
    return None


async def _get_accounts(corp_code: str, year: int, fs_div: str = "CFS") -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(f"{DART_BASE}/fnlttSinglAcntAll.json", params={
            "crtfc_key": DART_API_KEY,
            "corp_code": corp_code,
            "bsns_year": str(year),
            "reprt_code": "11011",
            "fs_div": fs_div,
        })
        data = resp.json()
    if data.get("status") != "000":
        return {}
    # sj_nm 별로 분리해서 반환 (중복 계정명 방지)
    result = {}
    for item in data.get("list", []):
        sj = item.get("sj_nm", "")
        key = f"{sj}|{item['account_nm']}"
        result[key] = item.get("thstrm_amount", "0")
    return result


def _get(items: dict, sj: str, *accts) -> str:
    """특정 표(sj_nm)에서 계정값 조회"""
    for acct in accts:
        v = items.get(f"{sj}|{acct}")
        if v and str(v).strip() not in ("0", ""):
            return v
    return ""


def _fmt(val: str) -> str:
    try:
        n = int(str(val).replace(",", "").replace(" ", ""))
        if abs(n) >= 1_0000_0000_0000:
            return f"{n / 1_0000_0000_0000:.1f}조원"
        elif abs(n) >= 1_0000_0000:
            return f"{n / 1_0000_0000:.0f}억원"
        return f"{n:,}원"
    except Exception:
        return val or "-"


def _pick(items: dict, *keys) -> str:
    for k in keys:
        v = items.get(k)
        if v and str(v).strip() not in ("0", "", None):
            return v
    return "0"


async def get_financial_summary(company_name: str) -> str:
    if not DART_API_KEY:
        return "❌ DART_API_KEY가 설정되지 않았습니다."

    corp_code = await get_corp_code(company_name)
    if not corp_code:
        return f"❌ '{company_name}'에 해당하는 기업을 DART에서 찾을 수 없습니다."

    results = []
    for year in [2024, 2023, 2022]:
        items = await _get_accounts(corp_code, year, "CFS")
        fs_label = "연결"
        if not items:
            items = await _get_accounts(corp_code, year, "OFS")
            fs_label = "별도"
        if not items:
            results.append(f"  {year}년: 데이터 없음")
            continue

        # 표 이름은 기업마다 다름: 포괄손익계산서 / 손익계산서
        def _is(acct):
            return _get(items, "포괄손익계산서", acct) or _get(items, "손익계산서", acct)
        def _bs(acct):
            return _get(items, "재무상태표", acct)

        revenue = (
            _is("매출액") or _is("매출") or _is("수익(매출액)") or
            _is("영업수익") or _is("이자수익") or _is("순이자이익") or
            _is("총영업이익") or _is("보험료수익") or _is("수수료수익") or "0"
        )
        op_income = (
            _is("영업이익") or _is("영업이익(손실)") or
            _is("순영업이익") or _is("충당금적립전이익") or "0"
        )
        net_income = (
            _is("연결당기순이익") or _is("당기순이익") or
            _is("당기순이익(손실)") or "0"
        )
        total_assets = _bs("자산총계")
        equity = _bs("자본총계")

        results.append(
            f"  {year}년 ({fs_label})\n"
            f"    영업수익: {_fmt(revenue)} | 영업이익: {_fmt(op_income)} | 순이익: {_fmt(net_income)}\n"
            f"    자산총계: {_fmt(total_assets)} | 자본총계: {_fmt(equity)}"
        )

    output = f"📊 [{company_name}] 재무제표 요약\n\n"
    output += "\n\n".join(results)
    output += "\n\n※ 출처: DART 전자공시시스템"
    return output


async def get_company_trends(company_name: str) -> str:
    if not DART_API_KEY:
        return "❌ DART_API_KEY가 설정되지 않았습니다."

    corp_code = await get_corp_code(company_name)
    if not corp_code:
        return f"❌ '{company_name}'에 해당하는 기업을 DART에서 찾을 수 없습니다."

    output = f"📈 [{company_name}] 최근 공시/트렌드\n\n"

    async with httpx.AsyncClient(timeout=20) as client:
        for pblntf_ty, label in [("B", "주요사항"), ("A", "정기공시")]:
            params = {
                "crtfc_key": DART_API_KEY,
                "corp_code": corp_code,
                "bgn_de": "20240101",
                "end_de": "20261231",
                "pblntf_ty": pblntf_ty,
                "page_count": "10",
            }
            try:
                resp = await client.get(f"{DART_BASE}/list.json", params=params)
                data = resp.json()
                filings = data.get("list", [])
                if filings:
                    output += f"  [{label}]\n"
                    for f in filings[:5]:
                        output += f"  • [{f.get('rcept_dt', '')}] {f.get('report_nm', '')}\n"
                    output += "\n"
            except Exception:
                continue

    if output == f"📈 [{company_name}] 최근 공시/트렌드\n\n":
        return f"📭 [{company_name}] 최근 공시를 찾을 수 없습니다."

    output += "💡 위 공시를 바탕으로 Claude가 트렌드를 분석합니다.\n"
    output += "※ 출처: DART 전자공시시스템"
    return output