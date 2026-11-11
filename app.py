#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高科大「教授狀態與課表查詢系統」— Python 後端
=================================================
僅使用 Python 標準函式庫（http.server + sqlite3），不需要安裝任何套件。

啟動方式：
    1) 安裝 Python 3（https://www.python.org/downloads/ 或 Microsoft Store）
    2) 在本資料夾開啟終端機，執行：
           python app.py
    3) 瀏覽器開啟 http://localhost:8000

頁面：
    學生端  http://localhost:8000/
    教授端  http://localhost:8000/professor
"""

import json  # 處理 JSON 編碼與解碼
import os  # 操作檔案路徑與檔案系統
import sqlite3  # 使用內建 SQLite 資料庫
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # 建立多執行緒 HTTP 伺服器
from urllib.parse import urlsplit  # 解析 HTTP 請求路徑

# ----------------------------------------------------------------------
# 基本設定
# ----------------------------------------------------------------------
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))  # 取得此程式所在資料夾
STATIC_DIR = os.path.join(BASE_DIR, "static")  # 設定前端靜態檔案資料夾
DB_PATH    = os.path.join(BASE_DIR, "professors.db")  # 設定 SQLite 資料庫檔案位置
HOST       = "0.0.0.0"  # 監聽所有網路介面
PORT       = 8000  # 設定 HTTP 伺服器連接埠

DEFAULT_PASSWORD = "0000"   # 教授首次登入的預設密碼

# 教授名單（資料來源：https://mee.nkust.edu.tw/p/412-1064-10047.php?Lang=zh-tw ）
ROSTER = [  # 定義系上教師初始資料
    {"id": "shchang",    "name": "張順雄", "title": "教授",             "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立中山大學 電機工程研究所 博士",   "ext": "23363", "email": "shchang@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["水下聲學訊號處理", "數位訊號處理", "通訊系統工程", "列陣信號處理"]},  # 設定研究專長
    {"id": "jinnwu",     "name": "吳晉昌", "title": "教授",             "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立成功大學 電機工程系 博士",       "ext": "23370", "email": "jinnwu@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["數位電路設計", "微處理機應用", "電能轉換電路設計", "綠色能源系統"]},  # 設定研究專長
    {"id": "minyen",     "name": "葉旻彥", "title": "教授",             "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立中山大學 電機工程研究所 博士",   "ext": "23354", "email": "minyen@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["半導體磊晶成長技術", "半導體光電元件", "CZTS太陽能電池", "微控器應用"]},  # 設定研究專長
    {"id": "chchyang",   "name": "楊誌欽", "title": "教授",             "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立中山大學 電機工程系 博士",       "ext": "23355", "email": "chchyang@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["奈米生醫感測元件", "呼吸感測元件", "半導體元件與量測", "共振穿透元件"]},  # 設定研究專長
    {"id": "cy-lee",     "name": "李重義", "title": "教授",             "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立清華大學 電機工程研究所 博士",   "ext": "23388", "email": "cy-lee@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["發光二極體", "III-V族磊晶技術", "光電半導體元件", "半導體製程技術"]},  # 設定研究專長
    {"id": "cdyang",     "name": "楊奇達", "title": "教授",             "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立清華大學 電子工程研究所 博士",   "ext": "23343", "email": "cdyang@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["光電半導體元件物理與製程", "光電子學", "光纖通訊系統",  # 列出研究專長項目
                   "半導體材料性質量測與分析", "光電半導體元件應用電路設計與製作"]},  # 完成研究專長清單
    {"id": "jennyulin",  "name": "林振宇", "title": "教授",             "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "美國喬治亞理工學院 電機與電腦工程系 博士", "ext": "23346", "email": "jennyulin@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["混合訊號積體電路設計", "電源管理積體電路設計", "IC科技市場行銷"]},  # 設定研究專長
    {"id": "ckwang",     "name": "王俊凱", "title": "教授",             "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立成功大學 微電子工程研究所 博士", "ext": "23348", "email": "ckwang@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["半導體元件物理", "半導體製程技術", "半導體光電元件",  # 列出研究專長項目
                   "III-V族化合物半導體磊晶技術", "發光二極體技術", "光檢測器"]},  # 完成研究專長清單
    {"id": "kkchong",    "name": "莊國強", "title": "副教授",           "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立成功大學 電機工程研究所 博士",   "ext": "23358", "email": "kkchong@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["半導體元件模擬", "射頻電子電路", "微機電元件設計"]},  # 設定研究專長
    {"id": "sfchao",     "name": "趙世峯", "title": "副教授兼系主任",   "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立台灣大學 電信工程所 博士",       "ext": "23365", "email": "sfchao@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["射頻積體電路", "毫米波積體電路"]},  # 設定研究專長
    {"id": "cfyen",      "name": "顏志峰", "title": "副教授",           "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立中山大學 電機工程研究所 博士",   "ext": "23374", "email": "cfyen@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["金氧半元件製程與分析", "化合物半導體", "太陽能電池"]},  # 設定研究專長
    {"id": "zclee",      "name": "李志成", "title": "副教授",           "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立成功大學 微電子工程研究所 博士", "ext": "23345", "email": "zclee@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["半導體元件模擬", "光電元件研製", "半導體元件物理與製程"]},  # 設定研究專長
    {"id": "yhchen",     "name": "陳玉鴻", "title": "副教授兼副系主任", "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立中興大學 電機工程系 博士",       "ext": "23288", "email": "yhchen@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["矽光子元件", "矽/鍺紅外光偵測器", "功能性氧化物薄膜電子元件",  # 列出研究專長項目
                   "矽基與高效疊層式太陽能電池元件", "真空鍍膜技術(CVD/PVD)"]},  # 完成研究專長清單
    {"id": "jftang",     "name": "唐健富", "title": "副教授",           "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立成功大學 電機工程研究所 博士",   "ext": "23347", "email": "jftang@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["高功率脈衝濺鍍技術", "奈米金屬氧化物合成", "微鑽頭與工具鍍膜", "材料與機械性質分析"]},  # 設定研究專長
    {"id": "whchang",    "name": "張煒旭", "title": "副教授",           "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立陽明交通大學 電子研究所 博士", "ext": "23373", "email": "whchang@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["混合訊號IC設計", "電源管理IC設計", "系統級晶片設計",  # 列出研究專長項目
                   "線性/數位控制系統", "數位訊號處理"]},  # 完成研究專長清單
    {"id": "changsp",    "name": "張勝博", "title": "副教授",           "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立成功大學 微電子工程研究所 博士", "ext": "23369", "email": "changsp@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["感測器元件", "奈米科技", "太陽能電池", "原子層沉積技術",  # 列出研究專長項目
                   "薄膜工程", "光檢測器", "薄膜電池", "半導體工程"]},  # 完成研究專長清單
    {"id": "yuchyao",    "name": "姚永正", "title": "助理教授",         "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立中正大學 電機工程研究所 博士",   "ext": "23344", "email": "yuchyao@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["微處理機/嵌入式系統", "電腦網路", "無線通訊", "感測器網路"]},  # 設定研究專長
    {"id": "jlhou",      "name": "侯杰利", "title": "助理教授",         "retired": False,  # 設定教師識別碼、姓名、職稱與在職狀態
     "degree": "國立成功大學 微電子工程研究所 博士", "ext": "23360", "email": "jlhou@nkust.edu.tw",  # 設定學歷、分機與電子郵件
     "expertise": ["太陽電池", "磊晶與薄膜沉積技術", "感測器元件", "光檢測器", "微處理機"]},  # 設定研究專長
    # ---- 退休教師 ----
    {"id": "chenghuang", "name": "黃成樑", "title": "副教授（退休）",   "retired": True,  # 設定退休教師資料
     "degree": "美國賓州州立大學 電機工程系 博士",   "ext": "",      "email": "chenghuang@nkust.edu.tw",  # 設定學歷與聯絡方式
     "expertise": ["半導體積體電路和理論（含奈米電子和太陽能）", "測試和元件模擬"]},  # 設定研究專長
    {"id": "yschang",    "name": "張永昇", "title": "助理教授（退休）", "retired": True,  # 設定退休教師資料
     "degree": "日本東京大學 電子工學 博士",         "ext": "",      "email": "yschang@nkust.edu.tw",  # 設定學歷與聯絡方式
     "expertise": ["OEIC on Si技術", "半導體奈米技術", "MBE/LPE磊晶成長技術",  # 列出研究專長項目
                   "Deep Submicron積體電路製程", "次世代半導體記憶體材料與元件"]},  # 完成研究專長清單
    {"id": "jennylee",   "name": "李致頤", "title": "助理教授（退休）", "retired": True,  # 設定退休教師資料
     "degree": "美國加州州立大學 數學 碩士",         "ext": "",      "email": "jennylee@nkust.edu.tw",  # 設定學歷與聯絡方式
     "expertise": ["數值分析", "物理數學"]},  # 設定研究專長
    {"id": "rbchen",     "name": "陳榮斌", "title": "教授（退休）",     "retired": True,  # 設定退休教師資料
     "degree": "國立成功大學 物理研究所 博士",       "ext": "",      "email": "rbchen@nkust.edu.tw",  # 設定學歷與聯絡方式
     "expertise": ["理論固態物理", "半導體"]},  # 設定研究專長
]  # 完成教師名單

CONTENT_TYPES = {  # 建立副檔名與 HTTP MIME 類型對照
    ".html": "text/html; charset=utf-8",  # HTML 網頁類型
    ".css":  "text/css; charset=utf-8",  # CSS 樣式類型
    ".js":   "application/javascript; charset=utf-8",  # JavaScript 程式類型
    ".json": "application/json; charset=utf-8",  # JSON 資料類型
    ".png":  "image/png",  # PNG 圖片類型
    ".jpg":  "image/jpeg",  # JPEG 圖片類型
    ".svg":  "image/svg+xml",  # SVG 向量圖類型
}  # 完成 MIME 類型對照


# ----------------------------------------------------------------------
# 資料庫：初始化與存取
# ----------------------------------------------------------------------
def db_connect():  # 建立資料庫連線
    con = sqlite3.connect(DB_PATH)  # 開啟指定的 SQLite 資料庫
    con.row_factory = sqlite3.Row  # 讓查詢列可使用欄位名稱存取
    return con  # 回傳資料庫連線物件


def init_db():  # 初始化教授資料表與預設教師資料
    """建立資料表，並在第一次執行時寫入教授名單（已存在則不覆蓋）。"""
    con = db_connect()  # 建立資料庫連線
    con.execute(  # 建立教授資料表
        """
        CREATE TABLE IF NOT EXISTS professors (
            id        TEXT PRIMARY KEY,
            name      TEXT NOT NULL,
            title     TEXT,
            degree    TEXT,
            ext       TEXT,
            email     TEXT,
            expertise TEXT,
            retired   INTEGER,
            status    TEXT,
            note      TEXT,
            updated   INTEGER,
            password  TEXT,
            schedule  TEXT
        )
        """
        )  # 完成資料表建立語句
    for p in ROSTER:  # 逐一處理初始教師名單
        con.execute(  # 新增尚未存在的教師資料
            """
            INSERT OR IGNORE INTO professors
                (id, name, title, degree, ext, email, expertise, retired,
                 status, note, updated, password, schedule)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (  # 準備新增資料列的欄位值
                p["id"], p["name"], p["title"], p["degree"], p["ext"], p["email"],  # 加入教師基本資料
                json.dumps(p["expertise"], ensure_ascii=False),  # 將研究專長序列化為 JSON
                1 if p["retired"] else 0,  # 將退休狀態轉成資料庫整數
                "unknown", "", 0, DEFAULT_PASSWORD, "{}",  # 設定狀態、備註、時間、密碼與空課表
            ),  # 完成新增資料參數
        )  # 執行新增或忽略已存在資料
    con.commit()  # 儲存初始化結果
    con.close()  # 關閉資料庫連線


