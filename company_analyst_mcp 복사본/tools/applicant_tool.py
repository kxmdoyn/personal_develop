import os
from pathlib import Path


def load_profile(profile_path: str = None) -> str:
    """profile.txt 로드"""
    if profile_path is None:
        # server.py 기준 같은 디렉토리의 profile.txt
        profile_path = Path(__file__).parent.parent / "profile.txt"
    
    path = Path(profile_path)
    if not path.exists():
        return "⚠️ profile.txt 파일이 없습니다. 프로젝트 루트에 profile.txt를 작성해주세요."
    
    return path.read_text(encoding="utf-8")


def generate_interview_questions(company_name: str, job_type: str = "") -> str:
    """
    기업 특화 면접 예상 질문 생성
    실제 Claude API 호출 없이 구조화된 프롬프트 반환
    (Claude Desktop에서 이 tool 결과를 받아 Claude가 추가 분석)
    """
    profile = load_profile()
    
    job_context = f" ({job_type} 직군)" if job_type else ""
    
    output = f"🎯 [{company_name}] 면접 예상 질문 생성 요청{job_context}\n\n"
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    output += "📋 지원자 프로필\n"
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    output += profile
    output += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    output += f"위 프로필을 바탕으로 {company_name}{job_context} 면접에서 나올 수 있는\n"
    output += "예상 질문 10개와 각 질문에 대한 답변 포인트를 생성해주세요.\n\n"
    output += "카테고리:\n"
    output += "  1. 지원동기 (2문항)\n"
    output += "  2. 직무 역량 (3문항)\n"
    output += "  3. 경험/프로젝트 기반 (3문항)\n"
    output += "  4. 기업 관련 (2문항)\n"
    
    return output


def analyze_applicant_fit(company_name: str, job_description: str) -> str:
    """
    JD + 내 프로필 매칭 분석 요청 생성
    """
    profile = load_profile()
    
    output = f"🔍 [{company_name}] 지원자 적합도 분석 요청\n\n"
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    output += "📋 지원자 프로필\n"
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    output += profile
    output += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    output += "📄 채용공고 (JD)\n"
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    output += job_description
    output += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    output += "위 정보를 바탕으로 다음을 분석해주세요:\n\n"
    output += "1. 📊 매칭 점수 (0~100점) + 근거\n"
    output += "2. ✅ 강점 (JD 요구사항과 일치하는 부분)\n"
    output += "3. ⚠️ 약점/보완점 (부족한 부분)\n"
    output += "4. 💡 지원 전략 (어필 포인트 추천)\n"
    output += "5. ❓ 이 JD 기반 예상 면접 질문 5개\n"
    
    return output
