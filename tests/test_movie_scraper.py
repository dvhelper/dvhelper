"""测试 MovieScraper 类的功能"""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from dvhelper import MovieScraper
import pytest
from selenium.common.exceptions import TimeoutException

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_scraper_initialize():
	with patch('dvhelper.requests') as mock_requests:
		mock_session = MagicMock()
		mock_requests.Session.return_value = mock_session

		scraper = MovieScraper()
		assert scraper is not None

def test_scraper_initialize_session_success():
	with patch('dvhelper.MovieScraper.check_cookies') as mock_check_cookies, \
		 patch('dvhelper.logger') as mock_logger:
		mock_session = MagicMock()
		mock_check_cookies.return_value = mock_session

		scraper = MovieScraper()
		scraper.initialize_session()

		mock_check_cookies.assert_called_once()
		mock_logger.warning.assert_not_called()

def test_scraper_initialize_session_failed():
	with patch('dvhelper.MovieScraper.check_cookies') as mock_check_cookies, \
		 patch('dvhelper.logger') as mock_logger:
		mock_check_cookies.return_value = None

		scraper = MovieScraper()
		scraper.initialize_session()

		mock_check_cookies.assert_called_once()
		mock_logger.warning.assert_called_once()

#region check_cookies tests
def test_scraper_check_cookies(cookies_file):
	with patch('dvhelper.config') as mock_config, \
		 patch('dvhelper.requests') as mock_requests, \
		 patch('json.load') as mock_json_load:
		mock_config.cookies_file = cookies_file

		mock_json_load.return_value = [{
			'name': 'remember_token',
			'value': 'test_token',
			'expiry': 2147483647,
			'domain': 'example.com',
			'path': '/'
		}]

		with patch('pathlib.Path.exists', return_value=True), \
			 patch('builtins.open', MagicMock()):
			mock_session = MagicMock()
			mock_requests.Session.return_value = mock_session

			scraper = MovieScraper()
			result = scraper.check_cookies()

			assert result is not None
			mock_requests.Session.assert_called_once()
			mock_session.cookies.set.assert_called()

def test_scraper_check_cookies_no_file():
	with patch('dvhelper.config') as mock_config, \
		 patch('pathlib.Path.exists', return_value=False):
		mock_config.cookies_file = Path('non_existent_file.json')

		scraper = MovieScraper()
		result = scraper.check_cookies()

		assert result is None

def test_scraper_check_cookies_expired(cookies_file):
	with patch('dvhelper.config') as mock_config, \
		 patch('dvhelper.requests') as mock_requests, \
		 patch('json.load') as mock_json_load, \
		 patch('datetime.datetime') as mock_datetime:
		mock_config.cookies_file = cookies_file

		mock_current_time = MagicMock()
		mock_current_time.timestamp.return_value = 1000
		mock_datetime.now.return_value = mock_current_time
		mock_datetime.fromtimestamp.return_value = MagicMock()
		mock_datetime.fromtimestamp.return_value.__lt__.return_value = True

		mock_json_load.return_value = [{
			'name': 'remember_token',
			'value': 'expired_token',
			'expiry': 500,
			'domain': 'example.com',
			'path': '/'
		}]

		with patch('pathlib.Path.exists', return_value=True), \
			 patch('builtins.open', MagicMock()), \
			 patch('dvhelper.logger') as mock_logger:

			mock_session = MagicMock()
			mock_requests.Session.return_value = mock_session

			scraper = MovieScraper()
			result = scraper.check_cookies()

			assert result is None
			mock_logger.warning.assert_called()

def test_scraper_check_cookies_error_handling(cookies_file):
	with patch('dvhelper.config') as mock_config, \
		 patch('dvhelper.requests') as mock_requests, \
		 patch('dvhelper.logger') as mock_logger, \
		 patch('pathlib.Path.exists', return_value=True), \
		 patch('builtins.open', MagicMock()), \
		 patch('json.load', side_effect=Exception('JSON parse error')):
		mock_config.cookies_file = cookies_file

		mock_session = MagicMock()
		mock_requests.Session.return_value = mock_session

		scraper = MovieScraper()
		result = scraper.check_cookies()

		assert result is None
		mock_logger.error.assert_called_once()
#endregion

