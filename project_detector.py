# global_tools/project_detector.py
import os
import glob  # Import glob for file searching

def detect_project_type(project_root):
    """
    Detects the project type based on characteristic files or presence of .py files.
    Priority: Node -> Python (req/toml) -> Python (any .py) -> Unknown.

    Args:
        project_root (str): The root directory of the project.

    Returns:
        str: 'python', 'node', or 'unknown'.
    """
    project_type = 'unknown'  # Default

    # Check for Node.js first
    package_json_path = os.path.join(project_root, 'package.json')
    pnpm_lock_path = os.path.join(project_root, 'pnpm-lock.yaml')
    is_node = os.path.exists(package_json_path) or os.path.exists(pnpm_lock_path)
    if is_node:
        project_type = 'node'

    # Check for Python marker files (requirements/pyproject)
    pyproject_path = os.path.join(project_root, 'pyproject.toml')
    requirements_path = os.path.join(project_root, 'requirements.txt')
    is_python_markers = os.path.exists(pyproject_path) or os.path.exists(requirements_path)

    # If Python markers found, override Node detection (assuming primary dev is Python)
    if is_python_markers:
        project_type = 'python'

    # If still 'unknown', check for any .py files
    if project_type == 'unknown':
        # Check for .py files in the root and potentially common src dirs
        py_files_found = False
        # Check root directory
        if glob.glob(os.path.join(project_root, '*.py')):
            py_files_found = True
        # Check common source directories (optional, adjust as needed)
        elif glob.glob(os.path.join(project_root, 'src', '*.py')):
            py_files_found = True
        elif glob.glob(os.path.join(project_root, os.path.basename(project_root), '*.py')):
            py_files_found = True

        if py_files_found:
            project_type = 'python'

    return project_type

    is_node = os.path.exists(package_json_path) or os.path.exists(pnpm_lock_path)

    project_type = 'unknown'
    if is_python and is_node:
        # print("警告：检测到 Python 和 Node.js 的特征文件。将优先识别为 Python。") # REMOVED
        project_type = 'python' # Prioritize Python if both exist
    elif is_python:
        # print("检测到 Python 项目。") # REMOVED
        project_type = 'python'
    elif is_node:
        # print("检测到 Node.js 项目。") # REMOVED
        project_type = 'node'
    # else: # print("未能识别特定项目类型。") # REMOVED

    return project_type # Just return the result