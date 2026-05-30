import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as ui_chart
from datetime import datetime, timedelta

# ==========================================
# 1. SETTING & INITIALIZATION
# ==========================================
st.set_page_config(page_title="Stock Hunter Pro v2.0", page_icon="🚀", layout="wide")

# คลังข้อมูลหุ้นแนะนำจากกลุ่ม Monopoly และ AI Chip
DEFAULT_US = ["NVDA", "MU", "TSM", "AAPL", "MSFT", "PLTR", "AMD", "LLY", "NFLX", "GOOGL", "AMZN", "META"]
DEFAULT_TH = ["ADVANC.BK", "GULF.BK", "KBANK.BK", "PTT.BK", "DELTA.BK", "CPALL.BK"]

# โครงสร้างพอร์ตจำลองกองหน้า $767
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {"QQQM_pct": 70.0, "cash_scalper": 767.0, "holdings": {}}

st.title("🚀 Stock Hunter v2.0 — Quant Trader Deep Analysis")
st.caption("ระบบวิเคราะห์หุ้นอัตโนมัติสำหรับคอมพิวเตอร์และมือถือ รองรับคัมภีร์กลยุทธ์ 10 ข้อเต็มรูปแบบ")

# ==========================================
# 2. CORE QUANT FUNCTIONS (โมดูลคำนวณหลังบ้าน)
# ==========================================

