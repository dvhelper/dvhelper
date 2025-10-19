"""测试 NFOGenerator 类的功能"""
import os
import sys
from xml.dom import minidom

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dvhelper import NFOGenerator


def test_nfo_generator_with_movie_info(movie_info):
	nfo_generator = NFOGenerator(movie_info)

	assert nfo_generator.root is not None
	assert nfo_generator.root.tag == 'movie'

	tag_elements = nfo_generator.root.findall('tag')
	assert tag_elements is not None
	for tag in tag_elements:
		assert tag.text in movie_info.tags

	actress_elements = nfo_generator.root.findall('actress')
	assert actress_elements is not None
	for actress in actress_elements:
		name_element = actress.find('name')
		assert name_element is not None
		assert name_element.text in movie_info.actresses

	director_element = nfo_generator.root.find('director')
	assert director_element is not None
	assert director_element.text == movie_info.director

	studio_element = nfo_generator.root.find('studio')
	assert studio_element is not None
	assert studio_element.text == movie_info.studio

	publisher_element = nfo_generator.root.find('publisher')
	assert publisher_element is not None
	assert publisher_element.text == movie_info.publisher

	uniqueid_element = nfo_generator.root.find('uniqueid')
	assert uniqueid_element is not None
	assert uniqueid_element.text == movie_info.number
	assert uniqueid_element.attrib['type'] == 'num'
	assert uniqueid_element.attrib['default'] == 'true'

def test_nfo_generator_with_empty_movie_info(empty_movie_info):
	nfo_generator = NFOGenerator(empty_movie_info)

	assert nfo_generator.root is not None
	assert nfo_generator.root.tag == 'movie'

	title_element = nfo_generator.root.find('title')
	assert title_element is not None
	assert title_element.text == empty_movie_info.title

	year_element = nfo_generator.root.find('year')
	assert year_element is not None
	assert year_element.text == empty_movie_info.year

	runtime_element = nfo_generator.root.find('runtime')
	assert runtime_element is not None
	assert runtime_element.text == empty_movie_info.runtime

def test_nfo_generator_save(nfo_save_file, movie_info):
	output_path = nfo_save_file
	nfo_generator = NFOGenerator(movie_info)
	nfo_generator.save(output_path)

	assert output_path.exists()
	
	with open(output_path, 'rb') as f:
		xml_content = f.read()

	dom = minidom.parseString(xml_content)
	root = dom.documentElement

	assert root.tagName == 'movie'

	title_node = root.getElementsByTagName('title')[0]
	assert title_node.firstChild.nodeValue == movie_info.title

	year_node = root.getElementsByTagName('year')[0]
	assert year_node.firstChild.nodeValue == movie_info.year

	uniqueid_node = root.getElementsByTagName('uniqueid')[0]
	assert uniqueid_node.firstChild.nodeValue == movie_info.number
	assert uniqueid_node.getAttribute('type') == 'num'
	assert uniqueid_node.getAttribute('default') == 'true'

	director_node = root.getElementsByTagName('director')[0]
	assert director_node.firstChild.nodeValue == movie_info.director

	studio_node = root.getElementsByTagName('studio')[0]
	assert studio_node.firstChild.nodeValue == movie_info.studio

	publisher_node = root.getElementsByTagName('publisher')[0]
	assert publisher_node.firstChild.nodeValue == movie_info.publisher

	premiered_node = root.getElementsByTagName('premiered')[0]
	assert premiered_node.firstChild.nodeValue == movie_info.premiered
