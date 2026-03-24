import re
import json
import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from google import genai
from google.genai import types

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

def filter_and_polish(client, extracted_data, job_description, skills_db):
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
        
    prompt = f"""
    你是一个资深且专业的HR。请根据以下职位需求和技能库，使用专业的职场英文重新润色我的简历经历。
    确保我的经历内容与职位需求高度相关，并且突出我的技能优势。
    不要删除任何经历内容，只需润色并优化表达。请确保输出的JSON格式正确，且所有原经历都包含在内。
    严格按照职位要求中的技能库来润色经历，确保每条经历都能体现相关技能。
    如果原文中只是单个的词语或者词组描述，如果识别到它只是一个技能，则尽可能不要修改它。
    
    绝对执行规则：
    1. 必须严格输出JSON格式，键为原文本，值为润色后的英文文本。
    2. 你的润色结果必须对所有的LaTeX特殊字符（如 &, %, $, #, _, {{, }}）进行标准转义，例如将 & 改为 \\&，防止编译出错。
    3. 保持客观专业，突出与职位相关的数据和成果。
    
    职位需求：
    {job_description}
    
    技能库：
    {skills_db}
    
    需要润色的经历列表：
    {list(long_texts.values())}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        polished_dict_raw = json.loads(response.text)
        
        final_polished_data = {}
        for placeholder, original_text in long_texts.items():
            new_text = polished_dict_raw.get(original_text, original_text)
            final_polished_data[placeholder] = new_text
            
        final_polished_data.update(short_texts)
        return final_polished_data
        
    except Exception as e:
        print(f"调用出错: {e}")
        extracted_data.update(short_texts)
        return extracted_data

def update_tex_and_save(tex_content_with_placeholders, polished_data, output_path):
    final_content = tex_content_with_placeholders
    for placeholder, text in polished_data.items():
        final_content = final_content.replace(placeholder, text)
        
    with open(output_path, "w", encoding="utf8") as f:
        f.write(final_content)

class ResumeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI 简历自动润色神器")
        self.root.geometry("650x850")
        
        self.filepath = ""
        
        # 1. API Key 输入区
        tk.Label(root, text="第一步：输入你的专属 API Key", font=("Arial", 10, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        self.api_entry = tk.Entry(root, width=80, show="*")
        self.api_entry.pack(padx=20)
        
        # 2. 文件拖拽区
        tk.Label(root, text="第二步：将 .tex 简历文件拖入下方灰色区域", font=("Arial", 10, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        self.drop_area = tk.Label(root, text="请将 .tex 文件拖拽到这里\n(支持直接拖放)", bg="#e8e8e8", width=80, height=4, relief="groove")
        self.drop_area.pack(padx=20)
        
        # 绑定拖拽事件
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.handle_drop)
        
        self.file_label = tk.Label(root, text="当前状态：还未放入文件", fg="gray")
        self.file_label.pack(pady=5)
        
        # 3. 职位需求区
        tk.Label(root, text="第三步：粘贴目标岗位的职位需求 (JD)", font=("Arial", 10, "bold")).pack(anchor="w", padx=20, pady=(10, 5))
        self.jd_text = tk.Text(root, height=10, width=80)
        self.jd_text.pack(padx=20)
        
        # 4. 技能库区
        tk.Label(root, text="第四步：粘贴你的个人技能库 (Skills)", font=("Arial", 10, "bold")).pack(anchor="w", padx=20, pady=(10, 5))
        self.skills_text = tk.Text(root, height=6, width=80)
        self.skills_text.pack(padx=20)
        
        # 5. 运行按钮
        self.run_btn = tk.Button(root, text="开始智能润色并生成新简历", command=self.start_processing, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), pady=5)
        self.run_btn.pack(pady=25)
        
        # 状态提示
        self.status_label = tk.Label(root, text="准备就绪", fg="blue", font=("Arial", 10))
        self.status_label.pack()

    def handle_drop(self, event):
        file_path = event.data
        # 兼容 Windows 拖拽路径可能带大括号的情况
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
            
        if file_path.lower().endswith('.tex'):
            self.filepath = file_path
            self.file_label.config(text=f"已成功加载: {self.filepath}", fg="green")
            self.drop_area.config(bg="#c8e6c9", text="文件已就绪")
        else:
            messagebox.showerror("格式错误", "请严格放入以 .tex 结尾的 LaTeX 源文件！")

    def start_processing(self):
        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showwarning("警告", "请先在最上方输入你的 API Key！")
            return
            
        if not self.filepath:
            messagebox.showwarning("警告", "请先将 tex 文件拖入指定区域！")
            return
            
        jd = self.jd_text.get("1.0", tk.END).strip()
        skills = self.skills_text.get("1.0", tk.END).strip()
        
        if not jd or not skills:
            messagebox.showwarning("警告", "职位需求和技能库不能为空！")
            return
            
        self.status_label.config(text="正在提取文本并呼叫大模型，请耐心等待...", fg="#FF9800")
        self.root.update()
        
        try:
            # 动态实例化 API 客户端
            client = genai.Client(api_key=api_key)
            
            with open(self.filepath, "r", encoding="utf8") as f:
                original_tex = f.read()
                
            tex_with_placeholders, extracted_data = process_tex_content(original_tex)
            
            final_data = filter_and_polish(client, extracted_data, jd, skills)
            
            output_path = self.filepath.replace(".tex", "_polished.tex")
            update_tex_and_save(tex_with_placeholders, final_data, output_path)
            
            self.status_label.config(text="润色完成！新文件已保存在原目录下。", fg="green")
            messagebox.showinfo("成功", f"恭喜！简历润色完毕。\n新文件已安全保存至:\n{output_path}")
            
        except Exception as e:
            self.status_label.config(text="发生错误，请查看弹窗提示。", fg="red")
            messagebox.showerror("运行错误", f"处理过程中发生异常:\n{e}")

if __name__ == "__main__":
    # 使用支持拖拽的 Tk 对象
    root = TkinterDnD.Tk()
    app = ResumeApp(root)
    root.mainloop()