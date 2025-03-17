import pandas as pd
import streamlit as st
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
import os

# CSVファイルからデータを読み込む関数
@st.cache_data
def load_data(file_path, key_column=None):
    df = pd.read_csv(file_path)

    # 必要な列を保持
    columns_to_keep = ['施設・場所名', '住所', '緯度', '経度', 'df2_地震', 'df2_津波', 'df2_高潮', 'df2_洪水', 'df2_土砂']
    if key_column and key_column in df.columns:
        columns_to_keep.append(key_column)
    df_filtered = df[columns_to_keep]
    
    return df_filtered

# 最も近い避難所を検索する関数
@st.cache_data
def find_nearest_shelters(df, lat, lon, filter_column=None, filter_value=None, top_n=5):
    df['距離(km)'] = df.apply(lambda row: geodesic((lat, lon), (row['緯度'], row['経度'])).km, axis=1)
    if filter_column and filter_value is not None:
        filtered_df = df[df[filter_column] == filter_value]
    else:
        filtered_df = df
    return filtered_df.sort_values(by='距離(km)').head(top_n)

# Streamlitアプリのメイン処理
def main():
    st.title("避難所検索アプリ")

    st.markdown(
        """
        <div style="font-size: 20px; line-height: 1.5;">
            <h2 style='margin-bottom: 5px;'>災害対応種別対応版</h2>
            <h3 style='margin-bottom: 10px;'>対象地域: 松山市、宇和島市、愛南町、砥部町、伊方町、鬼北町、久万高原町、松前町</h3>
        
            <strong>使い方:</strong>
            <ol>
                <li>Googleマップで目的地点の緯度経度を取得してください。
                <a href="https://www.google.com/maps/" target="_blank">Googleマップ</a>
                </li>
                <li>取得した緯度経度を入力してください。</li>
                <li>入力後、自動で最も近い避難所が検索され、地図上に表示されます。</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True
    )

    try:
        file_path1 = "mergeFromCity_1.csv"
        file_path2 = "ehime_hinan.csv"
        df1 = load_data(file_path1, key_column="共通ID")
        df2 = load_data(file_path2, key_column="共通ID")
        combined_df = pd.merge(df1, df2, on="共通ID", how="left")

        disaster_options = ["地震", "津波", "高潮", "洪水", "土砂"]
        selected_disaster = st.selectbox("対応災害を選択", disaster_options)

        status_options = {"対応可能（○ = 1）": 1, "一部対応（△ = 2）": 2, "対応不可（✕ = 0）": 0}
        selected_status = st.selectbox("対応状況を選択", list(status_options.keys()))
        filter_value = status_options[selected_status]

        disaster_columns = {"地震": "df2_地震", "津波": "df2_津波", "高潮": "df2_高潮", "洪水": "df2_洪水", "土砂": "df2_土砂"}
        filter_column = disaster_columns.get(selected_disaster)

        user_input = st.text_input("現在位置の緯度・経度を入力してください（例: 33.81167462685436, 132.77887072795122）:")
        if not user_input:
            st.info("緯度・経度を入力してください。")
            return

        user_input = user_input.strip().strip('()').replace(" ", "")
        lat, lon = map(float, user_input.split(","))

        nearest_shelters = find_nearest_shelters(combined_df, lat, lon, filter_column=filter_column, filter_value=filter_value, top_n=5)
        if len(nearest_shelters) == 0:
            st.warning(f"'{selected_disaster}' の '{selected_status}' に一致する避難所が見つかりませんでした。")
            return

        st.subheader("最も近い避難所一覧")
        display_columns = ['施設・場所名', '距離(km)', 'df2_地震', 'df2_津波', 'df2_高潮', 'df2_洪水', 'df2_土砂', '共通ID']
        st.table(nearest_shelters[display_columns])

    except ValueError as ve:
        st.error(f"エラーが発生しました: {ve}")
    except Exception as e:
        st.error(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
