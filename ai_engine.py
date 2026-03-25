import json

def process_and_polish(provider, api_key, doubao_id, extracted_texts, job_description, skills_db, target_lang="English", target_pages="自动", allow_pruning=False):
    if not extracted_texts:
        return {}, []
        
    prune_rule = "你有绝对的权力删除与 JD 完全无关的早期经历或次要职责，并大刀阔斧地精简啰嗦的描述。必须严肃的，严格的，确认过往的经历和学术内容与JD中要求的技能和经验相匹配。一旦发现有一点不同或者不相关的内容，必须坚决删除。如果实在不想删除，可以添加内容，甚至在一定程度上伪造内容以满足JD要求。" if allow_pruning else "只需润色和专业化表达。"
    
    if target_pages == "1页 (极简)":
        page_rule = "目标是 1 页纸或者更少的简历，请将所有经历的总字数严格压缩在极短的篇幅内，只保留最核心的 STAR 法则成果。"
    elif target_pages == "2页 (丰富)":
        page_rule = "目标是 2 页纸简历，可以在保证相关性的前提下提供充足的细节。"
    else:
        page_rule = "请根据内容自然输出，不强制限制篇幅。"

    prompt = f"""
    ROLE: Senior Executive Headhunter & LaTeX Expert.
    TASK: Transform a messy, poorly-written resume into a high-impact, professional document aligned with the target Job Description (JD).

    CORE DIRECTIVES:
    1. CRITICAL RESTRUCTURING: Do not just "polish". If the original content is unprofessional or vague, REWRITE it entirely using professional terminology.
    2. ACTION-RESULT ORIENTATION: Force every bullet point to follow the STAR method (Situation, Task, Action, Result). Use strong action verbs (e.g., Spearheaded, Engineered, Orchestrated).
    3. RUTHLESS PRUNING: {prune_rule} Eliminate subjective fluff and irrelevant filler.
    4. LENGTH CONTROL: {page_rule}
    5. LATEX SAFETY: Ensure all special characters are escaped. Output MUST be valid LaTeX code segments.
    
    TARGET LANGUAGE: {target_lang} (Translate all resume content into this language).

    INPUT DATA:
    - Raw Content: {extracted_texts}
    - Target JD: {job_description}
    - Skills DB: {skills_db}

    OUTPUT FORMAT: Return a strict JSON object with "polished_data" (mapping original to rewritten) and "new_skills".
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