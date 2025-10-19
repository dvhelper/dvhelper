"""测试 MovieParser 类的功能"""
import os
import sys
import pytest
from unittest.mock import patch
from dvhelper import MovieParser

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.mark.parametrize('keyword, use_search_html, expected_result', [
	('ABC-123', True, True),
	('XYZ-456', True, False),
	('ABC-123', False, False),
])
def test_parse_search_results(search_html, keyword, use_search_html, expected_result):
	with patch('dvhelper.config') as mock_config:
		mock_config.search_target_class = 'flex flex-col relative hover:bg-zinc-100 hover:dark:bg-zinc-800'
		mock_config.base_url = 'https://example.com'

		search_html = search_html if use_search_html else ''
		result = MovieParser.parse_search_results(search_html, keyword)

		if expected_result:
			assert result is not None
		else:
			assert result is None

def test_parse_movie_details(detail_html, actress_alias):
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

		result = MovieParser.parse_movie_details('')
		assert result == {}

def test_extract_info_from_list():
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

	parser = MovieParser()
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
	with patch('dvhelper.config') as mock_config:
		mock_config.actress_alias = actress_alias

		parser = MovieParser()
		assert parser._MovieParser__resolve_actress_alias('Alias A1') == 'Actress A'
		assert parser._MovieParser__resolve_actress_alias('Alias A2') == 'Actress A'
		assert parser._MovieParser__resolve_actress_alias('Alias B1') == 'Actress B'
		assert parser._MovieParser__resolve_actress_alias('Unknown Actress') == 'Unknown Actress'
