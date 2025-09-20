# -*- coding: utf-8 -*-
#region Imports
# 标准库导入
import os
import sys
import time
import json
import re
import argparse
from pathlib import Path
import urllib.parse
from datetime import datetime, timedelta
from dataclasses import dataclass

# 第三方库导入
from rich_argparse import RawTextRichHelpFormatter
# 其它第三方库由lazy_import()导入

# XML处理相关导入
from xml.dom import minidom
import xml.etree.ElementTree as ET
#endregion


#region Setup Console
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
#endregion


__version__ = '0.0.3'
__version_info__ = tuple(int(x) for x in __version__.split('.'))


@dataclass
class Config:
	# URLs
	base_url:    str = 'https://avfan.com'
	sign_in_url: str = f'{base_url}/zh-CN/sign_in'
	search_url:  str = f'{base_url}/search?q='

	#region File & Path names
	fanart_image:   str = 'fanart.jpg'
	poster_image:   str = 'poster.jpg'
	cookies_file:  Path = Path(__file__).parent.joinpath('cookies.json')
	completed_path: str = '#整理完成#'
	exclude_path: tuple[str] = (
		completed_path,
	)
	#endregion

	#region Regex pattern
	ignored_keyword_pattern: list[str] = (
		r'(144|240|360|480|720|1080)[Pp]',
		r'[24][Kk]',
		r'\w+2048\.com',
		r'Carib(beancom)?',
		r'[^a-z\d](f?hd|lt)[^a-z\d]',
	)
	ignored_movie_pattern:  re.Pattern = re.compile('|'.join(ignored_keyword_pattern))
	normal_movie_pattern:   re.Pattern = re.compile(r'([A-Z]{2,10})[-_](\d{2,5})', re.I)
	normal_movie_pattern2:  re.Pattern = re.compile(r'([A-Z]{2,})(\d{2,5})', re.I)
	fc2_movie_pattern:      re.Pattern = re.compile(r'FC2[^A-Z\d]{0,5}(PPV[^A-Z\d]{0,5})?(\d{5,7})', re.I)
	_259luxu_movie_pattern: re.Pattern = re.compile(r'259LUXU-(\d+)', re.I)
	#endregion

	# File extensions
	movie_file_extensions: tuple[str] = (
		'.3gp', '.avi', '.f4v', '.flv', '.iso', '.m2ts',
		'.m4v', '.mkv', '.mov', '.mp4', '.mpeg', '.rm',
		'.rmvb', '.ts', '.vob', '.webm', '.wmv', '.strm',
		'.mpg',
	)

	# CSS selectors
	search_target_class: str = 'flex flex-col relative hover:bg-zinc-100 hover:dark:bg-zinc-800'
	movie_target_class:  str = 'flex flex-col gap-2'

	# Exclude actors
	exclude_actors: tuple[str] = (
		'まーち', 'ニック', '大村', '平田司', '鮫島', '畑中哲也', '羽田', 'じゅうもんじ', 'マッスル澤野', '北こうじ',
		'吉野篤史', '南佳也', 'TECH', 'ハカー', '井口', 'タラオ', '日森一', '黒田悠斗', '池沼ミキオ', 'セツネヒデユキ',
		'えりぐち', '貞松大輔', '野島誠', 'ダイ', 'ナイアガラ翔', '矢野慎二', '阿部智広', '志良玉弾吾', '北山シロ',
		'真田京', '西島雄介', '堀内ハジメ', '藍井優太', '左慈半造', 'トニー大木', 'ラリアット黒川', '結城結弦', '中田一平',
		'市川潤', 'かめじろう', 'イセドン内村', '小田切ジュン', '上田昌宏', 'ジャイアント廣田', '杉山', '片山邦生',
		'松本ケン', '武田大樹', 'ようく', '市川哲也', '吉村卓', 'たこにゃん', '大沢真司', '今井勇太', '田淵正浩',
		'桜井ちんたろう',  'アベ', 'ゴロー', '優生', 'Qべぇ', '沢木和也', '岩下たろう', '戸川夏也', '松山伸也',
		'タツ', 'テツ神山', '瀧口', '左曲かおる', '杉浦ボッ樹', 'ウルフ田中', 'ゆうき', 'ピエール剣', '一馬', '--',
		'桐島達也', '七尾神', 'フランクフルト林', 'ナルシス小林', 'カルロス', 'たむらあゆむ', '橋本誠吾', '羽田貴史',
		'森林原人', 'およよ中野', 'ひょこり', '堀尾', 'しめじ', '太刀茜祢', '黒井ゆう', 'マサムー', 'レンジャー鏑木',
		'ドピュー', '佐川銀次', '渋谷優太', 'ハッピー池田',
	)

	#region argparse help messages
	description:   str = f'[b]DV Helper (version [i]{__version__}[/]) - 影片信息搜索和NFO生成工具\n\n  自动搜索影片信息、下载封面图片、生成NFO文件，并按演员分类整理影片\n  支持影片搜索和本地视频批量处理[/]'
	keywords_help: str = '搜索关键词（如影片编号）或本地视频文件夹路径\n可以使用逗号分隔多个关键词，或指定一个包含视频文件的文件夹路径进行批量处理'
	depth_help:    str = '文件夹搜索深度（默认：%(default)s，表示仅搜索当前目录）'
	login_help:    str = '忽略已保存的 Cookie 强制进行新的登录操作'
	gallery_help:  str = '下载影片的剧照和预告片'
	epilog:        str = '''
[argparse.groups]Examples:[/]
  [b]搜索影片编号[/]
    [argparse.prog]%(prog)s[/] [argparse.args]ABCDE-123[/]

    搜索编号为 [argparse.args]ABCDE-123[/] 的影片信息并在当前目录下生成整理好的影片目录
    可以使用逗号分隔多个搜索关键词

  [b]批量处理文件夹中的视频[/]
    [argparse.prog]%(prog)s[/] [argparse.args]/path/to/movies[/] -d [argparse.metavar]1[/]

    扫描指定文件夹及其子目录中的视频文件并生成整理好的影片目录
    使用 -d 参数可以指定子文件夹的扫描深度，否则仅扫描当前目录

  [b]强制重新登录[/]
    [argparse.prog]%(prog)s[/] [argparse.args]ABCDE-123[/] -l

    强制重新登录，忽略已保存的 Cookie 并进行新的登录操作
'''
	#endregion


