import re
import json
import base64
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from google import genai
from google.genai import types

BG_COLOR = "#f4f4f4"
SECTION_BG = "#ffffff"
TEXT_COLOR = "#333333"
ACCENT_COLOR = "#008080"
DISABLED_BG = "#e0e0e0"

# 双语字典
LANG_DICT = {
    "title": {"en": "AI Resume Polisher Pro", "zh": "AI 简历智能润色专家"},
    "step1": {"en": "Step 1: API & Prompt Settings", "zh": "第一步：API 与提示词配置"},
    "api_key": {"en": "API Key:", "zh": "API 密钥:"},
    "doubao_id": {"en": "Doubao ID:", "zh": "豆包专属 ID:"},
    "validate": {"en": "Validate", "zh": "验证连接"},
    "prompt_label": {"en": "Custom Prompt (Keep [JD], [SKILLS], [EXPERIENCES] placeholders):", 
                     "zh": "自定义提示词 (请务必保留 [JD], [SKILLS], [EXPERIENCES] 占位符):"},
    "step2": {"en": "Step 2: Load Resume (.tex)", "zh": "第二步：加载简历源文件 (.tex)"},
    "drop_text": {"en": "Drop .tex File Here\n(Or click Browse)", "zh": "将 .tex 文件拖拽至此\n(或点击浏览)"},
    "browse": {"en": "Browse File...", "zh": "浏览本地文件..."},
    "no_file": {"en": "Current: No file selected", "zh": "当前状态：未选择任何文件"},
    "step3": {"en": "Step 3: Target JD", "zh": "第三步：目标职位需求 (JD)"},
    "ocr_btn": {"en": "📷 Upload Screenshot", "zh": "📷 上传截图自动识别"},
    "step4": {"en": "Step 4: Skills (Optional)", "zh": "第四步：个人技能库 (可选)"},
    "run_btn": {"en": "🚀 START SMART POLISHING", "zh": "🚀 开始智能润色"},
    "status_ready": {"en": "🟢 Ready", "zh": "🟢 准备就绪"},
    "warn_api": {"en": "Please enter the API Key first.", "zh": "请先填写 API 密钥！"},
    "warn_file": {"en": "Please load a .tex file first.", "zh": "请先加载一个 .tex 文件！"},
    "warn_jd": {"en": "Job Description (JD) is required.", "zh": "职位需求 (JD) 不能为空！"},
    "processing": {"en": "Processing with AI, please wait...", "zh": "正在呼叫大模型进行处理，请耐心等待..."},
    "success": {"en": "Resume Polishing Complete!", "zh": "🎉 润色完美结束！"}
}

DEFAULT_PROMPT_EN = """You are an expert HR and resume writer. Polish my resume experiences based on the JD and skills.
Ensure high relevance, professional tone, and emphasize achievements using the STAR method.
Do not delete any experience. Output ONLY a valid JSON object where keys are the original text and values are the polished text.
Escape all LaTeX special characters (e.g., & to \\&, % to \\%).
If the original text is just a single short skill word, try not to change it.

Target JD:
[JD]

[SKILLS]

Experiences to polish:
[EXPERIENCES]"""

DEFAULT_PROMPT_ZH = """你是一个资深且专业的顶级HR。请根据以下职位需求，使用纯正、专业的职场英文重新润色我的简历经历。
确保内容与JD高度相关，突出数据和成果，并符合 STAR 法则。
不要删除任何经历，只需润色。必须严格输出 JSON 格式，键为原文本，值为润色后的英文文本。
必须对所有 LaTeX 特殊字符（如 &, %, $）进行转义（例如将 & 改为 \\&）。
如果原文只是单个技能词汇，请保持原样。

职位需求：
[JD]

[SKILLS]

需要润色的经历列表：
[EXPERIENCES]"""

def process_tex_content(tex_content):
    pattern_resume = r"\\resumeItem\{(.*?)\}"
    pattern_item = r"\\item\s+(.*?)(?=\\item|\\end\{)"
    
    placeholder_template = "[[EXP_{}]]"
    extracted_data = {}
    counter = 0
    
    def repl_resume(match):
        nonlocal counter
        text = match.group(1).strip()
        if not text: 
            return match.group(0)
        placeholder = placeholder_template.format(counter)
        extracted_data[placeholder] = text
        counter += 1
        return "\\resumeItem{" + placeholder + "}"
        
    tex_content = re.sub(pattern_resume, repl_resume, tex_content, flags=re.DOTALL)
    
    def repl_item(match):
        nonlocal counter
        text = match.group(1).strip()
        if not text: 
            return match.group(0)
        placeholder = placeholder_template.format(counter)
        extracted_data[placeholder] = text
        counter += 1
        return "\\item " + placeholder + "\n"
        
    tex_content = re.sub(pattern_item, repl_item, tex_content, flags=re.DOTALL)
    return tex_content, extracted_data

