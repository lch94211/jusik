import streamlit as st
import json
import yfinance as yf
import time
from ai_analyzer import analyze_stock_news, get_ticker_from_name

st.set_page_config(page_title="실전 주식 AI 퀀트 대시보드", page_icon="📊", layout="wide")

if 'search_count' not in st.session_state:
    st.session_state.search_count = 0
if 'last_search_time' not in st.session_state:
    st.session_state.last_search_time = 0.0

MAX_SEARCHES = 20  
COOLDOWN = 10      

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
    /* 면책조항 폰트 작고 흐리게 */
    .disclaimer { font-size: 0.8rem; color: #888; text-align: center; margin-top: 50px; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 나만의 실전 AI 퀀트 분석 대시보드 v2.0")
st.markdown("<p style='font-size: 1.3rem; color: #666;'>기업명(한글/영문)을 편하게 입력하고 <b>엔터(Enter)</b>를 누르세요!</p>", unsafe_allow_html=True)

# 💡 버그 픽스: st.empty()로 자리만 먼저 만들어두고, 숫자는 맨 나중에 채워넣음!
counter_placeholder = st.empty()
st.divider()

user_input = st.text_input("", placeholder="예: 삼성전자, 램리서치, 테슬라")

if user_input:
    current_time = time.time()
    time_passed = current_time - st.session_state.last_search_time
    
    if st.session_state.search_count >= MAX_SEARCHES:
        st.error("🚫 도배 방지: 현재 접속 창에서는 더 이상 검색할 수 없습니다. 내일 다시 이용해 주세요!")
    elif time_passed < COOLDOWN:
        st.warning(f"⏳ AI가 데이터를 수집 중입니다. {int(COOLDOWN - time_passed)}초 후에 다시 시도해 주세요.")
    else:
        # 💡 정식으로 검색이 시작될 때 카운트를 차감!
        st.session_state.search_count += 1
        st.session_state.last_search_time = current_time
        
        with st.spinner(f"'{user_input}'의 정확한 종목 코드를 찾는 중... 🔍"):
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

            result_text = get_cached_analysis(ticker)
            
            try:
                data = json.loads(result_text)
                
                st.subheader("💼 AI 주식 일타강사의 기업 가치 분석")
                st.success(data.get("financial_analysis", "재무 분석 정보가 없습니다."))
                
                st.subheader("📰 최신 뉴스 모멘텀 (호재/악재)")
                st.info(data.get("news_sentiment", "뉴스 동향 정보가 없습니다."))
                
                st.subheader("🔄 리스크 관리 및 포트폴리오 대안")
                st.warning(data.get("alternatives", "대안 정보가 없습니다."))
                
                # 💡 법적 리스크 차단: '추천 종목' -> 'AI 관심 편입 종목'으로 변경
                st.subheader("💡 AI 연관 관심 종목 (단순 참고용)")
                cols = st.columns(3)
                recs = data.get("recommendations", [])
                
                for i, col in enumerate(cols):
                    if i < len(recs):
                        with col:
                            st.metric(label="관심 종목", value=recs[i].get("ticker", "N/A"))
                            st.write(recs[i].get("reason", "이유 없음"))
                            
            except json.JSONDecodeError:
                st.error("AI가 분석 결과를 올바른 형식으로 주지 않았어. 다시 시도해 줘!")

# 💡 버그 픽스: 모든 로직이 끝난 후, 최종 계산된 남은 횟수를 아까 만들어둔 예약석에 덮어씀!
counter_placeholder.caption(f"🔒 봇 방지 모드 작동 중: 현재 남은 분석 횟수 ({MAX_SEARCHES - st.session_state.search_count} / {MAX_SEARCHES})")

# 💡 강력한 법적 면책 조항 (화면 맨 아래 고정)
st.markdown("""
<div class="disclaimer">
    <b>[법적 고지 및 면책 조항]</b><br>
    본 대시보드에서 제공하는 모든 정보(AI 분석, 재무 데이터, 뉴스 요약 등)는 투자 판단을 위한 단순 참고용이며, 투자 권유 또는 종목 추천을 의미하지 않습니다.<br>
    데이터의 정확성이나 완전성을 보장할 수 없으며, 제공된 정보에 의존하여 발생한 어떠한 형태의 투자 손실에 대해서도 개발자 및 운영자는 법적 책임을 지지 않습니다.<br>
    <b>최종 투자 결정과 그에 따른 모든 책임은 전적으로 투자자 본인에게 있습니다.</b>
</div>
""", unsafe_allow_html=True)