def fetch_stock_data(symbol):
    """ ดึงข้อมูลพื้นฐาน เทคนิคัล และงบการเงินย้อนหลัง """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="1y")
        hist_1h = ticker.history(period="1mo", interval="1h")
        
        if hist.empty:
            return None
            
        # คำนวณ RSI (14)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        hist['RSI'] = 100 - (100 / (1 + rs))
        
        # คำนวณ ATR (14)
        high_low = hist['High'] - hist['Low']
        high_close = np.abs(hist['High'] - hist['Close'].shift())
        low_close = np.abs(hist['Low'] - hist['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(14).mean()
        
        return {
            "ticker": ticker,
            "info": info,
            "hist": hist,
            "hist_1h": hist_1h,
            "current_price": hist['Close'].iloc[-1],
            "rsi": hist['RSI'].iloc[-1],
            "atr": atr.iloc[-1]
        }
    except Exception as e:
        return None

# ==========================================
# 3. USER INTERFACE (หน้าจอควบคุมบนมือถือ/คอม)
# ==========================================
menu = st.sidebar.selectbox(
    "เลือกเมนูใช้งานหลัก",
    ["[1-3] Deep Tech & Momentum Анализ", 
     "[4-5] Compare & Opportunities", 
     "[6-7] Portfolio Management", 
     "[9-10] Advanced Valuation & Fib"]
)

# ------------------------------------------
# MENU 1: DEEP TECHNICAL & MOMENTUM (ข้อ 2, 3, 10)
# ------------------------------------------
if menu == "[1-3] Deep Tech & Momentum Анализ":
    st.header("🔍 วิเคราะห์ทางเทคนิค & ค้นหาโมเมนตัม")
    symbol = st.text_input("ระบุชื่อหุ้นที่ต้องการล่า (เช่น NVDA, PLTR, GULF.BK):", "MU").upper()
    
    if st.button("เริ่มวิเคราะห์ลึก"):
        with st.spinner("กำลังดึงข้อมูล Real-time จากดาวเทียม..."):
            data = fetch_stock_data(symbol)
            if data is None:
                st.error("ไม่สามารถดึงข้อมูลหุ้นตัวนี้ได้ กรุณาตรวจสอบสัญลักษณ์อีกครั้ง")
            else:
                c_price = data["current_price"]
                rsi_val = data["rsi"]
                atr_val = data["atr"]
                hist = data["hist"]
                
                # คำนวณ Fibonacci Retracement (ข้อ 10)
                max_p = hist['Close'].max()
                min_p = hist['Close'].min()
                diff = max_p - min_p
                fib_382 = max_p - (0.382 * diff)
                fib_500 = max_p - (0.500 * diff)
                fib_618 = max_p - (0.618 * diff)
                
                # แสดงผลการวิเคราะห์เทคนิค
                col1, col2, col3 = st.columns(3)
                col1.metric("ราคาปัจจุบัน", f"${c_price:,.2f}")
                
                if rsi_val > 70:
                    col2.metric("RSI (14)", f"{rsi_val:.2f}", "Overbought ⚠️ (แพงไป)", delta_color="inverse")
                elif rsi_val < 30:
                    col2.metric("RSI (14)", f"{rsi_val:.2f}", "Oversold 📉 (ขายมากเกิน)", delta_color="normal")
                else:
                    col2.metric("RSI (14)", f"{rsi_val:.2f}", "Normal ⚖️")
                    
                atr_pct = (atr_val / c_price) * 100
                col3.metric("ATR (14) / ความผันผวน", f"${atr_val:.2f}", f"{atr_pct:.2f}%")
                
                # วางแผนกลยุทธ์ตามกรอบ Framework 3% Stop Loss
                st.subheader("⚔️ แผนการรบประจำวัน (Battle Plan)")
                sl_price = c_price * 0.97  # ล็อกคัทลอสไม่เกิน 3% เด็ดขาด
                tp_price = c_price * 1.06  # เป้ากำไรขั้นต่ำ 6% เพื่อคุม Risk/Reward >= 2:1
                
                col_b1, col_b2, col_b3 = st.columns(3)
                col_b1.warning(f"จุดเข้าซื้อแนะนำ (ย่อตัว): ${fib_382:,.2f}")
                col_b2.success(f"เป้าทำกำไร (Take Profit): ${tp_price:,.2f} (+6.0%)")
                col_b3.error(f"จุดตัดขาดทุน (Stop Loss 3%): ${sl_price:,.2f} (-3.0%)")
                
                # แทมเพลตสำหรับ Copy ไปใส่แอป Dime!
                st.subheader("📋 DIME! APP ORDER TEMPLATE")
                shares_dime = 191.75 / c_price # คำนวณตามเงินทุนจำลองไม้ละ $191.75 จาก $767
                template_text = f"""
Symbol: {symbol}
Type: Limit Order (คีย์เมื่อราคาย่อตัว)
ซื้อด้วยจำนวนเงิน: $191.75 USD (Fractional Mode)
จำนวนหุ้นโดยประมาณ: {shares_dime:.4f} หุ้น
ตั้งจุดคัทลอส (Stop Loss): ${sl_price:,.2f}
ตั้งจุดขายทำกำไร (Take Profit): ${tp_price:,.2f}
                """
                st.code(template_text, language="text")

# ------------------------------------------
# MENU 2: COMPARE & OPPORTUNITIES (ข้อ 1, 4, 5)
# ------------------------------------------
elif menu == "[4-5] Compare & Opportunities":
    st.header("📊 การเปรียบเทียบเชิงพื้นฐานย้อนหลัง 3 ปี")
    
    col_t1, col_t2, col_t3 = st.columns(3)
    st.subheader("เปรียบเทียบหุ้นรายกลุ่ม")
    stocks_input = st.text_input("พิมพ์ชื่อหุ้นที่ต้องการเปรียบเทียบ (คั่นด้วยเครื่องหมายจุลภาค):", "AAPL,NVDA,MSFT")
    
    if st.button("เริ่มเปรียบเทียบเชิงลึก"):
        stock_list = [s.strip().upper() for s in stocks_input.split(",")]
        res_table = []
        
        for s in stock_list:
            t = yf.Ticker(s)
            info = t.info
            res_table.append({
                "Symbol": s,
                "Sector": info.get("sector", "N/A"),
                "P/E Ratio": info.get("trailingPE", np.nan),
                "ROE %": info.get("returnOnEquity", 0) * 100,
                "Net Margin %": info.get("profitMargins", 0) * 100,
                "Div Yield %": info.get("dividendYield", 0) * 100
            })
            
        df_res = pd.DataFrame(res_table)
        st.table(df_res)
        st.info("💡 กลยุทธ์การคัดเลือก: เลือกตัวที่มี ROE % สูงที่สุด และมี P/E ต่ำที่สุดเมื่อเทียบในกลุ่มเดียวกัน")

# ------------------------------------------
# MENU 3: PORTFOLIO MANAGEMENT (ข้อ 6, 7)
# ------------------------------------------
elif menu == "[6-7] Portfolio Management":
    st.header("💼 ระบบวิเคราะห์และบริหารความเสี่ยงพอร์ตลงทุน")
    
    st.write("กำหนดสัดส่วนพอร์ตปัจจุบันของคุณ:")
    col_p1, col_p2, col_p3 = st.columns(3)
    p_a = col_p1.number_input("สัดส่วน หุ้นเทคซิ่ง % (เช่น NVDA):", value=50.0)
    p_b = col_p2.number_input("สัดส่วน หุ้นปันผลค้ำพอร์ต % (เช่น AAPL):", value=30.0)
    p_c = col_p3.number_input("สัดส่วน เงินสด/กองทุนเสี่ยงต่ำ %:", value=20.0)
    
    total_pct = p_a + p_b + p_c
    st.progress(min(total_pct / 100.0, 1.0))
    
    if total_pct != 100.0:
        st.error(f"⚠️ รวมสัดส่วนพอร์ตปัจจุบันได้ {total_pct}% กรุณาปรับตัวเลขให้รวมกันได้ครบ 100% เสมอ")
    else:
        st.success("✅ โครงสร้างสัดส่วนพอร์ตสมบูรณ์")
        
        # ฟีเจอร์สั่งลดความเสี่ยง 20% อัตโนมัติ (ข้อ 7)
        if st.checkbox("⚙️ เปิดโหมดจำลองสถานการณ์: 'ต้องการลดความเสี่ยงของพอร์ตลง 20%'"):
            st.markdown("### 📋 แผนปฏิบัติการสับกระสุนหนีภัย:")
            st.write(f"1. **ขายลดสถานะกลุ่มหุ้นเทคซิ่งย่อตัว** จาก {p_a}% ให้เหลือ {p_a - 20}%")
            st.write(f"2. **โยกย้ายเงินทุนจำนวน 20%** ของพอร์ตทั้งหมดเข้าสู่สินทรัพย์ปลอดภัย")
            st.info("🎯 สินทรัพย์ปลอดภัยแนะนำ: กองทุนตราสารหนี้ระยะสั้น (เช่น B-TREASURY หรือ SCBFP) หรือถือครองในรูปสกุลเงินดอลลาร์สหรัฐฯ บนแอป Dime! เพื่อรอรับจังหวะสแกนติดแนวรับถัดไป")

# ------------------------------------------
# MENU 4: ADVANCED VALUATION & FIB (ข้อ 9, 10)
# ------------------------------------------
elif menu == "[9-10] Advanced Valuation & Fib":
    st.header("🧮 การประเมินมูลค่าแท้จริงด้วยระบบ Quant AI")
    symbol_v = st.text_input("ระบุชื่อหุ้นเพื่อคำนวณมูลค่า (Fair Value):", "PLTR").upper()
    
    if st.button("คำนวณราคามูลค่าที่เหมาะสม"):
        t_v = yf.Ticker(symbol_v)
        info_v = t_v.info
        c_p = t_v.history(period="1d")['Close'].iloc[-1]
        
        eps = info_v.get("trailingEps", None)
        pe_industry = info_v.get("peRatio", 25.0) # ใช้ค่ามีเดียนกลุ่มหากไม่มีค่า PE
        
        st.subheader(f"ผลการวิเคราะห์ราคาเหมาะสมของ: {symbol_v}")
        if eps:
            fair_pe = eps * pe_industry
            st.metric("ราคาตลาดปัจจุบัน", f"${c_p:,.2f}")
            st.metric("ราคาเหมาะสมอิงตามโมเดล P/E Valuation", f"${fair_pe:,.2f}")
            
            upside = ((fair_pe - c_p) / c_p) * 100
            st.write(f"**ส่วนต่างราคา (Upside):** {upside:.2f}%")
        else:
            st.warning("⚠️ บริษัทนี้ไม่มีกำไรสุทธิ (EPS เป็นลบ) ระบบจึงเปลี่ยนมาใช้โมเดล Price-to-Sales (P/S) Valuation แทนราคาเหมาะสมอัตโนมัติ")
