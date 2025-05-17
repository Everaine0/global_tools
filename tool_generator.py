# global_tools/tool_generator.py
import os
import sys
import stat # For setting executable bit if needed (though not used here)
from pathlib import Path

# --- Allow direct execution ---
# Check if running as a script (__package__ is None) vs imported (__package__ is 'global_tools')
if __name__ == "__main__" and __package__ is None:
    # If run as a script, adjust sys.path to allow finding sibling modules like utils
    file_path = Path(__file__).resolve()
    # Add global_tools' parent directory (grandparent of this file) to sys.path
    # This allows `from global_tools import utils` below
    grandparent_dir = file_path.parent.parent
    if str(grandparent_dir) not in sys.path:
        sys.path.insert(0, str(grandparent_dir))
    # Now we can import utils using absolute path from the package perspective
    # We need utils for get_user_choice if we want confirmation when run directly
    try:
        from global_tools import utils
    except ImportError as e:
        print(f"错误: 无法导入 'utils' 模块。确保脚本位于 'global_tools' 内部，并且父目录结构正确。", file=sys.stderr)
        print(f" sys.path: {sys.path}", file=sys.stderr)
        print(f" Error: {e}", file=sys.stderr)
        sys.exit(1)
else:
    # If imported as part of the package (e.g., via -m), use relative import
    from . import utils
# --- End direct execution setup ---


