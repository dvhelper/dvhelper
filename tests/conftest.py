#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""pytest 共享配置和fixture"""
import sys
import os
import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# 确保可以导入被测试模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入dvhelper模块并初始化
sys.modules['dvhelper'] = __import__('dvhelper')
import dvhelper
# 调用lazy_import初始化所有依赖
dvhelper.lazy_import()

# 从dvhelper模块导入所有需要的类和函数
from dvhelper import (
	Config, MovieInfo, NFOGenerator, MovieParser, MovieScraper, DVHelper,
	set_language, get_logger, lazy_import, TqdmOut, HelpOnErrorParser
)


# 模拟全局config变量，dvhelper模块在main()函数中定义config
dvhelper.config = Config()

@pytest.fixture(scope="session", autouse=True)
def setup_dvhelper():
	"""全局设置，确保lazy_import被调用并初始化必要的全局变量"""
	# 确保全局config变量存在
	if not hasattr(dvhelper, 'config'):
		dvhelper.config = Config()
	
	# 确保全局logger变量存在
	if not hasattr(dvhelper, 'logger'):
		dvhelper.logger = get_logger()

	# 模拟requests模块，避免实际网络请求
	with patch('dvhelper.requests') as mock_requests:
		mock_response = MagicMock()
		mock_response.text = '<html>Test Content</html>'
		mock_response.raise_for_status.return_value = None
		mock_requests.get.return_value = mock_response
		mock_requests.Session.return_value = MagicMock()
		yield

@pytest.fixture
def temp_dir():
	"""创建临时目录的fixture"""
	temp_dir = tempfile.mkdtemp()
	yield Path(temp_dir)
	# 清理临时目录
	shutil.rmtree(temp_dir)

@pytest.fixture
def config():
	"""Config实例的fixture"""
	return Config()

@pytest.fixture
def movie_info_dict():
	"""影片信息字典的fixture"""
	return {
		'detail_url': 'https://example.com/movie/123',
		'fanart_url': 'https://example.com/image.jpg',
		'number': 'ABC-123',
		'title': 'Test Movie',
		'year': '2023',
		'runtime': '120',
		'tags': ['tag1', 'tag2'],
		'actresses': ['Actress A', 'Actress B'],
		'director': 'Director X',
		'studio': 'Studio Y',
		'publisher': 'Publisher Z',
		'premiered': '2023-01-01',
		'mpaa': 'NC-17',
		'country': 'Japan'
	}

@pytest.fixture
def movie_info(movie_info_dict):
	"""MovieInfo实例的fixture"""
	return MovieInfo(movie_info_dict)

@pytest.fixture
def search_html():
	"""模拟的搜索结果HTML的fixture"""
	return '''
	<div class="flex flex-col relative hover:bg-zinc-100 hover:dark:bg-zinc-800">
		<a href="/movie/123" title="ABC-123 Test Movie">
			<img src="https://example.com/image.jpg" alt="Test Movie">
		</a>
	</div>
	'''

@pytest.fixture
def detail_html():
	"""模拟的影片详情HTML的fixture"""
	return '''
	<ul class="flex flex-col gap-2">
		<li>番号:ABC-123复制</li>
		<li>发行日期:2023-01-01</li>
		<li>片长:120 分钟</li>
		<li>导演:Director X</li>
		<li>制作商:Studio Y</li>
		<li>发行商:Publisher Z</li>
		<li>标签:tag1,tag2</li>
		<li>演员:Actress A,Actress B</li>
	</ul>
	<a href="https://example.com/trailer.mp4" data-fancybox="gallery" data-caption="预告片"></a>
	<a href="https://example.com/gallery1.jpg" data-fancybox="gallery"></a>
	<a href="https://example.com/gallery2.jpg" data-fancybox="gallery"></a>
	'''

@pytest.fixture
def actress_alias():
	"""模拟的演员别名配置的fixture"""
	return {
		'Actress A': ['Alias A1', 'Alias A2'],
		'Actress B': ['Alias B1']
	}

@pytest.fixture
def dv_helper():
	"""DVHelper实例的fixture"""
	return DVHelper()


# 可测试的MovieScraper子类
class TestableMovieScraper(MovieScraper):
	"""可测试的MovieScraper子类，用于测试"""
	__test__ = False  # 告诉pytest不要将此类作为测试类收集
	
	def __init__(self):
		"""初始化测试类"""
		super().__init__()
		# 初始化会话为一个模拟对象
		self.__session = MagicMock()
		# 用于存储调用历史
		self.call_history = []
		# 默认行为是成功
		self.should_succeed = True
		# 用于模拟响应
		self.mock_response = '<html>Test Content</html>'
		# 用于模拟异常
		self.mock_exception = Exception('Request failed')
	
	def fetch_data(self, url, max_retries=3, initial_timeout=30, backoff_factor=2):
		"""重写fetch_data方法，避免实际的HTTP请求"""
		# 记录调用
		self.call_history.append({
			'url': url,
			'max_retries': max_retries,
			'initial_timeout': initial_timeout,
			'backoff_factor': backoff_factor,
			'is_media': False
		})
		
		# 根据should_succeed决定返回内容或None（按照实际方法的返回值行为）
		if self.should_succeed:
			return self.mock_response
		else:
			return None
	
	def fetch_media(self, movie_path, media_file, url, crop=False, max_retries=3, initial_timeout=30, backoff_factor=2):
		"""重写fetch_media方法，避免实际的HTTP请求和文件操作"""
		# 记录调用
		self.call_history.append({
			'movie_path': movie_path,
			'media_file': media_file,
			'url': url,
			'crop': crop,
			'max_retries': max_retries,
			'initial_timeout': initial_timeout,
			'backoff_factor': backoff_factor,
			'is_media': True
		})
		
		# 根据should_succeed决定返回True或False
		return self.should_succeed
	
	def check_cookies(self):
		"""重写check_cookies方法，返回一个模拟的会话"""
		mock_session = MagicMock()
		return mock_session


@pytest.fixture
def testable_movie_scraper():
	"""TestableMovieScraper实例的fixture"""
	return TestableMovieScraper()
