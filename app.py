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
