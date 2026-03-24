import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import re
import os
import shutil

import doc_parser
import ai_engine
import tex_compiler
import doc_converter
import template_manager

UI_TEXT = {
    "title": {"zh": "AI 简历全自动流水线 Pro", "en": "AI Resume Pipeline Pro"},
    "ui_lang": {"zh": "界面语言:", "en": "UI Language:"},
    "doc_lang": {"zh": "简历目标语言:", "en": "Target Language:"},
    "out_dir_btn": {"zh": "选择保存位置", "en": "Output Folder"},
    "out_dir_def": {"zh": "默认位置 (原文件同目录)", "en": "Default (Source Dir)"},
    "step1": {"zh": "第一步：选择模型并填写参数", "en": "Step 1: Select Model & Parameters"},
    "model_lbl": {"zh": "选择 AI 模型:", "en": "Select AI Model:"},
    "api_key": {"zh": "API 密钥:", "en": "API Key:"},
    "doubao_id": {"zh": "豆包专属 ID:", "en": "Doubao Endpoint ID:"},
    "step2": {"zh": "第二步：拖入内容源文件", "en": "Step 2: Drop Source File"},
    "drop_source": {"zh": "请将源文件拖拽到这里\n(或点击浏览)", "en": "Drop Source File Here"},
    "btn_browse": {"zh": "浏览文件...", "en": "Browse File..."},
    "lbl_no_file": {"zh": "当前状态：未选择文件", "en": "Status: No file"},
    "step3": {"zh": "第三步：拖入 LaTeX 模板", "en": "Step 3: Drop Template (TeX/ZIP)"},
    "drop_temp": {"zh": "请将模板文件拖拽到这里\n(或点击浏览)", "en": "Drop Template File Here"},
    "jd_frame": {"zh": "填写目标岗位描述 (JD)", "en": "Target Job Description (JD)"},
    "ctrl_frame": {"zh": "AI 瘦身控制台", "en": "AI Pruning Console"},
    "lbl_pages": {"zh": "目标页数限制:", "en": "Target Pages:"},
    "chk_prune": {"zh": "授权 AI 删除无关啰嗦经历", "en": "Allow AI to delete irrelevant info"},
    "step4": {"zh": "第四步：选择模式启动流水线", "en": "Step 4: Select Mode to Start"},
    "btn_m1": {"zh": "1. 自动无痕转换为 TeX (无模板 + 生成PDF)", "en": "1. Convert to TeX directly (No Template + PDF)"},
    "btn_m2": {"zh": "2. 提取内容并填入模板 (智能识别 + 生成PDF)", "en": "2. Inject Content into Template (Generate PDF)"},
    "btn_m3": {"zh": "3. 润色左侧现有 TeX 文件 (智能扩写 + 生成PDF)", "en": "3. Polish Existing TeX File (Generate PDF)"},
    "ready": {"zh": "🟢 准备就绪，请配置参数并加载文件。", "en": "🟢 Ready to start."},
    "msg_warn_api": {"zh": "请填入有效的 API Key！", "en": "Please enter a valid API Key!"},
    "msg_warn_doubao": {"zh": "使用豆包模型必须填写专属 ID！", "en": "Endpoint ID is required for Doubao!"},
    "msg_warn_src": {"zh": "请拖入内容源文件！", "en": "Please load a source file!"},
    "msg_warn_tmp": {"zh": "请拖入模板文件！", "en": "Please load a template file!"},
    "msg_success": {"zh": "操作成功！文件已保存至：\n", "en": "Success! Files saved to:\n"}
}

def ensure_chinese_support(tex_content, target_lang):
    if target_lang == "中文":
        if "xeCJK" not in tex_content and "ctex" not in tex_content:
            idx = tex_content.find(r"\begin{document}")
            if idx != -1:
                injection = "\n% AI Auto-injected for Chinese support\n\\usepackage{xeCJK}\n"
                tex_content = tex_content[:idx] + injection + tex_content[idx:]
    return tex_content

