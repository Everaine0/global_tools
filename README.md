# 环境辅助工具 (EnvAssist Tool )

本项目旨在提供一个统一、便捷的环境管理和项目辅助命令行界面，简化 Python 和 Node.js 开发者的日常工作流程。它围绕 Conda 环境管理、依赖处理、Git 操作以及常见项目结构生成等功能，通过模块化设计，提升开发效率。

**当前状态: [例如：Alpha / Beta / 稳定版 / 积极开发中]**

## ✨ 核心特性

*   🚀 **提升效率:** 自动化环境配置、依赖处理和项目初始化。
*   🔧 **统一管理:** 通过一个命令行工具管理 Conda 环境、Git 代理、项目依赖。
*   🐍 **Python 支持:**
    *   基于 Conda 的环境创建、删除、克隆（导出 yml）。
    *   依赖文件 (`requirements.txt` <=> `pyproject.toml`) 检查、转换和生成 (使用 `pipreqs`)。
    *   一键创建环境并安装依赖。
    *   自动生成项目启动脚本 (`run.bat`/`run.sh`)。
    *   FastAPI 工具：快速打开文档、启动开发服务器。
*   🟢 **Node.js 支持:**
    *   基于 Conda 创建包含 Node.js 和 pnpm 的环境。
    *   一键安装项目依赖 (`pnpm install`)。
    *   启动开发服务 (基于 `package.json` 脚本)。
    *   自动生成项目启动脚本。
    *   项目打包为 `.zip` 文件 (排除 `node_modules` 等)。
*   📁 **项目生成:** 根据预设模板快速生成常见项目目录结构。
*   ⚙️ **Git 辅助:** 快速设置/取消全局 Git 代理。
*   跨平台: 设计上考虑 Windows 和 Linux 兼容性。
*    modular: 后端功能库采用模块化设计，易于维护和扩展。

## 🚀 快速开始

### 依赖

*   **Python 3.x**
*   **Conda / Miniconda:** 必须已安装并配置到系统 PATH。
*   **pip:** 用于安装 Python 依赖。
*   **(可选) Git:** 用于 Git 相关功能。

### 安装与设置

1.  **获取工具库:**
    *   克隆本仓库到本地：
        ```bash
        git clone [您的仓库 URL]
        cd [仓库名]
        ```
    *   或者，下载 `global_tools` 目录。

2.  **放置 `global_tools` 目录:**
    将 `global_tools` 目录放置在一个您方便管理的位置，例如：
    *   `~/tools/global_tools` (Linux/macOS)
    *   `C:\Users\YourUser\Documents\tools\global_tools` (Windows)

3.  **安装 `global_tools` 的 Python 依赖:**
    进入 `global_tools` 目录，根据需要安装 `pypinyin` 和 `toml` (如果它们没有被打包到工具中)：
    
    ```bash
    # 假设您在 global_tools 目录下有一个 requirements.txt 文件
    # pip install -r requirements.txt
    # 或者手动安装：
    pip install pypinyin toml
    ```
    *(开发者注: 考虑为 global_tools 添加一个 `requirements.txt` 来列出其自身依赖)*
    
4.  **生成 `tool.py` 启动器:**
    `tool.py` 是您在每个项目中使用的入口脚本。您可以使用 `global_tools` 内的生成器来创建它：
    
    *   打开命令行/终端。
    *   导航到您的项目目录，例如 `cd /path/to/your/project`。
    *   运行以下命令 (请将 `/path/to/global_tools/` 替换为 `global_tools` 目录的实际绝对路径):
        ```bash
        python /path/to/global_tools/tool_generator.py .
        ```
        这会在您的项目目录下生成一个 `tool.py` 文件。
    
5.  **运行工具:**
    在您的项目目录下，通过 `tool.py` 启动：
    
    ```bash
    python tool.py
    ```
    您将看到主菜单。

## 📖 使用说明

启动工具后，您会看到一个交互式菜单。根据提示选择相应的功能即可。

### 主要功能概览

*   **Conda 环境管理:**
    *   创建环境 (可指定 Python 版本，默认基于项目名)。
    *   安装库到指定环境。
    *   打开指定环境的命令行。
    *   删除环境。
    *   导出环境配置为 `environment.yml` 文件。
    *   列出所有 Conda 环境。
*   **Python 项目辅助:**
    *   一键创建 Conda 环境并根据 `requirements.txt` 或 `pyproject.toml` (Poetry) 安装依赖。
    *   生成启动脚本 (`run.bat`/`run.sh`)。
    *   FastAPI:
        *   打开 API 文档 (Swagger/ReDoc)。
        *   启动开发服务器 (Uvicorn)。
*   **Python 依赖工具 (子菜单):**
    *   检查 `requirements.txt` 和 `pyproject.toml`，提示同步。
    *   使用 `pipreqs` 扫描项目生成 `requirements.txt`。
*   **Node.js 项目辅助:**
    *   创建包含 Node.js 和 pnpm 的 Conda 环境并运行 `pnpm install`。
    *   启动开发服务 (基于 `package.json` 中的 `scripts`)。
    *   生成启动脚本。
    *   打包项目为 `.zip`。
*   **Git 工具:** 设置/取消全局 HTTP/HTTPS 代理。
*   **生成常见目录结构:** 从预设模板创建项目骨架。
*   **配置工具默认设置:** 自定义默认 Python 版本、Git 代理等。

## 🛠️ 架构

*   **语言:** Python
*   **核心库:** `global_tools` 目录包含所有后端逻辑模块。
*   **入口:** 每个项目下的 `tool.py` 文件调用 `global_tools` 中的主函数。
*   **模块化:** 功能被拆分为独立的 `.py` 文件 (如 `conda_manager.py`, `git_manager.py` 等)，易于维护和扩展。

## 🤝 贡献

欢迎各种形式的贡献！如果您有任何建议、发现 Bug 或希望添加新功能，请随时：

1.  **Fork** 本仓库。
2.  创建您的特性分支 (`git checkout -b feature/AmazingFeature`)。
3.  提交您的更改 (`git commit -m 'Add some AmazingFeature'`)。
4.  推送到分支 (`git push origin feature/AmazingFeature`)。
5.  打开一个 **Pull Request**。

您也可以直接提出 **Issue** 来讨论问题或建议。

## 📝 待办事项 / 未来构想 (TODO)

*   [ ]  更完善的错误处理和用户反馈。
*   [ ]  将 `global_tools` 打包为可通过 `pip` 安装的 Python 包。
*   [ ]  支持更多项目模板。
*   [ ]  Node.js 项目依赖管理工具 (如检查未使用依赖、更新依赖等)。
*   [ ]  更智能的项目类型识别 (例如，识别 Flask, Django 等具体框架)。
*   [ ]  完善单元测试和集成测试。
*   [ ]  提供更详细的文档和使用示例。

## 📜 开源许可证

本项目采用 [MIT 许可证](LICENSE.txt) 

---

**感谢您的使用与贡献！**