#region Base Classes
class TqdmOut:
	"""用于将logging的stream输出重定向到tqdm"""
	@classmethod
	def write(cls, s, file=None, nolock=False):
		tqdm.write(s, file=file, end='', nolock=nolock)


class HelpOnErrorParser(argparse.ArgumentParser):
	def error(self, message):
		sys.stderr.write(f'错误: {message}\n')
		self.print_help()
		sys.exit(2)


class MovieInfo(object):
	"""影片信息数据类，统一管理影片相关信息
	
	Attributes:
		detail_url : 影片详情页URL
		fanart_url : 封面图片URL
		number     : 影片编号
		trailer_url: 预告片URL
		galleries  : 剧照URL列表
		title      : 影片标题
		year       : 发行年份
		runtime    : 影片时长(分钟)
		tags       : 标签列表
		actors     : 演员列表
		director   : 导演
		studio     : 制作商
		publisher  : 发行商
		premiered  : 发行日期
		mpaa       : 分级
		country    : 国家/地区
	"""

	def __init__(self, info: dict):
		self.info = info
		self.detail_url:      str = info.get('detail_url', '')
		self.fanart_url:      str = info.get('fanart_url', '')
		self.trailer_url:     str = info.get('trailer_url', '')
		self.galleries: list[str] = info.get('galleries', [])
		self.number:          str = info.get('number', '')
		self.title:           str = info.get('title', '')
		self.year:            str = info.get('year', '')
		self.runtime:         str = info.get('runtime', '')
		self.tags:      list[str] = info.get('tags', [])
		self.actors:    list[str] = info.get('actors', [])
		self.director:        str = info.get('director', '')
		self.studio:          str = info.get('studio', '')
		self.publisher:       str = info.get('publisher', '')
		self.premiered:       str = info.get('premiered', '')
		self.mpaa:            str = info.get('mpaa', 'NC-17')
		self.country:         str = info.get('country', '日本')


