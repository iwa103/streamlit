import pandas as pd
import folium
from geopy.distance import geodesic
import streamlit as st
from streamlit_folium import st_folium
import os

# CSVファイルからデータを読み込み、「要配慮者」の行を除外する関数
@st.cache_data
def load_and_preprocess_data(file_path):
    df = pd.read_csv(file_path)
    df_filtered = df[df['受入対象者'] != '要配慮者']
    columns_to_keep = ['施設・場所名', '住所', '緯度', '経度']
    df_filtered = df_filtered[columns_to_keep]
    return df_filtered

# 地図を生成する関数
def plot_on_map(current_lat, current_lon, nearest_shelters):
    map_center = [current_lat, current_lon]
    m = folium.Map(location=map_center, zoom_start=14, tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", attr="Google Maps")
    folium.Marker(
        location=[current_lat, current_lon],
        popup="現在位置",
        icon=folium.Icon(color="red", icon="home")
    ).add_to(m)

    for _, row in nearest_shelters.iterrows():
        distance_km = row['距離(km)']
        marker_color = "darkgreen" if distance_km < 0.5 else "darkblue" if distance_km < 1.0 else "lightgray"
        popup_content = f"<b>{row['施設・場所名']}</b><br>距離: {distance_km:.1f} km<br>"
        folium.Marker(
            location=[row['緯度'], row['経度']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color=marker_color, icon="info-sign")
        ).add_to(m)

    return m

# 最も近い避難所を検索する関数
@st.cache_data
def find_nearest_shelters(df, lat, lon, top_n=5):
    df['距離(km)'] = df.apply(lambda row: geodesic((lat, lon), (row['緯度'], row['経度'])).km, axis=1)
    return df.sort_values(by='距離(km)').head(top_n)

# 地図をHTMLファイルとして保存する関数
def save_map_as_html(map_object, file_name="map.html"):
    map_object.save(file_name)
    return file_name

# Streamlitアプリのメイン処理
def main():
    # アプリタイトルと説明
    st.title("避難所検索アプリ v1.0")
    st.markdown("""
    **概要:**  
    このアプリは、現在位置を基に最も近い避難所を検索し、地図上に表示します。避難所データはCSVファイルから読み込まれます。

    **使い方:**  
    - 現在位置の緯度と経度をカンマ区切りで入力してください（例: 33.81167462685436, 132.77887072795122）。
    - 入力後、自動で最も近い避難所が検索され、地図上に表示されます。

    **注意:**  
    - 「要配慮者」向けの避難所は除外されています。
    - 緯度・経度の形式が正しくない場合、エラーが発生します。

    **関連リンク:**  
    - [避難所データの出典](https://example.com/shelter-data)  
    - [Streamlit公式サイト](https://streamlit.io/)  
    - [Foliumドキュメント](https://python-visualization.github.io/folium/)
    """)

    # 現在位置の入力
    user_input = st.text_input("現在位置の緯度・経度を入力してください（例: 33.81167462685436, 132.77887072795122）:")
    
    try:
        if not user_input:
            st.info("緯度・経度を入力してください。")
            return
        
        user_input = user_input.strip().strip('()').replace(" ", "")
        lat, lon = map(float, user_input.split(","))

        file_path = "mergeFromCity_1.csv"
        df = load_and_preprocess_data(file_path)

        nearest_shelters = find_nearest_shelters(df, lat, lon, top_n=5)

        st.subheader("最も近い避難所一覧")
        nearest_shelters_display = nearest_shelters[['施設・場所名', '距離(km)']]
        st.table(nearest_shelters_display)

        map_object = plot_on_map(lat, lon, nearest_shelters)
        saved_file = save_map_as_html(map_object, file_name="nearest_shelters_map.html")

        st_folium(map_object, width=700, height=500)

        with open(saved_file, "rb") as f:
            st.download_button(
                label="地図をHTMLファイルとしてダウンロード",
                data=f,
                file_name=os.path.basename(saved_file),
                mime="text/html"
            )

    except ValueError:
        st.error("入力が正しくありません。緯度と経度をカンマ区切りで入力してください（例: 33.81167462685436, 132.77887072795122）。")
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()