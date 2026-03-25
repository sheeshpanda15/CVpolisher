import json

def process_and_polish(provider, api_key, doubao_id, extracted_texts, job_description, skills_db, target_lang="English", target_pages="自动", allow_pruning=False):
    if not extracted_texts:
        return {}, []
        
    # 判断是否提供了有效的 JD (字符长度大于5算作有效)
    has_jd = bool(job_description and len(job_description.strip()) > 5)
    
    if has_jd:
        # 模式A：有 JD，执行严格匹配和暴力裁剪
        jd_instruction = f"Target JD: {job_description}"
        task_instruction = "Transform a messy, poorly written resume into a high impact, professional document strictly aligned with the target Job Description (JD)."
        
        if allow_pruning:
            prune_rule = "You have absolute authority to delete early experiences or minor responsibilities completely unrelated to the JD, and to drastically streamline wordy descriptions. You must seriously and strictly ensure past experiences match the JD requirements. If any irrelevant content is found, it must be firmly deleted. To highly align with the JD, you may appropriately package or reasonably supplement missing key details."
        else:
            prune_rule = "Do not delete any experience content. Only polish and professionalize the expression to align logically with the JD."
            
    else:
        # 模式B：无 JD，降级为高质量翻译与基础润色
        jd_instruction = "Target JD: [NOT PROVIDED]"
        task_instruction = "Translate the provided resume content accurately into the target language and perform baseline professional polishing. DO NOT alter the core facts."
        prune_rule = "NO PRUNING ALLOWED. Because no JD is provided, you must keep all original information intact. Only focus on high quality translation and professional phrasing without deleting any details."

    if target_pages == "1 Page":
        page_rule = "The target is a 1 page resume. Condense all content to be extremely concise, keeping only the most high impact achievements."
    elif target_pages == "2 Pages":
        page_rule = "The target is a 2 page resume. Provide more detailed context and quantified results while maintaining relevance."
    else:
        page_rule = "Balance the length naturally based on the input content."

    prompt = f"""
    ROLE: Senior Executive Headhunter & LaTeX Expert.
    TASK: {task_instruction}

    CORE DIRECTIVES:
    1. CRITICAL RESTRUCTURING: Do not just "polish". If the original content is unprofessional or vague, REWRITE it entirely using professional terminology.
    2. ACTION RESULT ORIENTATION: Force every bullet point to follow the STAR method (Situation, Task, Action, Result). Use strong action verbs (e.g., Spearheaded, Engineered, Orchestrated).
    3. PRUNING RULE: {prune_rule}
    4. LENGTH CONTROL: {page_rule}
    5. LATEX SAFETY: Ensure all special characters are escaped. Output MUST be valid LaTeX code segments.
    
    TARGET LANGUAGE: {target_lang} (Translate all resume content into this language).

    INPUT DATA:
    * Raw Content: {extracted_texts}
    * {jd_instruction}
    * Skills DB: {skills_db}

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