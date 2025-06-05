import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib

st.title("モデル別・モード別スコア（科目ごと表示 + フィルター付き）")

# CSV読み込み
df = pd.read_csv("log_summary_by_model_mode_total.csv")
df = df[df["科目"] != "合計"]

# モデル表示列
df["モデルID"] = df["モデル"] + " (" + df["パラメータサイズ"].astype(str) + "B)"
df["モデル表示"] = df["モデルID"] + "\n[" + df["モード"] + "]"

# サイドバー：モデル選択
model_id_list = sorted(df["モデルID"].unique())
selected_models = st.sidebar.multiselect("表示するモデル（複数選択可）", model_id_list, default=model_id_list)

# サイドバー：モード選択
mode_list = sorted(df["モード"].unique())
selected_modes = st.sidebar.multiselect("表示するモード", mode_list, default=mode_list)

# フィルター
filtered_df = df[(df["モデルID"].isin(selected_models)) & (df["モード"].isin(selected_modes))]

if filtered_df.empty:
    st.warning("選択された条件に一致するデータがありません。")
else:
    subjects = filtered_df["科目"].unique()

    for subject in subjects:
        st.subheader(f"【{subject}】")

        sub_df = filtered_df[filtered_df["科目"] == subject]

        fig, ax = plt.subplots(figsize=(10, 4))
        bars = ax.bar(sub_df["モデル表示"], sub_df["スコア"], color="skyblue")
        
        ax.set_ylabel("スコア")
        ax.set_xlabel("モデル（モード）")
        ax.set_title(f"{subject}：モデル別スコア")
        ax.set_ylim(0, 105)
        ax.set_xticks(range(len(sub_df)))
        ax.set_xticklabels(sub_df["モデル表示"], rotation=45, ha="right")
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 1, f"{height:.1f}", ha='center', va='bottom')

        st.pyplot(fig)
