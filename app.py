import streamlit as st
import pandas as pd
import random
import requests
from collections import Counter
from datetime import datetime

# --- 1. 設定頁面組態 (手機友善設定) ---
st.set_page_config(
    page_title="大樂透智慧預測",
    page_icon="🎱",
    layout="centered"  # 手機上集中顯示較佳
)

# --- 2. 爬蟲與數據處理核心 ---
class LottoDataEngine:
    """
    負責抓取歷史數據並計算權重的核心引擎
    """
    def __init__(self):
        # 這裡使用一個常見的大樂透歷史數據公開頁面作為範例來源
        # 備註：若來源網站改版，此 URL 或解析邏輯可能需要更新
        self.source_url = "https://www.lotto-8.com/listlto.asp" 
        self.df = None

    def fetch_data(self):
        """
        嘗試爬取最近的開獎數據
        """
        try:
            # 使用 Pandas 的 read_html 快速解析網頁中的表格
            # 這是最專業且高效的表格爬蟲方式
            html = requests.get(self.source_url, timeout=10).text
            dfs = pd.read_html(html)
            
            # 通常數據會在頁面中較大的那個表格，這裡做簡單的篩選邏輯
            # 針對 lotto-8 網站結構的處理：
            target_df = None
            for df in dfs:
                if df.shape[1] > 5 and df.shape[0] > 10:
                    target_df = df
                    break
            
            if target_df is None:
                return False, "找不到相符的數據表格"

            # 資料清洗 (Data Cleaning)
            # 假設表格包含日期與號碼，我們需要提取出號碼部分
            # 這裡簡化處理：將表格轉為字串後，提取所有 1-49 的數字進行統計
            raw_text = target_df.to_string()
            import re
            numbers = re.findall(r'\b([1-4][0-9]|[1-9])\b', raw_text)
            
            # 過濾掉非獎號的雜訊 (簡單過濾：只留 1-49)
            valid_numbers = [int(n) for n in numbers if 1 <= int(n) <= 49]
            
            return True, valid_numbers

        except Exception as e:
            return False, str(e)

    def calculate_weights(self, numbers_history):
        """
        計算每個號碼的出現頻率，轉化為權重
        """
        counts = Counter(numbers_history)
        
        # 建立 1-49 的權重表，預設權重為 1
        weights = {i: 1 for i in range(1, 50)}
        
        # 根據頻率增加權重 (頻率越高，權重越高)
        for num, count in counts.items():
            weights[num] += count  # 簡單線性加權
            
        return weights

# --- 3. 介面與業務邏輯 ---

def main():
    st.title("🎱 大樂透 AI 預測")
    st.write("結合歷史數據爬蟲與加權演算法")

    # 初始化 Session State (保存狀態用)
    if 'weights' not in st.session_state:
        st.session_state['weights'] = {i: 1 for i in range(1, 50)}
        st.session_state['data_loaded'] = False

    # --- 區塊 A: 數據更新 ---
    with st.expander("📊 歷史數據中心 (點擊展開)"):
        st.info("點擊下方按鈕以爬取最新開獎紀錄來優化演算法")
        if st.button("🚀 抓取最新數據"):
            engine = LottoDataEngine()
            with st.spinner('正在連線至資料庫爬取分析...'):
                success, result = engine.fetch_data()
                
            if success:
                weights = engine.calculate_weights(result)
                st.session_state['weights'] = weights
                st.session_state['data_loaded'] = True
                
                # 顯示最熱門的 5 個號碼
                sorted_hot = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:5]
                st.success(f"數據更新成功！分析樣本數: {len(result)} 個號碼")
                st.write("**🔥 近期最熱門號碼:**")
                st.write(", ".join([f"{num}(權重{w})" for num, w in sorted_hot]))
            else:
                st.error(f"爬取失敗，將使用標準隨機模式。原因: {result}")

    st.divider()

    # --- 區塊 B: 號碼產生器 ---
    st.subheader("產出預測號碼")
    
    col1, col2 = st.columns(2)
    with col1:
        generate_btn = st.button("🎲 生成一組號碼", type="primary", use_container_width=True)
    with col2:
        clear_btn = st.button("🗑️ 清除紀錄", use_container_width=True)

    if generate_btn:
        # 核心演算法：加權隨機抽取
        population = list(st.session_state['weights'].keys())
        w = list(st.session_state['weights'].values())
        
        # 抽取 6 個不重複號碼 + 1 個特別號
        # 技巧：先依權重多抽幾個，再用 set 去重，直到滿 7 個
        selected = set()
        while len(selected) < 7:
            pick = random.choices(population, weights=w, k=1)[0]
            selected.add(pick)
            
        result_list = list(selected)
        main_nums = sorted(result_list[:6])
        special_num = result_list[6]
        
        # 手機版面顯示優化：使用大字體
        st.markdown(f"### 主號碼")
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between;">
                {''.join([f'<span style="background-color:#FFD700; color:black; padding:8px; border-radius:50%; margin:2px; font-weight:bold;">{n:02d}</span>' for n in main_nums])}
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        st.markdown(f"### 特別號")
        st.markdown(
            f'<span style="background-color:#FF4B4B; color:white; padding:8px; border-radius:50%; font-weight:bold;">{special_num:02d}</span>', 
            unsafe_allow_html=True
        )
        
        # 顯示使用的演算法模式
        mode = "大數據加權模式" if st.session_state['data_loaded'] else "標準隨機模式"
        st.caption(f"演算法: {mode}")

if __name__ == "__main__":
    main()