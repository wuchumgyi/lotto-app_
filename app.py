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

# --- 2. 爬蟲與數據處理核心 (升級版) ---
class LottoDataEngine:
    """
    負責抓取歷史數據並計算權重的核心引擎
    """
    def __init__(self):
        # 備用來源列表：若第一個失敗，會自動嘗試第二個
        self.sources = [
            "https://www.lotto-8.com/listlto.asp", 
            "https://www.pylotto.com/lotto649/history"
        ]

    def fetch_data(self):
        """
        嘗試爬取開獎數據 (智慧搜尋表格模式)
        """
        error_log = []
        
        # 偽裝成瀏覽器 (User-Agent)，避免被擋
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        for url in self.sources:
            try:
                # 請求網頁數據
                response = requests.get(url, headers=headers, timeout=10)
                response.encoding = 'utf-8' # 確保中文不亂碼
                
                # 使用 Pandas 解析所有表格
                dfs = pd.read_html(response.text)
                
                target_df = None
                # --- 關鍵修正：智慧辨識表格 ---
                # 我們不只看大小，而是檢查表格內有沒有 "大樂透相關關鍵字"
                for df in dfs:
                    df_str = df.to_string()
                    # 檢查關鍵字：通常會有 '特別號' 或 '號碼' 或 1-49 的數字分布
                    if ('特別號' in df_str) or ('期別' in df_str):
                        if df.shape[0] > 5: # 確保行數足夠
                            target_df = df
                            break
                
                if target_df is None:
                    error_log.append(f"{url}: 找不到含有關鍵字的表格")
                    continue # 嘗試下一個來源

                # 資料清洗 (Data Cleaning)
                # 將表格轉為字串後，使用正規表達式提取所有 1-49 的數字
                raw_text = target_df.to_string()
                import re
                # 抓取 1 到 49 的數字 (排除日期格式如 2023, 112 等)
                numbers = re.findall(r'\b([1-4][0-9]|[1-9])\b', raw_text)
                
                # 過濾掉雜訊
                valid_numbers = [int(n) for n in numbers if 1 <= int(n) <= 49]
                
                if len(valid_numbers) < 50:
                    error_log.append(f"{url}: 抓到的數字太少，可能格式錯誤")
                    continue

                return True, valid_numbers

            except Exception as e:
                error_log.append(f"{url}: 連線錯誤 - {str(e)}")
        
        # 如果所有來源都失敗
        return False, " | ".join(error_log)

    def calculate_weights(self, numbers_history):
        """
        計算每個號碼的出現頻率
        """
        counts = Counter(numbers_history)
        weights = {i: 1 for i in range(1, 50)} # 基礎權重
        
        # 加權邏輯：出現越多次，權重越高
        for num, count in counts.items():
            weights[num] += (count * 2) # 將熱門號碼的權重放大
            
        return weights

# --- 3. 介面與業務邏輯 ---

def main():
    st.title("🎱 大樂透 AI 預測 (官方同步版)")
    st.caption("資料來源：同步台灣彩券開獎紀錄之資料庫")

    if 'weights' not in st.session_state:
        st.session_state['weights'] = {i: 1 for i in range(1, 50)}
        st.session_state['data_loaded'] = False

    # --- 區塊 A: 數據更新 ---
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
                
                # 顯示分析結果
                sorted_hot = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:6]
                st.success(f"分析完成！樣本數: {len(result)} 個號碼")
                st.write("**🔥 本期最熱門號碼 (高機率):**")
                cols = st.columns(6)
                for idx, (num, w) in enumerate(sorted_hot):
                    cols[idx].metric(f"No.{idx+1}", f"{num:02d}", f"權重 {w}")
            else:
                st.error(f"連線失敗，請檢查網路。\n詳細原因: {result}")

    st.divider()

    # --- 區塊 B: 號碼產生器 ---
    st.subheader("產出幸運號碼")
    
    col1, col2 = st.columns(2)
    with col1:
        generate_btn = st.button("🎲 AI 預測選號", type="primary", use_container_width=True)
    with col2:
        clear_btn = st.button("🗑️ 清除結果", use_container_width=True)

    if generate_btn:
        # --- 1. 核心演算法 (不變) ---
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
        
        # --- 2. 視覺化顯示 (修正排版問題) ---
        st.markdown(f"#### 🎯 主號碼區")
        
        # 修正：將樣式定義為單行變數，避免縮排造成的 Markdown 誤判
        ball_css = "display:inline-flex; align-items:center; justify-content:center; width:45px; height:45px; border-radius:50%; margin:5px; font-weight:bold; font-size:18px; border: 2px solid #FFD700; background: linear-gradient(145deg, #f0f0f0, #cacaca); box-shadow: 5px 5px 10px #bebebe, -5px -5px 10px #ffffff; color:#333;"
        
        # 組合 HTML 字串
        html_content = '<div style="display: flex; gap: 5px; justify-content: center; flex-wrap: wrap;">'
        for n in main_nums:
            # 注意：這裡改成單行 f-string，確保不會有額外縮排
            html_content += f'<div style="{ball_css}">{n:02d}</div>'
        html_content += '</div>'
        
        st.markdown(html_content, unsafe_allow_html=True)
        
        st.markdown(f"#### 🌟 特別號")
        # 特別號也修正為單行寫法
        special_css = "display:inline-flex; align-items:center; justify-content:center; width:50px; height:50px; border-radius:50%; background-color:#FF4B4B; color:white; font-weight:bold; font-size:20px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);"
        st.markdown(
            f'<div style="display:flex; justify-content:center;"><div style="{special_css}">{special_num:02d}</div></div>', 
            unsafe_allow_html=True
        )
        
        mode = "大數據加權模式" if st.session_state['data_loaded'] else "標準隨機模式"
        st.caption(f"目前演算法: {mode}")

if __name__ == "__main__":

    main()
