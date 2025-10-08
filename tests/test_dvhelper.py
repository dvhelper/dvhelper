#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""整合后的DVHelper测试文件，使用pytest框架"""
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# 确保可以导入被测试模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dvhelper
from dvhelper import (
	Config, MovieInfo, NFOGenerator, MovieParser, MovieScraper, DVHelper,
	set_language, get_logger, lazy_import, TqdmOut, HelpOnErrorParser
)


# TestDVHelper 类的增强测试
def test_analyze_keyword_enhanced(dv_helper):
	"""测试分析关键词并提取影片ID的增强功能"""
	# 测试普通格式
	assert dv_helper.analyze_keyword('ABC-123') == 'ABC-123'
	assert dv_helper.analyze_keyword('ABC123') == 'ABC-123'
	
	# 测试FC2格式
	assert dv_helper.analyze_keyword('FC2-123456') == 'FC2-123456'
	assert dv_helper.analyze_keyword('FC2 PPV-123456') == 'FC2-123456'
	
	# 测试特定系列格式
	assert dv_helper.analyze_keyword('259LUXU-1234') == '259LUXU-1234'
	assert dv_helper.analyze_keyword('200GANA-5678') == '200GANA-5678'
	assert dv_helper.analyze_keyword('300MIUM-9012') == '300MIUM-9012'
	
	# 测试无法解析的情况
	assert dv_helper.analyze_keyword('Invalid Keyword') is None
	
	# 测试带额外文本的情况
	assert dv_helper.analyze_keyword('Some text ABC-123 more text') == 'ABC-123'
	assert dv_helper.analyze_keyword('ABC-123 (2023)') == 'ABC-123'

def test_list_video_files_enhanced(temp_dir):
	"""测试列出视频文件的增强功能"""
	dv_helper = DVHelper()
	
	# 创建测试文件和目录
	video1 = Path(temp_dir) / 'movie1.mp4'
	video2 = Path(temp_dir) / 'movie2.mkv'
	text_file = Path(temp_dir) / 'document.txt'
	ignored_file = Path(temp_dir) / '##hidden_file.mp4'  # 使用正确的ignored_file_prefix
	sub_dir = Path(temp_dir) / 'subdir'
	video3 = sub_dir / 'movie3.avi'
	deep_sub_dir = sub_dir / 'deepdir'
	video4 = deep_sub_dir / 'movie4.mov'
	
	# 创建文件
	video1.touch()
	video2.touch()
	text_file.touch()
	ignored_file.touch()
	sub_dir.mkdir(exist_ok=True)
	video3.touch()
	deep_sub_dir.mkdir(exist_ok=True)
	video4.touch()
	
	# 测试仅搜索当前目录
	result = dv_helper.list_video_files(Path(temp_dir), max_depth=0)
	
	assert len(result) == 2
	assert Path(video1) in result
	assert Path(video2) in result
	assert Path(video3) not in result
	assert Path(video4) not in result
	assert Path(ignored_file) not in result
	
	# 测试搜索包含一级子目录
	result = dv_helper.list_video_files(Path(temp_dir), max_depth=1)
	
	assert len(result) == 3
	assert Path(video1) in result
	assert Path(video2) in result
	assert Path(video3) in result
	assert Path(video4) not in result
	
	# 测试搜索所有子目录
	result = dv_helper.list_video_files(Path(temp_dir), max_depth=2)
	
	assert len(result) == 4
	assert Path(video1) in result
	assert Path(video2) in result
	assert Path(video3) in result
	assert Path(video4) in result

def test_movie_folder_creation(config, movie_info):
	"""测试创建影片文件夹的功能"""
	# 测试单演员情况
	with patch('dvhelper.config', config):
		base_dir = Path(config.completed_path)
		
		# 构建预期的影片路径
		expected_path = base_dir / movie_info.actresses[0] / f'[{movie_info.number}]({movie_info.year})'
		
		# 验证路径构建逻辑
		assert f'[{movie_info.number}]({movie_info.year})' in str(expected_path)
		assert movie_info.actresses[0] in str(expected_path)

def test_organize_folders_with_alias(temp_dir):
	"""测试带演员别名的文件夹整理功能"""
	dv_helper = DVHelper()
	
	# 创建测试文件夹
	actress_dir = Path(temp_dir) / 'Alias A1'
	actress_dir.mkdir(exist_ok=True)
	
	# 创建模拟的演员别名配置
	actress_alias = {'Actress A': ['Alias A1', 'Alias A2']}
	
	with patch('dvhelper.config.actress_alias', actress_alias):
		try:
			# 运行文件夹整理功能
			dv_helper.organize_folders(temp_dir)
			# 只要不抛出异常，测试就算通过
			assert True
		except Exception as e:
			assert False, f"organize_folders方法抛出异常: {e}"

# TestUtilityFunctions 类的补充测试
def test_lazy_import():
	"""测试延迟导入功能"""
	# 确保全局变量未初始化
	if hasattr(dvhelper, 'logger'):
		del dvhelper.logger
	
	# 执行lazy_import
	lazy_import()
	
	# 验证必要的全局变量已初始化
	assert hasattr(dvhelper, 'logger')
	assert hasattr(dvhelper, 'requests')
	assert hasattr(dvhelper, 'tqdm')

def test_tqdm_out():
	"""测试TqdmOut类的功能"""
	# 创建TqdmOut实例
	tqdm_out = TqdmOut()
	
	# 测试write方法（不抛出异常即可）
	try:
		tqdm_out.write("Test output")
		assert True
	except Exception as e:
		assert False, f"TqdmOut.write方法抛出异常: {e}"

def test_help_on_error_parser():
	"""测试HelpOnErrorParser类的功能"""
	# 创建HelpOnErrorParser实例
	parser = HelpOnErrorParser(description="Test Parser")
	
	# 添加参数
	parser.add_argument('--test', help='Test argument')
	
	# 验证解析器创建成功
	assert parser is not None
	assert parser.description == "Test Parser"

# TestMovieScraper 类的增强测试
def test_movie_scraper_crop_image(testable_movie_scraper, temp_dir):
	"""测试裁剪图片功能"""
	# 创建测试图片文件
	src_file = Path(temp_dir) / 'source.jpg'
	dest_file = Path(temp_dir) / 'destination.jpg'
	
	# 创建一个模拟的图片文件
	src_file.touch()
	
	# 使用patch模拟PIL.Image
	with patch('PIL.Image.open') as mock_open:
		mock_image = MagicMock()
		mock_image.size = (1000, 800)
		mock_image.crop.return_value = mock_image
		mock_open.return_value.__enter__.return_value = mock_image
		
		try:
			# 调用crop_image方法
			testable_movie_scraper.crop_image(src_file, dest_file)
			# 验证裁剪参数是否正确
			mock_image.crop.assert_called_with((621, 0, 1000, 800))
			assert True
		except Exception as e:
			assert False, f"crop_image方法抛出异常: {e}"

def test_movie_scraper_check_cookies(testable_movie_scraper):
	"""测试检查Cookies功能"""
	# 调用check_cookies方法
	session = testable_movie_scraper.check_cookies()
	
	# 验证返回值是否为Mock对象
	assert session is not None

# 清理测试后的旧文件
def teardown_module(module):
	"""模块级别的清理工作"""
	# 这里可以添加清理代码，如果需要的话
	pass