def generate_tool_py(target_dir):
    """Generates the tool.py file in the specified target directory."""
    tool_py_path = os.path.join(target_dir, 'tool.py')

    # --- Calculate Paths ---
    try:
        # Get the absolute path to the global_tools directory itself
        # __file__ should be the path to tool_generator.py
        global_tools_abs_path = Path(__file__).parent.resolve()
        if not global_tools_abs_path.name == 'global_tools':
             print("警告: tool_generator.py 不在名为 'global_tools' 的目录中。路径计算可能不准确。", file=sys.stderr)

        # Get the absolute path of the directory where tool.py will be created
        target_abs_path = Path(target_dir).resolve()
        # Get the parent directory of global_tools
        backend_parent_dir = global_tools_abs_path.parent

        # We need the absolute path of global_tools for embedding in the script
        # Using as_posix() for better cross-platform compatibility in the generated string
        global_tools_abs_path_str = global_tools_abs_path.as_posix()

    except Exception as e:
        print(f"错误: 计算路径时出错: {e}", file=sys.stderr)
        return False


    # --- Generate tool.py Content (Using corrected import logic) ---
    tool_py_content = f"""# -*- coding: utf-8 -*-
# Environment Auxiliary Tool Frontend (tool.py)
# This file is auto-generated.

import sys
import os
import traceback
from pathlib import Path # Use pathlib for robustness

# --- Dynamically Locate and Import Backend ---

def find_and_import_backend():
    '''
    Finds the backend 'global_tools' directory using the path embedded during generation,
    adds its parent directory to sys.path, and imports the main function using an absolute import.
    '''
    try:
        # Use the absolute path to global_tools that was determined when this file was generated.
        # This assumes the location of global_tools relative to this tool.py doesn't change drastically.
        # Convert the embedded posix path back to a Path object.
        global_tools_actual_path = Path(r"{global_tools_abs_path_str}")
        backend_parent_dir = global_tools_actual_path.parent

        if not global_tools_actual_path.is_dir():
            print(f"错误：无法找到后端工具库目录。", file=sys.stderr)
            print(f"预期路径 (基于生成时的位置): {{global_tools_actual_path}}", file=sys.stderr)
            print("请确保 'global_tools' 目录存在于预期位置, 或重新生成 tool.py。", file=sys.stderr)
            sys.exit(1)

        # Add the PARENT directory of 'global_tools' to sys.path
        # This allows Python to find the 'global_tools' package.
        if str(backend_parent_dir) not in sys.path:
            sys.path.insert(0, str(backend_parent_dir))
            # print(f"Backend parent path added to sys.path: {{backend_parent_dir}}") # Debug

        try:
            # Perform absolute import: from package_name.module_name import function_name
            from global_tools.main import run_main_menu
            # print("Successfully imported run_main_menu from global_tools.main") # Debug
            return run_main_menu
        except ImportError as e:
            print(f"错误：无法从后端工具库导入主函数。", file=sys.stderr)
            print(f"尝试从包 'global_tools' (其父目录 {{backend_parent_dir}} 应在 sys.path 中) 导入 'main.run_main_menu'。", file=sys.stderr)
            print(f"ImportError: {{e}}", file=sys.stderr)
            print("sys.path:", sys.path) # Print sys.path for debugging
            print("请检查：", file=sys.stderr)
            print("  1. 'global_tools' 目录是否在上面列出的 sys.path 中的某个路径下?", file=sys.stderr)
            print("  2. 'global_tools' 目录是否包含有效的 '__init__.py' 文件?", file=sys.stderr)
            print("  3. 'global_tools/main.py' 文件是否存在且包含 'run_main_menu' 函数?", file=sys.stderr)
            print("  4. 后端代码中是否有其他导入错误或语法错误?", file=sys.stderr)
            # traceback.print_exc() # Uncomment for more detailed import traceback
            sys.exit(1)
        except Exception as e:
            print(f"导入后端时发生未知错误: {{e}}", file=sys.stderr)
            traceback.print_exc()
            sys.exit(1)

    except Exception as e:
        print(f"在查找后端库时发生错误: {{e}}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


# --- Main Execution ---

if __name__ == "__main__":
    # print(f"Running tool.py from: {{os.getcwd()}}") # Debug
    # print(f"Python executable: {{sys.executable}}") # Debug
    main_func = find_and_import_backend()
    try:
        # Set current working directory to the directory containing tool.py
        # This ensures operations within the tool default to the project root.
        tool_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(tool_dir)
        # print(f"Changed working directory to: {{tool_dir}}") # Debug
        main_func() # Run the main menu from the backend
    except Exception as e:
        print(f"\\n运行工具时发生意外错误:", file=sys.stderr)
        traceback.print_exc()
        print("\\n工具已终止。")
        # input("按回车键退出...") # Optional pause before exit
        sys.exit(1)

"""

    # --- Write the file (with confirmation) ---
    try:
        if os.path.exists(tool_py_path):
             # Use utils.get_user_choice for confirmation
             overwrite = utils.get_user_choice(f"'tool.py' 已存在于 '{target_dir}'。是否覆盖?", ["否", "是"], default_index=0)
             if overwrite == "否" or overwrite is None: # Handle None case from cancellation
                 print("操作取消。")
                 return False

        with open(tool_py_path, 'w', encoding='utf-8') as f:
            f.write(tool_py_content)
        print(f"'tool.py' 已成功生成在 '{os.path.abspath(target_dir)}'。")
        return True
    except Exception as e:
        print(f"生成 'tool.py' 时出错: {e}", file=sys.stderr)
        return False


# --- Add main execution block for direct running ---
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("\n用法: python tool_generator.py <目标项目目录>")
        print("  <目标项目目录>: 要在其中生成 tool.py 的文件夹路径。")
        print("\n示例:")
        print("  # 在指定项目路径生成 tool.py")
        print(f"  python \"{Path(__file__).name}\" \"/path/to/my/project\"")
        print("\n  # 在当前目录下生成 tool.py (当您已 cd 到项目目录时)")
        print(f"  python \"{Path(__file__).resolve()}\" .") # Show absolute path to generator
        sys.exit(1)

    target_directory = sys.argv[1]

    # Validate target directory
    if not os.path.isdir(target_directory):
         # Try resolving relative paths like '.'
         target_directory = os.path.abspath(target_directory)
         if not os.path.isdir(target_directory):
             print(f"错误: 目标目录 '{sys.argv[1]}' 无效或不存在。", file=sys.stderr)
             sys.exit(1)

    print(f"\n将在目录 '{os.path.abspath(target_directory)}' 中生成 tool.py...")
    success = generate_tool_py(target_directory)

    if success:
        print("\ntool.py 生成完成。")
    else:
        print("\ntool.py 生成失败。")
        sys.exit(1)