# 🚀 AI Resume Pipeline Pro | AI 简历全自动流水线

**一键实现：内容提取 -> AI 润色 -> 格式转换 -> LaTeX 自动编译 PDF**

这是一个基于 Python 和 大模型（Gemini/ChatGPT/DeepSeek/豆包）开发的简历专家工具。它能将你凌乱的 Word/PDF 原始经历，自动翻译、润色并精准注入到精美的 LaTeX 模板中，最后全自动生成 PDF。

## ✨ 核心功能

* **多格式兼容**：支持拖拽 Word (.docx), PDF, TeX 文件作为内容源。
* **Overleaf 项目支持**：直接支持拖入从 Overleaf 下载的整个 .zip 工程包。
* **AI 聚合大脑**：自主选择 Gemini, ChatGPT, DeepSeek 或 豆包模型。
* **双语生成**：支持中英文界面切换，并能一键生成纯正的英文或中文简历。
* **AI 瘦身控制**：授权 AI 删除冗余内容，并可选 1 页或 2 页的篇幅限制。
* **本地自动化编译**：自动调用本地 xelatex 引擎，无需手动操作命令行。

## 🛠️ 安装要求

1.  **Python 环境**：Python 3.10+
2.  **LaTeX 环境**：电脑需安装 [TeX Live](https://www.tug.org/texlive/) 或 [MiKTeX](https://miktex.org/)。
    * *提示：请确保 `xelatex` 命令已加入系统环境变量。*
3.  **依赖库**：
    ```bash
    pip install google-genai openai tkinterdnd2 pdfplumber python-docx chardet
    ```

## 🚀 快速开始

1.  运行程序：`python main.py`
2.  配置 API Key，选择你心仪的 AI 模型。
3.  **左侧**：拖入你的原始简历文件。
4.  **右侧**：拖入从 Overleaf 下载的模板 ZIP 包。
5.  点击“启动流水线”，稍等片刻，PDF 就会出现在你指定的目录下！

---

## 🎨 如何从 Overleaf 获取海量模板

Overleaf 是全球最大的 LaTeX 模板库。按照以下步骤，你可以将任何精美模板变为己用：

### 1. 浏览与挑选
访问 [Overleaf Gallery - Résumé / CV](https://www.overleaf.com/gallery/tagged/cv) 页面。这里有数千种高颜值的简历模板。

### 2. 预览效果
点击你喜欢的模板，查看它的预览图。注意有些模板是多页的，有些是单页的。

### 3. 下载工程包 (关键)
* 点击 **"Open as Template"** 进入编辑界面。
* 在左上角菜单栏点击 **"Menu"** 图标。
* 在 "Download" 栏目下，选择 **"Source"**。
* 你会得到一个 **.zip** 格式的压缩包。

### 4. 导入本软件
**不需要解压！** 直接将下载好的这个 .zip 文件拖入我们软件右侧的“模板区域”。软件会自动识别其中的 `.cls` 样式文件和图片，确保排版原汁原味。

---

## 🤝 贡献与反馈
如果你在使用过程中遇到任何 Bug（比如特定的 LaTeX 宏包无法编译），欢迎提交 Issue！
