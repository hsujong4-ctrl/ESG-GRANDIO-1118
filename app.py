import os
import tempfile

import pandas as pd
import requests
import gradio as gr
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
LOCAL_CSV = os.path.join(BASE_DIR, "data01.csv")
DATA_URL = "https://data.tainan.gov.tw/File/ResourceCsvDownload/6c16b2c8-92b6-49d9-98b5-02966462172c"
ALL = "全部欄位"


def fetch_data(force: bool = False) -> pd.DataFrame:
    """下載並讀取 CSV，流程同原程式的 dropna()"""
    if force or not os.path.exists(LOCAL_CSV):
        try:
            r = requests.get(DATA_URL, timeout=30)
        except requests.exceptions.SSLError:
            r = requests.get(DATA_URL, timeout=30, verify=False)  # 僅 SSL 異常時退回
        r.raise_for_status()
        with open(LOCAL_CSV, "wb") as f:
            f.write(r.content)
    df = pd.read_csv(LOCAL_CSV, encoding="utf-8-sig")
    return df.dropna().reset_index(drop=True)


try:
    DF = fetch_data()
except Exception as e:
    print(f"資料載入失敗：{e}")
    DF = pd.DataFrame()

COLUMNS = list(DF.columns)


def apply_filter(column, keyword):
    df = DF
    kw = (keyword or "").strip()
    if not kw:
        return df
    if column in (None, ALL):
        mask = df.astype(str).apply(
            lambda s: s.str.contains(kw, case=False, regex=False)
        ).any(axis=1)
    else:
        mask = df[column].astype(str).str.contains(kw, case=False, regex=False)
    return df[mask]


def update_view(column, keyword, max_rows):
    df = apply_filter(column, keyword)
    info = f"📊 總筆數 **{len(DF):,}**　｜　符合條件 **{len(df):,}** 筆"
    return df.head(int(max_rows)), info


def make_chart(group_col, column, keyword, top_n):
    df = apply_filter(column, keyword)
    if not group_col or group_col not in df.columns or df.empty:
        return gr.update(value=None)
    counts = df[group_col].astype(str).value_counts().head(int(top_n)).reset_index()
    counts.columns = [group_col, "數量"]
    return gr.update(value=counts, x=group_col, y="數量", title=f"{group_col} 統計")


def export_csv(column, keyword):
    df = apply_filter(column, keyword)
    path = os.path.join(tempfile.gettempdir(), "tainan_export.csv")
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def reload_data():
    global DF, COLUMNS
    DF = fetch_data(force=True)
    COLUMNS = list(DF.columns)
    return (
        gr.update(choices=[ALL] + COLUMNS, value=ALL),
        gr.update(choices=COLUMNS, value=COLUMNS[0] if COLUMNS else None),
        f"✅ 已重新下載，共 {len(DF):,} 筆",
    )


PWA_HEAD = """
<link rel="manifest" href="/static/manifest.webmanifest">
<meta name="theme-color" content="#2563eb">
<link rel="apple-touch-icon" href="/static/icons/apple-touch-icon.png">
<script>
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js", { scope: "/" });
  }
</script>
"""

CSS = ".gradio-container { max-width: 1200px !important; }"


def build_ui() -> gr.Blocks:
    with gr.Blocks(
        title="台南市開放資料瀏覽器",
        css=CSS,
        theme=gr.themes.Soft(),
        head=PWA_HEAD,
    ) as demo:
        gr.Markdown(
            "# 🏙️ 台南市政府開放資料瀏覽器\n"
            "資料來源：[data.tainan.gov.tw](https://data.tainan.gov.tw)"
        )
        with gr.Row():
            with gr.Column(scale=1, min_width=260):
                col_dd = gr.Dropdown([ALL] + COLUMNS, value=ALL, label="搜尋欄位")
                keyword = gr.Textbox(label="關鍵字", placeholder="輸入關鍵字後按 Enter 或查詢")
                max_rows = gr.Slider(10, 500, value=50, step=10, label="顯示筆數")
                search_btn = gr.Button("🔍 查詢", variant="primary")

                with gr.Accordion("📈 統計圖表", open=False):
                    group_dd = gr.Dropdown(
                        COLUMNS, value=COLUMNS[0] if COLUMNS else None, label="分組欄位"
                    )
                    top_n = gr.Slider(5, 50, value=15, step=1, label="前幾名")
                    chart_btn = gr.Button("產生圖表")
                    chart = gr.BarPlot(label="統計結果")

                with gr.Accordion("⬇️ 匯出", open=False):
                    export_btn = gr.Button("匯出篩選結果 CSV")
                    file_out = gr.File(label="下載檔案")

                refresh_btn = gr.Button("🔄 重新下載資料")

            with gr.Column(scale=3):
                info = gr.Markdown()
                table = gr.Dataframe(value=DF.head(50), interactive=False, wrap=True)

        search_btn.click(update_view, [col_dd, keyword, max_rows], [table, info])
        keyword.submit(update_view, [col_dd, keyword, max_rows], [table, info])
        chart_btn.click(make_chart, [group_dd, col_dd, keyword, top_n], [chart])
        export_btn.click(export_csv, [col_dd, keyword], [file_out])
        refresh_btn.click(reload_data, None, [col_dd, group_dd, info])
        demo.load(update_view, [col_dd, keyword, max_rows], [table, info])
    return demo


DEMO = build_ui()

# ---------- FastAPI + PWA 路由 ----------
api = FastAPI(title="台南市開放資料瀏覽器")
api.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@api.get("/sw.js")
def service_worker():
    # Service Worker 必須從根路徑提供，才能控制整個網站
    return FileResponse(
        os.path.join(STATIC_DIR, "sw.js"),
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )


@api.get("/offline.html")
def offline_page():
    return FileResponse(os.path.join(STATIC_DIR, "offline.html"), media_type="text/html")


@api.get("/healthz")
def healthz():
    return JSONResponse({"status": "ok", "rows": len(DF)})


app = gr.mount_gradio_app(api, DEMO, path="/")

if __name__ == "__main__":
    if os.environ.get("PORT"):  # Render 會提供 PORT
        uvicorn.run(app, host="0.0.0.0", port=int(os.environ["PORT"]))
    else:  # 本機或 Colab：產生公開連結
        DEMO.queue().launch(share=True)
