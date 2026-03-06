import os
import google.generativeai as genai
from dotenv import load_dotenv
from data_fetcher import get_stock_news

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# 👇👇👇 [NEW] 여기에 종목명 변환 함수 추가! 👇👇👇
def get_ticker_from_name(name):
    # 입력값이 이미 영어 대문자나 숫자 조합이면(예: LRCX, 005930.KS) 그대로 반환
    import re
    if re.match(r'^[A-Z]{1,5}$', name.upper()) or re.match(r'^\d{6}\.(KS|KQ)$', name.upper()):
        return name.upper()
        
    # 한글이나 일반 이름이면 제미나이에게 검색을 시킴
    model =  genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    기업명 '{name}'의 야후 파이낸스(Yahoo Finance) 종목 코드를 찾아줘.
    - 미국 주식 (예: 램리서치 -> LRCX, 애플 -> AAPL, 노스롭그루먼 -> NOC)
    - 한국 코스피 (예: 삼성전자 -> 005930.KS)
    - 한국 코스닥 (예: 에코프로 -> 086520.KQ)
    다른 부가 설명은 일절 하지 말고, 오직 '종목 코드' 딱 하나만 대문자로 출력해.
    """
    response = model.generate_content(prompt)
    return response.text.strip().upper()
# 👆👆👆 여기까지 👆👆👆

def analyze_stock_news(ticker):
    print(f"\n🧠 [{ticker}] 제미나이 AI가 재무 데이터와 뉴스를 융합 분석 중... (잠시만!)")
    
    combined_data = get_stock_news(ticker)
    
    if "관련 뉴스를 찾을 수 없습니다" in combined_data and "[핵심 재무" not in combined_data:
        return '{"error": "데이터를 불러올 수 없습니다."}'
        
    model = genai.GenerativeModel('gemini-2.5-flash')
    
 # 👇👇👇 여기서부터 덮어쓰기! 👇👇👇
    prompt = f"""
    너는 주식 초보자(주린이)들에게 어려운 금융 개념을 아주 쉽고 친절하게 설명해 주는 최고의 주식 일타강사야.
    아래 제공된 '{ticker}' 종목의 [재무 데이터]와 [최신 뉴스]를 종합적으로 분석해 줘.
    
    초보자가 읽을 것이므로 PER, PBR, 목표가 같은 용어가 나오면 그게 무슨 의미인지(예: PER이 낮으면 본전 뽑는 기간이 짧아서 싸다는 뜻 등), 그래서 지금 이 주식이 비싼 건지 싼 건지 아주 쉽게 풀어서 설명해 줘야 해. 
    전문 용어를 남발하지 말고, 내용도 4~5문장 이상으로 아주 알차고 다정하게 적어줘.
    
    [수집된 데이터]
    {combined_data}
    
    결과는 반드시 아래의 JSON 형식으로만 출력해. 마크다운 기호나 다른 설명은 절대 추가하지 말고 오직 JSON 텍스트만 뱉어내.
    
    {{
        "financial_analysis": "PER, PBR, 목표가 등을 바탕으로 이 주식이 현재 싼지 비싼지 주린이 눈높이에 맞춰서 쉽고 친절하게 풀어서 설명 (4~5문장 정도로 알차게)",
        "news_sentiment": "최신 뉴스들에 나타난 주요 호재/악재를 초보자도 이해하기 쉽게 비유를 섞어 설명 (3~4문장)",
        "alternatives": "현재 상황을 고려할 때, 초보자가 조금 더 마음 편하게 접근할 수 있는 대안이나 리스크 헷지 전략 (친절한 설명 포함)",
        "recommendations": [
            {{"ticker": "추천종목코드1", "reason": "왜 이 종목을 추천하는지 주린이도 끄덕일 수 있는 쉬운 이유 한 줄"}},
            {{"ticker": "추천종목코드2", "reason": "추천 이유"}},
            {{"ticker": "추천종목코드3", "reason": "추천 이유"}}
        ]
    }}
    """
    # 👆👆👆 여기까지 덮어쓰기! 👆👆👆
    
    response = model.generate_content(prompt)
    
    result_text = response.text.strip()
    if result_text.startswith("```json"):
        result_text = result_text[7:]
    if result_text.endswith("```"):
        result_text = result_text[:-3]
        
    return result_text.strip()

if __name__ == "__main__":
    test_ticker = "005930.KS"
    result_json = analyze_stock_news(test_ticker)
    print("\n=== 🎯 실전 AI 분석 결과 (JSON) ===")
    print(result_json)