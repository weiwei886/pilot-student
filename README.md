# Crypto Content Aggregator（加密货币内容聚合器）

这是一个适合初学者的 Python 采集项目，用于抓取“可用于短视频生成”的加密货币素材。

## 功能概览

1. 抓取 RSS 新闻（CoinDesk、Cointelegraph）
2. 使用 X API v2 抓取相关帖子（Recent Search）
3. 识别帖子中的媒体（图片/视频）
4. 按热度、关键词进行筛选
5. 输出文件：
   - `output/news.json`
   - `output/x_posts.json`
   - `output/x_videos.json`

---

## 项目结构

```text
.
├─ main.py            # 主入口
├─ config.py          # 统一配置
├─ x_client.py        # X API 请求与数据标准化
├─ filters.py         # 筛选逻辑（热度、关键词、排除词）
├─ requirements.txt   # 依赖
├─ .env.example       # 环境变量示例
└─ output/            # 运行后自动生成
```

---

## Windows 安装与运行

> 以下示例以 PowerShell 为例。

### 1) 准备 Python 环境

```powershell
python --version
```

建议 Python 3.10+。

### 2) 创建并激活虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3) 安装依赖

```powershell
pip install -r requirements.txt
```

### 4) 配置环境变量

复制 `.env.example` 为 `.env`：

```powershell
copy .env.example .env
```

然后编辑 `.env`，填入你自己的 `X_BEARER_TOKEN`。

### 5) 运行

```powershell
python main.py
```

运行后会在终端打印：
- RSS 新闻前 5 条
- X 热门帖子前 5 条
- 含视频帖子前 5 条

并生成 JSON 文件到 `output/`。

---

## 可调参数

可在 `config.py` 或 `.env` 中调整：

- `MIN_ENGAGEMENT`：最低热度阈值（点赞+转发+回复）
- `FILTER_KEYWORDS`：保留关键词
- `EXCLUDE_KEYWORDS`：排除词（广告、抽奖等）
- `X_MAX_RESULTS`：X recent search 单次抓取数量

---

## 注意事项

1. 若 `X_BEARER_TOKEN` 未配置，程序会跳过 X 抓取，不会崩溃。
2. 若某个 RSS 源临时失败，程序会记录日志并继续处理其他来源。
3. 本项目优先保证代码直观易读，便于后续扩展为自动短视频工作流。
