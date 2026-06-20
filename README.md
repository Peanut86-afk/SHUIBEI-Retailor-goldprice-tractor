# 水贝金价监控 💰

实时监控深圳水贝黄金市场贵金属买卖价格，价格触达目标时自动弹窗提醒。

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey) ![License](https://img.shields.io/badge/License-MIT-green)

---

## 功能

- 实时显示黄金、铂金、钯金、白银的回购价与销售价
- 显示当日价格高低区间
- 自定义目标买入价，触达时蜂鸣声 + 弹窗提醒
- 小窗口置顶显示，不影响其他操作
- 每 30 秒自动刷新
- 支持开机自动启动（程序内勾选即可）

## 截图

> 小窗口置顶显示，实时更新水贝现货报价

---

## 直接使用（推荐）

从 [Releases](../../releases) 页面下载 `水贝金价.exe`，双击运行，无需安装任何环境。

---

## 从源码运行

**环境要求：** Python 3.8+，仅支持 Windows

```bash
# 克隆项目
git clone https://github.com/你的用户名/shuibei-gold-monitor.git
cd shuibei-gold-monitor

# 直接运行（无需安装第三方库，全部用标准库）
python gold_monitor.py
```

## 自行打包成 .exe

```bash
pip install pyinstaller

pyinstaller --onefile --windowed --name "水贝金价" gold_monitor.py
```

打包完成后在 `dist/` 文件夹找到 `水贝金价.exe`。

---

## 使用说明

| 字段 | 说明 |
|------|------|
| 回购价 | 商家收购价（你卖出时参考） |
| 销售价 | 商家销售价（你买入时参考） |
| 今日区间 | 当日最低～最高价 |

**设置目标价提醒：**
在底部输入框填入目标买入价（如黄金填 `900`），当销售价跌至该价格时自动提醒。留空表示不提醒。

**开机自启：**
勾选右下角"开机启动"即可，程序会自动写入注册表，下次开机自动弹出。

---

## 数据来源

数据来自深圳水贝黄金市场实时报价系统，反映水贝现货批发价格，与上海金交所期货价格存在差异，更接近实际购买价格。

---

## 免责声明

本工具仅供个人价格参考，不构成任何投资建议。黄金市场有风险，交易请谨慎。