def smart_inject_skills(tex_content, new_skills):
    if not new_skills:
        return tex_content
        
    skills_latex = "\n".join([f"    \\item \\textbf{{AI Recommended}}: {skill}" for skill in new_skills]) + "\n"
    
    skill_section_pattern = re.compile(r"\\section\{[^}]*?[Ss]kill[^}]*\}")
    match = skill_section_pattern.search(tex_content)
    
    if match:
        start_idx = match.end()
        end_itemize_idx = tex_content.find(r"\end{itemize}", start_idx)
        if end_itemize_idx != -1:
            return tex_content[:end_itemize_idx] + skills_latex + tex_content[end_itemize_idx:]
            
    fallback_pattern = re.compile(r"\\end\{document\}")
    fallback_match = fallback_pattern.search(tex_content)
    if fallback_match:
        end_doc_idx = fallback_match.start()
        fallback_latex = "\n\\section{Additional Skills}\n\\begin{itemize}\n" + skills_latex + "\\end{itemize}\n"
        return tex_content[:end_doc_idx] + fallback_latex + tex_content[end_doc_idx:]
        
    return tex_content + "\n" + skills_latex

class ResumeApp:
    def __init__(self, root):
        self.root = root
        self.root.title(UI_TEXT["title"]["zh"])
        self.root.geometry("820x980")
        self.root.configure(bg="#f5f5f5")
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.source_filepath = "" 
        self.template_project = None 
        self.output_dir = ""
        self.current_lang = "zh"
        
        top_bar = tk.Frame(root, bg="#ffffff", relief="flat", borderwidth=1)
        top_bar.pack(fill="x", padx=20, pady=(15, 10))
        
        self.lbl_title = tk.Label(top_bar, text=UI_TEXT["title"][self.current_lang], font=("Arial", 14, "bold"), fg="#008080", bg="#ffffff")
        self.lbl_title.pack(side="top", anchor="w", pady=(5, 10))
        
        settings_frame = tk.Frame(top_bar, bg="#ffffff")
        settings_frame.pack(side="top", fill="x", pady=5)
        
        self.lbl_ui_lang = tk.Label(settings_frame, text=UI_TEXT["ui_lang"][self.current_lang], bg="#ffffff")
        self.lbl_ui_lang.pack(side="left")
        self.ui_lang_cb = ttk.Combobox(settings_frame, values=["中文", "English"], width=6, state="readonly")
        self.ui_lang_cb.current(0)
        self.ui_lang_cb.pack(side="left", padx=5)
        self.ui_lang_cb.bind("<<ComboboxSelected>>", self.change_ui_lang)
        
        self.lbl_doc_lang = tk.Label(settings_frame, text=UI_TEXT["doc_lang"][self.current_lang], bg="#ffffff")
        self.lbl_doc_lang.pack(side="left", padx=(10, 0))
        self.doc_lang_cb = ttk.Combobox(settings_frame, values=["中文", "English"], width=6, state="readonly")
        self.doc_lang_cb.current(0)
        self.doc_lang_cb.pack(side="left", padx=5)
        
        self.btn_out_dir = tk.Button(settings_frame, text=UI_TEXT["out_dir_btn"][self.current_lang], command=self.choose_output_dir, relief="flat", bg="#e0e0e0")
        self.btn_out_dir.pack(side="left", padx=(10, 5))
        self.lbl_out_dir = tk.Label(settings_frame, text=UI_TEXT["out_dir_def"][self.current_lang], bg="#ffffff", fg="gray")
        self.lbl_out_dir.pack(side="left")
        
        api_frame = tk.Frame(top_bar, bg="#ffffff")
        api_frame.pack(side="top", fill="x", pady=10)
        self.lbl_step1 = tk.Label(api_frame, text=UI_TEXT["step1"][self.current_lang], font=("Arial", 10, "bold"), bg="#ffffff")
        self.lbl_step1.pack(anchor="w", pady=(0, 5))
        
        model_row = tk.Frame(api_frame, bg="#ffffff")
        model_row.pack(fill="x", pady=2)
        self.lbl_model = tk.Label(model_row, text=UI_TEXT["model_lbl"][self.current_lang], bg="#ffffff", width=12, anchor="w")
        self.lbl_model.pack(side="left")
        self.provider_cb = ttk.Combobox(model_row, values=["Gemini", "ChatGPT", "DeepSeek", "Doubao"], width=15, state="readonly")
        self.provider_cb.current(0)
        self.provider_cb.pack(side="left")
        self.provider_cb.bind("<<ComboboxSelected>>", self.toggle_doubao_id)
        
        key_row = tk.Frame(api_frame, bg="#ffffff")
        key_row.pack(fill="x", pady=2)
        self.lbl_key = tk.Label(key_row, text=UI_TEXT["api_key"][self.current_lang], bg="#ffffff", width=12, anchor="w")
        self.lbl_key.pack(side="left")
        self.api_entry = tk.Entry(key_row, show="*", font=("Courier New", 10), bg="#f5f5f5", relief="flat")
        self.api_entry.pack(side="left", fill="x", expand=True)
        
        self.doubao_row = tk.Frame(api_frame, bg="#ffffff")
        self.lbl_doubao = tk.Label(self.doubao_row, text=UI_TEXT["doubao_id"][self.current_lang], bg="#ffffff", width=12, anchor="w")
        self.lbl_doubao.pack(side="left")
        self.doubao_entry = tk.Entry(self.doubao_row, font=("Courier New", 10), bg="#f5f5f5", relief="flat")
        self.doubao_entry.pack(side="left", fill="x", expand=True)
        
        file_parent_frame = tk.Frame(root, bg="#f5f5f5")
        file_parent_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.source_section = tk.LabelFrame(file_parent_frame, text=f" {UI_TEXT['step2'][self.current_lang]} ", font=("Arial", 10, "bold"), bg="#ffffff", padx=10, pady=10)
        self.source_section.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.source_drop_area = tk.Label(self.source_section, text=UI_TEXT["drop_source"][self.current_lang], bg="#f5f5f5", font=("Arial", 11), fg="#008080", width=30, height=4, relief="groove")
        self.source_drop_area.pack(fill="both", pady=5)
        self.source_drop_area.drop_target_register(DND_FILES)
        self.source_drop_area.dnd_bind('<<Drop>>', self.handle_source_drop)
        btn_source_row = tk.Frame(self.source_section, bg="#ffffff")
        btn_source_row.pack(fill="x")
        self.source_label = tk.Label(btn_source_row, text=UI_TEXT["lbl_no_file"][self.current_lang], fg="gray", anchor="w", bg="#ffffff")
        self.source_label.pack(side="left", padx=5)
        self.btn_browse_source = tk.Button(btn_source_row, text=UI_TEXT["btn_browse"][self.current_lang], command=self.browse_source_file, relief="flat", bg="#e0e0e0", fg="#333", padx=8)
        self.btn_browse_source.pack(side="right")
        
        self.template_section = tk.LabelFrame(file_parent_frame, text=f" {UI_TEXT['step3'][self.current_lang]} ", font=("Arial", 10, "bold"), bg="#ffffff", padx=10, pady=10)
        self.template_section.pack(side="right", fill="both", expand=True)
        self.template_drop_area = tk.Label(self.template_section, text=UI_TEXT["drop_temp"][self.current_lang], bg="#f5f5f5", font=("Arial", 11), fg="#9C27B0", width=30, height=4, relief="groove")
        self.template_drop_area.pack(fill="both", pady=5)
        self.template_drop_area.drop_target_register(DND_FILES)
        self.template_drop_area.dnd_bind('<<Drop>>', self.handle_template_drop)
        btn_template_row = tk.Frame(self.template_section, bg="#ffffff")
        btn_template_row.pack(fill="x")
        self.template_label = tk.Label(btn_template_row, text=UI_TEXT["lbl_no_file"][self.current_lang], fg="gray", anchor="w", bg="#ffffff")
        self.template_label.pack(side="left", padx=5)
        self.btn_browse_template = tk.Button(btn_template_row, text=UI_TEXT["btn_browse"][self.current_lang], command=self.browse_template_file, relief="flat", bg="#e0e0e0", fg="#333", padx=8)
        self.btn_browse_template.pack(side="right")
        
        content_frame = tk.Frame(root, bg="#f5f5f5")
        content_frame.pack(fill="x", padx=20, pady=10)
        self.jd_section = tk.LabelFrame(content_frame, text=f" {UI_TEXT['jd_frame'][self.current_lang]} ", bg="#ffffff", padx=10, pady=10)
        self.jd_section.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.jd_text = tk.Text(self.jd_section, height=5, width=40, font=("Courier New", 9), bg="#f5f5f5", relief="flat")
        self.jd_text.pack(fill="both")
        
        # === 新增控制台界面 ===
        self.ctrl_section = tk.LabelFrame(content_frame, text=f" {UI_TEXT['ctrl_frame'][self.current_lang]} ", bg="#ffffff", padx=10, pady=10)
        self.ctrl_section.pack(side="right", fill="both", expand=True)
        
        page_row = tk.Frame(self.ctrl_section, bg="#ffffff")
        page_row.pack(fill="x", pady=5)
        self.lbl_pages = tk.Label(page_row, text=UI_TEXT["lbl_pages"][self.current_lang], bg="#ffffff")
        self.lbl_pages.pack(side="left")
        self.page_cb = ttk.Combobox(page_row, values=["自动判断", "1页 (极简)", "2页 (丰富)"], width=12, state="readonly")
        self.page_cb.current(0)
        self.page_cb.pack(side="left", padx=5)
        
        self.prune_var = tk.BooleanVar(value=False)
        self.chk_prune = tk.Checkbutton(self.ctrl_section, text=UI_TEXT["chk_prune"][self.current_lang], variable=self.prune_var, bg="#ffffff", activebackground="#ffffff")
        self.chk_prune.pack(anchor="w", pady=5)
        
        bottom_area = tk.Frame(root, bg="#ffffff", relief="flat", borderwidth=1)
        bottom_area.pack(fill="x", side="bottom", pady=15, padx=20)
        self.lbl_step4 = tk.Label(bottom_area, text=UI_TEXT["step4"][self.current_lang], font=("Arial", 11, "bold"), bg="#ffffff", fg="#333")
        self.lbl_step4.pack(pady=(5, 5))
        
        btn_m1 = tk.Frame(bottom_area, bg="#ffffff")
        btn_m1.pack(pady=2)
        self.run_btn_m1 = tk.Button(btn_m1, text=UI_TEXT["btn_m1"][self.current_lang], command=self.action_mode_m1, bg="#2196F3", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=15, pady=5)
        self.run_btn_m1.pack()
        
        btn_m2 = tk.Frame(bottom_area, bg="#ffffff")
        btn_m2.pack(pady=2)
        self.run_btn_m2 = tk.Button(btn_m2, text=UI_TEXT["btn_m2"][self.current_lang], command=self.action_mode_m2, bg="#9C27B0", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=15, pady=5)
        self.run_btn_m2.pack()
        
        self.run_btn_m3 = tk.Button(bottom_area, text=UI_TEXT["btn_m3"][self.current_lang], command=self.action_mode_m3, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=15, pady=5)
        self.run_btn_m3.pack()
        
        self.status_bar = tk.Frame(root, bg="#ffffff", relief="groove", borderwidth=1)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_label = tk.Label(self.status_bar, text=UI_TEXT["ready"][self.current_lang], font=("Arial", 9), fg="#333", bg="#ffffff", anchor="w", padx=10)
        self.status_label.pack(fill="x")

    def toggle_doubao_id(self, event=None):
        if self.provider_cb.get() == "Doubao":
            self.doubao_row.pack(fill="x", pady=2)
        else:
            self.doubao_row.pack_forget()

    def change_ui_lang(self, event=None):
        self.current_lang = "zh" if self.ui_lang_cb.get() == "中文" else "en"
        lang = self.current_lang
        
        self.root.title(UI_TEXT["title"][lang])
        self.lbl_title.config(text=UI_TEXT["title"][lang])
        self.lbl_ui_lang.config(text=UI_TEXT["ui_lang"][lang])
        self.lbl_doc_lang.config(text=UI_TEXT["doc_lang"][lang])
        self.btn_out_dir.config(text=UI_TEXT["out_dir_btn"][lang])
        if not self.output_dir:
            self.lbl_out_dir.config(text=UI_TEXT["out_dir_def"][lang])
        
        self.lbl_step1.config(text=UI_TEXT["step1"][lang])
        self.lbl_model.config(text=UI_TEXT["model_lbl"][lang])
        self.lbl_key.config(text=UI_TEXT["api_key"][lang])
        self.lbl_doubao.config(text=UI_TEXT["doubao_id"][lang])
        
        self.source_section.config(text=f" {UI_TEXT['step2'][lang]} ")
        self.template_section.config(text=f" {UI_TEXT['step3'][lang]} ")
        if not self.source_filepath:
            self.source_drop_area.config(text=UI_TEXT["drop_source"][lang])
            self.source_label.config(text=UI_TEXT["lbl_no_file"][lang])
        if not self.template_project:
            self.template_drop_area.config(text=UI_TEXT["drop_temp"][lang])
            self.template_label.config(text=UI_TEXT["lbl_no_file"][lang])
        self.btn_browse_source.config(text=UI_TEXT["btn_browse"][lang])
        self.btn_browse_template.config(text=UI_TEXT["btn_browse"][lang])
        self.jd_section.config(text=f" {UI_TEXT['jd_frame'][lang]} ")
        
        self.ctrl_section.config(text=f" {UI_TEXT['ctrl_frame'][lang]} ")
        self.lbl_pages.config(text=UI_TEXT["lbl_pages"][lang])
        self.chk_prune.config(text=UI_TEXT["chk_prune"][lang])
        
        self.lbl_step4.config(text=UI_TEXT["step4"][lang])
        self.run_btn_m1.config(text=UI_TEXT["btn_m1"][lang])
        self.run_btn_m2.config(text=UI_TEXT["btn_m2"][lang])
        self.run_btn_m3.config(text=UI_TEXT["btn_m3"][lang])

    def choose_output_dir(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir = dir_path
            self.lbl_out_dir.config(text=dir_path, fg="green")

    def get_save_paths(self, original_source_path, suffix, extension):
        base_name = os.path.splitext(os.path.basename(original_source_path))[0]
        file_name = f"{base_name}{suffix}{extension}"
        save_dir = self.output_dir if self.output_dir else os.path.dirname(original_source_path)
        return os.path.join(save_dir, file_name)

    def validate_and_get_api(self):
        key = self.api_entry.get().strip()
        if not key:
            messagebox.showwarning("Warning", UI_TEXT["msg_warn_api"][self.current_lang])
            return None, None, None
        provider = self.provider_cb.get()
        doubao_id = self.doubao_entry.get().strip()
        if provider == "Doubao" and not doubao_id:
            messagebox.showwarning("Warning", UI_TEXT["msg_warn_doubao"][self.current_lang])
            return None, None, None
        return key, provider, doubao_id

    def update_status(self, text, color="#FF9800"):
        self.status_label.config(text=f"⏳ {text}", fg=color)
        self.root.update()

    def handle_source_drop(self, event):
        self.source_filepath = event.data.strip('{}')
        self.source_label.config(text=f"File: {os.path.basename(self.source_filepath)}", fg="green")
        self.source_drop_area.config(bg="#c8e6c9", text="Loaded ✅")

    def browse_source_file(self):
        path = filedialog.askopenfilename(filetypes=[("Content Files", "*.docx;*.pdf;*.tex")])
        if path:
            self.source_filepath = path
            self.source_label.config(text=f"File: {os.path.basename(self.source_filepath)}", fg="green")
            self.source_drop_area.config(bg="#c8e6c9", text="Loaded ✅")

    def handle_template_drop(self, event):
        self.update_template_status(event.data.strip('{}'))

    def browse_template_file(self):
        path = filedialog.askopenfilename(filetypes=[("Template Files", "*.tex;*.zip")])
        if path:
            self.update_template_status(path)

    def update_template_status(self, path):
        if path.lower().endswith('.tex'):
            self.template_project = template_manager.TemplateProject(os.path.dirname(path), path)
            self.template_label.config(text=f"Template: {os.path.basename(path)}", fg="green")
            self.template_drop_area.config(bg="#e1bee7", text="Loaded ✅")
        elif path.lower().endswith('.zip'):
            self.update_status("Processing ZIP...", "#FF9800")
            success, project_or_msg = template_manager.prepare_template_injection(path)
            if success:
                self.template_project = project_or_msg 
                self.template_label.config(text=f"ZIP: {os.path.basename(path)}", fg="#9C27B0")
                self.template_drop_area.config(bg="#e1bee7", text="ZIP Loaded ✅")
                self.update_status("ZIP Ready", "green")
            else:
                messagebox.showerror("Error", project_or_msg)

    def action_mode_m1(self):
        api_key, provider, doubao_id = self.validate_and_get_api()
        if not api_key: return
        if not self.source_filepath:
            messagebox.showwarning("Warning", UI_TEXT["msg_warn_src"][self.current_lang])
            return
            
        target_language = "English" if self.doc_lang_cb.get() == "English" else "中文"
        target_pages = self.page_cb.get()
        allow_prune = self.prune_var.get()
        
        self.update_status(f"Converting using {provider}...")
        
        success, tex_code = doc_converter.convert_to_tex(
            provider, api_key, doubao_id, self.source_filepath, mode="auto", 
            target_lang=target_language, target_pages=target_pages, allow_pruning=allow_prune
        )
        if not success:
            messagebox.showerror("Error", tex_code)
            return

        tex_code = ensure_chinese_support(tex_code, target_language)

        output_tex_path = self.get_save_paths(self.source_filepath, "_converted", ".tex")
        with open(output_tex_path, "w", encoding="utf8") as f:
            f.write(tex_code)
            
        success_compile, msg = tex_compiler.compile_to_pdf(output_tex_path)
        
        if success_compile:
            final_pdf_path = output_tex_path.replace(".tex", ".pdf")
            self.status_label.config(text="🎉 Complete!", fg="green")
            messagebox.showinfo("Success", f"{UI_TEXT['msg_success'][self.current_lang]}{final_pdf_path}")
        else:
            messagebox.showerror("Compile Error", msg)

    def action_mode_m2(self):
        api_key, provider, doubao_id = self.validate_and_get_api()
        if not api_key: return
        if not self.source_filepath or not self.template_project:
            messagebox.showwarning("Warning", "Please ensure both Source and Template are loaded.")
            return
            
        target_language = "English" if self.doc_lang_cb.get() == "English" else "中文"
        target_pages = self.page_cb.get()
        allow_prune = self.prune_var.get()
        
        self.update_status(f"Injecting template using {provider}...")
        
        template_content = doc_parser.extract_text(self.template_project.main_tex_file)
        success, tex_code = doc_converter.convert_to_tex(
            provider, api_key, doubao_id, self.source_filepath, mode="template", 
            template_content=template_content, target_lang=target_language, 
            target_pages=target_pages, allow_pruning=allow_prune
        )
        
        if not success:
            messagebox.showerror("Error", tex_code)
            return

        tex_code = ensure_chinese_support(tex_code, target_language)

        success_save, final_project_obj_or_msg = template_manager.finalize_project(self.template_project, tex_code)
        if not success_save:
            messagebox.showerror("Save Error", final_project_obj_or_msg)
            return
            
        self.update_status("Compiling Project...")
        final_project_obj = final_project_obj_or_msg
        success_compile, msg = tex_compiler.compile_to_pdf(final_project_obj.main_tex_file)
        
        if success_compile:
            final_pdf_path = final_project_obj.main_tex_file.replace(".tex", ".pdf")
            display_path = final_pdf_path
            
            if self.output_dir:
                try:
                    dest_pdf = self.get_save_paths(self.source_filepath, "_final", ".pdf")
                    dest_tex = self.get_save_paths(self.source_filepath, "_final", ".tex")
                    shutil.copy2(final_pdf_path, dest_pdf)
                    shutil.copy2(final_project_obj.main_tex_file, dest_tex)
                    display_path = dest_pdf
                except Exception as e:
                    print("Copy failed:", e)

            self.status_label.config(text="🎉 Complete!", fg="green")
            messagebox.showinfo("Success", f"{UI_TEXT['msg_success'][self.current_lang]}{display_path}")
        else:
            messagebox.showerror("Compile Error", msg)

    def action_mode_m3(self):
        api_key, provider, doubao_id = self.validate_and_get_api()
        if not api_key: return
        if not self.source_filepath:
            messagebox.showwarning("Warning", UI_TEXT["msg_warn_src"][self.current_lang])
            return
            
        jd = self.jd_text.get("1.0", tk.END).strip()
        target_language = "English" if self.doc_lang_cb.get() == "English" else "中文"
        target_pages = self.page_cb.get()
        allow_prune = self.prune_var.get()
        
        self.update_status(f"Polishing existing TeX using {provider}...")
        raw_text = doc_parser.extract_text(self.source_filepath)
        matches = re.findall(r"\\resumeItem\{(.*?)\}", raw_text, re.DOTALL)
        experiences_to_polish = [m.strip() for m in matches if len(m.strip().split()) > 3]
        
        polished_data, new_skills = ai_engine.process_and_polish(
            provider, api_key, doubao_id, experiences_to_polish, jd, "", 
            target_lang=target_language, target_pages=target_pages, allow_pruning=allow_prune
        )
        
        final_tex_content = raw_text
        for old_text, new_text in polished_data.items():
            final_tex_content = final_tex_content.replace(old_text, new_text)
            
        final_tex_content = smart_inject_skills(final_tex_content, new_skills)
        final_tex_content = ensure_chinese_support(final_tex_content, target_language)
            
        output_tex_path = self.get_save_paths(self.source_filepath, "_polished", ".tex")
        with open(output_tex_path, "w", encoding="utf8") as f:
            f.write(final_tex_content)
            
        self.update_status("Compiling...")
        success_compile, msg = tex_compiler.compile_to_pdf(output_tex_path)
        
        if success_compile:
            final_pdf_path = output_tex_path.replace(".tex", ".pdf")
            self.status_label.config(text="🎉 Complete!", fg="green")
            messagebox.showinfo("Success", f"{UI_TEXT['msg_success'][self.current_lang]}{final_pdf_path}")
        else:
            messagebox.showerror("Compile Error", msg)

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ResumeApp(root)
    root.mainloop()