#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试NFOGenerator类的功能"""
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open
import xml.etree.ElementTree as ET
from xml.dom import minidom

# 确保可以导入被测试模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dvhelper import NFOGenerator, MovieInfo


def test_nfo_generator_initialization(movie_info):
	"""测试NFOGenerator类的初始化"""
	# 创建NFOGenerator实例
	nfo_generator = NFOGenerator(movie_info)
	
	# 验证root元素正确创建
	assert nfo_generator.root is not None
	assert nfo_generator.root.tag == 'movie'
	
	# 验证基本信息正确添加
	title_element = nfo_generator.root.find('title')
	assert title_element is not None
	assert title_element.text == movie_info.title
	
	year_element = nfo_generator.root.find('year')
	assert year_element is not None
	assert year_element.text == movie_info.year

def test_nfo_generator_with_empty_movie_info():
	"""测试使用空的MovieInfo对象初始化NFOGenerator"""
	# 创建一个只有必要字段的MovieInfo对象
	empty_movie_info = MovieInfo({
		'number': 'EMPTY-001',
		'title': '',
		'year': '',
		'runtime': '',
		'mpaa': 'NC-17',  # 默认值
		'country': '日本',  # 默认值
		'tags': [],
		'actresses': []
	})
	
	# 创建NFOGenerator实例
	nfo_generator = NFOGenerator(empty_movie_info)
	
	# 验证root元素正确创建
	assert nfo_generator.root is not None
	assert nfo_generator.root.tag == 'movie'
	
	# 验证必要字段即使为空也被添加
	title_element = nfo_generator.root.find('title')
	assert title_element is not None
	assert title_element.text == ''
	
	# 验证唯一标识正确添加
	uniqueid_element = nfo_generator.root.find('uniqueid')
	assert uniqueid_element is not None
	assert uniqueid_element.text == 'EMPTY-001'
	assert uniqueid_element.attrib['type'] == 'num'
	assert uniqueid_element.attrib['default'] == 'true'

def test_nfo_generator_with_tags_and_actresses():
	"""测试NFOGenerator处理标签和演员信息"""
	# 创建包含标签和演员的MovieInfo对象
	movie_info = MovieInfo({
		'number': 'TEST-001',
		'title': 'Test Movie',
		'year': '2023',
		'runtime': '120',
		'mpaa': 'NC-17',
		'country': '日本',
		'tags': ['Tag1', 'Tag2', 'Tag3'],
		'actresses': ['Actress A', 'Actress B']
	})
	
	# 创建NFOGenerator实例
	nfo_generator = NFOGenerator(movie_info)
	
	# 验证标签正确添加
	genre_elements = nfo_generator.root.findall('genre')
	assert len(genre_elements) == 3
	assert {elem.text for elem in genre_elements} == {'Tag1', 'Tag2', 'Tag3'}
	
	# 验证标签也添加为tag元素
	tag_elements = nfo_generator.root.findall('tag')
	assert len(tag_elements) == 3
	assert {elem.text for elem in tag_elements} == {'Tag1', 'Tag2', 'Tag3'}
	
	# 验证演员正确添加
	actress_elements = nfo_generator.root.findall('actress')
	assert len(actress_elements) == 2
	
	# 验证每个actress元素都有正确的name子元素
	actress_names = []
	for actress in actress_elements:
		name_element = actress.find('name')
		assert name_element is not None
		actress_names.append(name_element.text)
	
	assert set(actress_names) == {'Actress A', 'Actress B'}