#region perform_login tests
@pytest.mark.parametrize("test_case,chrome_side_effect,wait_side_effect,cookies_file,expected_result,expected_chrome_calls,expected_logger_call", [
	# 正常登录场景
	("success", 
	 None,  # 无异常
	 None,  # 无超时
	 "cookies.json", 
	 "session",  # 成功返回session
	 1,  # Chrome调用1次
	 "info"  # 记录info日志
	),
	# WebDriver创建失败回退场景
	("driver_creation_fallback", 
	 lambda mock_driver: create_driver_fallback_side_effect(mock_driver),  # Chrome创建失败回退
	 None,  # 无超时
	 "cookies.json", 
	 "session",  # 成功返回session
	 2,  # Chrome调用2次
	 "info"  # 记录info日志
	),
	# 登录超时失败场景
	("login_timeout", 
	 None,  # 无异常
	 TimeoutException("Login timeout"),  # 超时异常
	 None,  # 不需要cookies_file
	 None,  # 失败返回None
	 1,  # Chrome调用1次
	 "error"  # 记录error日志
	),
])
def test_scraper_perform_login(test_case, chrome_side_effect, wait_side_effect, cookies_file,
								expected_result, expected_chrome_calls, expected_logger_call):
	mock_driver = MagicMock()
	mock_driver.get_cookies.return_value = [
		{'name': 'remember_token', 'value': 'test_token', 'domain': 'example.com', 'path': '/', 'secure': True},
		{'name': 'user_id', 'value': '123', 'domain': 'example.com', 'path': '/', 'secure': True}
	] if test_case != "login_timeout" else []
	mock_driver.get.return_value = None
	mock_driver.quit.return_value = None

	if chrome_side_effect:
		if test_case == "driver_creation_fallback":
			chrome_effect = create_driver_fallback_side_effect(mock_driver)
		else:
			chrome_effect = chrome_side_effect
	else:
		chrome_effect = mock_driver

	with patch('dvhelper.config') as mock_config, \
		 patch('dvhelper.requests') as mock_requests, \
		 patch('builtins.open', MagicMock()) as mock_open, \
		 patch('dvhelper.logger') as mock_logger, \
		 patch('selenium.webdriver.Chrome') as mock_chrome, \
		 patch('selenium.webdriver.support.ui.WebDriverWait') as mock_web_driver_wait, \
		 patch('selenium.webdriver.support.expected_conditions.url_to_be') as mock_url_to_be, \
		 patch('selenium.webdriver.chrome.options.Options') as mock_options, \
		 patch('webdriver_manager.chrome.ChromeDriverManager') as mock_driver_manager, \
		 patch('selenium.webdriver.chrome.service.Service') as mock_service:
		mock_config.sign_in_url = 'https://example.com/sign_in'
		mock_config.base_url = 'https://example.com'
		mock_config.cookies_file = cookies_file

		if test_case == "driver_creation_fallback":
			mock_chrome.side_effect = chrome_effect
		else:
			mock_chrome.return_value = chrome_effect

		mock_service_instance = MagicMock()
		mock_options_instance = MagicMock()
		mock_driver_manager_instance = MagicMock()
		mock_driver_manager.return_value = mock_driver_manager_instance
		mock_driver_manager_instance.install.return_value = 'chromedriver_path'
		mock_service.return_value = mock_service_instance
		mock_options.return_value = mock_options_instance

		mock_wait = MagicMock()
		mock_web_driver_wait.return_value = mock_wait
		mock_url_condition = MagicMock()
		mock_url_to_be.return_value = mock_url_condition
		if wait_side_effect:
			mock_wait.until.side_effect = wait_side_effect
		else:
			mock_wait.until.return_value = True

		mock_session = MagicMock()
		mock_requests.Session.return_value = mock_session
		mock_file = MagicMock()
		mock_open.return_value.__enter__.return_value = mock_file

		scraper = MovieScraper()
		result = scraper.perform_login()

		if expected_result == "session":
			assert result is not None
			assert result == mock_session
		else:
			assert result is expected_result

		if test_case == "driver_creation_fallback":
			assert mock_chrome.call_count == 2

			all_calls = mock_chrome.call_args_list
			_, kwargs1 = all_calls[0]
			assert 'service' in kwargs1
			assert 'options' in kwargs1
			_, kwargs2 = all_calls[1]
			assert 'service' not in kwargs2
			assert 'options' in kwargs2
		else:
			assert mock_chrome.call_count == expected_chrome_calls

		if expected_logger_call == "info":
			mock_logger.info.assert_called()
		elif expected_logger_call == "error":
			mock_logger.error.assert_called_once()

		mock_driver.get.assert_called_once_with(mock_config.sign_in_url)
		mock_driver.quit.assert_called_once()

