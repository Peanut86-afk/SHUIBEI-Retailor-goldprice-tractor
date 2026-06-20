"""
水贝黄金价格监控
- 实时显示贵金属买卖价
- 设置目标价，触发时弹窗+声音提醒
- 小窗口置顶，每30秒自动刷新
"""

import tkinter as tk
from tkinter import ttk
import urllib.request
import ssl
import json
import threading
import time
import datetime
import winsound  # Windows 系统声音

# ── 配置 ──────────────────────────────────────────
API_URL     = "https://sdj.ldywt.com/api/product/all"
REFRESH_SEC = 30   # 刷新间隔（秒）
WIN_WIDTH   = 340
WIN_HEIGHT  = 420

# 目标价设置：跌到或低于这个价格时提醒（0 = 不提醒）
TARGETS = {
    "黄金": 900.0,
    "铂金": 0,
    "钯金": 0,
    "白银": 0,
}

# 颜色
CLR_BG      = "#1a1a2e"
CLR_CARD    = "#16213e"
CLR_ACCENT  = "#e2b96f"
CLR_UP      = "#4caf8a"
CLR_DOWN    = "#e25757"
CLR_TEXT    = "#f0e6d3"
CLR_MUTED   = "#888899"
CLR_BORDER  = "#2a2a4a"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode    = ssl.CERT_NONE

# ── 数据获取 ──────────────────────────────────────
def fetch_prices():
    req = urllib.request.Request(API_URL, headers={
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)",
        "Accept":     "application/json",
        "Referer":    "https://sdj.ldywt.com/",
    })
    with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
        return json.loads(r.read().decode("utf-8"))

def parse_prices(raw):
    result = []
    for item in raw["data"]["list"]:
        d = item["0"]
        result.append({
            "name":     d["name"],
            "buy":      float(d["bidprice"]),   # 回购价（你卖给商家）
            "sell":     float(d["askprice"]),   # 销售价（你买入）
            "high":     float(d["high"]),
            "low":      float(d["low"]),
            "isup":     d["isup"],
        })
    return result

