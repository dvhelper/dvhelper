"""pytest 共享配置和 fixture"""
import sys
import os
import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dvhelper
dvhelper.lazy_import()

from dvhelper import Config, MovieInfo, DVHelper
dvhelper.config = Config()


@pytest.fixture(scope="session", autouse=True)
def setup_dvhelper():
	with patch('dvhelper.requests') as mock_requests:
		mock_response = MagicMock()
		mock_response.text = '<html>Test Content</html>'
		mock_response.raise_for_status.return_value = None
		mock_requests.get.return_value = mock_response
		mock_requests.Session.return_value = MagicMock()
		yield

@pytest.fixture
def temp_dir():
	temp_dir = tempfile.mkdtemp()
	yield Path(temp_dir)
	shutil.rmtree(temp_dir)

@pytest.fixture
def config():
	return Config()

@pytest.fixture
def movie_info_dict():
	return {
		'detail_url': 'https://example.com/movie/123',
		'fanart_url': 'https://example.com/image.jpg',
		'trailer_url': 'https://example.com/trailer.mp4',
		'galleries': ['https://example.com/gallery1.jpg', 'https://example.com/gallery2.jpg'],
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
def empty_movie_info_dict():
	return {
		'title': 'Test Movie',
		'year': '2023',
		'runtime': '120',
		'mpaa': 'NC-17',
		'country': 'Japan'
	}

@pytest.fixture
def movie_info(movie_info_dict):
	return MovieInfo(movie_info_dict)

@pytest.fixture
def empty_movie_info(empty_movie_info_dict):
	return MovieInfo(empty_movie_info_dict)

@pytest.fixture
def search_html():
	return '''
	<div class="flex flex-col relative hover:bg-zinc-100 hover:dark:bg-zinc-800">
		<a href="/movie/123" title="ABC-123 Test Movie">
			<img src="https://example.com/image.jpg" alt="Test Movie">
		</a>
	</div>
	<div class="flex flex-col relative hover:bg-zinc-100 hover:dark:bg-zinc-800">
	</div>
	'''

@pytest.fixture
def detail_html():
	return '''
	<ul class="flex flex-col gap-2">
		<li>番号:ABC-123复制</li>
		<li>发行日期:2023-01-01</li>
		<li>片长:120 分钟</li>
		<li>导演:Director X</li>
		<li>制作商:Studio Y</li>
		<li>发行商:Publisher Z</li>
		<li>标签:tag1,tag2</li>
		<li>演员:Actress A,Actress B,<a class="male">Actress Male</a></li>
		<li>凑数</li>
	</ul>
	<a href="https://example.com/trailer.mp4" data-fancybox="gallery" data-caption="预告片"></a>
	<a href="https://example.com/gallery1.jpg" data-fancybox="gallery"></a>
	<a href="https://example.com/gallery2.jpg" data-fancybox="gallery"></a>
	'''

@pytest.fixture
def crop_image(temp_dir):
	src_file = Path(temp_dir) / 'source.jpg'
	dest_file = Path(temp_dir) / 'destination.jpg'
	return {
		'src_file': src_file,
		'dest_file': dest_file
	}

@pytest.fixture
def nfo_save_file(temp_dir):
	return Path(temp_dir) / 'TEST-001.nfo'

@pytest.fixture
def actress_alias():
	return {
		'Actress A': ['Alias A1', 'Alias A2'],
		'Actress B': ['Alias B1']
	}

@pytest.fixture
def dv_helper():
	return DVHelper()

@pytest.fixture
def movie_folders(temp_dir):
	source_folder = Path(temp_dir) / 'source_movie'
	target_folder = Path(temp_dir) / 'target_movie'
	source_folder.mkdir()
	target_folder.mkdir()

	# 1. source_size > target_size
	source_movie_large = source_folder / 'movie1.mp4'
	with open(source_movie_large, 'w') as f:
		f.write('source large movie content' * 300)

	target_movie_small = target_folder / 'movie1.mp4'
	with open(target_movie_small, 'w') as f:
		f.write('target small movie content')

	# 2. source_size <= target_size
	source_movie_small = source_folder / 'movie2.mp4'
	with open(source_movie_small, 'w') as f:
		f.write('source small movie content')

	target_movie_large = target_folder / 'movie2.mp4'
	with open(target_movie_large, 'w') as f:
		f.write('target large movie content' * 200)

	# 3. movie_name not in target_movies
	source_movie_new = source_folder / 'movie3.mp4'
	with open(source_movie_new, 'w') as f:
		f.write('new movie content')

	# 4. other files
	with open(source_folder / 'poster.jpg', 'w') as f:
		f.write('poster content')

	# 5. other files unlink
	with open(source_folder / 'info.txt', 'w') as f:
		f.write('source info content')
	with open(target_folder / 'info.txt', 'w') as f:
		f.write('target info content')

	original_target_small_size = target_movie_small.stat().st_size
	original_target_large_size = target_movie_large.stat().st_size

	return {
		'source_folder': source_folder,
		'target_folder': target_folder,
		'original_target_small_size': original_target_small_size,
		'original_target_large_size': original_target_large_size
	}

@pytest.fixture(params=[
	(True), # subfolder exists
	(False),
])
def folders(temp_dir, request):
	source_folder = Path(temp_dir) / 'source'
	target_folder = Path(temp_dir) / 'target'
	source_folder.mkdir()
	target_folder.mkdir()

	target_subfolder_exists = request.param

	with open(source_folder / 'file1.txt', 'w') as f:
		f.write('test1')

	source_subfolder = source_folder / 'subfolder'
	source_subfolder.mkdir()
	with open(source_subfolder / 'subfile.txt', 'w') as f:
		f.write('subfolder content')

	target_subfolder = target_folder / 'subfolder'
	if target_subfolder_exists:
		target_subfolder.mkdir()
		with open(target_subfolder / 'existing_file.txt', 'w') as f:
			f.write('existing content')

	result = {
		'source_folder': source_folder,
		'target_folder': target_folder,
		'source_subfolder': source_subfolder
	}

	if target_subfolder_exists:
		result['target_subfolder'] = target_folder / 'subfolder'
	return result

@pytest.fixture
def folders_basic(temp_dir):
	source_folder = Path(temp_dir) / 'source'
	target_folder = Path(temp_dir) / 'target'
	source_folder.mkdir()
	target_folder.mkdir()

	with open(source_folder / 'file1.txt', 'w') as f:
		f.write('test1')

	return {
		'source_folder': source_folder,
		'target_folder': target_folder
	}

@pytest.fixture
def video_files(temp_dir):
	video1 = Path(temp_dir) / 'movie1.mp4'
	video2 = Path(temp_dir) / 'movie2.mkv'
	text_file = Path(temp_dir) / 'document.txt'
	ignored_file = Path(temp_dir) / '##hidden_file.mp4'
	sub_dir = Path(temp_dir) / 'subdir'
	video3 = sub_dir / 'movie3.avi'
	deep_sub_dir = sub_dir / 'deepdir'
	video4 = deep_sub_dir / 'movie4.mov'

	video1.touch()
	video2.touch()
	text_file.touch()
	ignored_file.touch()
	sub_dir.mkdir(exist_ok=True)
	video3.touch()
	deep_sub_dir.mkdir(exist_ok=True)
	video4.touch()

	return {
		'base_dir': Path(temp_dir),
		'video1': video1,
		'video2': video2,
		'video3': video3,
		'video4': video4,
		'text_file': text_file,
		'ignored_file': ignored_file,
		'sub_dir': sub_dir,
		'deep_sub_dir': deep_sub_dir
	}

@pytest.fixture
def actress_folders_with_alias(temp_dir):
	"""创建演员文件夹和别名测试所需的目录结构"""
	actress_dir = Path(temp_dir) / 'Alias A1'
	actress_dir.mkdir(exist_ok=True)
	actress_alias = {'Actress A': ['Alias A1', 'Alias A2']}

	return {
		'base_dir': Path(temp_dir),
		'actress_alias': actress_alias
	}

@pytest.fixture
def test_video_file(temp_dir):
	"""创建测试用视频文件"""
	video_file = temp_dir / 'movie.mp4'
	video_file.touch()

	return {
		'base_dir': Path(temp_dir),
		'video_file': video_file
	}
