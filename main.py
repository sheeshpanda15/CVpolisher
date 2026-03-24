import re
import json
from google import genai
from google.genai import types

# 初始配置：请务必替换为你的真实 API Key
client = genai.Client(api_key="API")

def process_tex_content(tex_content):
    # 匹配自定义包裹命令和普通item
    pattern_resume = r"\\resumeItem\{(.*?)\}"
    pattern_item = r"\\item\s+(.*?)(?=\\item|\\end\{)"
    
    # 占位符模板，用于安全隔离 LaTeX 代码
    placeholder_template = "[[EXP_{}]]"
    extracted_data = {}
    counter = 0
    
    # 替换 \resumeItem 的逻辑
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
    
    # 替换 \item 的逻辑
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

def filter_and_polish(extracted_data, job_description, skills_db):
    short_texts = {}
    long_texts = {}
    
    # 智能分类：增加冒号识别规则
    for placeholder, text in extracted_data.items():
        word_count = len(text.split())
        # 如果包含英文冒号、中文冒号，或者单词数少于5个，直接跳过不改
        if ":" in text or "：" in text or word_count < 5:
            short_texts[placeholder] = text
        else:
            long_texts[placeholder] = text
            
    if not long_texts:
        print("没有找到需要润色的长句结构。")
        return short_texts
        
    # 构造带有严格转义指令的 Prompt
    prompt = f"""
   你是一个资深且专业的HR。请根据以下职位需求和技能库，使用专业的职场英文重新润色我的简历经历。
    确保我的经历内容与职位需求高度相关，并且突出我的技能优势。 
    不要删除任何经历内容，只需润色并优化表达。请确保输出的JSON格式正确，且所有原经历都包含在内。尽量不要修改原本的格式和结构，只需提升语言质量和专业度。    
    严格按照职位要求中的技能库来润色经历，确保每条经历都能体现相关技能。请务必保持原经历的完整性，不要删除任何内容，只需优化表达方式。  
    如果原文中只是单个的词语或者词组描述，如果识别到它只是一个技能，则尽可能不要修改它，除非它的表达方式非常不专业或者不清晰。请确保润色后的文本既专业又自然，同时保持原经历的核心信息不变。    
    
    
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
        print("正在调用大模型进行润色，请稍候...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        
        polished_dict_raw = json.loads(response.text)
        
        # 将润色结果重新映射回占位符字典
        final_polished_data = {}
        for placeholder, original_text in long_texts.items():
            new_text = polished_dict_raw.get(original_text, original_text)
            final_polished_data[placeholder] = new_text
            
        # 合并安全保留的短句和润色后的长句
        final_polished_data.update(short_texts)
        return final_polished_data
        
    except Exception as e:
        print(f"调用大模型API时发生错误: {e}")
        # 发生意外错误时，将原文本安全退回，防止文件损坏
        extracted_data.update(short_texts)
        return extracted_data
    short_texts = {}
    long_texts = {}
    
    # 智能长度分类：通过切分空格计算单词数
    for placeholder, text in extracted_data.items():
        word_count = len(text.split())
        # 如果单词数少于5个，判定为技能短语或专有名词，直接跳过
        if word_count < 5:
            short_texts[placeholder] = text
        else:
            long_texts[placeholder] = text
            
    if not long_texts:
        print("没有找到需要润色的长句结构。")
        return short_texts
        
    # 构造带有严格转义指令的 Prompt
    prompt = f"""
    你是一个资深且专业的HR。请根据以下职位需求和技能库，使用专业的职场英文重新润色我的简历经历。
    
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
        print("正在调用大模型进行润色，请稍候...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        
        polished_dict_raw = json.loads(response.text)
        
        # 将润色结果重新映射回占位符字典
        final_polished_data = {}
        for placeholder, original_text in long_texts.items():
            new_text = polished_dict_raw.get(original_text, original_text)
            final_polished_data[placeholder] = new_text
            
        # 合并安全保留的短句和润色后的长句
        final_polished_data.update(short_texts)
        return final_polished_data
        
    except Exception as e:
        print(f"调用大模型API时发生错误: {e}")
        # 发生意外错误时，将原文本安全退回，防止文件损坏
        extracted_data.update(short_texts)
        return extracted_data

def update_tex_and_save(tex_content_with_placeholders, polished_data, output_path):
    final_content = tex_content_with_placeholders
    # 遍历字典，将占位符替换为最终文本
    for placeholder, text in polished_data.items():
        final_content = final_content.replace(placeholder, text)
        
    with open(output_path, "w", encoding="utf8") as f:
        f.write(final_content)
    print("简历已成功更新并保存至：", output_path)

def main():
    try:
        with open("resume.tex", "r", encoding="utf8") as f:
            original_tex = f.read()
    except FileNotFoundError:
        print("错误：找不到 resume.tex 文件，请确认文件路径。")
        return
        
    # 测试用的求职JD和个人技能库
    job_desc = "Need a full stack developer familiar with Python, frontend frameworks, and database optimization."
    skills = "Python, JavaScript, React, PostgreSQL, Docker"
    
    # 步骤一：提取文本并植入占位符
    tex_with_placeholders, extracted_data = process_tex_content(original_tex)
    print(f"共提取到 {len(extracted_data)} 条经历或技能。")
    
    # 步骤二：智能分类并交给AI处理长句
    final_data = filter_and_polish(extracted_data, job_desc, skills)
    
    # 步骤三：精准替换并输出文件
    output_path = "resume_polished.tex"
    update_tex_and_save(tex_with_placeholders, final_data, output_path)

if __name__ == "__main__":
    main()