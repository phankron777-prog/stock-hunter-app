import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Volatility Hunter (Radar)", page_icon="⚡", layout="wide")

# คลังหุ้นทั้งหมดที่ต้องการให้เรดาร์คอยเฝ้าจับตา
WATCHLIST = ["NVDA", "MU", "TSM", "AAPL", "MSFT", "PLTR", "AMD", "LLY", "NFLX", "GOOGL", "AMZN", "META", "AVGO", "ASML"]

st.title("⚡ Volatility Hunter — เครื่องมือค้นหาหุ้นซิ่งสายสเปกคูเลเตอร์")
st.caption("ระบบเรดาร์สแกนหาหุ้นที่มีความผันผวน (ATR) สูง และมี Volume กระตุกเข้าผิดปกติ")

atr_threshold = st.sidebar.slider("ตั้งค่ากรองความซิ่งต่ำสุด (ATR %)", 1.5, 8.0, 2.5, step=0.1)
vol_threshold = st.sidebar.slider("โวลลุ่มสไปค์กี่เท่าของค่าเฉลี่ย (Volume X)", 1.0, 5.0, 1.5, step=0.1)

if st.button("📡 เริ่มยิงเรดาร์ค้นหาหุ้นซิ่ง"):
    with st.spinner("กำลังสแกนตลาดหุ้นเพื่อหาตัวแรง..."):
        hot_stocks = []
        
        for symbol in WATCHLIST:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="20d") # ดึงข้อมูล 20 วันล่าสุดมาเทียบค่าเฉลี่ย
                
                if len(hist) < 14:
                    continue
                    
                c_price = hist['Close'].iloc[-1]
                
                # 1. คำนวณ ATR % แบบด่วน
                high_low = hist['High'] - hist['Low']
                high_close = np.abs(hist['High'] - hist['Close'].shift())
                low_close = np.abs(hist['Low'] - hist['Close'].shift())
                true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr_val = true_range.rolling(14).mean().iloc[-1]
                atr_pct = (atr_val / c_price) * 100
                
                # 2. คำนวณ Volume Spike (เทียบโวลลุ่มวันนี้ กับ ค่าเฉลี่ย 15 วันก่อนหน้า)
                current_vol = hist['Volume'].iloc[-1]
                avg_vol = hist['Volume'].iloc[-15:-1].mean()
                vol_ratio = current_vol / (avg_vol + 1e-9)
                
                # เงื่อนไขคัดกรอง "หุ้นซิ่งของจริง"
                if atr_pct >= atr_threshold and vol_ratio >= vol_threshold:
                    hot_stocks.append({
                        "ชื่อหุ้น": symbol,
                        "ราคาปัจจุบัน": f"${c_price:,.2f}",
                        "ความแรง/ผันผวน (ATR %)": f"{atr_pct:.2f}%",
                        "แรงซื้อขายเข้า (กี่เท่า)": f"{vol_ratio:.2f}x 🔥",
                        "สถานะเรดาร์": "🎯 พร้อมลุยซิ่ง"
                    })
            except:
                continue
                
        if len(hot_stocks) > 0:
            df = pd.DataFrame(hot_stocks)
            st.success(f"🎯 เจอหุ้นซิ่งเข้าข่ายทั้งหมด {len(hot_stocks)} ตัว!")
            st.table(df)
            st.balloons()
        else:
            st.warning("📡 เรดาร์เงียบกริบ ตลาดช่วงนี้ยังไม่มีหุ้นตัวไหนซิ่งสไปค์ขึ้นมาตามเงื่อนไขครับ")