def public_professor(row):  # 將資料庫列轉成公開資料格式
    """把資料庫列轉成可回傳給前端的 dict（不含密碼）。"""
    d = dict(row)  # 將資料列轉換成字典
    d["expertise"] = json.loads(d.get("expertise") or "[]")  # 解碼研究專長資料
    d["schedule"] = json.loads(d.get("schedule") or "{}")  # 解碼課表資料
    d["retired"] = bool(d.get("retired"))  # 將退休欄位轉為布林值
    d.pop("password", None)  # 移除不可公開的密碼欄位
    return d  # 回傳整理後的教師資料


def get_row(pid):  # 依教師識別碼取得單筆資料
    con = db_connect()  # 建立資料庫連線
    row = con.execute("SELECT * FROM professors WHERE id = ?", (pid,)).fetchone()  # 執行參數化查詢
    con.close()  # 關閉資料庫連線
    return row  # 回傳資料列或查無資料的 None


def list_public():  # 取得所有教師的公開資料
    con = db_connect()  # 建立資料庫連線
    rows = con.execute("SELECT * FROM professors ORDER BY retired ASC").fetchall()  # 依在職狀態查詢名單
    con.close()  # 關閉資料庫連線
    return [public_professor(r) for r in rows]  # 轉換每筆資料並回傳清單


