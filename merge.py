import os

# 配置：需要包含的文件后缀和需要排除的文件夹
include_extensions = ('.py', '.md', '.mmd', '.txt', '.env')
exclude_dirs = {'venv', '__pycache__', '.git', '.idea', 'node_modules'}

def merge_project(root_dir, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for root, dirs, files in os.walk(root_dir):
            # 过滤掉排除目录
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith(include_extensions) and file != output_file:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, root_dir)
                    
                    f.write(f"\n\n{'='*50}\n")
                    f.write(f"FILE: {rel_path}\n")
                    f.write(f"{'='*50}\n\n")
                    
                    f.write(f"```{os.path.splitext(file)[1][1:] or 'text'}\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as code_f:
                            f.write(code_f.read())
                    except Exception as e:
                        f.write(f"Error reading file: {e}")
                    f.write("\n```\n")

if __name__ == "__main__":
    merge_project('.', 'all_code.md')
    print("项目已整合至 all_code.md")
