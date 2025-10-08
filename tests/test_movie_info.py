#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试MovieInfo类的功能"""
from dvhelper import MovieInfo


def test_movie_info_initialization(movie_info_dict, movie_info):
	"""测试影片信息类的初始化"""
	# 验证所有属性是否正确初始化
	assert movie_info.detail_url == movie_info_dict['detail_url']
	assert movie_info.fanart_url == movie_info_dict['fanart_url']
	assert movie_info.number == movie_info_dict['number']
	assert movie_info.title == movie_info_dict['title']
	assert movie_info.year == movie_info_dict['year']
	assert movie_info.runtime == movie_info_dict['runtime']
	assert movie_info.tags == movie_info_dict['tags']
	assert movie_info.actresses == movie_info_dict['actresses']
	assert movie_info.director == movie_info_dict['director']
	assert movie_info.studio == movie_info_dict['studio']
	assert movie_info.publisher == movie_info_dict['publisher']
	assert movie_info.premiered == movie_info_dict['premiered']
	assert movie_info.mpaa == movie_info_dict['mpaa']
	assert movie_info.country == movie_info_dict['country']

def test_movie_info_with_default_values():
	"""测试带有默认值的影片信息初始化"""
	info_dict = {'number': 'ABC-123'}
	movie_info = MovieInfo(info_dict)
	
	assert movie_info.number == 'ABC-123'
	assert movie_info.title == ''
	assert movie_info.tags == []
	assert movie_info.actresses == []
	assert movie_info.country == '日本'  # 默认值
	assert movie_info.mpaa == 'NC-17'   # 默认值
