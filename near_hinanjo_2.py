import pandas as pd
import streamlit as st
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

# CSVファイルからデータを読み込む関数
@st.cache_data
def load_data(file_path, key_column=None):
    # CSVファイルを読み込む
    df = pd.read_csv(file_path)

    # 必要な列を保持
    columns_to_keep = []
    if '施設・場所名' in df.columns:
        columns_to_keep.append('施設・場所名')
    if '住所' in df.columns:
        columns_to_keep.append('住所')
    if '緯度' in df.columns:
        columns_to_keep.append('緯度')
    if '経度' in df.columns:
        columns_to_keep.append('経度')
    if 'df2_地震' in df.columns:
        columns_to_keep.append('df2_地震')

    if 'df2_津波' in df.columns:
        columns_to_keep.append('df2_津波')
    if 'df2_高潮' in df.columns:
        columns_to_keep.append('df2_高潮')
    if 'df2_洪水' in df.columns:
        columns_to_keep.append('df2_洪水')
    if 'df2_土砂' in df.columns:
        columns_to_keep.append('df2_土砂')

    if key_column and key_column in df.columns:
        columns_to_keep.append(key_column)  # キー列も保持

    # 必要な列のみを残す
    df_filtered = df[columns_to_keep]

    return df_filtered

# 最も近い避難所を検索する関数
@st.cache_data
def find_nearest_shelters(df, lat, lon, top_n=5):
    # 現在地からの距離を計算
    df['距離(km)'] = df.apply(
        lambda row: geodesic((lat, lon), (row['緯度'], row['経度'])).km, axis=1
    )
    # 距離が近い順にソートし、上位N件を取得
    return df.sort_values(by='距離(km)').head(top_n)

# 地図を生成する関数
def plot_on_map(current_lat, current_lon, nearest_shelters):
    # 地図の中心を現在位置に設定
    map_center = [current_lat, current_lon]
    m = folium.Map(location=map_center, zoom_start=14, tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", attr="Google Maps")

    # 現在位置を赤いマーカーで表示
    folium.Marker(
        location=[current_lat, current_lon],
        popup="現在位置",
        icon=folium.Icon(color="red", icon="home")
    ).add_to(m)

    # 避難所をマーカーで表示
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

# Streamlitアプリのメイン処理
def main():
    st.title("避難所検索アプリ")

    try:
        # 現在位置の入力
        user_input = st.text_input("現在位置の緯度・経度を入力してください（例: 33.81167462685436, 132.77887072795122）:")

        # 入力フォーマットの正規化
        if not user_input:
            st.info("緯度・経度を入力してください。")
            return

        user_input = user_input.strip()  # 前後の空白を削除
        user_input = user_input.strip('()')  # カッコを削除
        user_input = user_input.replace(" ", "")  # スペースを削除

        # 緯度と経度を分割して数値に変換
        lat, lon = map(float, user_input.split(","))

        # 2つのCSVファイルを読み込み
        file_path1 = "mergeFromCity_1.csv"  # DF1
        file_path2 = "matsu_hinan.csv"     # DF2

        # データを前処理（それぞれのキー列を指定）
        df1 = load_data(file_path1, key_column="共通ID")
        df2 = load_data(file_path2, key_column="共通ID")

        # キー列の名前を統一して結合
        combined_df = pd.merge(df1, df2, on="共通ID", how="left")

        # フィルタリング条件の選択 追加部分
        filter_option = st.selectbox("地震情報を選択", ["全て", "〇", "△", "✕"])
        filter_value = None
        if filter_option != "全て":
            filter_value = filter_option

        # 最も近い避難所を検索
        nearest_shelters = find_nearest_shelters(
            combined_df,
            lat,
            lon,
            filter_column="df2_地震",
            filter_value=filter_value,
            top_n=5
        )

        # 結合結果を確認
        #st.subheader("結合されたデータ (DF3)")
        #st.write(combined_df)

        # 最も近い避難所を検索（上位5つ）
        nearest_shelters = find_nearest_shelters(combined_df, lat, lon, top_n=5)

        # 結果をテーブルで表示
        st.subheader("最も近い避難所一覧")
        display_columns = ['施設・場所名', '距離(km)', 'df2_地震','df2_津波','df2_高潮','df2_洪水','df2_土砂','共通ID']
        nearest_shelters_display = nearest_shelters[display_columns]
        st.table(nearest_shelters_display)

        # 地図を生成
        map_object = plot_on_map(lat, lon, nearest_shelters)

        # 地図をStreamlitで表示
        st.subheader("地図表示")
        st_folium(map_object, width=700, height=500)

    except ValueError as ve:
        st.error(f"エラーが発生しました: {ve}")
    except Exception as e:
        st.error(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    main()