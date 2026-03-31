# Douban Backup

[![v1.5](https://img.shields.io/badge/version-1.5-blue.svg)](https://github.com/zx2592/douban_backup)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

豆瓣个人数据备份工具 — 一键导出你在豆瓣上的 **电影、书籍、音乐、游戏** 全部记录，包括评分、评语、标签和标记日期，输出为精美 Excel 和结构化 JSON。

---

## 功能概览

### 数据采集

| 类别 | 状态 | 采集字段 |
|------|------|----------|
| 电影 | 想看 / 在看 / 看过 | 标题、评分、评语、标签、标记日期、豆瓣链接、封面 |
| 书籍 | 想读 / 在读 / 已读 | 标题、评分、评语、作者/出版信息、标记日期、豆瓣链接、封面 |
| 音乐 | 想听 / 在听 / 听过 | 标题、评分、评语、艺术家、简介、豆瓣链接、封面 |
| 游戏 | 想玩 / 在玩 / 玩过 | 标题、评分、评语、简介、标记日期、豆瓣链接、封面 |

### Excel 导出

- **总览页** — 各类别 x 各状态的数量汇总表，一眼掌握全貌
- **分类页** — 电影、书籍、音乐、游戏各一个独立 Sheet
- **状态分组** — 看过/在看/想看 用绿/蓝/橙色标题行分隔
- **星级评分** — 数字自动转换为 ★★★★☆ 直观显示
- **可点击链接** — 豆瓣条目链接直接跳转
- **交替行色** — 斑马纹行底色，阅读不串行
- **冻结表头** — 滚动时表头始终可见

### 认证方式

| 方式 | 说明 | 推荐场景 |
|------|------|----------|
| Cookie 导入 | 从浏览器复制 Cookie 粘贴导入 | **首选**，安全便捷，规避验证码 |
| 账号密码 | 交互式输入，密码不回显 | Cookie 失效时的备选 |
| 免登录 | `crawl_public.py` 爬取公开数据 | 爬取他人公开主页 |

### 防反爬策略

- 请求间隔 2 秒智能延迟
- 失败自动重试（最多 3 次）
- 30 秒请求超时保护
- 浏览器级 User-Agent 伪装

---

## 快速开始

### 1. 安装依赖

需要 Python 3.8+

```bash
pip install -r requirements.txt
```

### 2. 导入 Cookie（推荐）

豆瓣登录有滑块/验证码保护，推荐通过浏览器 Cookie 完成认证：

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
# 备份全部类别（电影+书籍+音乐+游戏）
python main.py

# 只备份电影
python main.py movies

# 只备份书籍
python main.py books

# 查看历史备份
python main.py list
```

### 4. 查看结果

备份文件保存在 `data/backup/` 目录：

```
data/backup/
├── douban_backup_20260331_143000.xlsx   # 精美 Excel 报告
└── douban_backup_20260331_143000.json   # 结构化原始数据
```

### 5. 爬取公开数据（无需登录）

```bash
# 通过命令行参数指定用户 ID
python crawl_public.py <用户ID>

# 或直接运行，交互式输入
python crawl_public.py
```

---

## 项目结构

```
├── main.py              # 主程序入口，CLI 命令分发
├── auth.py              # 认证模块（Cookie / 账号密码登录）
├── import_cookies.py    # 浏览器 Cookie 导入工具
├── config.py            # 全局配置（超时、延迟、备份项目）
├── base.py              # 爬虫基类（请求、重试、分页）
├── movies.py            # 电影数据爬取
├── books.py             # 书籍数据爬取
├── music.py             # 音乐数据爬取
├── games.py             # 游戏数据爬取
├── crawl_public.py      # 免登录公开数据爬取（独立脚本）
├── storage.py           # 数据存储（JSON + 美化 Excel 导出）
├── requirements.txt     # Python 依赖
└── data/
    ├── cookies.json     # 登录凭据（自动生成，权限 600）
    ├── user_info.json   # 用户信息缓存
    └── backup/          # 导出文件输出目录
```

---

## 更新日志

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
- 请合理控制运行频率，避免对豆瓣服务器造成压力
- `cookies.json` 包含登录凭据，请妥善保管，切勿上传到公开仓库