def create_driver_fallback_side_effect(mock_driver):
	def side_effect(*args, **kwargs):
		if not hasattr(side_effect, 'call_count'):
			side_effect.call_count = 0
		side_effect.call_count += 1

		if side_effect.call_count == 1 and 'service' in kwargs:
			raise Exception("Service creation failed")

		return mock_driver

	side_effect.call_count = 0
	return side_effect
#endregion

#region fetch data & media tests
@pytest.mark.parametrize('use_session, expected_content', [
	(False, '<html><body>Test Data</body></html>'),
	(True, '<html><body>Session Test Data</body></html>'),
])
def test_scraper_fetch_data(use_session, expected_content):
	if use_session:
		scraper = MovieScraper()
		mock_session = MagicMock()
		scraper._MovieScraper__session = mock_session

		mock_response = MagicMock()
		mock_response.text = expected_content
		mock_response.raise_for_status.return_value = None
		mock_session.get.return_value = mock_response

		result = scraper.fetch_data('https://example.com')

		assert result == expected_content
		mock_session.get.assert_called_once()

		call_args = mock_session.get.call_args
		assert call_args[1]['url'] == 'https://example.com'
		assert 'timeout' in call_args[1]
		assert 'headers' in call_args[1]
	else:
		with patch('dvhelper.requests.get') as mock_get:
			mock_response = MagicMock()
			mock_response.text = expected_content
			mock_response.raise_for_status.return_value = None

			mock_get.return_value = mock_response
			scraper = MovieScraper()
			result = scraper.fetch_data('https://example.com')

			assert result == expected_content
			mock_get.assert_called_once()

			call_args = mock_get.call_args
			assert call_args[1]['url'] == 'https://example.com'
			assert 'timeout' in call_args[1]
			assert 'headers' in call_args[1]

def test_scraper_fetch_data_failure():
	with patch('dvhelper.requests.get') as mock_get:
		from requests.exceptions import RequestException

		mock_get.side_effect = RequestException("Connection error")
		scraper = MovieScraper()
		result = scraper.fetch_data('https://example.com', max_retries=2)

		assert result is None
		assert mock_get.call_count == 2

@pytest.mark.parametrize('crop', [False, True])
def test_scraper_fetch_media_success(temp_dir, crop):
	with patch('dvhelper.requests.get') as mock_get:
		mock_response = MagicMock()
		mock_response.headers = {'content-length': '10'}
		mock_response.iter_content.return_value = [b'test_data']
		mock_get.return_value = mock_response

		with patch('dvhelper.MovieScraper.crop_image') as mock_crop_image:
			scraper = MovieScraper()
			media_file = 'cover.jpg'
			url = 'https://example.com/image.jpg'
			result = scraper.fetch_media(temp_dir, media_file, url, crop=crop)

			assert result is True
			assert mock_get.called
			assert (temp_dir / media_file).exists()

			call_args = mock_get.call_args
			assert call_args[0][0] == url
			assert call_args[1]['stream'] is True
			assert 'timeout' in call_args[1]

			with open(temp_dir / media_file, 'rb') as f:
				content = f.read()
			assert content == b'test_data'

			if crop:
				from dvhelper import config
				mock_crop_image.assert_called_once_with(temp_dir / media_file, temp_dir / config.poster_image)
			else:
				mock_crop_image.assert_not_called()

def test_scraper_fetch_media_failure(temp_dir):
	with patch('dvhelper.requests.get') as mock_get:
		from requests.exceptions import RequestException

		mock_get.side_effect = RequestException("Connection error")

		scraper = MovieScraper()
		movie_path = Path(temp_dir)
		media_file = 'cover.jpg'
		url = 'https://example.com/image.jpg'
		result = scraper.fetch_media(movie_path, media_file, url, max_retries=2)

		assert result is False
		assert mock_get.call_count == 2
#endregion

def test_scraper_crop_image(crop_image):
	scraper = MovieScraper()
	src_file = crop_image['src_file']
	dest_file = crop_image['dest_file']
	src_file.touch()

	with patch('PIL.Image.open') as mock_open:
		mock_image = MagicMock()
		mock_image.size = (1000, 800)
		mock_image.crop.return_value = mock_image
		mock_open.return_value.__enter__.return_value = mock_image

		scraper.crop_image(src_file, dest_file)

		expected_left = 1000 - 379
		expected_right = 1000
		mock_image.crop.assert_called_with((expected_left, 0, expected_right, 800))

		mock_image.save.assert_any_call(src_file, format='JPEG')
		mock_image.save.assert_any_call(dest_file, format='JPEG')

		assert mock_image.save.call_count == 2
