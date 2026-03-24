# 🚀 AI Resume Pipeline Pro  
### AI 简历全自动流水线 | AI-Powered Resume Automation Pipeline

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg">
  <img src="https://img.shields.io/badge/LaTeX-XeLaTeX-green.svg">
  <img src="https://img.shields.io/badge/AI-Gemini%20%7C%20ChatGPT%20%7C%20DeepSeek-orange">
  <img src="https://img.shields.io/badge/Status-Active-success">
</p>

---

## 📌 Overview | 项目简介

**One-click workflow: Content Extraction → AI Refinement → Format Injection → LaTeX Auto PDF Compilation**  
**一键实现：内容提取 → AI 润色 → 模板注入 → LaTeX 自动生成 PDF**

AI Resume Pipeline Pro is an end-to-end automation tool that transforms raw resume materials (Word/PDF) into professionally formatted LaTeX CVs using large language models.

本项目基于 Python + 大语言模型（Gemini / ChatGPT / DeepSeek / 豆包），可将原始简历内容自动翻译、润色并精准填充至 LaTeX 模板中，最终生成高质量 PDF。

---

## ✨ Features | 核心功能

### 📂 Input & Template System | 输入与模板系统
- Multi-format input: `.docx`, `.pdf`, `.tex`
- Drag-and-drop Overleaf `.zip` project support  
- Automatic parsing of LaTeX class and assets  

- 多格式支持：Word / PDF / TeX  
- 支持直接导入 Overleaf `.zip` 工程  
- 自动识别 `.cls` 样式与资源文件  

---

### 🧠 AI Processing Engine | AI 智能处理引擎
- Supports multiple LLM providers (Gemini / ChatGPT / DeepSeek / 豆包)
- Automatic translation (CN ↔ EN)
- Context-aware rewriting for professional tone
- Content compression (1-page / 2-page control)

- 多模型聚合（Gemini / ChatGPT / DeepSeek / 豆包）  
- 自动中英双语生成  
- 专业语境润色（符合求职语境）  
- 内容压缩与篇幅控制  

---

### 🎯 JD-Aware Optimisation（新增核心能力）
- **Tailor resumes based on Job Description (JD)**
- Extract keywords and requirements from JD
- Align experience descriptions with target roles
- Improve ATS (Applicant Tracking System) compatibility

- **支持根据岗位 JD 定向优化简历**
- 自动提取 JD 关键词与能力要求  
- 将经历重写为岗位匹配表达  
- 提升 ATS（自动筛选系统）通过率  

---

### ⚙️ Automation Pipeline | 自动化流水线
- Fully automated LaTeX compilation via `xelatex`
- No manual editing or command-line required
- End-to-end pipeline execution with one click

- 自动调用 `xelatex` 编译  
- 无需手动操作 LaTeX  
- 一键完成全流程  

---

## 🛠️ Installation | 安装说明

### 1. Python Environment
```bash
Python 3.10+
```

### 2. LaTeX Environment
Install one of:
- TeX Live  
- MiKTeX  

⚠️ Ensure:
```bash
xelatex --version
```
is available in your system PATH.

---

### 3. Dependencies
```bash
pip install google-genai openai tkinterdnd2 pdfplumber python-docx chardet
```

---

## 🚀 Quick Start | 快速开始

```bash
python main.py
```

### Steps:

1. Configure API Key and select AI model  
2. Drag your **raw resume** into the left panel  
3. Drag **Overleaf template ZIP** into the right panel  
4. Click **Start Pipeline**  

📄 Output: A polished PDF resume will be generated automatically  

---

## 🎨 Templates via Overleaf | 模板获取指南

### Step 1 — Browse
👉 https://www.overleaf.com/gallery/tagged/cv  

### Step 2 — Preview
Check layout (single-page vs multi-page)

### Step 3 — Download Source
- Click **Open as Template**
- Menu → Download → **Source (.zip)**

### Step 4 — Import
❗ Do NOT unzip  
Drag `.zip` directly into the tool  

---

## 📊 Typical Workflow | 典型使用流程

```
Raw Resume (Word/PDF)
        ↓
Content Extraction
        ↓
AI Refinement + JD Optimisation
        ↓
LaTeX Template Injection
        ↓
XeLaTeX Compilation
        ↓
Final PDF Resume
```

---

## 🧩 Tech Stack | 技术栈

- Python (Core Pipeline)
- LLM APIs (OpenAI / Google / DeepSeek)
- LaTeX (XeLaTeX)
- PDF Parsing (pdfplumber)
- GUI (tkinter + drag & drop)

---

## 🤝 Contribution | 贡献

Contributions, issues, and feature requests are welcome.  

欢迎提交 Issue 或 PR，包括：
- LaTeX 编译问题  
- 模板兼容问题  
- 新模型接入  

---

## 📬 Feedback | 反馈

If you encounter:
- Compilation errors  
- Model output issues  
- Formatting bugs  

Please open an Issue with:
- Input file
- Template used
- Error logs  

---

## ⭐ Star This Repo

If this project helps you land interviews, consider giving it a ⭐  
如果这个项目帮你拿到面试，欢迎点个 ⭐
