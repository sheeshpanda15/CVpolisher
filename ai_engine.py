import json

def process_and_polish(provider, api_key, doubao_id, extracted_texts, job_description, skills_db, target_lang="English", target_pages="自动", allow_pruning=False):
    if not extracted_texts:
        return {}, []
        
    prune_rule = "你有绝对的权力删除与 JD 完全无关的早期经历或次要职责，并大刀阔斧地精简啰嗦的描述。" if allow_pruning else "绝对不要删除任何经历内容，只需润色和专业化表达。"
    
    if target_pages == "1页 (极简)":
        page_rule = "目标是 1 页纸简历，请将所有经历的总字数严格压缩在极短的篇幅内，只保留最核心的 STAR 法则成果。"
    elif target_pages == "2页 (丰富)":
        page_rule = "目标是 2 页纸简历，可以在保证相关性的前提下提供充足的细节。"
    else:
        page_rule = "请根据内容自然输出，不强制限制篇幅。"

    prompt = f"""
    你是一个顶级HR。请根据职位需求(JD)，优化我的简历经历。
    重要指令：请务必将润色后的简历内容全部使用 {target_lang} 输出。
    
    【篇幅与删减规则】：
    1. {prune_rule}
    2. {page_rule}
    
    你必须输出一个严格的 JSON 对象，包含两个顶级键：
    1. "polished_data": 一个字典。键为我提供的原经历文本，值为润色后的 {target_lang} 文本。请严格转义 LaTeX 特殊字符。
    2. "new_skills": 一个数组。请分析 JD，提取缺失的技能成为简短的 {target_lang} 词组放入此数组。如果足够匹配，请返回空数组 []。
    
    职位需求 (JD)：
    {job_description}
    
    现有技能库：
    {skills_db}
    
    需要润色的经历：
    {extracted_texts}
    """
    
    try:
        if provider == "Gemini":
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
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
                messages=[{"role": "user", "content": prompt}]
            )
            raw_text = response.choices[0].message.content
            
        raw_text = raw_text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        result = json.loads(raw_text.strip())
        polished_data = result.get("polished_data", {})
        new_skills = result.get("new_skills", [])
        
        return polished_data, new_skills
        
    except Exception as e:
        print(f"AI 调用失败: {e}")
        return {}, []