class NFOGenerator(object):
	"""NFO文件生成器，将影片信息转换为通用的NFO格式"""

	def __init__(self, movie_info: MovieInfo):
		self.root = ET.Element('movie')
		self.__add_movie_info(movie_info)

	def __add_movie_info(self, movie_info: MovieInfo):
		"""将影片信息添加到XML结构中

		Args:
			movie_info: 包含影片信息的MovieInfo对象
		"""
		# 基本信息
		ET.SubElement(self.root, 'title').text   = movie_info.title
		ET.SubElement(self.root, 'year').text    = movie_info.year
		ET.SubElement(self.root, 'runtime').text = movie_info.runtime
		ET.SubElement(self.root, 'mpaa').text    = movie_info.mpaa

		# 影片编号作为唯一标识
		if movie_info.number:
			uniqueid        = ET.SubElement(self.root, 'uniqueid')
			uniqueid.text   = movie_info.number
			uniqueid.attrib = {'type': 'num', 'default': 'true'}

		# 分类和标签
		if movie_info.tags:
			for genre in movie_info.tags:
				ET.SubElement(self.root, 'genre').text = genre
			for tag in movie_info.tags:
				ET.SubElement(self.root, 'tag').text   = tag

		# 其他元数据
		ET.SubElement(self.root, 'country').text = movie_info.country

		if movie_info.director:
			ET.SubElement(self.root, 'director').text  = movie_info.director
		if movie_info.premiered:
			ET.SubElement(self.root, 'premiered').text = movie_info.premiered
		if movie_info.studio:
			ET.SubElement(self.root, 'studio').text    = movie_info.studio
		if movie_info.publisher:
			ET.SubElement(self.root, 'publisher').text = movie_info.publisher

		# 演员信息
		if movie_info.actors:
			for actor_info in movie_info.actors:
				actor = ET.SubElement(self.root, 'actor')
				ET.SubElement(actor, 'name').text = actor_info

		# 媒体信息
		if movie_info.fanart_url:
			fanart = ET.SubElement(self.root, 'fanart')
			ET.SubElement(fanart, 'thumb').text      = movie_info.fanart_url
		if movie_info.trailer_url:
			ET.SubElement(self.root, 'trailer').text = movie_info.trailer_url

	def save(self, output_path: Path):
		"""将XML结构保存为格式化的NFO文件

		Args:
			output_path: 输出文件路径
		"""
		# 生成格式化的XML字符串
		rough_string = ET.tostring(self.root, 'utf-8')
		reparsed = minidom.parseString(rough_string)
		pretty_xml = reparsed.toprettyxml(
			indent='    ', encoding='utf-8', standalone=True
		).replace(b'&amp;', b'&')

		with open(output_path, 'wb') as f:
			f.write(pretty_xml)


