#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试Config类的功能"""

def test_config_initialization(config):
	"""测试配置类的初始化"""
	assert config.base_url == 'https://avfan.com'
	assert config.sign_in_url == 'https://avfan.com/zh-CN/sign_in'
	assert config.search_url == 'https://avfan.com/search?q='
	assert isinstance(config.movie_file_extensions, tuple)
	assert '.mp4' in config.movie_file_extensions

def test_regex_patterns(config):
	"""测试正则表达式模式"""
	# 测试普通影片模式
	assert config.normal_movie_pattern.match('ABC-123')
	assert config.normal_movie_pattern.match('XYZ-4567')
	
	# 测试FC2模式
	assert config.fc2_movie_pattern.match('FC2-123456')
	assert config.fc2_movie_pattern.match('FC2 PPV-123456')
	
	# 测试特定系列模式
	assert config._259luxu_movie_pattern.match('259LUXU-1234')
	assert config._200gana_movie_pattern.match('200GANA-5678')
	assert config._300mium_movie_pattern.match('300MIUM-9012')
