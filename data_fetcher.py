import yfinance as yf
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_stock_news(ticker_symbol):
    print(f"[{ticker_symbol}] 기업 재무 데이터와 뉴스 긁어오는 중...\n")
    stock = yf.Ticker(ticker_symbol)
    
    # 💡 1. 실전에 필요한 핵심 재무 지표(숫자) 긁어오기
    info = stock.info
    current_price = info.get('currentPrice', 'N/A')
    target_price = info.get('targetMeanPrice', 'N/A')
    per = info.get('trailingPE', 'N/A')
    pbr = info.get('priceToBook', 'N/A')
    recommendation = info.get('recommendationKey', 'N/A')
    
    financial_data = f"""
    [핵심 재무 및 시장 지표]
    - 현재가: {current_price}
    - 애널리스트 평균 목표가: {target_price}
    - PER (주가수익비율): {per}
    - PBR (주가순자산비율): {pbr}
    - 월가 투자의견: {recommendation}
    """
    
    # 💡 2. 기존처럼 뉴스 가져오기
    news_list = stock.news
    news_data = "\n[최신 뉴스 요약]\n"
    
    if not news_list:
        news_data += "관련 뉴스를 찾을 수 없습니다.\n"
    else:
        for idx, news in enumerate(news_list[:3]):
            content = news.get('content') or {}
            title = content.get('title', '제목 없음')
            summary = content.get('summary', '내용 없음')
            news_data += f"{idx+1}. {title} (요약: {summary})\n"
            
    # 재무 데이터와 뉴스를 하나로 합쳐서 반환!
    return financial_data + news_data

if __name__ == "__main__":
    # 한국 주식 테스트: 삼성전자 (005930.KS)
    test_ticker = "005930.KS"
    result = get_stock_news(test_ticker)
    print("=== 📊 수집된 실전 투자 데이터 ===")
    print(result)