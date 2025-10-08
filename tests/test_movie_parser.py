#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试MovieParser类的功能"""
import os
import sys
from unittest.mock import patch
from dvhelper import MovieParser

# 确保可以导入被测试模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_parse_search_results(search_html):
	"""测试解析搜索结果的功能"""
	with patch('dvhelper.config') as mock_config:
		mock_config.search_target_class = 'flex flex-col relative hover:bg-zinc-100 hover:dark:bg-zinc-800'
		mock_config.base_url = 'https://example.com'
		
		result = MovieParser.parse_search_results(search_html, 'ABC-123')
		
		assert result is not None
		assert result['detail_url'] == 'https://example.com/movie/123'
		assert result['title'] == 'ABC-123 Test Movie'
		assert result['fanart_url'] == 'https://example.com/image.jpg'
		
		# 测试未找到匹配结果的情况
		result = MovieParser.parse_search_results(search_html, 'XYZ-456')
		assert result is None
		
		# 测试空HTML的情况
		result = MovieParser.parse_search_results('', 'ABC-123')
		assert result is None

def test_parse_movie_details(detail_html, actress_alias):
	"""测试解析影片详情的功能"""
	with patch('dvhelper.config') as mock_config:
		mock_config.movie_target_class = 'flex flex-col gap-2'
		mock_config.actress_alias = actress_alias
		
		result = MovieParser.parse_movie_details(detail_html)
		
		assert result is not None
		assert result['number'] == 'ABC-123'
		assert result['premiered'] == '2023-01-01'
		assert result['year'] == '2023'
		assert result['runtime'] == '120'
		assert result['director'] == 'Director X'
		assert result['studio'] == 'Studio Y'
		assert result['publisher'] == 'Publisher Z'
		assert result['tags'] == ['tag1', 'tag2']
		assert result['actresses'] == ['Actress A', 'Actress B']
		assert result['trailer_url'] == 'https://example.com/trailer.mp4'
		assert len(result['galleries']) == 2
		
		# 测试空HTML的情况
		result = MovieParser.parse_movie_details('')
		assert result == {}

def test_extract_info_from_list():
	"""测试从列表内容提取影片信息的功能"""
	content_list = [
		'番号:ABC-123复制',
		'发行日期:2023-01-01',
		'片长:120 分钟',
		'导演:Director X',
		'制作商:Studio Y',
		'发行商:Publisher Z',
		'标签:tag1,tag2',
		'演员:Actress A,Actress B'
	]
	
	# 创建一个MovieParser实例
	parser = MovieParser()
	# 在Python中，私有方法通过名称修饰机制转换为_MovieParser__extract_info_from_list
	result = parser._MovieParser__extract_info_from_list(content_list)
	
	assert result['number'] == 'ABC-123'
	assert result['premiered'] == '2023-01-01'
	assert result['year'] == '2023'
	assert result['runtime'] == '120'
	assert result['director'] == 'Director X'
	assert result['studio'] == 'Studio Y'
	assert result['publisher'] == 'Publisher Z'
	assert result['tags'] == ['tag1', 'tag2']
	assert result['actresses'] == ['Actress A', 'Actress B']

def test_resolve_actress_alias(actress_alias):
	"""测试解析演员别名的功能"""
	# 配置dvhelper.config.actress_alias
	with patch('dvhelper.config') as mock_config:
		mock_config.actress_alias = actress_alias
		
		# 创建一个MovieParser实例
		parser = MovieParser()
		# 调用名称修饰后的私有方法
		assert parser._MovieParser__resolve_actress_alias('Alias A1') == 'Actress A'
		assert parser._MovieParser__resolve_actress_alias('Alias A2') == 'Actress A'
		assert parser._MovieParser__resolve_actress_alias('Alias B1') == 'Actress B'
		assert parser._MovieParser__resolve_actress_alias('Unknown Actress') == 'Unknown Actress'
