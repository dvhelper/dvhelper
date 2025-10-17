"""测试 NFOGenerator 类的功能"""
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open
import xml.etree.ElementTree as ET
from xml.dom import minidom

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dvhelper import NFOGenerator, MovieInfo


def test_nfo_generator_initialize(movie_info):
	nfo_generator = NFOGenerator(movie_info)

	assert nfo_generator.root is not None
	assert nfo_generator.root.tag == 'movie'

	title_element = nfo_generator.root.find('title')
	assert title_element is not None
	assert title_element.text == movie_info.title

	year_element = nfo_generator.root.find('year')
	assert year_element is not None
	assert year_element.text == movie_info.year

def test_nfo_generator_with_empty_movie_info():
	empty_movie_info = MovieInfo({
		'number': 'EMPTY-001',
		'title': '',
		'year': '',
		'runtime': '',
		'mpaa': 'NC-17',
		'country': '日本',
		'tags': [],
		'actresses': []
	})

	nfo_generator = NFOGenerator(empty_movie_info)

	assert nfo_generator.root is not None
	assert nfo_generator.root.tag == 'movie'

	title_element = nfo_generator.root.find('title')
	assert title_element is not None
	assert title_element.text == ''

	uniqueid_element = nfo_generator.root.find('uniqueid')
	assert uniqueid_element is not None
	assert uniqueid_element.text == 'EMPTY-001'
	assert uniqueid_element.attrib['type'] == 'num'
	assert uniqueid_element.attrib['default'] == 'true'

def test_nfo_generator_with_tags_and_actresses():
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

	nfo_generator = NFOGenerator(movie_info)

	genre_elements = nfo_generator.root.findall('genre')
	assert len(genre_elements) == 3
	assert {elem.text for elem in genre_elements} == {'Tag1', 'Tag2', 'Tag3'}

	tag_elements = nfo_generator.root.findall('tag')
	assert len(tag_elements) == 3
	assert {elem.text for elem in tag_elements} == {'Tag1', 'Tag2', 'Tag3'}

	actress_elements = nfo_generator.root.findall('actress')
	assert len(actress_elements) == 2

	actress_names = []
	for actress in actress_elements:
		name_element = actress.find('name')
		assert name_element is not None
		actress_names.append(name_element.text)

	assert set(actress_names) == {'Actress A', 'Actress B'}

def test_nfo_generator_save(nfo_save_file):
	output_path = nfo_save_file

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

	nfo_generator = NFOGenerator(movie_info)
	nfo_generator.save(output_path)

	assert output_path.exists()
	
	with open(output_path, 'rb') as f:
		xml_content = f.read()

	dom = minidom.parseString(xml_content)
	root = dom.documentElement

	assert root.tagName == 'movie'

	title_node = root.getElementsByTagName('title')[0]
	assert title_node.firstChild.nodeValue == 'Complete Test Movie'

	year_node = root.getElementsByTagName('year')[0]
	assert year_node.firstChild.nodeValue == '2023'

	uniqueid_node = root.getElementsByTagName('uniqueid')[0]
	assert uniqueid_node.firstChild.nodeValue == 'TEST-002'
	assert uniqueid_node.getAttribute('type') == 'num'
	assert uniqueid_node.getAttribute('default') == 'true'

	director_node = root.getElementsByTagName('director')[0]
	assert director_node.firstChild.nodeValue == 'Director X'

	studio_node = root.getElementsByTagName('studio')[0]
	assert studio_node.firstChild.nodeValue == 'Studio Y'

	publisher_node = root.getElementsByTagName('publisher')[0]
	assert publisher_node.firstChild.nodeValue == 'Publisher Z'

	premiered_node = root.getElementsByTagName('premiered')[0]
	assert premiered_node.firstChild.nodeValue == '2023-01-01'

def test_nfo_generator_with_media_info(movie_info):
	nfo_generator = NFOGenerator(movie_info)

	trailer_element = nfo_generator.root.find('trailer')
	assert trailer_element is not None
	assert trailer_element.text == movie_info.trailer_url

	fanart_element = nfo_generator.root.find('fanart')
	assert fanart_element is not None
	thumb_element = fanart_element.find('thumb')
	assert thumb_element is not None
	assert thumb_element.text == movie_info.fanart_url