class MovieParser(object):
	"""影片信息解析器，从HTML内容提取影片相关信息"""

	@staticmethod
	def parse_search_results(html: str, keyword: str):
		"""解析搜索结果页面，提取匹配的影片信息

		Args:
			html: 搜索结果页面HTML内容
			keyword: 搜索关键词

		Returns:
			包含影片URL、标题和封面图片URL的字典，未找到则返回None
		"""
		if not html:
			return

		soup = BeautifulSoup(html, 'html.parser')
		elements = soup.find_all(class_=config.search_target_class)

		for element in elements:
			a_tag = element.find('a')

			if not a_tag:
				continue

			href: str    = a_tag.get('href', '')
			title: str   = a_tag.get('title', '').strip()
			img_tag      = a_tag.find('img')
			img_src: str = img_tag.get('src', '')

			if keyword.lower() in title.lower():
				return {
					'detail_url': f'{config.base_url}{href}',
					'title'     : title,
					'fanart_url': img_src
				}
		return

	@staticmethod
	def parse_movie_details(html: str):
		"""解析影片详情页面，提取详细信息

		Args:
			html: 影片详情页HTML内容

		Returns:
			包含影片详细信息的字典，未找到则返回空字典
		"""
		results = {}

		if not html:
			return results

		soup = BeautifulSoup(html, 'html.parser')
		ul_elements = soup.find_all('ul', class_=config.movie_target_class)

		# 提取影片详情
		for ul_element in ul_elements:
			li_elements = ul_element.find_all('li')

			if li_elements:
				li_contents = [li.get_text(strip=True) for li in li_elements]
				results = MovieParser.__extract_info_from_list(li_contents)

		results['galleries'] = []
		a_elements = soup.find_all('a', {'data-fancybox': 'gallery'})

		# 提取预告片和剧照
		for a_tag in a_elements:
			href: str = a_tag.get('href', '')
			data_caption: str = a_tag.get('data-caption', '').strip()

			if data_caption == '预告片':
				results['trailer_url'] = href
			else:
				results['galleries'].append(href)

		return results

	@staticmethod
	def __extract_info_from_list(content_list: list[str]):
		"""从列表内容提取影片信息

		Args:
			content_list: 包含影片信息的字符串列表

		Returns:
			提取的影片信息字典
		"""
		result = {}

		for item in content_list:
			if item.startswith('番号:'):
				result['number'] = item.replace('番号:', '').replace('复制', '').strip()
			elif item.startswith('发行日期:'):
				result['premiered'] = item.replace('发行日期:', '').strip()
				if len(result['premiered']) >= 4:
					result['year'] = result['premiered'][:4]
			elif item.startswith('片长:'):
				result['runtime'] = item.replace('片长:', '').replace(' 分钟', '').strip()
			elif item.startswith('导演:'):
				result['director'] = item.replace('导演:', '').strip()
			elif item.startswith('制作商:'):
				result['studio'] = item.replace('制作商:', '').strip()
			elif item.startswith('发行商:'):
				result['publisher'] = item.replace('发行商:', '').strip()
			elif item.startswith('标签:'):
				result['tags'] = [tag.strip() for tag in item.replace('标签:', '').split(',') if tag.strip()]
			elif item.startswith('演员:'):
				result['actors'] = [actor.strip() for actor in item.replace('演员:', '').split(',') if actor.strip()]
				result['actors'] = [actor for actor in result['actors'] if actor not in config.exclude_actors]

		return result


