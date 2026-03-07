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
    .disclaimer { font-size: 0.8rem; color: #888; text-align: center; margin-top: 50px; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 나만의 실전 AI 퀀트 분석 대시보드 v3.0")
st.markdown("<p style='font-size: 1.3rem; color: #666;'>기업명(한글/영문)을 편하게 입력하고 <b>엔터(Enter)</b>를 누르세요!</p>", unsafe_allow_html=True)

# 잔여 횟수 표시용 예약석 (버그 해결)
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
        st.session_state.search_count += 1
        st.session_state.last_search_time = current_time
        
        with st.spinner(f"'{user_input}'의 정확한 종목 코드를 찾는 중... 🔍"):
            ticker = get_cached_ticker(user_input)
            st.info(f"💡 인식된 종목 코드: **{ticker}**")
            
        with st.spinner(f"[{ticker}] 기업 펀더멘털과 최신 뉴스를 융합 분석 중입니다... 🧠"):
            try:
                stock = yf.Ticker(ticker)
                
                # 배당률 및 52주 변동폭 상단 표시
                info = stock.info
                div_yield = info.get('dividendYield', 0)
                div_yield_str = f"{round(div_yield * 100, 2)}%" if div_yield else "배당 없음"
                high_52 = info.get('fiftyTwoWeekHigh', 'N/A')
                low_52 = info.get('fiftyTwoWeekLow', 'N/A')
                
                st.markdown(f"**🏷️ 52주 변동폭:** {low_52} ~ {high_52} | **💰 예상 배당수익률:** {div_yield_str}")
                
                # 3개월 주가 및 20일 이동평균선(MA20) 차트
                hist = stock.history(period="3mo")
                if not hist.empty:
                    hist['MA20 (20일선)'] = hist['Close'].rolling(window=20).mean()
                    hist = hist.rename(columns={'Close': '종가'})
                    
                    st.subheader(f"📈 {ticker} 최근 3개월 주가 및 추세선")
                    st.line_chart(hist[['종가', 'MA20 (20일선)']]) 
            except Exception as e:
                st.error(f"차트 로딩 에러: {e}")

            result_text = get_cached_analysis(ticker)
            
            try:
                data = json.loads(result_text)
                
                st.subheader("💼 AI 주식 일타강사의 기업 가치 분석")
                st.success(data.get("financial_analysis", "재무 분석 정보가 없습니다."))
                
                st.subheader("⚔️ 라이벌 기업과의 경쟁력 비교")
                st.info(data.get("competitor_analysis", "경쟁사 분석 정보가 없습니다."))
                
                st.subheader("📰 최신 뉴스 모멘텀 (호재/악재)")
                st.write(data.get("news_sentiment", "뉴스 동향 정보가 없습니다."))
                
                st.subheader("🔄 리스크 관리 및 포트폴리오 대안")
                st.warning(data.get("alternatives", "대안 정보가 없습니다."))
                
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

# 로직 종료 후 남은 횟수 업데이트
counter_placeholder.caption(f"🔒 봇 방지 모드 작동 중: 현재 남은 분석 횟수 ({MAX_SEARCHES - st.session_state.search_count} / {MAX_SEARCHES})")
st.divider()

# 👇👇👇 [NEW] 수익 창출 (Monetization) 섹션 👇👇👇
st.subheader("☕ AI 퀀트 분석기가 도움이 되셨나요?")
st.write("여러분의 작은 후원과 관심이 AI 서버를 끄지 않고 유지하는 데 큰 힘이 됩니다! 🙌")

col1, col2 = st.columns(2)

with col1:
    # 1. 카카오페이 익명 송금 버튼 (카카오 옐로우)
    # 👉 주의: href 안의 링크를 방금 카카오톡에서 복사한 '송금 링크'로 반드시 변경해!
    st.markdown("""
    <a href="https://u2x6hofm6exebnxb8ex4ho.streamlit.app/" target="_blank" style="text-decoration: none;">
        <div style="background-color: #FEE500; color: #000000; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 1.05rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            💬 카카오페이로 AI 커피 한 잔 사주기
        </div>
    </a>
    """, unsafe_allow_html=True)

with col2:
    # 2. 증권사 제휴(어필리에이트) 링크 버튼 (빨간색)
    st.markdown("""
    <a href="https://여기에_증권사_추천인_링크_입력" target="_blank" style="text-decoration: none;">
        <div style="background-color: #ff3366; color: white; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 1.05rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            📈 수수료 혜택받고 증권사 계좌 개설하기
        </div>
    </a>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True) # 면책 조항과의 간격을 위한 여백
# 👆👆👆 여기까지 👆👆👆
st.markdown("""
<div class="disclaimer">
    <b>[법적 고지 및 면책 조항]</b><br>
    본 대시보드에서 제공하는 모든 정보(AI 분석, 재무 데이터, 뉴스 요약 등)는 투자 판단을 위한 단순 참고용이며, 투자 권유 또는 종목 추천을 의미하지 않습니다.<br>
    데이터의 정확성이나 완전성을 보장할 수 없으며, 제공된 정보에 의존하여 발생한 어떠한 형태의 투자 손실에 대해서도 개발자 및 운영자는 법적 책임을 지지 않습니다.<br>
    <b>최종 투자 결정과 그에 따른 모든 책임은 전적으로 투자자 본인에게 있습니다.</b>
</div>
""", unsafe_allow_html=True)



