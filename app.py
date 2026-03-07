import streamlit as st
import json
import yfinance as yf
import requests
import time  # 💡 쿨타임 계산을 위해 추가!
from ai_analyzer import analyze_stock_news, get_ticker_from_name

st.set_page_config(page_title="실전 주식 AI 퀀트 대시보드", page_icon="📊", layout="wide")

# 👇👇👇 [NEW] 사용자별 도배 방지 시스템 도입 👇👇👇
if 'search_count' not in st.session_state:
    st.session_state.search_count = 0  # 접속 후 검색한 횟수
if 'last_search_time' not in st.session_state:
    st.session_state.last_search_time = 0.0  # 마지막으로 검색한 시간

MAX_SEARCHES = 20  # 한 사람당 최대 허용 검색 횟수
COOLDOWN = 10      # 한 번 검색 후 기다려야 하는 쿨타임 (초)
# 👆👆👆 여기까지 👆👆👆

@st.cache_data(ttl="1d")
def get_cached_ticker(name):
    return get_ticker_from_name(name)

@st.cache_data(ttl="1d")
def get_cached_analysis(ticker):
    return analyze_stock_news(ticker)

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

# 💡 상단에 현재 남은 횟수 표시
st.caption(f"🔒 보안 모드 작동 중: 현재 세션 남은 검색 횟수 ({MAX_SEARCHES - st.session_state.search_count} / {MAX_SEARCHES})")
st.divider()

user_input = st.text_input("", placeholder="예: 삼성전자, 램리서치, 테슬라")

if user_input:
    current_time = time.time()
    time_passed = current_time - st.session_state.last_search_time
    
    # 🛡️ 1단계 방어: 최대 검색 횟수 초과 시
    if st.session_state.search_count >= MAX_SEARCHES:
        st.error("🚫 도배 방지: 현재 접속 창에서는 더 이상 검색할 수 없습니다. 새로고침 후 이용해 주세요!")
        
    # 🛡️ 2단계 방어: 쿨타임(10초)이 지나기 전에 연타했을 시
    elif time_passed < COOLDOWN:
        st.warning(f"⏳ AI가 생각할 시간이 필요해요! {int(COOLDOWN - time_passed)}초 후에 다시 시도해 주세요.")
        
    # 🟢 정상적인 검색 통과!
    else:
        # 검색 횟수 1 증가 및 마지막 검색 시간 업데이트
        st.session_state.search_count += 1
        st.session_state.last_search_time = current_time
        
        with st.spinner(f"'{user_input}'의 정확한 종목 코드를 찾는 중... 🔍"):
            ticker = get_cached_ticker(user_input)
            st.info(f"💡 인식된 종목 코드: **{ticker}**")
            
        with st.spinner(f"[{ticker}] 기업 펀더멘털과 최신 뉴스를 융합 분석 중입니다... 🧠"):
            try:
                session = requests.Session()
                session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"})
                
                stock = yf.Ticker(ticker, session=session)
                hist = stock.history(period="1mo")
                if not hist.empty:
                    st.subheader(f"📈 {ticker} 최근 1개월 주가 흐름")
                    st.line_chart(hist['Close']) 
            except Exception as e:
                st.error(f"차트 로딩 에러: {e}")

            result_text = get_cached_analysis(ticker)
            
            try:
                data = json.loads(result_text)
                
                st.subheader("💼 AI 주식 일타강사의 친절한 가치 평가")
                st.success(data.get("financial_analysis", "재무 분석 정보가 없습니다."))
                
                st.subheader("📰 최신 뉴스 모멘텀 (호재/악재)")
                st.info(data.get("news_sentiment", "뉴스 동향 정보가 없습니다."))
                
                st.subheader("🔄 주린이를 위한 투자 대안 및 전략")
                st.warning(data.get("alternatives", "대안 정보가 없습니다."))
                
                st.subheader("💡 AI 추천 종목 Top 3")
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