def test_nfo_generator_save_function(temp_dir):
	"""测试NFOGenerator的save方法"""
	# 创建一个临时输出文件路径
	output_path = Path(temp_dir) / 'TEST-001.nfo'
	
	# 创建MovieInfo对象
	movie_info = MovieInfo({
		'number': 'TEST-001',
		'title': 'Test Movie',
		'year': '2023',
		'runtime': '120',
		'mpaa': 'NC-17',
		'country': '日本'
	})
	
	# 创建NFOGenerator实例
	nfo_generator = NFOGenerator(movie_info)
	
	# 使用mock_open来模拟文件写入
	with patch('builtins.open', mock_open()) as m:
		# 调用save方法
		nfo_generator.save(output_path)
		
		# 验证文件被正确打开和写入
		m.assert_called_once_with(output_path, 'wb')
		handle = m()
		assert handle.write.called

def test_nfo_generator_actual_file_generation(temp_dir):
	"""测试NFOGenerator实际生成的NFO文件内容"""
	# 创建一个临时输出文件路径
	output_path = Path(temp_dir) / 'TEST-002.nfo'
	
	# 创建包含完整信息的MovieInfo对象
	movie_info = MovieInfo({
		'number': 'TEST-002',
		'title': 'Complete Test Movie',
		'year': '2023',
		'runtime': '120',
		'mpaa': 'NC-17',
		'country': '日本',
		'director': 'Director X',
		'studio': 'Studio Y',
		'publisher': 'Publisher Z',
		'premiered': '2023-01-01',
		'tags': ['Tag1', 'Tag2'],
		'actresses': ['Actress A']
	})
	
	# 创建NFOGenerator实例并保存文件
	nfo_generator = NFOGenerator(movie_info)
	nfo_generator.save(output_path)
	
	# 验证文件已创建
	assert output_path.exists()
	
	# 读取并解析生成的XML文件
	with open(output_path, 'rb') as f:
		xml_content = f.read()
		
	# 解析XML内容
	try:
		# 使用minidom解析，因为输出的是格式化的XML
		dom = minidom.parseString(xml_content)
		root = dom.documentElement
		
		# 验证基本信息
		assert root.tagName == 'movie'
		
		title_node = root.getElementsByTagName('title')[0]
		assert title_node.firstChild.nodeValue == 'Complete Test Movie'
		
		year_node = root.getElementsByTagName('year')[0]
		assert year_node.firstChild.nodeValue == '2023'
		
		# 验证唯一标识
		uniqueid_node = root.getElementsByTagName('uniqueid')[0]
		assert uniqueid_node.firstChild.nodeValue == 'TEST-002'
		assert uniqueid_node.getAttribute('type') == 'num'
		assert uniqueid_node.getAttribute('default') == 'true'
		
		# 验证其他元数据
		director_node = root.getElementsByTagName('director')[0]
		assert director_node.firstChild.nodeValue == 'Director X'
		
		studio_node = root.getElementsByTagName('studio')[0]
		assert studio_node.firstChild.nodeValue == 'Studio Y'
		
		publisher_node = root.getElementsByTagName('publisher')[0]
		assert publisher_node.firstChild.nodeValue == 'Publisher Z'
		
		premiered_node = root.getElementsByTagName('premiered')[0]
		assert premiered_node.firstChild.nodeValue == '2023-01-01'
		
	except Exception as e:
		assert False, f"解析生成的XML文件时出错: {e}"

def test_nfo_generator_with_special_characters():
	"""测试NFOGenerator处理特殊字符"""
	# 创建包含特殊字符的MovieInfo对象
	movie_info = MovieInfo({
		'number': 'TEST-003',
		'title': 'Movie with & < > " \' special characters',
		'year': '2023',
		'runtime': '120',
		'mpaa': 'NC-17',
		'country': '日本'
	})
	
	# 创建NFOGenerator实例
	nfo_generator = NFOGenerator(movie_info)
	
	# 验证特殊字符被正确处理（不会导致XML解析错误）
	try:
		# 将XML转换为字符串进行验证
		rough_string = ET.tostring(nfo_generator.root, 'utf-8')
		# 尝试解析以验证XML有效性
		minidom.parseString(rough_string)
		assert True
	except Exception as e:
		assert False, f"包含特殊字符的XML解析失败: {e}"
