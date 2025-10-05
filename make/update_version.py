#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新版本号脚本
从dvhelper.py读取版本号，并更新make/version_info.txt中的版本信息
"""
import re
from pathlib import Path


def update_version():
	project_root = Path(__file__).parent.parent
	dvhelper_path = project_root / 'dvhelper.py'

	if not dvhelper_path.exists():
		print(f"错误: 找不到文件 {dvhelper_path}")
		return False

	try:
		with open(dvhelper_path, 'r', encoding='utf-8') as f:
			content = f.read()
			version_match = re.search(r"__version__\s*=\s*['\"](.*?)['\"]", content)

			if not version_match:
				print("错误: 在 dvhelper.py 中找不到__version__变量")
				return False

			current_version = version_match.group(1)
			print(f"从 dvhelper.py 获取到当前版本号: {current_version}")
	except Exception as e:
		print(f"读取 dvhelper.py 文件时出错: {e}")
		return False

	version_parts = current_version.split('.')

	try:
		version_numbers = [int(part) for part in version_parts]
	except ValueError:
		print(f"错误: 版本号 {current_version} 格式不正确，必须全部由数字组成")
		return False

	# 对于filevers和prodvers，需要确保是4位数字的元组格式
	while len(version_numbers) < 4:
		version_numbers.append(0)

	version_numbers = version_numbers[:4]
	tuple_version = f"({', '.join(map(str, version_numbers))})"
	version_info_path = Path(__file__).parent / 'version_info.txt'

	if not version_info_path.exists():
		print(f"错误: 找不到文件 {version_info_path}")
		return False

	try:
		with open(version_info_path, 'r', encoding='utf-8') as f:
			file_content = f.read()

		# 更新filevers行
		file_content = re.sub(r'filevers=\(.*?\),\s*#\s*文件版本', f'filevers={tuple_version},  # 文件版本', file_content)
		# 更新prodvers行
		file_content = re.sub(r'prodvers=\(.*?\),', f'prodvers={tuple_version},', file_content)
		# 更新FileVersion行
		file_content = re.sub(r'StringStruct\(u\'FileVersion\',\s*u\'.*?\'\),', f'StringStruct(u\'FileVersion\', u\'{current_version}\'),', file_content)
		# 更新ProductVersion行
		file_content = re.sub(r'StringStruct\(u\'ProductVersion\',\s*u\'.*?\'\)\]\)', f'StringStruct(u\'ProductVersion\', u\'{current_version}\')])', file_content)

		with open(version_info_path, 'w', encoding='utf-8') as f:
			f.write(file_content)

		print(f"已成功更新 {version_info_path.name} 文件中的版本信息")
		print(f"  - filevers 和 prodvers 更新为: {tuple_version}")
		print(f"  - FileVersion 和 ProductVersion 更新为: {current_version}")
		return True
	except Exception as e:
		print(f"更新 {version_info_path.name} 文件时出错: {e}")
		return False


def main():
	update_version()


if __name__ == "__main__":
	main()
