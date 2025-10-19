# -*- coding: utf-8 -*-
"""
This file is part of the DV Helper project, https://github.com/dvhelper/dvhelper
The MIT License (MIT)
Copyright © 2025 Walkline Wang <walkline@gmail.com>
"""
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
from dataclasses import dataclass, field
import locale
import gettext

# 第三方库导入，其它第三方库由 lazy_import() 导入
from lxml import etree as ET
from rich_argparse import RawTextRichHelpFormatter
from colorama import Fore, Style

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
#endregion


#region Setup Console
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
#endregion


__version__ = '0.0.9.2'
__version_info__ = tuple(int(x) for x in __version__.split('.'))


def set_language(lang: str = 'zh_CN'):
	gettext.install('dvhelper')

	i18n_dir = Path(__file__).parent / 'i18n'
	if not i18n_dir.exists():
		return

	if lang != 'zh_CN': # default language
		try:
			gettext.translation('dvhelper', localedir=str(i18n_dir), languages=[lang]).install()
		except FileNotFoundError:
			try:
				gettext.translation('dvhelper', localedir=str(i18n_dir), languages=['en_US']).install()
			except FileNotFoundError:
				pass

set_language(locale.getdefaultlocale()[0])


@dataclass
class Config:
	# URLs
	base_url:    str = 'https://avfan.com'
	sign_in_url: str = f'{base_url}/zh-CN/sign_in'
	search_url:  str = f'{base_url}/search?q='

	#region File & Path names
	fanart_image:        str = 'fanart.jpg'
	poster_image:        str = 'poster.jpg'
	cookies_file:       Path = Path(__file__).parent / 'cookies.json'
	actress_alias_file: Path = Path(__file__).parent / 'actress_alias.json'
	completed_path:      str = _('#整理完成#')
	ignored_file_prefix: str = '##'
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
	_200gana_movie_pattern: re.Pattern = re.compile(r'200GANA-(\d+)', re.I)
	_300mium_movie_pattern: re.Pattern = re.compile(r'300MIUM-(\d+)', re.I)
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

	# Actress name map
	actress_alias: dict[str, list[str]] = field(default_factory=dict)

	#region argparse help messages
	description:   str = f'[b]DV Helper (version [i]{__version__}[/]) - ' + _('影片信息搜索工具\n\n  自动搜索影片信息，下载封面、剧照图片以及预告片，生成NFO文件，\n  并按演员分类整理影片，支持在线搜索影片信息和批量处理本地影片目录。')
	keywords_help: str = _('搜索关键词（如影片编号）或本地影片目录路径\n可以使用逗号分隔多个关键词，或指定一个包含影片文件的目录进行批量处理')
	depth_help:    str = _('目录搜索深度（默认: %(default)s，表示仅搜索当前目录）')
	gallery_help:  str = _('下载影片剧照和预告片')
	login_help:    str = _('忽略已保存的 Cookie 强制进行新的登录操作')
	organize_help: str = _('整理并重命名指定目录下的影片文件夹')
	epilog:        str = '''
[argparse.groups]Examples:[/]
  [b]搜索影片编号[/]
    [argparse.prog]%(prog)s[/] [argparse.args]ABCDE-123[/]

    搜索编号为 [argparse.args]ABCDE-123[/] 的影片信息并在当前目录下生成整理好的影片目录
    可以使用逗号分隔多个搜索关键词

  [b]批量处理目录中的影片文件[/]
    [argparse.prog]%(prog)s[/] [argparse.args]/path/to/movies[/] -d [argparse.metavar]1[/]

    扫描指定目录及其子目录中的影片文件并生成整理好的影片目录
    使用 -d 参数可以指定子目录的扫描深度，否则仅扫描当前目录

  [b]强制重新登录[/]
    [argparse.prog]%(prog)s[/] [argparse.args]ABCDE-123[/] -l

    强制重新登录，忽略已保存的 Cookie 并进行新的登录操作

  [b]整理并重命名影片文件夹[/]
    [argparse.prog]%(prog)s[/] [argparse.args]/path/to/movies[/] -o

    整理并重命名指定目录下的影片文件夹，不会实际执行文件操作
    该功能会根据actress_alias.json中的映射表递归查找并识别需要重命名的文件夹
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
		sys.stderr.write(f'{Style.BRIGHT}{Fore.RED}' + _('错误: ') + message + f'{Style.RESET_ALL}\n\n')
		self.print_help()
		sys.exit(2)


class MovieInfo():
	"""
	影片信息数据类，统一管理影片相关信息
	
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
		actresses  : 女演员列表
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
		self.actresses: list[str] = info.get('actresses', [])
		self.director:        str = info.get('director', '')
		self.studio:          str = info.get('studio', '')
		self.publisher:       str = info.get('publisher', '')
		self.premiered:       str = info.get('premiered', '')
		self.mpaa:            str = info.get('mpaa', 'NC-17')
		self.country:         str = info.get('country', _('日本'))


class NFOGenerator():
	"""NFO文件生成器，将影片信息转换为通用的NFO格式"""
	def __init__(self, movie_info: MovieInfo):
		self.root = ET.Element('movie')
		self.__add_movie_info(movie_info)

	def __add_movie_info(self, movie_info: MovieInfo):
		"""
		将影片信息添加到XML结构中

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
			uniqueid = ET.SubElement(self.root, 'uniqueid')
			uniqueid.text = movie_info.number
			uniqueid.set('type', 'num')
			uniqueid.set('default', 'true')

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

		# 女演员信息
		if movie_info.actresses:
			for actress_info in movie_info.actresses:
				actress = ET.SubElement(self.root, 'actress')
				ET.SubElement(actress, 'name').text = actress_info

		# 媒体信息
		if movie_info.fanart_url:
			fanart = ET.SubElement(self.root, 'fanart')
			ET.SubElement(fanart, 'thumb').text      = movie_info.fanart_url
		if movie_info.trailer_url:
			ET.SubElement(self.root, 'trailer').text = movie_info.trailer_url

	def save(self, output_path: Path):
		"""
		将XML结构保存为格式化的NFO文件

		Args:
			output_path: 输出文件路径
		"""
		ET.indent(self.root, space='    ')
		pretty_xml = ET.tostring(
			self.root,
			encoding='utf-8',
			pretty_print=True,
			xml_declaration=True,
			standalone=True
		).replace(b'&amp;', b'&')

		with open(output_path, 'w', encoding='utf-8') as f:
			f.write(pretty_xml.decode('utf-8'))


class MovieParser():
	"""影片信息解析器，从HTML内容提取影片相关信息"""
	@staticmethod
	def parse_search_results(html: str, keyword: str):
		"""
		解析搜索结果页面，提取匹配的影片信息

		Args:
			html: 搜索结果页面HTML内容
			keyword: 搜索关键词

		Returns:
			包含影片URL、标题和封面图片URL的字典，未找到则返回None
		"""
		if not html:
			return

		from lxml import etree

		parser = etree.HTMLParser()
		tree = etree.fromstring(html, parser)
		xpath = f'//div[contains(@class, "{config.search_target_class}")]'
		elements = tree.xpath(xpath)

		for element in elements:
			a_tag = element.find('./a')

			if a_tag is None:
				continue

			href:    str = a_tag.get('href', '')
			title:   str = a_tag.get('title', '').strip()
			img_tag      = a_tag.find('./img')
			img_src: str = img_tag.get('src', '') if img_tag is not None else ''

			if keyword.lower() in title.lower():
				return {
					'detail_url': f'{config.base_url}{href}',
					'title'     : title,
					'fanart_url': img_src
				}
		return

	@staticmethod
	def parse_movie_details(html: str):
		"""
		解析影片详情页面，提取详细信息

		Args:
			html: 影片详情页HTML内容

		Returns:
			包含影片详细信息的字典，未找到则返回空字典
		"""
		results = {}

		if not html:
			return results

		from lxml import etree

		parser = etree.HTMLParser()
		tree = etree.fromstring(html, parser)
		xpath = f'//ul[contains(@class, "{config.movie_target_class}")]'
		ul_elements = tree.xpath(xpath)

		for ul_element in ul_elements:
			li_elements = ul_element.findall('./li')

			li_contents = []
			for li in li_elements:
				male_elements = li.xpath('./a[@class="male"]')
				for male_a in male_elements:
					li.remove(male_a)
				text_content = ''.join(li.xpath('.//text()')).strip()
				li_contents.append(text_content)

			results = MovieParser.__extract_info_from_list(li_contents)

		results['galleries'] = []
		a_elements = tree.xpath('//a[@data-fancybox="gallery"]')

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
		"""
		从列表内容提取影片信息

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
				result['tags'] = [tag.strip() for tag in item.replace('标签:', '').replace('--', '').split(',') if tag.strip()]
			elif item.startswith('演员:'):
				result['actresses'] = [actress.strip() for actress in item.replace('演员:', '').replace('--', '').split(',') if actress.strip()]

				if len(config.actress_alias):
					result['actresses'] = [MovieParser.__resolve_actress_alias(actress) for actress in result['actresses']]

		return result

	@staticmethod
	# https://github.com/Yuukiy/JavSP/blob/master/javsp/__main__.py#L53
	def __resolve_actress_alias(name: str):
		"""将别名解析为固定的名字"""
		for fixed_name, aliases in config.actress_alias.items():
			if name in aliases:
				return fixed_name

		return name


class MovieScraper():
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
			logger.warning(_('未找到有效Cookies，将使用匿名会话，或使用 -l 参数重新登录'))

	def check_cookies(self):
		"""
		检查并加载Cookie，验证有效性

		Returns:
			有效的requests会话对象，Cookies过期或不存在则返回None
		"""
		if not config.cookies_file.exists():
			return

		session = requests.Session()

		try:
			with open(config.cookies_file, 'r', encoding='utf-8') as f:
				cookies: list[dict] = json.load(f)

			for cookie in cookies:
				if 'expiry' in cookie and cookie['name'] == 'remember_token':
					expiry_time = datetime.fromtimestamp(cookie['expiry'])

					if expiry_time < datetime.now() - timedelta(seconds=60):
						logger.warning(_('当前 Cookie 已过期'))

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
			logger.error(_('Cookies 文件处理失败: ') + str(e))
			return

	def perform_login(self):
		"""
		通过浏览器模拟登录，获取Cookie

		Returns:
			登录后的requests会话对象，登录失败则返回None
		"""
		from selenium import webdriver
		from selenium.webdriver.support.ui import WebDriverWait
		from selenium.webdriver.support import expected_conditions as EC
		from selenium.webdriver.chrome.options import Options
		from webdriver_manager.chrome import ChromeDriverManager
		from selenium.webdriver.chrome.service import Service

		# 配置Chrome选项
		chrome_options = Options()
		chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

		# 使用webdriver-manager自动管理ChromeDriver
		driver = None
		try:
			service = Service(ChromeDriverManager().install())
			driver = webdriver.Chrome(service=service, options=chrome_options)
		except:
			driver = webdriver.Chrome(options=chrome_options)

		try:
			logger.info(_('正在启动 Chrome 浏览器...'))

			print(_('在弹出的网页中完成登录操作，等待浏览器自动关闭！\n')*3)
			driver.get(config.sign_in_url)

			# 等待用户完成登录并重定向
			WebDriverWait(driver, 3 * 60).until(
				EC.url_to_be(f'{config.base_url}/')
			)

			# 获取并保存Cookie
			cookies = driver.get_cookies()
			with open(config.cookies_file, 'w', encoding='utf-8') as f:
				json.dump(cookies, f, ensure_ascii=False, indent=2)

			logger.info(_('已保存 {count} 个 Cookie 到 {file}')
				.format(count=len(cookies), file=config.cookies_file))

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
		except Exception:
			session = None
			logger.error(_('用户登录失败'))
		finally:
			time.sleep(2)
			driver.quit()

		return session

	def fetch_data(self, url: str, max_retries: int=3, initial_timeout: int=30, backoff_factor: int=2):
		"""
		获取指定网站的文本内容，支持重试操作

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

			if retry > 1:
				print(_('第 {retry}/{retries} 次尝试（超时时间: {timeout} 秒）')
					.format(retry=retry, retries=max_retries, timeout=current_timeout))

			try:
				if self.__session:
					response =  self.__session.get(url=url, headers=self.REQUESTS_HEADERS, timeout=current_timeout)
				else:
					response = requests.get(url=url, headers=self.REQUESTS_HEADERS, timeout=current_timeout)

				response.encoding = 'utf-8' # response.apparent_encoding
				response.raise_for_status()

				return response.text
			except (RequestException, Timeout):
				if retry >= max_retries:
					return

	def fetch_media(self, movie_path: Path, media_file: str, url: str, crop: bool=False, max_retries=3, initial_timeout=30, backoff_factor=2):
		"""
		下载影片相关媒体文件（包含影片封面图片、剧照、预告片等）

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

			if retry > 1:
				print(_('第 {retry}/{retries} 次尝试（超时时间: {timeout} 秒）')
					.format(retry=retry, retries=max_retries, timeout=current_timeout))

			try:
				response = requests.get(url, stream=True, timeout=current_timeout)
				response.raise_for_status()

				# 获取文件大小
				total_size = int(response.headers.get('content-length', 0))
				chunk_size = 8192

				media_file = movie_path / media_file
				with open(media_file, 'wb') as f:
					with tqdm(total=total_size, unit='B', unit_scale=True, desc=_('媒体文件 - ') + media_file.name, leave=False, ncols=80, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
						for chunk in response.iter_content(chunk_size=chunk_size):
							if chunk:
								f.write(chunk)
								pbar.update(len(chunk))

				if crop:
					self.crop_image(media_file, movie_path / config.poster_image)

				return True
			except (RequestException, Timeout):
				if retry >= max_retries:
					return False

	def crop_image(self, src_file: Path, dest_file: Path):
		"""
		裁剪图片以提取右侧指定区域

		Args:
			src_file: 输入图片文件路径
			dest_file: 输出图片文件路径
		"""
		from PIL import Image

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

	def organize_folders(self, root_dir: Path):
		"""
		整理指定目录下的影片文件夹

		Args:
			root_dir: 要整理的根目录
		"""
		# 构建反向别名映射表，用于快速查找固定名称
		reverse_alias_map = {}
		for fixed_name, aliases in config.actress_alias.items():
			for alias in aliases:
				reverse_alias_map[alias] = fixed_name

		# 收集所有子目录中的需要处理的文件夹
		def collect_folders_recursive(directory: Path):
			for item in directory.iterdir():
				if item.is_dir():
					fixed_name = reverse_alias_map.get(item.name)

					if fixed_name:
						if item.name == fixed_name:
							continue

						folders_to_process.append((item, fixed_name))
					else:
						collect_folders_recursive(item)

		folders_to_process = []
		collect_folders_recursive(root_dir)

		if not folders_to_process:
			logger.info(_('未发现需要整理的影片文件夹'))
			return

		logger.info(_('发现 {count} 个需要整理的影片文件夹:').format(count=len(folders_to_process)))

		for index, (source_folder, target_name) in enumerate(folders_to_process, 1):
			print(f'    {index}.{Path(source_folder).relative_to(root_dir)}')

		# 处理每个需要重命名的目录
		for index, (source_folder, target_name) in enumerate(folders_to_process, start=1):
			target_folder = source_folder.parent / target_name

			print()
			logger.info(f'[{index}/{len(folders_to_process)}] ' + _('正在处理: {folder}...')
				.format(folder=source_folder))

			try:
				if not target_folder.exists():
					source_folder.rename(target_folder)
					logger.info(_('影片文件夹已重命名为: ') + str(target_folder))
				else:
					logger.info(_('目标文件夹 {folder} 已存在，正在合并文件夹...')
						.format(folder=target_folder))
					self.__merge_folders(source_folder, target_folder)
					logger.info(_('已完成与目标文件夹 {folder} 的合并')
						.format(folder=target_folder))
			except Exception as e:
				logger.error(_('处理文件夹 {folder} 时出错: {error}')
					.format(folder=source_folder, error=str(e)))

	def __merge_folders(self, source_folder: Path, target_folder: Path):
		"""
		合并两个文件夹的内容

		Args:
			source_folder: 源文件夹
			target_folder: 目标文件夹
		"""
		for item in source_folder.iterdir():
			if item.is_dir():
				target_item = target_folder / item.name
				if target_item.exists() and target_item.is_dir():
					logger.info(_('正在比较文件夹: {folder}...').format(folder=item.name))
					self.__merge_movie_folders(item, target_item)
				else:
					item.rename(target_item)
					logger.info(_('已移动子文件夹: ') + item.name)
			else:
				target_item = target_folder / item.name
				if not target_item.exists():
					item.rename(target_item)
					logger.info(_('已移动文件: ') + item.name)

		try:
			source_folder.rmdir()
			logger.info(_('已删除源文件夹: ') + str(source_folder))
		except Exception:
			logger.error(_('无法删除源文件夹: ') + str(source_folder))

	def __merge_movie_folders(self, source_folder: Path, target_folder: Path):
		"""
		合并两个影片文件夹，保留较大的视频文件

		Args:
			source_folder: 源影片文件夹
			target_folder: 目标影片文件夹
		"""
		source_movies = {}
		for item in source_folder.iterdir():
			if item.is_file() and any(item.name.lower().endswith(ext) for ext in config.movie_file_extensions):
				source_movies[item.name.lower()] = item

		target_movies = {}
		for item in target_folder.iterdir():
			if item.is_file() and any(item.name.lower().endswith(ext) for ext in config.movie_file_extensions):
				target_movies[item.name.lower()] = item

		for movie_name, source_movie in source_movies.items():
			if movie_name in target_movies:
				target_movie = target_movies[movie_name]
				source_size = source_movie.stat().st_size
				target_size = target_movie.stat().st_size

				if source_size > target_size:
					target_movie.unlink()
					source_movie.rename(target_folder / source_movie.name)
					logger.info(_('保留源视频并删除目标文件夹同名文件: ') + source_movie.name)
				else:
					source_movie.unlink()
					logger.info(_('保留目标视频并删除源文件夹同名文件: ') + target_movie.name)
			else:
				source_movie.rename(target_folder / source_movie.name)
				logger.info(_('已移动视频文件: ') + source_movie.name)

		# 移动源文件夹中的非视频文件
		for item in source_folder.iterdir():
			if item.is_file() and not any(item.name.lower().endswith(ext) for ext in config.movie_file_extensions):
				target_item = target_folder / item.name

				if not target_item.exists():
					item.rename(target_item)
				else:
					item.unlink()

		try:
			source_folder.rmdir()
			logger.info(_('已删除源影片文件夹: ') + str(source_folder))
		except Exception:
			logger.error(_('无法删除源影片文件夹: ') + str(source_folder))

	def analyze_keyword(self, keyword: str):
		"""
		从已知信息中分析并提取影片ID

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
		elif '200GANA' in keyword:
			match = config._200gana_movie_pattern.search(keyword)
			if match:
				return f'200GANA-{match.group(1)}'
		elif '300MIUM' in keyword:
			match = config._300mium_movie_pattern.search(keyword)
			if match:
				return f'300MIUM-{match.group(1)}'
		else:
			match = config.normal_movie_pattern.search(keyword)
			if match:
				return match.group(1) + '-' + match.group(2)

			match = config.normal_movie_pattern2.search(keyword)
			if match:
				return match.group(1) + '-' + match.group(2)

	def list_video_files(self, root_dir: Path, max_depth: int=0):
		"""
		在指定目录中搜索视频文件

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
				if filename.startswith(config.ignored_file_prefix):
					continue

				if any(filename.lower().endswith(ext) for ext in config.movie_file_extensions):
					found_files.append(Path(dirpath) / filename)

		return found_files

	def batch_process(self, keywords: list[str], *, gallery: bool=False, dir_mode: bool=False, root_dir: Path=None):
		"""
		处理影片的信息搜索与整理

		根据关键词列表或目录路径批量处理影片文件，包括搜索影片信息、下载封面图片、
		剧照、预告片、生成 NFO 文件并按演员分类整理文件结构

		Args:
			keywords: 搜索关键词列表或文件路径列表
			gallery: 是否下载剧照和预告片，默认为False
			dir_mode: 是否为目录模式，默认为False
			root_dir: 目录模式下的根目录，默认为None
		"""
		if dir_mode:
			assert root_dir is not None, _('目录模式下必须提供根目录路径')

		failed_movies  = []
		ignored_movies = []

		for index, item in enumerate(keywords, 1):
			keyword = Path(item).name if dir_mode else item

			print()
			logger.info(f'[{index}/{len(keywords)}] ' + _('正在搜索: {keyword}...')
				.format(keyword=keyword))

			movie_id = self.analyze_keyword(keyword)

			if not movie_id:
				logger.warning(_('无法解析影片ID，尝试修改文件名后重试'))
				failed_movies.append(item)
				continue

			tqdm_steps = 6 if dir_mode else 5

			with trange(tqdm_steps, desc=_('处理 ') + movie_id, unit='步',
						leave=False, ncols=80, bar_format='{l_bar}{bar}|') as step_pbar:
				#region 1. 搜索影片
				step_pbar.set_description(_('正在搜索影片'))
				response_text = self.fetch_data(f'{config.search_url}{urllib.parse.quote_plus(movie_id)}')
				search_results = MovieParser.parse_search_results(response_text, movie_id)

				if not search_results:
					logger.warning(_('未找到匹配的影片'))
					failed_movies.append(item)
					continue

				step_pbar.update()
				#endregion

				#region 2. 获取影片详情
				step_pbar.set_description(_('正在获取影片详情'))
				response_text = self.fetch_data(search_results['detail_url'])
				movie_details = MovieParser.parse_movie_details(response_text)

				if not movie_details:
					logger.warning(_('无法获取影片详情'))
					failed_movies.append(item)
					continue

				step_pbar.update()

				movie_details.update({
					'detail_url': search_results['detail_url'],
					'title'     : search_results['title'],
					'fanart_url': search_results['fanart_url'],
				})

				movie_info = MovieInfo(movie_details)
				#endregion

				#region 3. 按演员组织目录结果并创建影片目录
				step_pbar.set_description(_('正在创建影片目录'))
				actress_count = len(movie_info.actresses)

				if actress_count == 0:
					dir1 = _('==无名演员==')
				elif actress_count == 1:
					dir1 = movie_info.actresses[0]
				else:
					dir1 = _('==多演员==')

				base_dir = (Path(root_dir) if dir_mode else Path.cwd()) / config.completed_path
				movie_path = base_dir / dir1 / f'[{movie_info.number}]({movie_info.year})'
				movie_path.mkdir(parents=True, exist_ok=True)
				step_pbar.update()
				#endregion

				#region 4. 下载并处理封面图片
				step_pbar.set_description(_('正在下载封面') + _('和剧照') if gallery and movie_info.galleries else '')

				if not self.fetch_media(movie_path, config.fanart_image, movie_info.fanart_url, crop=True):
					logger.warning(_('封面图片下载失败'))
					failed_movies.append(item)
					continue

				# 下载剧照
				if gallery and movie_info.galleries:
					for i, gallery_url in enumerate(movie_info.galleries):
						root, ext = os.path.splitext(gallery_url.split('?')[0])
						ext = ext.lower() or '.jpg'
						self.fetch_media(movie_path, f'gallery_{i:02d}{ext}', gallery_url)

				# 下载预告片
				if gallery and movie_info.trailer_url:
					root, ext = os.path.splitext(movie_info.trailer_url.split('?')[0])
					ext = ext.lower() or '.mp4'
					self.fetch_media(movie_path, f'{movie_info.number}_trailer{ext}', movie_info.trailer_url)

				step_pbar.update()
				#endregion

				#region 5. 生成NFO文件
				step_pbar.set_description(_('正在生成 NFO 文件'))
				nfo = NFOGenerator(movie_info)
				nfo.save(f'{movie_path}/{movie_info.number}.nfo')
				step_pbar.update()
				#endregion

				#region 6. 移动影片源文件到整理后的文件夹并改名
				if dir_mode:
					step_pbar.set_description(_('正在移动影片文件'))

					old_path = Path(item)
					new_path = movie_path / old_path.with_stem(movie_info.number.upper())\
													.with_suffix(old_path.suffix.lower()).name

					if new_path.exists():
						old_file_size = old_path.stat().st_size
						new_file_size = new_path.stat().st_size

						if old_file_size <= new_file_size:
							ignored_path = old_path.parent / f'{config.ignored_file_prefix}{old_path.name}'
							old_path.rename(ignored_path)
							ignored_movies.append(old_path)
						else:
							old_path.rename(new_path)
					else:
						old_path.rename(new_path)

					step_pbar.update()

				logger.info(_('影片相关文件已保存至: ') + str(movie_path))
				#endregion

		print()
		logger.info(_('处理完成，共搜索整理 {count} 部影片，其中 {failed} 部影片获取信息失败')
			.format(count=len(keywords), failed=len(failed_movies)))

		if failed_movies:
			print(_('获取信息失败的影片文件:'))
			for index, movie in enumerate(failed_movies, 1):
				print(f'    {index}.{Path(movie).relative_to(root_dir) if dir_mode else movie}')

		if ignored_movies:
			print(_('已忽略的影片文件:'))
			for index, movie in enumerate(ignored_movies, 1):
				print(f'    {index}.{Path(movie).relative_to(root_dir) if dir_mode else movie}')


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

	class ColoredFormatter(logging.Formatter):
		"""根据日志等级添加颜色的格式化器"""
		def format(self, record):
			message = record.getMessage()

			# 根据日志等级设置颜色
			if record.levelno == logging.ERROR:
				message = f'{Style.BRIGHT}{Fore.RED}{message}{Style.RESET_ALL}'
			elif record.levelno == logging.WARNING:
				message = f'{Style.BRIGHT}{Fore.YELLOW}{message}{Style.RESET_ALL}'

			return message

	console_formatter = ColoredFormatter()
	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setFormatter(console_formatter)
	console_handler.stream = TqdmOut

	# 添加处理器到日志器
	logger.addHandler(file_handler)
	logger.addHandler(console_handler)

	return logger

def lazy_import():
	global logger
	global requests, RequestException, Timeout
	global tqdm, trange

	import requests
	from requests.exceptions import RequestException, Timeout
	from tqdm import tqdm, trange

	logger = get_logger()

def main():
	"""应用程序入口点"""
	global config
	config = Config()

	if getattr(sys, 'frozen', False):
		current_dir = Path(sys.executable).parent
		config.actress_alias_file = current_dir / 'actress_alias.json'
		config.cookies_file = current_dir / 'cookies.json'

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
	# parser.add_argument('-o', '--organize', action='store_true', help=config.organize_help)

	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(0)

	args, unknown_args = parser.parse_known_args()

	if '--lang' in unknown_args:
		set_language('en_US')

	lazy_import()

	dv_helper = DVHelper()
	keywords_or_path: str = args.keywords_or_path

	if args.login:
		if dv_helper.perform_login() is None:
			sys.exit(0)

	dv_helper.initialize_session()

	if config.actress_alias_file.exists():
		with open(config.actress_alias_file, 'r', encoding='utf-8') as file:
			config.actress_alias = json.load(file)

	try:
		if Path(keywords_or_path).absolute().is_dir():
			root_dir = Path(keywords_or_path)

			if any(arg in unknown_args for arg in ['-o', '--organize']):
				if not config.actress_alias:
					logger.warning(_('actress_alias.json 文件为空或不存在，无法执行整理操作'))
				else:
					dv_helper.organize_folders(root_dir)
				return

			found_files = dv_helper.list_video_files(root_dir, max_depth=args.depth)

			if found_files:
				logger.info(_('发现 {count} 个影片文件:').format(count=len(found_files)))
				for index, file_path in enumerate(found_files, 1):
					print(f'    {index}.{Path(file_path).relative_to(root_dir)}')

				dv_helper.batch_process(found_files, gallery=args.gallery, dir_mode=True, root_dir=root_dir)
			else:
				logger.info(_('在 {root_dir} {else_part}中未发现影片文件')
					.format(root_dir=root_dir, else_part=_('及其子目录') if args.depth > 0 else ''))
		else:
			keywords = [keyword.strip() for keyword in keywords_or_path.split(',')]

			logger.info(_('发现 {count} 个影片关键词:').format(count=len(keywords)))
			for index, keyword in enumerate(keywords, 1):
				print(f'    {index}.{keyword}')

			dv_helper.batch_process(keywords, gallery=args.gallery)
	except KeyboardInterrupt:
		sys.exit(0)


if __name__ == '__main__':
	main()
