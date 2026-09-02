# Douban Backup

[![v1.81](https://img.shields.io/badge/version-1.81-blue.svg)](https://github.com/zx2592/douban_backup)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

豆瓣个人数据备份工具 — 一键导出你在豆瓣上的 **电影、书籍、音乐、游戏和长评**，包括评分、评语、标签、标记日期和封面图片，输出为精美 Excel、CSV、Markdown 和结构化 JSON。

> **v1.8** 新增封面本地下载、长评备份、CSV / Markdown 导出，并可通过 pip 安装为命令行工具。

[English README](README.en-US.md)

---

## 功能概览

### 备份内容

| 类别 | 状态 | 采集字段 |
|------|------|----------|
| 电影 | 想看 / 在看 / 看过 | 标题、评分、评语、标签、标记日期、豆瓣链接、封面 |
| 书籍 | 想读 / 在读 / 已读 | 标题、评分、评语、作者/出版信息、标记日期、豆瓣链接、封面 |
| 音乐 | 想听 / 在听 / 听过 | 标题、评分、评语、艺术家、简介、豆瓣链接、封面 |
| 游戏 | 想玩 / 在玩 / 玩过 | 标题、评分、评语、简介、标记日期、豆瓣链接、封面 |
| 长评 | 影评 / 书评 / 乐评 / 游戏评 | 标题、评论对象、评分、发表时间、正文、豆瓣链接 |

封面默认只记录 URL；加上 `--download-covers` 才会把图片下载到本地。长评默认只保存正文摘要，`--full-reviews` 抓取完整正文。

### 导出格式

| 格式 | 说明 |
|------|------|
| JSON | 结构化原始数据与备份元数据，**始终导出** |
| Excel | 美化报告：总览页、分类页、状态分组、星级、可点击链接（默认） |
| CSV | 每分类一个文件，状态单独成列、评分保留数字，便于统计（`--format csv`） |
| Markdown | 可读文档，按分类和状态分节，适合放进笔记或版本库（`--format md`） |

Excel 报告包含：总览页（各类别 × 各状态数量汇总）、每个分类一个独立 Sheet、状态分组彩色标题行、星级评分（★★★★☆）、可点击的豆瓣链接、交替行色和冻结表头。

### 核心能力

- **增量备份** — 只抓取上次备份之后新增和改动的条目，收藏无变化时每个收藏夹只需 1 次请求
- **断点续传** — 请求失败或手动中断时保留进度，下次运行从中断处继续；按豆瓣账号隔离
- **封面本地化** — 把封面下载到本地，备份不再依赖随时可能失效的豆瓣图床
- **响应诊断** — 明确区分登录失效、访问限制、风控、页面不存在和服务端错误
- **分页完整性保护** — 无法确认已到最后一页时不会误报成功，也不会清除断点
- **导出安全** — 防止外部文本在 Excel / CSV 中被当作公式执行；Cookie 文件权限收紧为 `0600`

### 认证方式

| 方式 | 说明 | 适用场景 |
|------|------|----------|
| Cookie 导入 | 从浏览器复制 Cookie 粘贴导入 | 备份自己的数据，**唯一支持的登录方式** |
| 免登录 | 公开数据模式 | 备份任意用户的公开主页 |

> 豆瓣登录页受滑块验证保护，无法用账号密码自动登录，因此本工具只支持 Cookie 导入。Cookie 失效时重新导入即可。

---

## 快速开始

### 1. 安装

需要 Python 3.8+。两种方式任选：

```bash
# 方式一：装成命令行工具（推荐）
pip install .

# 之后在任何目录都能直接用
douban-backup --help
douban-backup-public <用户ID>
douban-import-cookies

# 方式二：直接从源码运行
pip install -r requirements.txt
python main.py
```

两种方式功能完全一致，命令一一对应：

| 源码运行 | 安装后 |
|----------|--------|
| `python main.py` | `douban-backup` |
| `python crawl_public.py` | `douban-backup-public` |
| `python import_cookies.py` | `douban-import-cookies` |

**数据存放位置**：从源码运行时在项目下的 `data/`；pip 安装后在 `~/.douban_backup`（往 site-packages 里写会在升级时被清掉）。用环境变量 `DOUBAN_BACKUP_HOME` 可以指定到别处。

> 下文示例统一使用 `python main.py`。如果你是 pip 安装的，换成 `douban-backup` 即可，参数完全相同。

### 2. 导入 Cookie

```bash
python import_cookies.py
```

按提示操作：

1. 在浏览器（Chrome / Edge）登录 [douban.com](https://www.douban.com)
2. 按 `F12` 打开开发者工具 → `Network` 标签
3. 刷新页面，点击第一个请求（`www.douban.com`）
4. 在 Request Headers 中复制 `Cookie:` 后面的全部内容
5. 粘贴到终端并回车

工具会自动验证 Cookie 有效性并保存。

### 3. 开始备份

```bash
# 备份全部内容（电影 + 书籍 + 音乐 + 游戏 + 长评）
python main.py

# 先校验登录状态和各分类页面是否可访问
python main.py verify

# 查看历史备份
python main.py list
```

单独备份某一类：

```bash
python main.py movies     # 电影
python main.py books      # 书籍
python main.py music      # 音乐
python main.py games      # 游戏
python main.py reviews    # 长评
```

常用组合：

```bash
# 自由选择或排除分类
python main.py --only movies,books
python main.py --skip music,games

# 增量备份 + 全部导出格式 + 下载封面（日常备份推荐）
python main.py --incremental --format all --download-covers

# 放慢节奏，降低被限制的风险
python main.py --delay 5

# 导出到指定目录
python main.py --output D:\douban-backup
```

### 4. 查看结果

默认保存在 `data/backup/`：

```
data/backup/
├── douban_backup_20260331_143000.json          # 结构化数据与备份元数据
├── douban_backup_20260331_143000.xlsx          # 美化 Excel 报告
├── douban_backup_20260331_143000.md            # Markdown 文档（--format md）
├── douban_backup_20260331_143000_movies.csv    # CSV，每分类一个（--format csv）
├── douban_backup_20260331_143000_reviews.csv
├── douban_movies_20260331_150000.xlsx          # 单分类备份（python main.py movies）
├── covers/                                      # 封面图片（--download-covers）
│   ├── movies/1292052.jpg
│   └── books/1084336.jpg
├── backup_state_<账号摘要>.json                 # 未完成任务的断点
└── backup_baseline_<账号摘要>.json              # 增量备份的基线
```

所有导出文件名都带时间戳，历次备份不会互相覆盖；同一次备份的各种格式共用一个时间戳，方便配对。

JSON 使用统一的顶层结构：

```json
{
  "metadata": {
    "app_version": "1.8",
    "backup_mode": "authenticated",
    "generated_at": "2026-08-06T20:00:00-07:00",
    "selected_categories": ["movies", "books"]
  },
  "data": {}
}
```

---

## 命令行参数

| 参数 | 说明 |
|------|------|
| `verify` | 校验登录状态和各分类页面可访问性 |
| `list` | 列出已有备份文件 |
| `movies` / `books` / `music` / `games` / `reviews` | 只备份指定的一类 |
| `--only 分类,分类` | 仅备份指定分类，逗号分隔 |
| `--skip 分类,分类` | 跳过指定分类，逗号分隔 |
| `--incremental` | 增量备份：只抓新增和改动的条目 |
| `--format 格式` | 导出格式：`xlsx`（默认）、`csv`、`md`，或 `all`；JSON 始终导出 |
| `--download-covers` | 把封面下载到 `covers/` 子目录 |
| `--full-reviews` | 抓取长评完整正文（每篇额外一次请求） |
| `--delay 秒数` | 每次请求之间的等待时间（登录默认 2 秒，公开默认 1 秒） |
| `--output 目录` | 导出目录，默认 `data/backup` |
| `--no-resume` | 禁用断点续传 |
| `--public 用户ID` | 公开数据模式，备份指定用户的公开主页 |

### 退出码

便于在脚本或定时任务中判断结果：

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 失败（Cookie 过期、抓取中断、校验不通过等） |
| 2 | 命令行参数有误 |

---

## 进阶用法

### 增量备份

收藏较多时，每次全量重爬既慢又容易触发访问限制。增量模式利用豆瓣收藏页按标记时间倒序排列的特点，从第一页往后抓，一旦遇到上次备份中已有且没有改动的条目就停止翻页：

```bash
# 首次运行：完整备份并建立基线
python main.py --incremental

# 之后每次运行：通常只需一两次请求
python main.py --incremental
```

基线保存在 `backup_baseline_<账号摘要>.json`，按豆瓣账号隔离。**每次完整跑完的备份都会刷新基线**（无论是否加 `--incremental`），所以随时可以在两种模式之间切换。导出的文件始终是合并后的全量数据，不是只有新增部分。

几点需要知道：

- **改动会被正确捕获** — 判断依据是标题、评分、评语、标记日期、标签组成的指纹，而不只是条目 ID。修改评分或评语会让条目重新排到最前面，工具会重新抓取并覆盖旧记录
- **删除不会同步** — 你在豆瓣上取消收藏的条目不会再出现在页面上，但它仍留在基线里。需要清理时运行一次不加 `--incremental` 的完整备份
- **中断不会污染基线** — 备份未完整结束时基线保持不变，避免下次增量在残缺数据的边界就停下
- **公开模式同样支持** — 其断点和基线与登录模式分开存放

### 封面下载

只保存图片 URL 算不上完整备份——豆瓣图床对外链有 Referer 校验，条目下架或改版后旧地址也会失效。加上 `--download-covers` 会把封面存到导出目录的 `covers/<分类>/` 下，并在 JSON 里记下相对路径：

```bash
python main.py --download-covers
```

- 已下载过的文件直接跳过，中断后重跑是增量的
- 单张失败只记一笔，不影响已经抓好的数据
- 只下载豆瓣自家图床的地址；文件名只用条目 ID 或 URL 摘要，不用标题

封面走图床，比正文页面宽松，默认间隔 0.5 秒而不是 2 秒。

### 长评备份

长评（影评 / 书评 / 乐评 / 游戏评）默认一并备份。列表页只给出正文摘要，完整正文需要逐篇打开评论页：

```bash
# 默认：只保存摘要，代价很小（长评列表通常只有几页）
python main.py

# 抓取完整正文，每篇长评额外一次请求
python main.py --full-reviews

# 只备份长评
python main.py reviews
```

长评在 Excel 里是独立的「长评」Sheet，在 Markdown 里正文单独成段。

### 公开数据模式（无需登录）

```bash
# 独立脚本
python crawl_public.py <用户ID>
python crawl_public.py <用户ID> --incremental --format all

# 或直接运行，交互式输入用户 ID
python crawl_public.py

# 通过统一入口
python main.py --public <用户ID>
python main.py --public <用户ID> --only movies,books --output D:\douban-backup
```

公开模式与登录备份共用同一套抓取逻辑，因此失败重试、响应诊断、断点续传、增量备份、封面下载和全部导出格式都可用。

公开模式的断点和基线与登录模式分开存放——同一个账号的公开主页看不到设为私密的条目，两者的数据并不相同，共用基线会让增量比对得出错误结论。

### 降低被限制的风险

按效果从大到小：

1. **用增量备份** — `--incremental` 把请求量降低一个数量级，这是最有效的手段
2. **放慢节奏** — `--delay 5` 拉长请求间隔
3. 失败自动重试（最多 3 次）、30 秒超时保护、浏览器级 User-Agent 已内置

---

## 项目结构

```
├── main.py              # 主程序入口，CLI 命令分发
├── crawl_public.py      # 免登录公开数据备份入口
├── import_cookies.py    # 浏览器 Cookie 导入工具
├── auth.py              # 认证模块（Cookie 登录）
├── config.py            # 全局配置（超时、延迟、数据目录、备份项目）
├── cli.py               # 退出码翻译与导出格式解析
├── base.py              # 爬虫基类（请求、重试、分页、增量早停）
├── movies.py            # 电影数据爬取
├── books.py             # 书籍数据爬取
├── music.py             # 音乐数据爬取
├── games.py             # 游戏数据爬取
├── reviews.py           # 长评（影评/书评/乐评/游戏评）爬取
├── comments.py          # 「我的评语」提取（四类页面的标记并不统一）
├── covers.py            # 封面图片本地下载
├── storage.py           # 导出（JSON / 美化 Excel / CSV / Markdown）
├── incremental.py       # 增量备份的指纹比对与基线存储
├── backup_state.py      # 账号隔离的断点恢复
├── backup_metadata.py   # 备份版本、模式和生成时间元数据
├── diagnostics.py       # 登录失效、风控和页面异常诊断
├── excel_safety.py      # 表格公式注入保护
├── file_security.py     # Cookie 文件权限保护
├── pyproject.toml       # 打包配置与控制台命令
├── requirements.txt     # Python 依赖
├── .github/workflows/   # CI：多版本测试与打包检查
├── tests/               # 离线解析和流程测试
└── data/
    ├── cookies.json     # 登录凭据（自动生成，权限 600）
    ├── user_info.json   # 用户信息缓存
    └── backup/          # 导出文件、封面、断点和增量基线
```

---

## 更新日志

### v1.81 — 修复音乐 / 游戏的「我的评语」备份

**修复**

- **音乐和游戏的评语不再全空** — 豆瓣四类收藏页对评语的标记并不统一：电影用 `<span class="comment">`、书籍用 `<p class="comment">`，而音乐把评语放在条目信息列表里最后一个**没有 class** 的 `<li>`，游戏放在条目末尾一个**没有 class** 的 `<p>`。四个解析器此前都只认 `.comment`，所以电影和书籍正常，音乐和游戏其余字段照抓、唯独「我的评语」一列全空
- **游戏标题不再被评分说法覆盖** — 评分只以 `title="力荐"` 给出的条目，换算评分时误用了 `title` 变量接住这个中文，把条目标题冲掉，备份里的游戏名变成「力荐 / 推荐 / 还行」

**改进**

- **评语提取收敛到一处** — 新增 `comments.py`，四类解析器共用同一个提取函数：优先认 `.comment`（豆瓣哪天补上这个 class 也能直接命中），取不到再在纯文本的 `li` / `p` 里找，并排除标题、简介、日期、评分、标签等已解析成别的字段的节点，避免把日期或简介误写成评语。没写评语的条目仍然留空

### v1.8 — 封面下载、长评备份、多格式导出与打包

**新功能**

- **封面本地下载** — `--download-covers` 把封面存到 `covers/<分类>/`，备份不再依赖豆瓣图床。已下载的跳过，中断后重跑是增量的；文件名只用条目 ID 或 URL 摘要（标题来自页面，含 `..` 时会写到目录之外），且只下载豆瓣自家图床的地址
- **长评备份** — 新增 `reviews` 分类，备份影评 / 书评 / 乐评 / 游戏评。用长评自身的 ID 作标识（同一部片子可以写多篇），默认保存摘要，`--full-reviews` 抓取完整正文
- **CSV 与 Markdown 导出** — `--format xlsx,csv,md` 或 `--format all`。CSV 每分类一个文件，状态单独成列、评分保留数字，用 BOM 写入以免 Windows 上的 Excel 显示乱码；Markdown 按分类和状态分节
- **增量备份** — `--incremental` 只抓取上次备份之后新增和改动的条目。比对的是标题、评分、评语、日期、标签构成的指纹而非条目 ID，所以修改评分或评语后条目会被重新抓取并覆盖旧记录。导出仍是合并后的全量数据
- **可 pip 安装** — 新增 `pyproject.toml`，提供 `douban-backup`、`douban-backup-public`、`douban-import-cookies` 三个命令

**改进**

- **公开模式合并到统一抓取栈** — `crawl_public.py` 此前自带一整套抓取、分页、解析和导出逻辑，与主流程大量重复，豆瓣改一次页面结构要改两处；现已复用同一套代码（该文件从 691 行降到 203 行），并因此获得失败重试、响应诊断、断点续传、增量备份和美化 Excel 导出
- **安装后的数据目录** — 装进 site-packages 后再往那里写会被升级清掉、有时还是只读的，因此改用 `~/.douban_backup`；源码运行仍用项目下的 `data/`，`DOUBAN_BACKUP_HOME` 可覆盖
- **命令行失败时返回非零退出码** — 此前 Cookie 过期、抓取中断、校验不通过全都以退出码 0 结束，脚本无法判断成败。现约定成功 0、失败 1、参数错误 2；参数写错也不再抛 traceback
- **持续集成** — GitHub Actions 在 Python 3.8/3.10/3.12 上跑测试与静态检查，并验证发行包和控制台命令可用
- **补充 LICENSE** — README 一直挂着 MIT 徽章却没有许可证文件
- **移除未使用的 pandas 依赖** — 四个依赖里最重的一个，代码里从未引用

**修复**

- **移除已失效的账号密码登录** — 豆瓣登录页受滑块验证保护，原有的表单式登录早已无法成功，保留只会误导用户在 Cookie 失效时去试一条走不通的路。Cookie 导入成为唯一认证方式，Cookie 文件缺失或损坏时给出明确提示而不是抛异常
- **单分类备份不再覆盖历史文件** — `python main.py movies` 此前固定写入 `movies.xlsx`，每次运行覆盖上一次；现改为带时间戳命名，与全量备份一致
- **同一次备份共用时间戳** — 各种导出格式不再各自取当前时间，避免跨秒时文件名对不上
- **音乐评分不再漏读** — 原先只检查 class 列表的第一项，遇到评分 class 不在首位的结构会把评分整个丢掉
- **游戏评分不再写入中文** — 部分条目的评分只以 `title="力荐"` 给出，此前原样写入：JSON 里是中文，Excel 又因为不是数字而静默丢弃。现换算成 5/4/3/2/1

### v1.53 — 可配置请求间隔

- **降低访问限制风险** — 登录和公开数据备份均支持 `--delay 秒数`，可按需调整每次请求之间的等待时间；默认分别为 2 秒和 1 秒

### v1.52 — 可靠性与命令行增强

- **可靠的断点恢复** — 请求失败、分页异常或手动中断时保留进度；状态按豆瓣账号隔离并采用原子写入
- **分页完整性保护** — 无法确认最后一页时不再误报成功或清除断点
- **响应诊断** — 明确区分登录失效、访问限制、风控、页面不存在和服务端错误
- **备份元数据** — JSON 和 Excel 记录应用版本、备份模式、账号、生成时间和所选分类
- **导出安全加固** — 防止外部文本在 Excel 中被解释为公式，并收紧 Cookie 文件访问权限
- **命令行完善** — 支持电影、书籍、音乐和游戏四类快捷命令，以及 `verify`、`--only`、`--skip`、`--output` 和 `--no-resume`
- **测试覆盖** — 增加四类页面结构、断点隔离、原子写入、错误重试和分页异常测试

### v1.51 — 公开数据短评修复

- **修复短评导出** — 公开和登录模式统一精确读取电影、书籍、音乐、游戏短评，避免音乐短评与日期同项时被忽略，也不再将游戏简介误作短评

### v1.5 — 安全性加固

- **移除命令行密码传递** — 不再支持通过 CLI 参数传入账号密码，杜绝密码泄露到 shell 历史和进程列表
- **密码输入隐藏** — 交互式密码输入改用 `getpass`，输入时不回显
- **Cookie 文件权限控制** — 写入 `cookies.json` 后自动设置 `0o600` 权限，仅所有者可读写
- **异常处理规范化** — 全项目裸 `except:` 替换为 `except Exception:`，不再吞掉 `KeyboardInterrupt` 等关键异常
- **修复评分解析** — 电影/书籍的 rating class 提取从索引取值改为安全遍历，消除越界风险
- **移除硬编码用户 ID** — `crawl_public.py` 改为命令行参数或交互输入，不再泄露目标用户身份

### v1.2 — 美化 Excel 导出

- 新增总览 Sheet，汇总各类别/状态数据量
- 各类别独立 Sheet，状态分组彩色标题行
- 星级评分符号显示（★★★★☆）
- 豆瓣链接可点击跳转
- 交替行色、冻结表头、自适应列宽

### v1.0 — 初始版本

- 支持电影、书籍、音乐、游戏四类数据备份
- Cookie 导入认证
- JSON 格式导出
- 自动分页爬取、重试机制

---

## 注意事项

- 本工具仅供个人数据备份和学习使用，请勿用于商业用途
- 请合理控制运行频率，避免对豆瓣服务器造成压力；日常备份建议使用 `--incremental`
- `cookies.json` 包含登录凭据，请妥善保管，切勿上传到公开仓库
- 增量备份不会同步你在豆瓣上删除的收藏，需要清理时运行一次完整备份
