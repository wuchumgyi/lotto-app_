import streamlit as st
import pandas as pd
import random
import requests
from collections import Counter

# --- 1. 設定頁面組態 ---
st.set_page_config(
    page_title="大樂透智慧預測 (Pro)",
    page_icon="🎱",
    layout="centered"
)

# --- 2. 爬蟲與數據處理核心 ---
class LottoDataEngine:
    def __init__(self):
        # 備用來源列表
        self.sources = [
            "https://www.lotto-8.com/listlto.asp", 
            "https://www.pylotto.com/lotto649/history"
        ]

    def fetch_data(self):
        error_log = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        for url in self.sources:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.encoding = 'utf-8'
                
                # 使用 Pandas 解析表格
                dfs = pd.read_html(response.text)
                target_df = None
                
                for df in dfs:
                    df_str = df.to_string()
                    if ('特別號' in df_str) or ('期別' in df_str):
                        if df.shape[0] > 5:
                            target_df = df
                            break
                
                if target_df is None:
                    error_log.append(f"{url}: 未找到數據表格")
                    continue

                raw_text = target_df.to_string()
                import re
                numbers = re.findall(r'\b([1-4][0-9]|[1-9])\b', raw_text)
                valid_numbers = [int(n) for n in numbers if 1 <= int(n) <= 49]
                
                if len(valid_numbers) < 50:
                    continue

                return True, valid_numbers

            except Exception as e:
                error_log.append(f"{url}: {str(e)}")
        
        return False, " | ".join(error_log)

    def calculate_weights(self, numbers_history):
        counts = Counter(numbers_history)
        weights = {i: 1 for i in range(1, 50)}
        for num, count in counts.items():
            weights[num] += (count * 2)
        return weights

# --- 3. 主程式邏輯 ---
def main():
    st.title("🎱 大樂透 AI 預測 (官方同步版)")
    st.caption("資料來源：同步台灣彩券開獎紀錄之資料庫")

    if 'weights' not in st.session_state:
        st.session_state['weights'] = {i: 1 for i in range(1, 50)}
        st.session_state['data_loaded'] = False

    # --- 數據更新區 ---
    with st.expander("📊 歷史數據中心 (Status: " + ("已連線" if st.session_state['data_loaded'] else "未連線") + ")", expanded=True):
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.info("💡 系統將自動連線至歷史資料庫進行大數據分析。")
        with col_b:
            update_btn = st.button("🚀 更新數據庫", use_container_width=True)
            
        if update_btn:
            engine = LottoDataEngine()
            with st.spinner('正在分析近 100 期開獎走勢...'):
                success, result = engine.fetch_data()
                
            if success:
                weights = engine.calculate_weights(result)
                st.session_state['weights'] = weights
                st.session_state['data_loaded'] = True
                
                sorted_hot = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:6]
                st.success(f"分析完成！樣本數: {len(result)} 個號碼")
                st.write("**🔥 本期最熱門號碼:**")
                cols = st.columns(6)
                for idx, (num, w) in enumerate(sorted_hot):
                    cols[idx].metric(f"No.{idx+1}", f"{num:02d}", f"權重 {w}")
            else:
                st.error(f"連線失敗: {result}")

    st.divider()

    # --- 號碼生成區 ---
    st.subheader("產出幸運號碼")
    
    col1, col2 = st.columns(2)
    with col1:
        generate_btn = st.button("🎲 AI 預測選號", type="primary", use_container_width=True)
    with col2:
        clear_btn = st.button("🗑️ 清除結果", use_container_width=True)

    if generate_btn:
        # 1. 演算法選號
        population = list(st.session_state['weights'].keys())
        w = list(st.session_state['weights'].values())
        
        selected = set()
        retry = 0
        while len(selected) < 7 and retry < 100:
            pick = random.choices(population, weights=w, k=1)[0]
            selected.add(pick)
            retry += 1
            
        result_list = list(selected)
        while len(result_list) < 7:
             missing = [x for x in range(1,50) if x not in result_list]
             result_list.append(random.choice(missing))

        main_nums = sorted(result_list[:6])
        special_num = result_list[6]
        
        # 2. 視覺化顯示 (已修復 HTML 排版問題)
        st.markdown(f"#### 🎯 主號碼區")
        
        # 定義 CSS 樣式 (單行寫法避免錯誤)
        ball_css = "display:inline-flex; align-items:center; justify-content:center; width:45px; height:45px; border-radius:50%; margin:5px; font-weight:bold; font-size:18px; border: 2px solid #FFD700; background: linear-gradient(145deg, #f0f0f0, #cacaca); box-shadow: 5px 5px 10px #bebebe, -5px -5px 10px #ffffff; color:#333;"
        
        html_content = '<div style="display: flex; gap: 5px; justify-content: center; flex-wrap: wrap;">'
        for n in main_nums:
            html_content += f'<div style="{ball_css}">{n:02d}</div>'
        html_content += '</div>'
        
        st.markdown(html_content, unsafe_allow_html=True)
        
        st.markdown(f"#### 🌟 特別號")
        special_css = "display:inline-flex; align-items:center; justify-content:center; width:50px; height:50px; border-radius:50%; background-color:#FF4B4B; color:white; font-weight:bold; font-size:20px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);"
        st.markdown(
            f'<div style="display:flex; justify-content:center;"><div style="{special_css}">{special_num:02d}</div></div>', 
            unsafe_allow_html=True
        )
        
        mode = "大數據加權模式" if st.session_state['data_loaded'] else "標準隨機模式"
        st.caption(f"目前演算法: {mode}")

if __name__ == "__main__":
    main()
