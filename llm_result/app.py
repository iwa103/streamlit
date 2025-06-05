import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

# --- 日本語フォントを明示的に指定（Streamlit Cloud でも動作）
matplotlib.rcParams['font.family'] = 'IPAexGothic'  # 'Noto Sans CJK JP' も可

st.title("モデル別・モード別スコア（科目ごと + 並び順・色付き）")

# --- CSV読み込み
#df = pd.read_csv("log_summary_by_model_mode_total.csv")
df = pd.read_csv("llm_result/log_summary_by_model_mode_total.csv")
df = df[df["科目"] != "合計"]

# --- モデル表示列
df["モデルID"] = df["モデル"] + " (" + df["パラメータサイズ"].astype(str) + "B)"
df["モデル表示"] = df["モデルID"] + "\n[" + df["モード"] + "]"

# --- モデル並び順：LLMJP → Qwen3 → QwQ、かつサイズ昇順
model_order = []
model_bases = ["llm-jp", "qwen3", "qwq"]
for model_base in model_bases:
    candidates = df[df["モデル"].str.startswith(model_base)]
    sizes = sorted(candidates["パラメータサイズ"].unique())
    for size in sizes:
        matched_models = candidates[candidates["パラメータサイズ"] == size]["モデル"].unique()
        for m in matched_models:
            model_order.append(f"{m} ({size}B)")

# --- 並び順をカテゴリで制御
df["モデルID"] = pd.Categorical(df["モデルID"], categories=model_order, ordered=True)
df = df.sort_values(["モデルID", "モード"])

# --- 色分け関数
def get_color(row):
    if row["モデル"].startswith("llm-jp"):
        return "#4A90E2"  # 青
    elif row["モデル"].startswith("qwen3"):
        return "#E74C3C" if row["モード"] == "no_think" else "#F39C12"  # 赤/オレンジ
    elif row["モデル"].startswith("qwq"):
        return "#27AE60"  # 緑
    else:
        return "gray"

df["color"] = df.apply(get_color, axis=1)

# --- サイドバー：モデル/モード選択
model_id_list = df["モデルID"].cat.categories.tolist()
selected_models = st.sidebar.multiselect("表示するモデル（複数選択可）", model_id_list, default=model_id_list)

mode_list = sorted(df["モード"].unique())
selected_modes = st.sidebar.multiselect("表示するモード", mode_list, default=mode_list)

# --- フィルタ適用
filtered_df = df[(df["モデルID"].isin(selected_models)) & (df["モード"].isin(selected_modes))]

if filtered_df.empty:
    st.warning("選択された条件に一致するデータがありません。")
else:
    for subject in filtered_df["科目"].unique():
        st.subheader(f"【{subject}】")

        sub_df = filtered_df[filtered_df["科目"] == subject]

        fig, ax = plt.subplots(figsize=(10, 4))
        bars = ax.bar(sub_df["モデル表示"], sub_df["スコア"], color=sub_df["color"])

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
