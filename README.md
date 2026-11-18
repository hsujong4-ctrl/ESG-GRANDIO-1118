# 台南市政府開放資料瀏覽器（Gradio + FastAPI + PWA）

```
.
├── app.py                  # 主程式（Gradio 介面 + FastAPI + PWA 路由）
├── requirements.txt
├── render.yaml             # Render Blueprint（選用）
├── .python-version
├── static/
│   ├── manifest.webmanifest
│   ├── sw.js               # Service Worker
│   ├── offline.html        # 離線頁
│   └── icons/              # 192 / 512 / maskable / apple-touch / svg
└── tools/make_icons.py     # 重新產生圖示（選用，需 pip install pillow numpy）
```

## 本機執行
```bash
pip install -r requirements.txt
python app.py          # 本機：會產生 gradio.live 公開連結
PORT=8000 python app.py  # 指定埠號並啟動 FastAPI 服務
```

## Google Colab
```python
!pip install -q "gradio>=5" fastapi uvicorn
```
貼上 `app.py` 後執行即可（Colab 會以 `share=True` 啟動）。

## 部署到 Render
1. 將專案推到 GitHub
2. Render → **New +** → **Blueprint**，選擇此倉庫，Render 會讀取 `render.yaml`
   （或手動建立 Web Service：Build `pip install -r requirements.txt`，Start `uvicorn app:app --host 0.0.0.0 --port $PORT`）
3. 部署完成後以手機開啟網址，即可「加入主畫面」

## PWA 注意事項
- Service Worker 由 `/sw.js` 提供，範圍為整個網站。
- 修改 `static/` 內容後，請把 `static/sw.js` 的 `CACHE` 版本號改掉，使用者才會取得新版本。
- PWA 需要 HTTPS；Render 預設提供。

## 資料來源
臺南市政府資料開放平台：https://data.tainan.gov.tw
