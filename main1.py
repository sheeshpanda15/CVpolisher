import re
import json
import google.generativeai as genai

def extract_experience_from_tex(tex_content):
    # 规则一：匹配自定义的包裹命令
    pattern_resume = r"\\resumeItem\{(.*?)\}"
    matches_resume = re.findall(pattern_resume, tex_content, re.DOTALL)
    
    # 规则二：匹配普通的 item 命令
    # 逻辑：寻找 item 后面的内容，直到遇到下一个 item 或者遇到 end 环境结束符为止
    pattern_item = r"\\item\s+(.*?)(?=\\item|\\end\{)"
    matches_item = re.findall(pattern_item, tex_content, re.DOTALL)
    
    # 将两种规则提取到的原始结果合并在一起
    all_matches = matches_resume + matches_item
    
    # 核心优化：清理文本
    # 去除首尾多余的空白字符和换行符，这能极大提高后续大模型处理和替换的成功率
    cleaned_matches = []
    for text in all_matches:
        clean_text = text.strip()
        if clean_text:
            cleaned_matches.append(clean_text)
            
    return cleaned_matches




# 配置你的专属 API Key
# 请前往 Google AI Studio 免费获取
genai.configure(api_key="AIzaSyDLDAGIHd2wkxfthmUCYkzzr-LUy-IwpCQ")

def call_llm_to_polish(experiences, job_description, skills_db):
    # 初始化模型，处理文本推荐使用反应迅速的版本
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 构建结构化的Prompt
    prompt = f"""
    你是一个资深且专业的HR。请根据以下职位需求和技能库，使用专业的职场英文重新润色我的简历经历。
    必须严格输出JSON格式，键为原文本，值为润色后的英文文本。确保我的经历内容与职位需求高度相关，并且突出我的技能优势。 
    不要删除任何经历内容，只需润色并优化表达。请确保输出的JSON格式正确，且所有原经历都包含在内。尽量不要修改原本的格式和结构，只需提升语言质量和专业度。    
    严格按照职位要求中的技能库来润色经历，确保每条经历都能体现相关技能。请务必保持原经历的完整性，不要删除任何内容，只需优化表达方式。  
    如果原文中只是单个的词语或者词组描述，如果识别到它只是一个技能，则尽可能不要修改它，除非它的表达方式非常不专业或者不清晰。请确保润色后的文本既专业又自然，同时保持原经历的核心信息不变。    
    
    职位需求：
    {job_description}
    
    技能库：
    {skills_db}
    
    原经历列表：
    {experiences}
    """
    
    try:
        # 发起网络请求，并强制要求模型返回JSON格式
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        
        # 将返回的JSON字符串解析为Python字典
        polished_dict = json.loads(response.text)
        return polished_dict
        
    except Exception as e:
        print(f"调用大模型API时发生错误: {e}")
        # 如果发生网络错误或解析错误，生成一个键值相同的安全字典原样返回
        # 这样可以防止程序崩溃或误删原文
        fallback_dict = {}
        for exp in experiences:
            fallback_dict[exp] = exp
        return fallback_dict

def update_tex_and_save(tex_content, polished_dict, output_path):
    updated_content = tex_content
    for old_text, new_text in polished_dict.items():
        # 注意：这里直接替换，如果遇到特殊的LaTeX转义字符需要额外处理
        updated_content = updated_content.replace(old_text, new_text)
        
    with open(output_path, "w", encoding="utf8") as f:
        f.write(updated_content)
    print("简历已成功更新并保存至：", output_path)

def main():
    with open("resume.tex", "r", encoding="utf8") as f:
        sample_tex = f.read()
    
    job_desc = "Need a full stack developer familiar with Python, frontend frameworks, and database optimization."
    skills = "Python, JavaScript, React, PostgreSQL, Docker"
    
    # 提取文本
    extracted_texts = extract_experience_from_tex(sample_tex)
    print("提取到的经历：", extracted_texts)
    
    # 交给AI润色
    polished_data = call_llm_to_polish(extracted_texts, job_desc, skills)
    print("AI润色结果：", polished_data)
    
    # 替换回原文件并保存
    output_path = "resume_polished.tex"
    update_tex_and_save(sample_tex, polished_data, output_path)

if __name__ == "__main__":
    main()