def filter_and_polish(provider, api_key, doubao_id, custom_prompt, extracted_data, job_description, skills_db):
    short_texts = {}
    long_texts = {}
    
    for placeholder, text in extracted_data.items():
        word_count = len(text.split())
        if ":" in text or "：" in text or word_count < 5:
            short_texts[placeholder] = text
        else:
            long_texts[placeholder] = text
            
    if not long_texts:
        return short_texts
        
    if skills_db:
        skills_prompt = f"Skills Library:\n{skills_db}"
    else:
        skills_prompt = "Note: No specific skills provided. Please naturally match the JD based on the original experiences."
        
    # 安全的字符串替换，防止大括号冲突
    final_prompt = custom_prompt.replace("[JD]", job_description)
    final_prompt = final_prompt.replace("[SKILLS]", skills_prompt)
    final_prompt = final_prompt.replace("[EXPERIENCES]", str(list(long_texts.values())))
    
    try:
        if provider == "Gemini":
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=final_prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            raw_text = response.text
        else:
            from openai import OpenAI
            if provider == "ChatGPT":
                client = OpenAI(api_key=api_key)
                model_name = "gpt-4o-mini"
            elif provider == "DeepSeek":
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                model_name = "deepseek-chat"
            elif provider == "Doubao":
                client = OpenAI(api_key=api_key, base_url="https://ark.cn-beijing.volces.com/api/v3")
                model_name = doubao_id
                
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": final_prompt}]
            )
            raw_text = response.choices[0].message.content
            
        raw_text = raw_text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        polished_dict_raw = json.loads(raw_text.strip())
        
        final_polished_data = {}
        for placeholder, original_text in long_texts.items():
            new_text = polished_dict_raw.get(original_text, original_text)
            final_polished_data[placeholder] = new_text
            
        final_polished_data.update(short_texts)
        return final_polished_data
        
    except Exception as e:
        print(f"Error: {e}")
        extracted_data.update(short_texts)
        return extracted_data

def update_tex_and_save(tex_content_with_placeholders, polished_data, output_path):
    final_content = tex_content_with_placeholders
    for placeholder, text in polished_data.items():
        final_content = final_content.replace(placeholder, text)
        
    with open(output_path, "w", encoding="utf8") as f:
        f.write(final_content)

class StyledLabelFrame(ttk.LabelFrame):
    def __init__(self, master, text, **kwargs):
        super().__init__(master, text=f" {text} ", style="Styled.TLabelframe", **kwargs)
        self.pack_propagate(0)

class ResumeApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("850x850")
        self.root.configure(bg=BG_COLOR)
        self.lang = "zh" 
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        default_font = ("Arial", 10)
        bold_font = ("Arial", 10, "bold")
        
        self.style.configure(".", font=default_font, background=BG_COLOR, foreground=TEXT_COLOR)
        self.style.configure("Styled.TLabelframe", background=SECTION_BG, relief="flat", borderwidth=1, bordercolor=DISABLED_BG)
        self.style.configure("Styled.TLabelframe.Label", font=bold_font, foreground=TEXT_COLOR, background=SECTION_BG)
        self.style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=BG_COLOR, foreground=TEXT_COLOR, font=bold_font, padding=[15, 5])
        self.style.map("TNotebook.Tab", background=[("selected", ACCENT_COLOR)], foreground=[("selected", "white")])
        self.style.configure("Accent.TButton", font=bold_font, foreground="white", background=ACCENT_COLOR, relief="flat", padding=[20, 10])
        self.style.map("Accent.TButton", background=[("active", "#006060")])
        
        self.filepath = ""

        # 顶部栏：标题与语言切换
        top_frame = tk.Frame(root, bg=BG_COLOR)
        top_frame.pack(fill="x", padx=20, pady=10)
        
        self.title_label = tk.Label(top_frame, text=LANG_DICT["title"][self.lang], font=("Arial", 14, "bold"), fg=ACCENT_COLOR, bg=BG_COLOR)
        self.title_label.pack(side="left")
        
        lang_frame = tk.Frame(top_frame, bg=BG_COLOR)
        lang_frame.pack(side="right")
        tk.Label(lang_frame, text="🌐", bg=BG_COLOR).pack(side="left")
        self.lang_cb = ttk.Combobox(lang_frame, values=["中文", "English"], width=8, state="readonly")
        self.lang_cb.current(0)
        self.lang_cb.pack(side="left", padx=5)
        self.lang_cb.bind("<<ComboboxSelected>>", self.switch_language)
        
        self.provider_notebook = ttk.Notebook(root)
        self.provider_notebook.pack(fill="x", padx=20, pady=(0, 5))
        
        self.tabs = {}
        for p in ["Gemini", "ChatGPT", "DeepSeek", "Doubao"]:
            frame = tk.Frame(self.provider_notebook, bg=SECTION_BG, pady=5)
            self.tabs[p] = frame
            self.provider_notebook.add(frame, text=p)
            
        config_parent_frame = tk.Frame(root, bg=BG_COLOR)
        config_parent_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        # 左列：配置与文件
        left_config_frame = tk.Frame(config_parent_frame, bg=BG_COLOR)
        left_config_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.config_section = StyledLabelFrame(left_config_frame, text=LANG_DICT["step1"][self.lang])
        self.config_section.pack(fill="both", expand=True)
        
        inner_config = tk.Frame(self.config_section, bg=SECTION_BG)
        inner_config.pack(padx=15, pady=10, fill="x")
        
        self.api_key_var = tk.StringVar()
        self.lbl_api = tk.Label(inner_config, text=LANG_DICT["api_key"][self.lang], anchor="w", bg=SECTION_BG)
        self.lbl_api.pack(fill="x")
        self.api_entry = tk.Entry(inner_config, textvariable=self.api_key_var, show="*", font=("Courier New", 10), bg=BG_COLOR, relief="flat")
        self.api_entry.pack(fill="x", pady=(2, 5))
        
        self.doubao_id_var = tk.StringVar()
        self.lbl_doubao = tk.Label(inner_config, text=LANG_DICT["doubao_id"][self.lang], anchor="w", bg=SECTION_BG)
        self.doubao_entry = tk.Entry(inner_config, textvariable=self.doubao_id_var, font=("Courier New", 10), bg=BG_COLOR, relief="flat")
        
        self.provider_notebook.bind("<<NotebookTabChanged>>", self.update_api_input_fields)
        
        self.lbl_prompt = tk.Label(inner_config, text=LANG_DICT["prompt_label"][self.lang], anchor="w", bg=SECTION_BG, fg=ACCENT_COLOR, font=("Arial", 9, "bold"))
        self.lbl_prompt.pack(fill="x", pady=(10, 2))
        self.prompt_text = tk.Text(inner_config, height=8, bg=BG_COLOR, relief="flat", wrap="word", font=("Arial", 9))
        self.prompt_text.pack(fill="x")
        self.prompt_text.insert("1.0", DEFAULT_PROMPT_ZH)
        
        self.file_section = StyledLabelFrame(left_config_frame, text=LANG_DICT["step2"][self.lang])
        self.file_section.pack(fill="both", expand=True, pady=(10, 0))
        
        inner_file = tk.Frame(self.file_section, bg=SECTION_BG)
        inner_file.pack(padx=15, pady=10, fill="both", expand=True)
        
        self.drop_area = tk.Label(inner_file, text=LANG_DICT["drop_text"][self.lang], bg=BG_COLOR, font=("Arial", 11, "bold"), fg=ACCENT_COLOR, width=25, height=3, relief="groove", borderwidth=2)
        self.drop_area.pack(pady=5)
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.handle_drop)
        
        self.btn_browse = tk.Button(inner_file, text=LANG_DICT["browse"][self.lang], command=self.browse_tex_file, font=("Arial", 9), relief="flat", bg=DISABLED_BG, fg=TEXT_COLOR, padx=10, pady=3)
        self.btn_browse.pack(pady=(0, 5))
        
        self.lbl_file_status = tk.Label(inner_file, text=LANG_DICT["no_file"][self.lang], fg="gray", anchor="w", bg=SECTION_BG, font=("Arial", 9))
        self.lbl_file_status.pack(fill="x")
        
        # 右列：内容定义区
        right_parent_frame = tk.Frame(config_parent_frame, bg=BG_COLOR)
        right_parent_frame.pack(side="right", fill="both", expand=True)
        
        self.jd_section = StyledLabelFrame(right_parent_frame, text=LANG_DICT["step3"][self.lang])
        self.jd_section.pack(fill="both", expand=True)
        
        inner_jd = tk.Frame(self.jd_section, bg=SECTION_BG)
        inner_jd.pack(padx=15, pady=10, fill="both", expand=True)
        
        ocr_row = tk.Frame(inner_jd, bg=SECTION_BG)
        ocr_row.pack(fill="x", pady=(0, 5))
        
        self.btn_ocr = tk.Button(ocr_row, text=LANG_DICT["ocr_btn"][self.lang], command=self.extract_jd_from_image, bg="#2196F3", fg="white", font=("Arial", 9, "bold"), relief="flat", padx=10, pady=3)
        self.btn_ocr.pack(side="right")
        
        self.jd_scroll = ttk.Scrollbar(inner_jd)
        self.jd_scroll.pack(side="right", fill="y")
        self.jd_text = tk.Text(inner_jd, height=14, bg=BG_COLOR, relief="flat", yscrollcommand=self.jd_scroll.set, wrap="word")
        self.jd_text.pack(side="left", fill="both", expand=True)
        self.jd_scroll.config(command=self.jd_text.yview)
        
        self.skills_section = StyledLabelFrame(right_parent_frame, text=LANG_DICT["step4"][self.lang])
        self.skills_section.pack(fill="both", expand=True, pady=(10, 0))
        
        inner_skills = tk.Frame(self.skills_section, bg=SECTION_BG)
        inner_skills.pack(padx=15, pady=10, fill="both", expand=True)
        
        self.skills_scroll = ttk.Scrollbar(inner_skills)
        self.skills_scroll.pack(side="right", fill="y")
        self.skills_text = tk.Text(inner_skills, height=6, bg=BG_COLOR, relief="flat", yscrollcommand=self.skills_scroll.set, wrap="word")
        self.skills_text.pack(side="left", fill="both", expand=True)
        self.skills_scroll.config(command=self.skills_text.yview)
        
        bottom_frame = tk.Frame(root, bg=BG_COLOR)
        bottom_frame.pack(fill="x", side="bottom", pady=15)
        
        self.btn_run = ttk.Button(bottom_frame, text=LANG_DICT["run_btn"][self.lang], command=self.start_processing, style="Accent.TButton")
        self.btn_run.pack()
        
        self.status_bar = tk.Frame(root, bg=SECTION_BG, relief="groove", borderwidth=1)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_label = tk.Label(self.status_bar, text=LANG_DICT["status_ready"][self.lang], font=("Arial", 9), fg=TEXT_COLOR, bg=SECTION_BG, anchor="w", padx=10)
        self.status_label.pack(fill="x")
        
        self.update_api_input_fields(None)

    def switch_language(self, event):
        selection = self.lang_cb.get()
        self.lang = "zh" if selection == "中文" else "en"
        
        self.root.title(LANG_DICT["title"][self.lang])
        self.title_label.config(text=LANG_DICT["title"][self.lang])
        self.config_section.config(text=f" {LANG_DICT['step1'][self.lang]} ")
        self.lbl_api.config(text=LANG_DICT["api_key"][self.lang])
        self.lbl_doubao.config(text=LANG_DICT["doubao_id"][self.lang])
        self.lbl_prompt.config(text=LANG_DICT["prompt_label"][self.lang])
        
        self.file_section.config(text=f" {LANG_DICT['step2'][self.lang]} ")
        if not self.filepath:
            self.drop_area.config(text=LANG_DICT["drop_text"][self.lang])
            self.lbl_file_status.config(text=LANG_DICT["no_file"][self.lang])
        self.btn_browse.config(text=LANG_DICT["browse"][self.lang])
        
        self.jd_section.config(text=f" {LANG_DICT['step3'][self.lang]} ")
        self.btn_ocr.config(text=LANG_DICT["ocr_btn"][self.lang])
        self.skills_section.config(text=f" {LANG_DICT['step4'][self.lang]} ")
        self.btn_run.config(text=LANG_DICT["run_btn"][self.lang])
        self.status_label.config(text=LANG_DICT["status_ready"][self.lang])
        
        current_prompt = self.prompt_text.get("1.0", tk.END).strip()
        if current_prompt == DEFAULT_PROMPT_ZH.strip() or current_prompt == DEFAULT_PROMPT_EN.strip():
            self.prompt_text.delete("1.0", tk.END)
            self.prompt_text.insert("1.0", DEFAULT_PROMPT_ZH if self.lang == "zh" else DEFAULT_PROMPT_EN)

    def get_current_provider(self):
        tab_id = self.provider_notebook.select()
        return self.provider_notebook.tab(tab_id, "text")

    def update_api_input_fields(self, event):
        provider = self.get_current_provider()
        if provider == "Doubao":
            self.lbl_doubao.pack(fill="x", pady=(5, 0))
            self.doubao_entry.pack(fill="x", pady=(2, 5))
        else:
            self.lbl_doubao.pack_forget()
            self.doubao_entry.pack_forget()

    def update_file_status(self, path):
        if path:
            filename = path.split('/')[-1] if '/' in path else path.split('\\')[-1]
            self.lbl_file_status.config(text=f"Loaded: {filename}", fg=ACCENT_COLOR, font=("Arial", 10, "bold"))
            self.drop_area.config(bg="#c8e6c9", text="✅", fg="#333333")
        else:
            self.lbl_file_status.config(text=LANG_DICT["no_file"][self.lang], fg="gray", font=("Arial", 9))
            self.drop_area.config(bg=BG_COLOR, text=LANG_DICT["drop_text"][self.lang], fg=ACCENT_COLOR)

    def handle_drop(self, event):
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        if file_path.lower().endswith('.tex'):
            self.filepath = file_path
            self.update_file_status(file_path)

    def browse_tex_file(self):
        path = filedialog.askopenfilename(filetypes=[("TeX Files", "*.tex")])
        if path:
            self.filepath = path
            self.update_file_status(path)

    def extract_jd_from_image(self):
        provider = self.get_current_provider()
        api_key = self.api_key_var.get().strip()
        
        if not api_key:
            messagebox.showwarning("Warning", LANG_DICT["warn_api"][self.lang])
            return
            
        img_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if not img_path: return
            
        self.status_label.config(text="Processing OCR...", fg="#FF9800")
        self.root.update()
        
        try:
            if provider == "Gemini":
                from PIL import Image
                img = Image.open(img_path)
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=["Extract all text. Output text only.", img]
                )
                extracted_text = response.text.strip()
            elif provider == "ChatGPT":
                from openai import OpenAI
                with open(img_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": "Extract all text. Output text only."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]}]
                )
                extracted_text = response.choices[0].message.content.strip()
            else:
                messagebox.showwarning("Warning", "OCR only supports Gemini or ChatGPT.")
                return
                
            self.jd_text.delete("1.0", tk.END)
            self.jd_text.insert(tk.END, extracted_text)
            self.status_label.config(text="OCR Complete", fg="green")
            
        except Exception as e:
            self.status_label.config(text="OCR Failed", fg="red")
            messagebox.showerror("Error", str(e))

    def start_processing(self):
        provider = self.get_current_provider()
        api_key = self.api_key_var.get().strip()
        doubao_id = self.doubao_id_var.get().strip()
        custom_prompt = self.prompt_text.get("1.0", tk.END).strip()
        
        if not api_key:
            messagebox.showwarning("Warning", LANG_DICT["warn_api"][self.lang])
            return
        if not self.filepath:
            messagebox.showwarning("Warning", LANG_DICT["warn_file"][self.lang])
            return
            
        jd = self.jd_text.get("1.0", tk.END).strip()
        skills = self.skills_text.get("1.0", tk.END).strip()
        
        if not jd:
            messagebox.showwarning("Warning", LANG_DICT["warn_jd"][self.lang])
            return
            
        self.status_label.config(text=LANG_DICT["processing"][self.lang], fg="#FF9800")
        self.root.update()
        
        try:
            with open(self.filepath, "r", encoding="utf8") as f:
                original_tex = f.read()
                
            tex_with_placeholders, extracted_data = process_tex_content(original_tex)
            final_data = filter_and_polish(provider, api_key, doubao_id, custom_prompt, extracted_data, jd, skills)
            
            output_path = self.filepath.replace(".tex", "_polished.tex")
            update_tex_and_save(tex_with_placeholders, final_data, output_path)
            
            self.status_label.config(text=LANG_DICT["success"][self.lang], fg="green")
            messagebox.showinfo("Success", f"File saved to:\n{output_path}")
            
        except Exception as e:
            self.status_label.config(text="Error occurred", fg="red")
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ResumeApp(root)
    root.mainloop()