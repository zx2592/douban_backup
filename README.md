# Douban Data Backup (豆瓣数据备份工具)

[![v1.0](https://img.shields.io/badge/version-1.0-blue.svg)](https://github.com/your-repo/douban-backup)

一个强大的豆瓣个人数据备份工具，支持导出 **电影、书籍、音乐、游戏** 的完整记录，包括用户评分、观看时间、标签以及 **个人评语**。

## ✨ 功能特点 (v1.0)

*   **全类别支持**：覆盖 电影 (Movies)、书籍 (Books)、音乐 (Music)、游戏 (Games)。
*   **状态全覆盖**：支持 想看 (Wish)、在看 (Do)、看过 (Collect) 等所有状态。
*   **隐私与安全**：
    *   **Cookie 导入**：内置工具支持通过浏览器 Cookie 登录，无需明文保存密码，无需处理复杂验证码。
    *   **自动重连**：Cookie 自动保存到本地，后续运行自动登录。
*   **完整数据**：
    *   支持导出 Excel (.xlsx) 和 JSON 格式。
    *   **包含评语**：完整保留您对条目的文字评价。
    *   **包含标签**：保留您打的个人标签。
*   **防反爬**：
    *   内置智能延迟和重试机制。
    *   支持断点续传（基于页码）。

## 🚀 快速开始

### 1. 安装依赖

确保已安装 Python 3.8+。

```bash
pip install -r requirements.txt
```

### 2. 首次登录 (推荐)

由于豆瓣登录验证（滑块/验证码）较复杂，推荐使用 Cookie 导入工具完成首次认证：

1.  在浏览器（Chrome/Edge）登录 [豆瓣官网](https://www.douban.com)。
2.  按 `F12` 打开开发者工具，点击 `Network` 标签。
3.  刷新页面，点击第一个请求 (`www.douban.com`)。
4.  在右侧 Headers 中复制 `Cookie:` 后面的全部内容。
5.  运行导入工具：
    ```bash
    python import_cookies.py
    ```
6.  按提示粘贴 Cookie 并回车。

### 3. 开始备份

运行主程序备份所有数据：

```bash
python main.py
```

程序将自动爬取所有类别数据，并在控制台显示进度。

### 4. 导出结果

备份完成后，文件将保存在 `data/backup/` 目录下：

*   `douban_backup_YYYYMMDD_HHMMSS.xlsx`：精美的 Excel 表格，包含所有类别的工作表。
*   `douban_backup_YYYYMMDD_HHMMSS.json`：原始数据文件。

## 🛠️ 高级用法

也可以只备份特定类别：

```bash
# 只备份电影
python main.py movies

# 只备份书籍
python main.py books
```

## 📂 文件结构

```
douban_backup/
├── main.py              # 主程序入口
├── import_cookies.py    # Cookie 导入工具
├── crawlers/            # (逻辑代码: movies.py, books.py, etc.)
├── data/
│   └── backup/          # 您的数据将保存在这里
├── requirements.txt     # 项目依赖
└── README.md            # 说明文档
```

## ⚠️ 注意事项

*   本工具仅供个人备份学习使用，请勿用于商业用途。
*   请合理控制运行频率，以免对豆瓣服务器造成压力。
