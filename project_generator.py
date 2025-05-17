# global_tools/project_generator.py
import os
import shutil
import sys # <--- ADD THIS IMPORT
from pathlib import Path
from . import utils

# Define template locations relative to this file's directory
_TEMPLATE_DIR = Path(__file__).parent / "assets" / "templates"

# Basic template definitions (can be expanded significantly)
TEMPLATES = {
    "github_standard": {
        "description": "标准的 GitHub 项目结构 (README, .gitignore)", # Removed LICENSE for simplicity unless you provide one
        "source": _TEMPLATE_DIR / "github_standard"
    },
    "python_flask": {
        "description": "简单的 Python Flask Web 应用结构",
        "source": _TEMPLATE_DIR / "python_flask" # Assumes this dir exists
        # Add more structure definition if copying files individually
    },
    # Add more templates here:
    # "nodejs_react": { ... }
    # "python_datasci": { ... }
}

def list_available_templates():
    """Returns a list of available template names."""
    return list(TEMPLATES.keys())

def generate_project_structure(project_root):
    """Generates project structure based on user-selected template."""
    # print("\n--- 生成项目目录结构 ---") # <--- REMOVE OR ENSURE THIS LINE IS NOT HERE

    template_names = list(TEMPLATES.keys())
    if not template_names:
        print("错误: 没有可用的项目模板。", file=sys.stderr)
        return

    template_descriptions = [f"{name} - {TEMPLATES[name]['description']}" for name in template_names]

    chosen_template_desc = utils.get_user_choice(
        "请选择要生成的项目结构模板:",
        template_descriptions
    )
    if chosen_template_desc is None: # Handle cancellation
        print("操作取消。")
        return

    # Extract the name from the description
    chosen_template_name = chosen_template_desc.split(" - ")[0]

    template_info = TEMPLATES.get(chosen_template_name)
    if not template_info or not template_info.get('source'):
        print(f"错误: 模板 '{chosen_template_name}' 配置不正确或源目录丢失。", file=sys.stderr)
        return

    template_source_dir = template_info['source']

    # --- Check if template source exists, create placeholder if known type ---
    if not template_source_dir.is_dir():
        print(f"错误: 模板源目录 '{template_source_dir}' 不存在。", file=sys.stderr) # Use sys.stderr here correctly now

        # --- Placeholder Creation Logic (Example for github_standard) ---
        if chosen_template_name == "github_standard":
            create_placeholder = utils.get_user_choice(
                f"是否尝试在 '{template_source_dir}' 创建占位符模板文件?",
                ["否", "是"], default_index=0
            )
            if create_placeholder == "是":
                print("正在创建 GitHub 标准模板的占位符文件...")
                try:
                    template_source_dir.mkdir(parents=True, exist_ok=True)
                    readme_content = f"# {os.path.basename(project_root)}\n\n项目描述。\n"
                    gitignore_content = (
                        "# Python\n__pycache__/\n*.py[cod]\n*$py.class\n\n# Environments\n.env\n.venv\nvenv/\nenv/\nENV/\n\n"
                        "# IDE / Editor Folders\n.vscode/\n.idea/\n\n# OS Files\n.DS_Store\nThumbs.db\n\n# Build Artifacts\ndist/\nbuild/\n*.egg-info/\n"
                    )
                    (template_source_dir / "README.md").write_text(readme_content, encoding='utf-8')
                    (template_source_dir / ".gitignore").write_text(gitignore_content, encoding='utf-8')
                    print(f"占位符模板已创建于: {template_source_dir}")
                    # Re-check if it exists now
                    if not template_source_dir.is_dir():
                         print("错误: 创建占位符后，目录仍然无效。", file=sys.stderr)
                         return # Stop if still not valid
                except Exception as e:
                    print(f"创建占位符模板时出错: {e}", file=sys.stderr)
                    return # Stop if placeholder creation failed
            else:
                print("操作取消，无法继续生成。")
                return # Stop if user chose not to create placeholders
        # --- Add placeholder creation for other templates if desired ---
        else:
            # For other templates where placeholder creation isn't defined
            print("请在 global_tools/assets/templates/ 中手动创建对应的模板目录和文件。")
            return # Stop if template dir doesn't exist and no placeholder logic

    # --- Proceed with copying ---
    print(f"将在 '{project_root}' 中生成 '{chosen_template_name}' 结构...")
    target_path = Path(project_root)
    potential_conflicts = []
    items_to_copy = list(template_source_dir.iterdir()) # Get items before checking conflicts

    if not items_to_copy:
        print(f"警告: 模板源目录 '{template_source_dir}' 为空。没有文件或目录可复制。")
        # Decide if you want to stop or continue (creating an empty structure)
        # return # Optional: stop if template is empty

    for item in items_to_copy:
        destination_item = target_path / item.name
        if destination_item.exists():
            potential_conflicts.append(item.name)

    if potential_conflicts:
        print("\n警告: 以下文件/目录已存在于目标位置:")
        for name in potential_conflicts: print(f"  - {name}")
        confirm = utils.get_user_choice("是否继续并可能覆盖这些文件/目录?", ["否", "是"], default_index=0)
        if confirm == "否" or confirm is None:
            print("操作取消。")
            return

    # Copy files and directories from template source to project root
    try:
        for item in items_to_copy:
            src_item = template_source_dir / item.name
            dst_item = target_path / item.name

            if dst_item.exists():
                print(f"  覆盖: {item.name}")
                if dst_item.is_dir():
                    shutil.rmtree(dst_item)
                else:
                    dst_item.unlink()

            if src_item.is_dir():
                shutil.copytree(src_item, dst_item)
                print(f"  已复制目录: {item.name}/")
            else:
                shutil.copy2(src_item, dst_item) # copy2 preserves metadata
                print(f"  已复制文件: {item.name}")

        print(f"\n项目结构 '{chosen_template_name}' 生成成功。")

    except Exception as e:
        print(f"生成项目结构时出错: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc() # Print full traceback for unexpected errors during copy