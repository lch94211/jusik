import streamlit as st
import json
import yfinance as yf
import requests # 👈 여기도 import requests 추가!
from ai_analyzer import analyze_stock_news, get_ticker_from_name

st.set_page_config(page_title="실전 주식 AI 퀀트 대시보드", page_icon="📊", layout="wide")

# 👇 [NEW] 이 부분 추가! 하루(24시간) 단위로 결과 캐싱(저장)
@st.cache_data(ttl="1d")
def get_cached_ticker(name):
    return get_ticker_from_name(name)

@st.cache_data(ttl="1d")
def get_cached_analysis(ticker):
    return analyze_stock_news(ticker)
# 👆 여기까지 추가

st.markdown("""
    <style>
    div[data-baseweb="input"] { height: 100px !important; }
    div[data-baseweb="input"] input {
        font-size: 2.5rem !important; text-align: center !important;
        height: 100px !important; line-height: 100px !important; font-weight: 900 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 나만의 실전 AI 퀀트 분석 대시보드 v2.0")
st.markdown("<p style='font-size: 1.3rem; color: #666;'>기업명(한글/영문)을 편하게 입력하고 <b>엔터(Enter)</b>를 누르세요!</p>", unsafe_allow_html=True)
st.divider()

user_input = st.text_input("", placeholder="예: 삼성전자, 램리서치, LRCX")

if user_input:
    with st.spinner(f"'{user_input}'의 정확한 종목 코드를 찾는 중... 🔍"):
        # 💡 [변경] 이제 캐싱된 함수를 부름!
        ticker = get_cached_ticker(user_input)
        st.info(f"💡 인식된 종목 코드: **{ticker}**")
        
    with st.spinner(f"[{ticker}] 기업 펀더멘털과 최신 뉴스를 융합 분석 중입니다... 🧠"):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            if not hist.empty:
                st.subheader(f"📈 {ticker} 최근 1개월 주가 흐름")
                st.line_chart(hist['Close']) 
        except Exception as e:
            st.error(f"차트 로딩 에러: {e}")

        # 💡 [변경] API를 또 찌르지 않고 캐시(메모리)에서 가져옴!
        result_text = get_cached_analysis(ticker)
        
        try:
            data = json.loads(result_text)
            
            st.subheader("💼 AI 퀀트 재무 분석 (가치 평가)")
            st.success(data.get("financial_analysis", "재무 분석 정보가 없습니다."))
            
            st.subheader("📰 최신 뉴스 모멘텀 동향")
            st.info(data.get("news_sentiment", "뉴스 동향 정보가 없습니다."))
            
            st.subheader("🔄 투자 대안 및 리스크 헷지 전략")
            st.warning(data.get("alternatives", "대안 정보가 없습니다."))
            
            st.subheader("💡 AI 실전 추천 종목 Top 3")
            cols = st.columns(3)
            recs = data.get("recommendations", [])
            
            for i, col in enumerate(cols):
                if i < len(recs):
                    with col:
                        st.metric(label="추천 종목", value=recs[i].get("ticker", "N/A"))
                        st.write(recs[i].get("reason", "이유 없음"))
                        
        except json.JSONDecodeError:
            st.error("AI가 분석 결과를 올바른 형식으로 주지 않았어. 다시 시도해 줘!")

            st.write("원본 데이터 확인:", result_text)
