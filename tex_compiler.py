import subprocess
import os

def compile_to_pdf(tex_filepath):
    directory = os.path.dirname(tex_filepath)
    filename = os.path.basename(tex_filepath)
    
    try:
        # 使用 xelatex 编译，开启 nonstopmode 防止报错卡住进程
        subprocess.run(
            ["xelatex", "-interaction=nonstopmode", filename],
            cwd=directory,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True, "PDF 编译成功！"
    except subprocess.CalledProcessError as e:
        return False, f"编译失败，请检查 TeX 语法是否正确。\n错误信息: {e.stderr.decode('utf8', errors='ignore')}"
    except FileNotFoundError:
        return False, "系统未找到 xelatex 命令，请确认已安装 TeX Live 或 MiKTeX，并已配置环境变量。"