# ── 主窗口 ────────────────────────────────────────
class GoldMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("水贝金价")
        self.root.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}+20+20")
        self.root.configure(bg=CLR_BG)
        self.root.attributes("-topmost", True)      # 置顶
        self.root.resizable(False, False)

        self.prices   = []
        self.alerted  = set()   # 已提醒过的品种，避免重复
        self.targets  = dict(TARGETS)

        self._build_ui()
        self._refresh()         # 启动时立刻拉一次

    # ── UI 构建 ───────────────────────────────────
    def _build_ui(self):
        # 标题栏
        hdr = tk.Frame(self.root, bg=CLR_BG, pady=8)
        hdr.pack(fill="x", padx=14)

        tk.Label(hdr, text="水贝金价", font=("微软雅黑", 13, "bold"),
                 bg=CLR_BG, fg=CLR_ACCENT).pack(side="left")

        self.lbl_time = tk.Label(hdr, text="--:--:--",
                                  font=("Consolas", 10),
                                  bg=CLR_BG, fg=CLR_MUTED)
        self.lbl_time.pack(side="right")

        # 列标题
        cols = tk.Frame(self.root, bg=CLR_BG)
        cols.pack(fill="x", padx=14, pady=(0, 4))
        for txt, w, anchor in [
            ("品种", 70, "w"),
            ("回购价", 72, "center"),
            ("销售价", 72, "center"),
            ("今日区间", 100, "center"),
        ]:
            tk.Label(cols, text=txt, width=w//8, font=("微软雅黑", 9),
                     bg=CLR_BG, fg=CLR_MUTED, anchor=anchor).pack(side="left")

        tk.Frame(self.root, bg=CLR_BORDER, height=1).pack(fill="x", padx=14)

        # 价格卡片容器
        self.cards_frame = tk.Frame(self.root, bg=CLR_BG)
        self.cards_frame.pack(fill="x", padx=14, pady=6)

        # 目标价设置区
        tk.Frame(self.root, bg=CLR_BORDER, height=1).pack(fill="x", padx=14, pady=(4,0))

        tgt_hdr = tk.Frame(self.root, bg=CLR_BG, pady=4)
        tgt_hdr.pack(fill="x", padx=14)
        tk.Label(tgt_hdr, text="目标买入价提醒", font=("微软雅黑", 9),
                 bg=CLR_BG, fg=CLR_MUTED).pack(side="left")

        self.tgt_frame = tk.Frame(self.root, bg=CLR_BG)
        self.tgt_frame.pack(fill="x", padx=14, pady=(0, 6))
        self.tgt_vars = {}

        for name in TARGETS:
            row = tk.Frame(self.tgt_frame, bg=CLR_BG, pady=2)
            row.pack(fill="x")
            tk.Label(row, text=name, width=5, font=("微软雅黑", 10),
                     bg=CLR_BG, fg=CLR_TEXT, anchor="w").pack(side="left")
            var = tk.StringVar(value=str(TARGETS[name]) if TARGETS[name] else "")
            self.tgt_vars[name] = var
            entry = tk.Entry(row, textvariable=var, width=8,
                             font=("Consolas", 10),
                             bg=CLR_CARD, fg=CLR_ACCENT,
                             insertbackground=CLR_ACCENT,
                             relief="flat", bd=4)
            entry.pack(side="left", padx=(6, 0))
            tk.Label(row, text="元/克  (0=关闭)", font=("微软雅黑", 9),
                     bg=CLR_BG, fg=CLR_MUTED).pack(side="left", padx=4)

        # 底部栏
        tk.Frame(self.root, bg=CLR_BORDER, height=1).pack(fill="x", padx=14, pady=(4,0))
        btm = tk.Frame(self.root, bg=CLR_BG, pady=6)
        btm.pack(fill="x", padx=14)

        self.lbl_status = tk.Label(btm, text="等待刷新...",
                                    font=("微软雅黑", 9),
                                    bg=CLR_BG, fg=CLR_MUTED)
        self.lbl_status.pack(side="left")

        btn = tk.Button(btm, text="立即刷新",
                        font=("微软雅黑", 9),
                        bg=CLR_CARD, fg=CLR_ACCENT,
                        relief="flat", bd=0, padx=8, pady=2,
                        cursor="hand2",
                        command=self._refresh)
        btn.pack(side="right")

        self._build_cards()

    def _build_cards(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()

        names = list(TARGETS.keys()) if not self.prices else [p["name"] for p in self.prices]
        for name in names:
            row = tk.Frame(self.cards_frame, bg=CLR_CARD,
                           pady=7, padx=8,
                           highlightbackground=CLR_BORDER,
                           highlightthickness=1)
            row.pack(fill="x", pady=2)

            tk.Label(row, text=name, width=5,
                     font=("微软雅黑", 11, "bold"),
                     bg=CLR_CARD, fg=CLR_ACCENT, anchor="w").pack(side="left")

            # 占位 label，等刷新时填数据
            lbl_buy = tk.Label(row, text="---", width=8,
                                font=("Consolas", 11),
                                bg=CLR_CARD, fg=CLR_UP, anchor="center")
            lbl_buy.pack(side="left")

            lbl_sell = tk.Label(row, text="---", width=8,
                                 font=("Consolas", 11),
                                 bg=CLR_CARD, fg=CLR_TEXT, anchor="center")
            lbl_sell.pack(side="left")

            lbl_range = tk.Label(row, text="---", width=13,
                                  font=("Consolas", 9),
                                  bg=CLR_CARD, fg=CLR_MUTED, anchor="center")
            lbl_range.pack(side="left")

            row._name_ref   = name
            row._lbl_buy    = lbl_buy
            row._lbl_sell   = lbl_sell
            row._lbl_range  = lbl_range

    def _update_cards(self):
        price_map = {p["name"]: p for p in self.prices}
        for row in self.cards_frame.winfo_children():
            name = getattr(row, "_name_ref", None)
            if not name or name not in price_map:
                continue
            p = price_map[name]
            clr = CLR_UP if p["isup"] == "up" else CLR_DOWN
            row._lbl_buy.config(text=f"{p['buy']:.2f}", fg=CLR_UP)
            row._lbl_sell.config(text=f"{p['sell']:.2f}", fg=clr)
            row._lbl_range.config(text=f"{p['low']:.2f}~{p['high']:.2f}")

    # ── 刷新逻辑 ──────────────────────────────────
    def _refresh(self):
        def worker():
            try:
                raw = fetch_prices()
                self.prices = parse_prices(raw)
                self.root.after(0, self._on_data)
            except Exception as e:
                self.root.after(0, lambda: self.lbl_status.config(
                    text=f"获取失败: {e}", fg=CLR_DOWN))
        threading.Thread(target=worker, daemon=True).start()

        # 读取用户设定的目标价
        for name, var in self.tgt_vars.items():
            try:
                v = float(var.get())
                self.targets[name] = v
            except ValueError:
                self.targets[name] = 0

        # 安排下一次刷新
        self.root.after(REFRESH_SEC * 1000, self._refresh)

    def _on_data(self):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.lbl_time.config(text=now)
        self.lbl_status.config(text=f"更新于 {now}", fg=CLR_MUTED)
        self._update_cards()
        self._check_alerts()

    def _check_alerts(self):
        for p in self.prices:
            name   = p["name"]
            target = self.targets.get(name, 0)
            if target <= 0:
                continue
            # 用销售价（你买入的价格）与目标比较
            if p["sell"] <= target and name not in self.alerted:
                self.alerted.add(name)
                self._alert(name, p["sell"], target)
            elif p["sell"] > target and name in self.alerted:
                self.alerted.discard(name)  # 价格回升，重置

    def _alert(self, name, price, target):
        # 声音提醒
        try:
            for _ in range(3):
                winsound.Beep(1000, 400)
                time.sleep(0.2)
        except Exception:
            pass

        # 弹窗提醒
        popup = tk.Toplevel(self.root)
        popup.title("价格提醒！")
        popup.geometry("280x160")
        popup.configure(bg=CLR_BG)
        popup.attributes("-topmost", True)

        tk.Label(popup, text="🔔 目标价触发！",
                 font=("微软雅黑", 13, "bold"),
                 bg=CLR_BG, fg=CLR_ACCENT).pack(pady=(20, 6))
        tk.Label(popup,
                 text=f"{name}  销售价 {price:.2f} 元/克",
                 font=("微软雅黑", 11),
                 bg=CLR_BG, fg=CLR_TEXT).pack()
        tk.Label(popup,
                 text=f"已达到你的目标 ≤ {target:.2f}",
                 font=("微软雅黑", 10),
                 bg=CLR_BG, fg=CLR_UP).pack(pady=4)
        tk.Button(popup, text="知道了",
                  font=("微软雅黑", 10),
                  bg=CLR_CARD, fg=CLR_ACCENT,
                  relief="flat", bd=0, padx=16, pady=4,
                  command=popup.destroy).pack(pady=10)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    GoldMonitor().run()
