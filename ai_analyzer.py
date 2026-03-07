import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
from data_fetcher import get_stock_news

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = 'gemini-2.5-flash'

def get_ticker_from_name(name):
    # 영문 대문자 1~5자리(미국주식) 또는 숫자6자리.KS/KQ(한국주식) 형태면 그대로 반환
    if re.match(r'^[A-Z]{1,5}$', name.upper()) or re.match(r'^\d{6}\.(KS|KQ)$', name.upper()):
        return name.upper()
        
    model = genai.GenerativeModel(MODEL_NAME)
    
    # 💡 띄어쓰기, 오타, 약칭까지 다 잡아내는 강력한 프롬프트!
    prompt = f"""
    너는 금융 데이터 전문가야. 사용자가 입력한 기업명 '{name}'의 정확한 Yahoo Finance 종목 코드(Ticker)를 찾아줘.
    
    [검색 및 보정 규칙]
    1. 사용자가 띄어쓰기를 무시하거나 오타를 내도(예: 두산로보틱스, 에코프로 비엠, 램 리서치 등) 찰떡같이 공식 명칭으로 인식해서 찾아줘.
    2. 한국 코스피 주식은 반드시 숫자 6자리 뒤에 '.KS'를 붙여. (예: 삼성전자 -> 005930.KS, 두산로보틱스 -> 454910.KS)
    3. 한국 코스닥 주식은 반드시 숫자 6자리 뒤에 '.KQ'를 붙여. (예: 에코프로비엠 -> 247540.KQ)
    4. 미국 주식은 심볼만 대문자로 출력해. (예: 애플 -> AAPL, 테슬라 -> TSLA)
    5. 공식 명칭뿐만 아니라 사람들이 흔히 부르는 약칭이나 영문/한글 혼용도 알아서 보정해.
    
    다른 부가 설명은 일절 하지 말고, 오직 '종목 코드' 딱 하나만 대문자로 출력해.
    만약 도저히 못 찾겠다면 'UNKNOWN'이라고 출력해.
    """
    
    try:
        response = model.generate_content(prompt)
        ticker = response.text.strip().upper()
        
        # AI가 혹시라도 마침표나 쓸데없는 특수문자를 붙였을 경우를 대비한 안전장치
        ticker = re.sub(r'[^A-Z0-9.]', '', ticker)
        return ticker
    except Exception as e:
        print(f"티커 검색 중 에러: {e}")
        return "UNKNOWN"

def analyze_stock_news(ticker):
    print(f"\n🧠 [{ticker}] 제미나이 AI가 융합 분석 중... (잠시만!)")
    
    combined_data = get_stock_news(ticker)
    
    if "일시적 오류 발생" in combined_data or ("관련 뉴스가 없습니다" in combined_data and "[핵심 재무" not in combined_data):
        return '{"error": "데이터를 불러올 수 없습니다. 야후 파이낸스 접속 지연일 수 있습니다."}'
        
    model = genai.GenerativeModel(MODEL_NAME)
    
    prompt = f"""
    너는 주식 초보자들에게 어려운 금융 개념을 친절하게 설명해 주는 AI 어시스턴트야.
    아래 제공된 '{ticker}' 종목의 [재무 데이터]와 [최신 뉴스]를 분석해 줘. 
    절대로 '매수/매도'를 직접적으로 권유하거나 확정적인 수익을 보장하는 뉘앙스로 말하면 안 돼. 철저히 '객관적 데이터 기반의 참고용 설명'만 제공해.
    
    [수집된 데이터]
    {combined_data}
    
    결과는 반드시 아래의 JSON 형식으로만 출력해.
    
    {{
        "financial_analysis": "PER, PBR, 목표가 등을 바탕으로 이 주식의 현재 가치 상태를 초보자 눈높이에서 쉽게 설명 (4~5문장, 단정적인 표현 금지)",
        "competitor_analysis": "이 기업의 가장 강력한 경쟁사(라이벌) 1~2곳을 언급하고, 현재 이 기업이 경쟁사 대비 가진 장점이나 단점을 주린이 눈높이에서 비교 설명 (3~4문장)",
        "news_sentiment": "최신 뉴스들에 나타난 주요 호재/악재를 객관적으로 요약 설명 (3~4문장)",
        "alternatives": "현재 상황을 고려할 때, 포트폴리오 다각화 차원에서 함께 공부해보면 좋을 대안 섹터나 리스크 헷지 방법",
        "recommendations": [
            {{"ticker": "관심종목코드1", "reason": "이 종목을 함께 살펴보면 좋은 이유 (투자 권유가 아님을 명시할 것)"}},
            {{"ticker": "관심종목코드2", "reason": "함께 볼만한 이유"}},
            {{"ticker": "관심종목코드3", "reason": "함께 볼만한 이유"}}
        ]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # 마크다운 백틱(```json) 제거 로직
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        return result_text.strip()
    except Exception as e:
        print(f"AI 분석 중 에러: {e}")
        return '{"error": "AI 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."}'
