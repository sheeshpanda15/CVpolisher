import os
import zipfile
import shutil
import re
import uuid

# 全局临时工作目录前缀
TEMP_DIR_PREFIX = "tex_pipeline_tmp_"

class TemplateProject:
    def __init__(self, temp_dir_path, main_tex_path):
        self.root_dir = temp_dir_path
        self.main_tex_file = main_tex_path

def identify_main_tex(directory):
    """
    智能寻路引擎：在解压后的文件夹里自动识别出主 TeX 源码骨架文件。
    优先级逻辑：
    1. 寻找带有 \\begin{document} 的文件
    2. 寻找带有标准简历名称的文件 (main, cv, resume, awesome-cv)
    3. 排除那些明显的 cls, sty 或其关联数据文件
    """
    
    potential_mains = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.tex'):
                full_path = os.path.join(root, file)
                try:
                    # 读取一小段内容进行语义分析
                    with open(full_path, "r", errors='ignore') as f:
                        content_sample = f.read(2048) # 读取前2KB
                        
                        # 强信号：包含 document 环境
                        if r"\begin{document}" in content_sample:
                            potential_mains.append((full_path, 10))
                        
                        # 中等信号：标准命名且不是宏包声明
                        elif file.lower() in ['main.tex', 'cv.tex', 'resume.tex', 'awesome-cv.tex']:
                            if r"\documentclass" not in content_sample: # 有些 cls 只是声明但不是主文件
                                potential_mains.append((full_path, 5))
                                
                except Exception:
                    pass
    
    if not potential_mains:
        return None
        
    # 根据优先级评分排序，返回评分最高的文件
    potential_mains.sort(key=lambda x: x[1], reverse=True)
    return potential_mains[0][0]

def prepare_template_injection(zip_path):
    """
    智能解压与环境隔离引擎：
    1. 在原目录旁边建立临时隔离区。
    2. 解压 Overleaf 工程包。
    3. 找到主文件路径并封装。
    """
    try:
        # 获取原 zip 所在目录和基础文件名，用于建立临时文件夹
        source_dir = os.path.dirname(zip_path)
        base_name = os.path.splitext(os.path.basename(zip_path))[0]
        
        # 建立全局唯一的临时文件夹名
        unique_id = str(uuid.uuid4())[:8]
        tmp_dir_name = f"{TEMP_DIR_PREFIX}{base_name}_{unique_id}"
        temp_working_dir = os.path.join(source_dir, tmp_dir_name)
        
        # 如果临时目录存在则删除，确保环境纯净
        if os.path.exists(temp_working_dir):
            shutil.rmtree(temp_working_dir)
            
        os.makedirs(temp_working_dir, exist_ok=True)
        
        # 1. 执行智能解压 (安全模式，防止 ZIP 炸弹)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_working_dir)
            
        # 2. 执行智能寻路：找到主 tex 文件
        main_tex_file = identify_main_tex(temp_working_dir)
        
        if not main_tex_file:
            # 自动清理失败的工作区
            shutil.rmtree(temp_working_dir)
            return False, "未能在这个 ZIP 工程包里找到主核心 .tex 文件。请确保 Overleaf 工程格式正确。"
            
        return True, TemplateProject(temp_working_dir, main_tex_file)
        
    except zipfile.BadZipFile:
        return False, "无效的 ZIP 压缩包文件，无法解压。"
    except Exception as e:
        return False, f"模板项目准备过程中发生未知错误: {e}"

def finalize_project(project_obj, final_content, polish_suffix="_polished"):
    """
    项目封装引擎：
    将注入后的内容保存回主核心文件。
    """
    try:
        # 将注入后的最终内容，安全覆盖回工作区里的那个主 tex 文件
        with open(project_obj.main_tex_file, "w", encoding="utf8") as f:
            f.write(final_content)
            
        return True, project_obj
    except Exception as e:
        return False, f"无法保存注入后的 LaTeX 代码: {e}"

def cleanup_tmp_dirs(target_dir):
    """
    全自动环境清理工具：
    编译完成后，自动删除之前建立的所有临时隔离工作区，保持电脑整洁。
    """
    try:
        for item in os.listdir(target_dir):
            if item.startswith(TEMP_DIR_PREFIX) and os.path.isdir(os.path.join(target_dir, item)):
                shutil.rmtree(os.path.join(target_dir, item))
    except Exception:
        pass