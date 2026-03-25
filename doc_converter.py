import doc_parser 
import re

def convert_to_tex(provider, api_key, doubao_id, filepath, mode="auto", template_content="", target_lang="English", target_pages="自动", allow_pruning=False):
    raw_text = doc_parser.extract_text(filepath)
    if not raw_text.strip():
        return False, "未能从文件中提取到有效文本，请检查文件内容是否为空。"

    prune_rule = "允许大幅删减：你可以直接删除与JD或目标岗位完全无关的冗长经历，并极度精简啰嗦的句子。" if allow_pruning else "严禁删除：你必须将提取到的所有经历毫无保留地放进模板中，只需润色表达。"
    
    if target_pages == "1 Page":
        page_rule = "The target is a 1 page resume. Condense all content to be extremely concise, keeping only the most high impact achievements."
    elif target_pages == "2 Pages":
        page_rule = "The target is a 2 page resume. Provide more detailed context and quantified results while maintaining relevance."
    else:
        page_rule = "Balance the length naturally based on the input content."

    if mode == "template":
        prompt = f"""
        你是一个精通 LaTeX 排版的顶级简历撰写专家。
        你的任务是将提取到的凌乱的简历原始文本，精准地填入我提供的 LaTeX 模板中。
        重要指令：请务必将生成的简历正文内容翻译并输出为 {target_lang}。

        绝对执行指令：
        1. 篇幅与删减：{prune_rule} {page_rule}
        2. 页眉信息精确提取：请特别关注原始文本开头的个人联系信息并填入模板占位符中。
        3. LaTeX 安全：必须对所有原始文本中的 LaTeX 特殊字符进行标准转义。

        提取出的原始简历文本：
        {raw_text}

        提供的专属 LaTeX 模板：
        {template_content}

        请只输出最终的、无 Markdown 标记的完整 LaTeX 代码。
        """
    else:
        prompt = f"""
        你是一个精通 LaTeX 排版的顶级专家。
        请根据以下提取出的简历纯文本，从零开始编写一份结构清晰、排版专业且符合 documentclass 以及 document 环境的标准 LaTeX 简历源码。
        重要指令：请务必将生成的简历内容翻译并输出为 {target_lang}。
        
        执行要求：
        1. 篇幅与精简：{prune_rule} {page_rule}
        2. 请特别关注并提取文本中的核心页眉信息并在显著位置排版。
        
        请只输出最终的 LaTeX 源码，不要包含任何 Markdown 标记。

        提取出的原始简历内容：
        {raw_text}
        """

    try:
        if provider == "Gemini":
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            result_text = response.text
        else:
            from openai import OpenAI
            if provider == "ChatGPT":
                client = OpenAI(api_key=api_key)
                model_name = "gpt-4o-mini"
            elif provider == "DeepSeek":
                client = OpenAI(api_key=api_key, base_url="[https://api.deepseek.com](https://api.deepseek.com)")
                model_name = "deepseek-chat"
            elif provider == "Doubao":
                client = OpenAI(api_key=api_key, base_url="[https://ark.cn-beijing.volces.com/api/v3](https://ark.cn-beijing.volces.com/api/v3)")
                model_name = doubao_id
                
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            result_text = response.choices[0].message.content
        
        result_text = result_text.strip()
        cleaned_text = re.sub(r'^```latex\n', '', result_text)
        cleaned_text = re.sub(r'^```\n', '', cleaned_text)
        cleaned_text = re.sub(r'\n```$', '', cleaned_text)
        cleaned_text = re.sub(r'```$', '', cleaned_text)
            
        return True, cleaned_text.strip()
        
    except Exception as e:
        return False, f"代码转换过程中发生意外错误: {e}"