def check_login(pid, password):  # 驗證教師識別碼與密碼
    row = get_row(pid)  # 查詢教師帳號資料
    return bool(row) and row["password"] == password  # 確認帳號存在且密碼相符


def update_status(pid, status, note):  # 更新教師目前狀態與備註
    con = db_connect()  # 建立資料庫連線
    con.execute(  # 寫入新的狀態資料
        "UPDATE professors SET status = ?, note = ?, updated = ? WHERE id = ?",
        (status, note, int(__import__("time").time() * 1000), pid),  # 傳入狀態、備註、時間戳與教師識別碼
    )  # 執行狀態更新
    con.commit()  # 儲存狀態更新
    con.close()  # 關閉資料庫連線


def update_schedule(pid, schedule):  # 更新教師課表
    con = db_connect()  # 建立資料庫連線
    con.execute(  # 寫入序列化課表
        "UPDATE professors SET schedule = ? WHERE id = ?",
        (json.dumps(schedule, ensure_ascii=False), pid),  # 傳入課表 JSON 與教師識別碼
    )  # 執行課表更新
    con.commit()  # 儲存課表更新
    con.close()  # 關閉資料庫連線


def update_password(pid, new_password):  # 更新教師登入密碼
    con = db_connect()  # 建立資料庫連線
    con.execute("UPDATE professors SET password = ? WHERE id = ?", (new_password, pid))  # 依識別碼更新密碼欄位
    con.commit()  # 儲存密碼變更
    con.close()  # 關閉資料庫連線


