#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试工具函数和类的功能"""
import os
import sys
import logging
from unittest.mock import patch, MagicMock
import dvhelper
from dvhelper import set_language, get_logger, TqdmOut, HelpOnErrorParser
from colorama import Fore, Style

# 确保可以导入被测试模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_set_language():
	"""测试设置语言的功能"""
	# 测试设置为英文
	with patch('dvhelper.gettext') as mock_gettext:
		mock_translation = MagicMock()
		mock_gettext.translation.return_value = mock_translation
		
		set_language('en_US')
		
		# 验证gettext.translation被正确调用
		mock_gettext.translation.assert_any_call('dvhelper', localedir=str(dvhelper.Path(__file__).parent.parent.joinpath('i18n')), languages=['en_US'])
		mock_translation.install.assert_called()

def test_get_logger():
	"""测试获取日志器的功能"""
	# 清理已存在的logger，避免测试之间的相互影响
	if hasattr(dvhelper, 'logger'):
		del dvhelper.logger
	
	# 测试get_logger函数
	with patch('logging.getLogger') as mock_getLogger:
		mock_logger = MagicMock()
		mock_getLogger.return_value = mock_logger
		mock_logger.hasHandlers.return_value = False
		
		with patch('logging.FileHandler') as mock_FileHandler:
			with patch('logging.StreamHandler') as mock_StreamHandler:
				logger = get_logger()
				
				# 验证返回的logger是正确的
				assert logger == mock_logger
				mock_getLogger.assert_called_with(dvhelper.__name__)
				
				# 验证设置了日志级别
				mock_logger.setLevel.assert_called_with(logging.INFO)
				
				# 验证添加了处理器
				assert mock_logger.addHandler.call_count >= 2

def test_lazy_import():
	"""测试延迟导入的功能"""
	# 直接验证lazy_import函数能正常执行，不检查具体调用
	try:
		dvhelper.lazy_import()
		# 如果执行到这里，说明没有抛出异常
		success = True
	except Exception as e:
		success = False
		print(f"lazy_import抛出异常: {e}")
	
	assert success, "lazy_import函数执行失败"

def test_tqdm_out():
	"""测试TqdmOut类的功能"""
	# 模拟tqdm.write函数
	with patch('dvhelper.tqdm.write') as mock_tqdm_write:
		# 测试write方法
		TqdmOut.write("test message")
		
		# 验证tqdm.write被正确调用
		mock_tqdm_write.assert_called_with("test message", file=None, end='', nolock=False)

def test_help_on_error_parser():
	"""测试HelpOnErrorParser类的功能"""
	# 测试error方法
	with patch('sys.stderr.write') as mock_write:
		with patch('argparse.ArgumentParser.print_help') as mock_print_help:
			with patch('sys.exit') as mock_exit:
				parser = HelpOnErrorParser()
				
				try:
					# 调用error方法
					parser.error("test error")
				except SystemExit:
					# 这个异常是由sys.exit()抛出的，我们捕获它以继续测试
					pass
				
				# 验证sys.stderr.write被正确调用
				mock_write.assert_called_with(f'{Style.BRIGHT}{Fore.RED}' + '错误: test error' + f'{Style.RESET_ALL}\n\n')
				
				# 验证print_help被正确调用
				mock_print_help.assert_called()
				
				# 验证sys.exit被正确调用
				mock_exit.assert_called_with(2)