class MovieScraper(object):
	"""影片信息抓取器，实现登录管理、数据和图片的抓取流程"""

	REQUESTS_HEADERS = {
		'Accept-Language': 'zh-CN,zh;q=0.9',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
	}

	def __init__(self):
		self.__session = None

	def initialize_session(self):
		self.__session = self.check_cookies()

		if not self.__session:
			logger.warning('❌未找到有效Cookies，将使用匿名会话，或使用 -l 参数进行登录操作')

	def check_cookies(self):
		"""检查并加载Cookie，验证有效性

		Returns:
			有效的requests会话对象，Cookies过期或不存在则返回None
		"""
		if not config.cookies_file.exists():
			logger.warning('❌Cookies 文件不存在')
			return

		session = requests.Session()

		try:
			with open(config.cookies_file, 'r', encoding='utf-8') as f:
				cookies: list[dict] = json.load(f)

			for cookie in cookies:
				if 'expiry' in cookie and cookie['name'] == 'remember_token':
					expiry_time = datetime.fromtimestamp(cookie['expiry'])

					if expiry_time < datetime.now() - timedelta(seconds=60):
						logger.warning('❌当前 Cookie 已过期')

						return

				session.cookies.set(
					cookie['name'], 
					cookie['value'],
					domain=cookie.get('domain'),
					path=cookie.get('path', '/'),
					secure=cookie.get('secure', False)
				)

			return session
		except Exception as e:
			logger.error(f'❌Cookies 文件处理失败：{str(e)}')
			return

	def perform_login(self):
		"""使用Selenium执行登录并保存Cookie

		Returns:
			登录后的requests会话对象，登录失败则返回None
		"""
		# 配置Chrome选项
		chrome_options = Options()
		chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

		driver = webdriver.Chrome(options=chrome_options)

		try:
			logger.info('♻正在启动 Chrome 浏览器...')

			print('在弹出的网页中完成登录操作\n'*3)
			driver.get(config.sign_in_url)

			# 等待用户完成登录并重定向
			WebDriverWait(driver, 120).until(
				EC.url_to_be(f'{config.base_url}/')
			)

			# 获取并保存Cookie
			cookies = driver.get_cookies()
			with open(config.cookies_file, 'w', encoding='utf-8') as f:
				json.dump(cookies, f, ensure_ascii=False, indent=2)

			logger.info(f'已保存 {len(cookies)} 个 Cookie 到 {config.cookies_file}')

			# 创建会话并加载Cookie
			session = requests.Session()

			for cookie in cookies:
				session.cookies.set(
					cookie['name'], 
					cookie['value'],
					domain=cookie.get('domain'),
					path=cookie.get('path', '/'),
					secure=cookie.get('secure', False)
				)
		except Exception as e:
			session = None
			logger.error(f'❌用户登录失败')
		finally:
			time.sleep(2)
			driver.quit()

		return session

	def fetch_data(self, url: str, max_retries: int=3, initial_timeout: int=30, backoff_factor: int=2):
		"""获取指定网站的文本内容，支持重试操作

		Args:
			url: 目标网址
			max_retries: 最大重试次数，默认3次
			initial_timeout: 初始超时时间（秒），默认30秒
			backoff_factor: 退避因子，默认2

		Returns:
			响应内容文本，所有重试失败则返回None
		"""

		for retry in range(1, max_retries + 1):
			current_timeout = initial_timeout * (backoff_factor ** (retry - 1))

			if retry > max_retries:
				print(f'第 {retry}/{max_retries} 次尝试（超时时间：{current_timeout} 秒）')

			try:
				if self.__session:
					response =  self.__session.get(url=url, headers=self.REQUESTS_HEADERS, timeout=current_timeout)
				else:
					response = requests.get(url=url, headers=self.REQUESTS_HEADERS, timeout=current_timeout)

				response.encoding = 'utf-8' # response.apparent_encoding
				response.raise_for_status()

				return response.text
			except (RequestException, Timeout) as e:
				if retry >= max_retries:
					return

	def fetch_media(self, movie_path: Path, media_file: str, url: str, crop: bool=False, max_retries=3, initial_timeout=30, backoff_factor=2):
		"""下载影片相关媒体文件（包含影片封面图片、剧照、预告片等）

		从指定地址下载影片媒体文件，支持重试机制，并显示下载进度

		Args:
			movie_path: 媒体文件保存路径
			media_file: 媒体文件名
			url: 媒体文件下载地址
			crop: 是否裁剪图片，默认False
			max_retries: 最大重试次数，默认3次
			initial_timeout: 初始超时时间（秒），默认30秒
			backoff_factor: 退避因子，用于指数退避算法，默认2

		Returns:
			下载和裁剪成功返回True，失败则返回False
		"""
		for retry in range(1, max_retries + 1):
			current_timeout = initial_timeout * (backoff_factor ** (retry - 1))

			if retry > max_retries:
				print(f'第 {retry}/{max_retries} 次尝试（超时时间：{current_timeout} 秒）')

			try:
				response = requests.get(url, stream=True, timeout=current_timeout)
				response.raise_for_status()

				# 获取文件大小
				total_size = int(response.headers.get('content-length', 0))
				chunk_size = 8192

				media_file = movie_path / media_file
				with open(media_file, 'wb') as f:
					with tqdm(total=total_size, unit='B', unit_scale=True, desc=f'媒体文件：{media_file.name}', leave=False, ncols=80, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
						for chunk in response.iter_content(chunk_size=chunk_size):
							if chunk:
								f.write(chunk)
								pbar.update(len(chunk))

				if crop:
					self.crop_image(media_file, movie_path / config.poster_image)

				return True
			except (RequestException, Timeout) as e:
				if retry >= max_retries:
					return False

	def crop_image(self, src_file: Path, dest_file: Path):
		"""裁剪图片以提取右侧指定区域

		Args:
			src_file: 输入图片文件路径
			dest_file: 输出图片文件路径
		"""
		with Image.open(src_file) as source_img:
			width, height = source_img.size

			left = width - 379
			top = 0
			right = width
			bottom = height

			cropped_img = source_img.crop((left, top, right, bottom))
			cropped_img.save(dest_file, format='JPEG')
			source_img.save(src_file, format='JPEG')
#endregion


class DVHelper(MovieScraper):
	"""DV助手主类，协调各模块完成影片信息获取和整理工作"""

	def __init__(self):
		super().__init__()

	def analyze_keyword(self, keyword: str):
		"""从已知信息中分析并提取影片ID

		Args:
			keyword: 已知的影片名称或关键词

		Returns:
			提取的影片ID，否则返回None
		"""
		keyword = config.ignored_movie_pattern.sub('', keyword).upper()

		if 'FC2' in keyword:
			match = config.fc2_movie_pattern.search(keyword)
			if match:
				return f'FC2-{match.group(2)}'
		elif '259LUXU' in keyword:
			match = config._259luxu_movie_pattern.search(keyword)
			if match:
				return f'259LUXU-{match.group(1)}'
		else:
			match = config.normal_movie_pattern.search(keyword)
			if match:
				return match.group(1) + '-' + match.group(2)

			match = config.normal_movie_pattern2.search(keyword)
			if match:
				return match.group(1) + '-' + match.group(2)

	def list_video_files(self, root_dir: Path, max_depth: int=0):
		"""在指定目录中搜索视频文件

		Args:
			root_dir: 根目录路径
			max_depth: 最大搜索深度，0表示仅搜索当前目录

		Returns:
			符合条件的视频文件路径列表
		"""
		found_files = []
		root_depth = len(root_dir.absolute().parts)
		max_depth = max_depth if max_depth >= 0 else 1

		for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
			current_depth = len(Path(dirpath).absolute().parts) - root_depth

			if current_depth > max_depth:
				continue

			# 排除指定名称的文件夹
			dirnames[:] = [dir_name for dir_name in dirnames if dir_name not in config.exclude_path]

			for filename in filenames:
				if any(filename.lower().endswith(ext) for ext in config.movie_file_extensions):
					found_files.append(Path(dirpath) / filename)

		return found_files

	def batch_process(self, keywords: list[str], *, gallery: bool=False, dir_mode: bool=False, root_dir: Path=None):
		"""处理影片的信息搜索与整理

		根据关键词列表或目录路径批量处理影片文件，包括搜索影片信息、下载封面图片、
		剧照、预告片、生成 NFO 文件并按演员分类整理文件结构

		Args:
			keywords: 搜索关键词列表或文件路径列表
			gallery: 是否下载剧照和预告片，默认为False
			dir_mode: 是否为目录模式，默认为False
			root_dir: 目录模式下的根目录，默认为None
		"""

		if dir_mode:
			assert root_dir is not None, '目录模式下必须提供根目录路径'

		failed_movies = []

		for index, item in enumerate(keywords, 1):
			keyword = Path(item).name if dir_mode else item

			print()
			logger.info(f'[{index}/{len(keywords)}] ♻ 正在搜索 {keyword}...')

			movie_id = self.analyze_keyword(keyword)

			if not movie_id:
				logger.warning('❌无法提取影片ID，可以尝试修改文件名后再试')
				failed_movies.append(item)
				continue

			tqdm_steps = 6 if dir_mode else 5

			with trange(tqdm_steps, desc=f'处理 {movie_id}', unit='步', leave=False, ncols=80, bar_format='{l_bar}{bar}|') as step_pbar:
				# 1. 搜索影片
				step_pbar.set_description(f'搜索影片')
				response_text = self.fetch_data(f'{config.search_url}{urllib.parse.quote_plus(movie_id)}')
				search_results = MovieParser.parse_search_results(response_text, movie_id)

				if not search_results:
					logger.warning('❌未找到匹配的影片')
					failed_movies.append(item)
					continue

				step_pbar.update()

				# 2. 获取影片详情
				step_pbar.set_description('获取影片详情')
				response_text = self.fetch_data(search_results['detail_url'])
				movie_details = MovieParser.parse_movie_details(response_text)

				if not movie_details:
					logger.warning('❌无法获取影片详情')
					failed_movies.append(item)
					continue

				step_pbar.update()

				movie_details.update({
					'detail_url': search_results['detail_url'],
					'title'     : search_results['title'],
					'fanart_url': search_results['fanart_url'],
				})

				movie_info = MovieInfo(movie_details)

				# 3. 按演员组织目录结果并创建影片目录
				step_pbar.set_description('创建影片目录')
				actor_count = len(movie_info.actors)

				if actor_count == 0:
					dir1 = '==无名演员=='
				elif actor_count == 1:
					dir1 = movie_info.actors[0]
				else:
					dir1 = '==多演员=='

				base_dir = (Path(root_dir) if dir_mode else Path(os.getcwd())) / config.completed_path
				movie_path = base_dir / dir1 / f'[{movie_info.number}]({movie_info.year})'
				movie_path.mkdir(parents=True, exist_ok=True)
				step_pbar.update()

				# 4. 下载并处理封面图片
				step_pbar.set_description('下载封面图片' + '和剧照' if gallery and movie_info.galleries else '')

				if not self.fetch_media(movie_path, config.fanart_image, movie_info.fanart_url, crop=True):
					logger.warning('❌封面图片下载失败')
					failed_movies.append(item)
					continue

				# 下载剧照
				if gallery and movie_info.galleries:
					for i, gallery_url in enumerate(movie_info.galleries):
						_, ext = os.path.splitext(gallery_url.split('?')[0])
						ext = ext.lower() if ext else '.jpg'
						self.fetch_media(movie_path, f'gallery_{i:02d}{ext}', gallery_url)

				# 下载预告片
				if gallery and movie_info.trailer_url:
					_, ext = os.path.splitext(movie_info.trailer_url.split('?')[0])
					ext = ext.lower() if ext else '.mp4'
					self.fetch_media(movie_path, f'{movie_info.number}_trailer{ext}', movie_info.trailer_url)

				step_pbar.update()

				# 5. 生成NFO文件
				step_pbar.set_description(f'生成 NFO 文件')
				nfo = NFOGenerator(movie_info)
				nfo.save(f'{movie_path}/{movie_info.number}.nfo')
				step_pbar.update()

				# 6. 移动影片源文件到整理后的文件夹并改名
				if dir_mode:
					step_pbar.set_description(f'移动影片文件')

					old_path = Path(item)
					new_path = movie_path / old_path.with_stem(movie_info.number.upper())\
													.with_suffix(old_path.suffix.lower()).name

					if new_path.exists():
						logger.warning(f'❌影片文件已存在，请自行比较后手动操作。源文件：{root_dir / old_path}，目标文件：{new_path}')
						continue

					old_path.rename(new_path)
					step_pbar.update()

				logger.info(f'✔ 影片相关文件已保存至：{movie_path}')

		print()
		logger.info(f'搜索完成，共搜索整理 {len(keywords)} 部影片，其中 {len(failed_movies)} 部影片获取信息失败')

		if failed_movies:
			print('获取信息失败的影片：')
			for index, movie in enumerate(failed_movies, 1):
				print(f'    {index}.{Path(movie).relative_to(root_dir) if dir_mode else movie}')


def lazy_import():
	global logger
	global requests, RequestException, Timeout
	global BeautifulSoup, Image
	global webdriver, WebDriverWait, EC, Options
	global tqdm, trange

	import requests
	from requests.exceptions import RequestException, Timeout
	from bs4 import BeautifulSoup
	from PIL import Image
	from selenium import webdriver
	from selenium.webdriver.support.ui import WebDriverWait
	from selenium.webdriver.support import expected_conditions as EC
	from selenium.webdriver.chrome.options import Options
	from tqdm import tqdm, trange

	logger = get_logger()

def get_logger():
	import logging

	logger = logging.getLogger(__name__)
	logger.setLevel(logging.INFO)

	# 移除现有的处理器，避免重复
	if logger.hasHandlers():
		logger.handlers = []

	# 文件处理器 - 详细格式用于持久化
	file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	file_handler = logging.FileHandler('dvhelper.log', encoding='utf-8')
	file_handler.setFormatter(file_formatter)

	# 控制台处理器 - 简洁格式用于控制台显示
	console_formatter = logging.Formatter('%(message)s')
	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setFormatter(console_formatter)
	console_handler.stream = TqdmOut

	# 添加处理器到日志器
	logger.addHandler(file_handler)
	logger.addHandler(console_handler)

	return logger

def main():
	"""应用程序入口点"""

	global config
	config = Config()

	parser = HelpOnErrorParser(
		description=config.description,
		usage='%(prog)s [options] keywords_or_path',
		formatter_class=RawTextRichHelpFormatter,
		# epilog=config.epilog
	)

	parser.add_argument('-v', '--version', action='version', version=f'[argparse.prog]DV Helper[/] (version [i]{__version__}[/])')
	parser.add_argument('keywords_or_path', type=str, help=config.keywords_help)
	parser.add_argument('-d', '--depth', type=int, default=0, help=config.depth_help)
	parser.add_argument('-g', '--gallery', action='store_true', help=config.gallery_help)
	parser.add_argument('-l', '--login', action='store_true', help=config.login_help)

	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(0)

	lazy_import()

	dv_helper = DVHelper()
	args = parser.parse_args()
	keywords_or_path: str = args.keywords_or_path

	if args.login:
		if dv_helper.perform_login() is None:
			sys.exit(0)

	dv_helper.initialize_session()

	if Path(keywords_or_path).absolute().is_dir():
		root_dir = Path(keywords_or_path)
		found_files = dv_helper.list_video_files(root_dir, max_depth=args.depth)

		if found_files:
			logger.info(f'发现 {len(found_files)} 个视频文件')
			for index, file_path in enumerate(found_files, 1):
				print(f'    {index}.{Path(file_path).relative_to(root_dir)}')

			dv_helper.batch_process(found_files, gallery=args.gallery, dir_mode=True, root_dir=root_dir)
		else:
			logger.info(f"在 {root_dir} {'及其子目录' if args.depth > 0 else ''}中未发现视频文件")
	else:
		keywords = [keyword.strip() for keyword in keywords_or_path.split(',')]
		logger.info(f'待处理 {len(keywords)} 个影片关键词')

		for index, keyword in enumerate(keywords, 1):
			print(f'    {index}.{keyword}')

		dv_helper.batch_process(keywords, gallery=args.gallery)


if __name__ == '__main__':
	main()