# ----------------------------------------------------------------------
# HTTP 伺服器
# ----------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):  # 定義 HTTP 請求處理器
    server_version = "NKUSTProfServer/1.0"  # 設定伺服器識別字串

    # ---------- 工具 ----------
    def _send_json(self, obj, code=200):  # 傳送 JSON 格式 HTTP 回應
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")  # 將資料編碼為 UTF-8 JSON
        self.send_response(code)  # 設定 HTTP 狀態碼
        self.send_header("Content-Type", "application/json; charset=utf-8")  # 指定 JSON 回應類型
        self.send_header("Content-Length", str(len(payload)))  # 設定回應本文長度
        self.send_header("Cache-Control", "no-store")  # 要求用戶端不要快取回應
        self.end_headers()  # 結束 HTTP 標頭
        self.wfile.write(payload)  # 寫入 JSON 回應本文

    def _read_json(self):  # 讀取並解析 JSON 請求本文
        try:  # 嘗試讀取請求長度標頭
            length = int(self.headers.get("Content-Length") or 0)  # 取得請求本文長度
        except ValueError:  # 處理無法轉成整數的長度值
            length = 0  # 長度格式錯誤時視為空本文
        if length <= 0:  # 檢查請求本文是否為空
            return {}  # 空本文以空字典表示
        raw = self.rfile.read(length)  # 讀取指定長度的請求本文
        try:  # 嘗試解碼並解析 JSON
            return json.loads(raw.decode("utf-8"))  # 解碼並解析 JSON 資料
        except (ValueError, UnicodeDecodeError):  # 處理 JSON 或文字編碼錯誤
            return {}  # 格式錯誤或非 UTF-8 時回傳空字典

    def _serve_file(self, rel_name):  # 傳送指定的靜態檔案
        # 防止路徑跳脫（../）
        safe_name = os.path.normpath(rel_name).lstrip("\\/")  # 正規化相對路徑並移除開頭斜線
        full = os.path.join(STATIC_DIR, safe_name)  # 組合靜態檔案完整路徑
        if not os.path.abspath(full).startswith(os.path.abspath(STATIC_DIR)):  # 確認檔案仍位於靜態資料夾
            return self._send_plain("403 Forbidden", 403)  # 拒絕存取資料夾以外的路徑
        if not os.path.isfile(full):  # 確認要求的檔案存在
            return self._send_plain("404 Not Found", 404)  # 找不到檔案時回傳 404
        ext = os.path.splitext(full)[1].lower()  # 取得小寫副檔名
        with open(full, "rb") as fh:  # 開啟檔案並確保讀取後自動關閉
            data = fh.read()  # 以二進位模式讀取檔案
        self.send_response(200)  # 設定成功狀態碼
        self.send_header("Content-Type", CONTENT_TYPES.get(ext, "application/octet-stream"))  # 設定檔案 MIME 類型
        self.send_header("Content-Length", str(len(data)))  # 設定檔案內容長度
        self.end_headers()  # 結束 HTTP 標頭
        self.wfile.write(data)  # 傳送檔案內容

    def _send_plain(self, text, code):  # 傳送純文字 HTTP 回應
        data = text.encode("utf-8")  # 將回應文字編碼為 UTF-8
        self.send_response(code)  # 設定 HTTP 狀態碼
        self.send_header("Content-Type", "text/plain; charset=utf-8")  # 指定純文字回應類型
        self.send_header("Content-Length", str(len(data)))  # 設定回應本文長度
        self.end_headers()  # 結束 HTTP 標頭
        self.wfile.write(data)  # 寫入純文字回應本文

    # ---------- 路由 ----------
    def do_GET(self):  # 處理 HTTP GET 請求
        path = urlsplit(self.path).path  # 取得不含查詢參數的路徑
        if path in ("/", "/index.html"):  # 比對學生端首頁路徑
            return self._serve_file("index.html")  # 提供學生端首頁
        if path in ("/professor", "/professor.html"):  # 比對教授端頁面路徑
            return self._serve_file("professor.html")  # 提供教授端頁面
        if path == "/api/professors":  # 比對教師名單 API 路徑
            return self._send_json({"ok": True, "professors": list_public()})  # 回傳公開教師名單 API 資料
        if path.startswith("/static/"):  # 判斷是否要求靜態資源
            return self._serve_file(path[len("/static/"):])  # 提供 static 資料夾內的資源
        return self._send_plain("404 Not Found", 404)  # 未知路徑回傳 404

    def do_POST(self):  # 處理 HTTP POST API 請求
        path = urlsplit(self.path).path  # 取得不含查詢參數的路徑
        body = self._read_json()  # 解析 JSON 請求資料
        pid = str(body.get("id", "")).strip()  # 取得並清理教師識別碼
        pwd = str(body.get("password", ""))  # 取得登入密碼字串

        if path == "/api/login":  # 處理教師登入 API
            if check_login(pid, pwd):  # 驗證教師帳號與密碼
                return self._send_json({"ok": True, "professor": public_professor(get_row(pid))})  # 登入成功時回傳教師資料
            return self._send_json({"ok": False, "error": "姓名或密碼錯誤"}, 401)  # 登入失敗時回傳 401

        if not check_login(pid, pwd):  # 驗證其餘修改 API 的登入狀態
            return self._send_json({"ok": False, "error": "驗證失敗，請重新登入"}, 401)  # 未通過驗證則拒絕操作

        if path == "/api/status":  # 處理教師狀態更新 API
            update_status(pid, str(body.get("status", "unknown")), str(body.get("note", "")).strip())  # 更新狀態與備註
            return self._send_json({"ok": True, "professor": public_professor(get_row(pid))})  # 回傳更新後的教師資料

        if path == "/api/schedule":  # 處理教師課表更新 API
            schedule = body.get("schedule") or {}  # 取得課表資料或空字典
            if not isinstance(schedule, dict):  # 確認課表資料為字典格式
                schedule = {}  # 非字典格式時改用空課表
            # 只保留有內容的格子
            schedule = {k: str(v).strip() for k, v in schedule.items() if str(v).strip()}  # 清除空白課表欄位
            update_schedule(pid, schedule)  # 儲存整理後的課表
            return self._send_json({"ok": True, "professor": public_professor(get_row(pid))})  # 回傳更新後的教師資料

        if path == "/api/password":  # 處理教師密碼修改 API
            new_pwd = str(body.get("newPassword", ""))  # 取得新密碼字串
            if not new_pwd:  # 確認新密碼不是空字串
                return self._send_json({"ok": False, "error": "新密碼不可為空"}, 400)  # 空密碼時回傳錯誤
            update_password(pid, new_pwd)  # 儲存新密碼
            return self._send_json({"ok": True})  # 回傳密碼更新成功

        return self._send_plain("404 Not Found", 404)  # 未知 API 路徑回傳 404

    # 簡化終端機訊息
    def log_message(self, fmt, *args):  # 自訂 HTTP 存取記錄格式
        print("[{}] {}".format(self.address_string(), fmt % args))  # 顯示用戶端位址與請求資訊


