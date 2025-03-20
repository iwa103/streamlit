import pandas as pd
import streamlit as st
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
import os

@st.cache_data
def load_data(file_path, key_column=None):
    df = pd.read_csv(file_path)

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
        columns_to_keep.append(key_column)

    df_filtered = df[columns_to_keep]
    return df_filtered

@st.cache_data
def find_nearest_shelters(df, lat, lon, filter_column=None, filter_value=None, top_n=5):
    df['距離(km)'] = df.apply(
        lambda row: geodesic((lat, lon), (row['緯度'], row['経度'])).km, axis=1
    )

    if filter_column and filter_value:
        filtered_df = df[df[filter_column] == filter_value]
    else:
        filtered_df = df

    return filtered_df.sort_values(by='距離(km)').head(top_n)

def plot_on_map(current_lat, current_lon, nearest_shelters):
    m = folium.Map(
        location=[current_lat, current_lon],
        zoom_start=14,
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Google Maps"
    )

    folium.Marker(
        location=[current_lat, current_lon],
        popup=folium.Popup("<b>現在位置</b>", max_width=300),
        icon=folium.Icon(color="red", icon="home")
    ).add_to(m)

    for _, row in nearest_shelters.iterrows():
        distance_km = row['距離(km)']
        if distance_km < 0.5:
            marker_color = "darkgreen"
        elif distance_km < 1.0:
            marker_color = "darkblue"
        else:
            marker_color = "lightgray"

        popup_content = f"<b>{row['施設・場所名']}</b><br>距離: {distance_km:.1f} km<br>"
        folium.Marker(
            location=[row['緯度'], row['経度']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color=marker_color, icon="info-sign")
        ).add_to(m)

    return m

def save_map_as_html(map_object, file_name="map.html"):
    map_object.save(file_name)
    return file_name

def main():
    # -------------------------
    # フォントサイズを変数管理
    # -------------------------
    TITLE_FONT_SIZE = "26px"       # メインタイトル
    SUBTITLE_FONT_SIZE = "20px"    # サブ見出し
    DESC_FONT_SIZE = "16px"        # 説明文
    SUBTEXT_FONT_SIZE = "12px"     # さらに小さい補助テキスト

    # メインタイトル
    st.markdown(f"""
    <h1 style="font-size: {TITLE_FONT_SIZE}; font-weight: normal; margin-bottom: 10px;">
        避難所検索アプリ（災害別絞込み）
    </h1>
    """, unsafe_allow_html=True)

    # アプリの説明
    st.markdown(f"""
    <div style="font-size: {DESC_FONT_SIZE}; line-height: 1.5;">
        <!-- サブ見出しを h3 で定義し、font-size を明示的に指定 -->
        <h3 style="font-size: {SUBTITLE_FONT_SIZE}; margin-bottom: 10px;">
            対象地域: 愛媛県＋隣接自治体
        </h3>
        <p style="margin-bottom: 5px;">
            <strong>隣接自治体名:</strong><br>
            <span style="font-size: {SUBTEXT_FONT_SIZE};">
                徳島県: 三好市、香川県: 観音寺市<br>
                高知県: 宿毛市、四万十市、四万十町、本山町、土佐町、いの町、仁淀川町、津野町、梼原町
            </span>
        </p>
        <p><strong>使い方:</strong></p>
        <ol style="padding-left: 20px;">
            <li>
                Googleマップで目的地点の緯度経度を取得してください。
                <a href="https://www.google.com/maps/" target="_blank">Googleマップを開く</a>
            </li>
            <li>取得した緯度経度を入力してください。</li>
            <li>入力後、自動で最も近い避難所が検索され、地図上に表示されます。</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        file_path1 = "mergeFromCity_1.csv"
        file_path2 = "ehime_hinan.csv"

        df1 = load_data(file_path1, key_column="共通ID")
        df2 = load_data(file_path2, key_column="共通ID")

        combined_df = pd.merge(df1, df2, on="共通ID", how="left")

        disaster_options = ["地震", "津波", "高潮", "洪水", "土砂"]
        selected_disaster = st.selectbox("対応災害を選択", disaster_options)

        status_options = ["O", "A", "X"]
        selected_status = st.selectbox("対応状況を選択", status_options)

        disaster_columns = {
            "地震": "df2_地震",
            "津波": "df2_津波",
            "高潮": "df2_高潮",
            "洪水": "df2_洪水",
            "土砂": "df2_土砂"
        }
        filter_column = disaster_columns.get(selected_disaster)
        filter_value = selected_status

        user_input = st.text_input("現在位置の緯度・経度を入力してください（例: 33.81167462685436, 132.77887072795122）:")

        if not user_input:
            st.info("緯度・経度を入力してください。")
            return

        user_input = user_input.strip().strip('()').replace(" ", "")
        lat, lon = map(float, user_input.split(","))

        nearest_shelters = find_nearest_shelters(
            combined_df,
            lat,
            lon,
            filter_column=filter_column,
            filter_value=filter_value,
            top_n=5
        )

        if len(nearest_shelters) == 0:
            st.warning(f"'{selected_disaster}' の '{selected_status}' に一致する避難所が見つかりませんでした。")
            return

        st.subheader("最も近い避難所一覧")
        display_columns = [
            '施設・場所名', '距離(km)', 'df2_地震', 'df2_津波',
            'df2_高潮', 'df2_洪水', 'df2_土砂', '共通ID'
        ]
        st.table(nearest_shelters[display_columns])

        map_object = plot_on_map(lat, lon, nearest_shelters)
        saved_file = save_map_as_html(map_object, file_name="nearest_shelters_map.html")

        st.subheader("地図表示")
        st_folium(map_object, width=700, height=500)

        with open(saved_file, "rb") as f:
            st.download_button(
                label="地図をHTMLファイルとしてダウンロード",
                data=f,
                file_name=os.path.basename(saved_file),
                mime="text/html"
            )

    except ValueError as ve:
        st.error(f"エラーが発生しました: {ve}")
    except Exception as e:
        st.error(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