def main():  # 執行資料庫初始化並啟動伺服器
    if not os.path.isdir(STATIC_DIR):  # 確認前端靜態檔案資料夾存在
        raise SystemExit("找不到 static 資料夾：{}".format(STATIC_DIR))  # 缺少前端目錄時停止程式
    init_db()  # 建立資料表並寫入初始名單
    server = ThreadingHTTPServer((HOST, PORT), Handler)  # 建立多執行緒 HTTP 伺服器
    print("=" * 56)  # 顯示啟動訊息分隔線
    print(" 高科大 教授狀態與課表查詢系統（Python 後端）已啟動")  # 顯示伺服器啟動狀態
    print("   學生端：http://localhost:{}/".format(PORT))  # 顯示學生端網址
    print("   教授端：http://localhost:{}/professor".format(PORT))  # 顯示教授端網址
    print("   按 Ctrl + C 可停止伺服器")  # 提示停止伺服器的方法
    print("=" * 56)  # 顯示啟動訊息結尾分隔線
    try:  # 進入伺服器主迴圈
        server.serve_forever()  # 持續處理用戶端請求
    except KeyboardInterrupt:  # 接收使用者的中斷指令
        print("\n伺服器已停止")  # 顯示伺服器停止訊息
        server.server_close()  # 關閉伺服器連線


if __name__ == "__main__":  # 確認程式是直接執行而非被匯入
    main()  # 執行伺服器啟動流程
