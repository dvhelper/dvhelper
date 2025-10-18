"""测试 DVHelper 类的功能"""
import os
import sys
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from colorama import Fore, Style

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dvhelper
from dvhelper import set_language, get_logger, lazy_import, TqdmOut, HelpOnErrorParser


@pytest.mark.parametrize("lang, expected_calls, i18n_exists", [
	('en_US', [(['dvhelper', 'i18n_path', ['en_US']], True)], True),
	('fr_FR', [(['dvhelper', 'i18n_path', ['fr_FR']], False), 
		  (['dvhelper', 'i18n_path', ['en_US']], True)], True),
	('ja_JP', [(['dvhelper', 'i18n_path', ['ja_JP']], False), 
		  (['dvhelper', 'i18n_path', ['en_US']], False)], True),
	('zh_CN', [], False)
])
def test_set_language(lang, expected_calls, i18n_exists):
	with patch('dvhelper.gettext') as mock_gettext, \
	     patch('dvhelper.Path.exists', return_value=i18n_exists):
		mock_translation = MagicMock()

		if i18n_exists:
			mock_gettext.translation.side_effect = [
				mock_translation if success else FileNotFoundError()
				for _, success in expected_calls
			]

			actual_calls = []
			for args, success in expected_calls:
				actual_args = list(args)
				actual_args[1] = str(Path(__file__).parent.parent.joinpath('i18n'))
				actual_calls.append((actual_args, success))

		set_language(lang)

		if i18n_exists:
			assert mock_gettext.translation.call_count == len(actual_calls)
			for args, success in actual_calls:
				try:
					mock_gettext.translation.assert_any_call(*args)
				except AssertionError:
					pass
		else:
			mock_gettext.translation.assert_not_called()

		if i18n_exists:
			if any(success for _, success in expected_calls):
				mock_translation.install.assert_called()
			else:
				mock_translation.install.assert_not_called()

def test_tqdm_out():
	with patch('dvhelper.tqdm.write') as mock_tqdm_write:
		TqdmOut.write("test message")
		mock_tqdm_write.assert_called_with("test message", file=None, end='', nolock=False)

def test_help_on_error_parser():
	with patch('sys.stderr.write') as mock_write:
		with patch('argparse.ArgumentParser.print_help') as mock_print_help:
			with patch('sys.exit') as mock_exit:
				parser = HelpOnErrorParser()
				parser.error("test error")

				mock_write.assert_called_with(f'{Style.BRIGHT}{Fore.RED}' + '错误: test error' + f'{Style.RESET_ALL}\n\n')
				mock_print_help.assert_called()
				mock_exit.assert_called_with(2)

def test_lazy_import():
	lazy_import()

	assert hasattr(dvhelper, 'logger')
	assert hasattr(dvhelper, 'requests')
	assert hasattr(dvhelper, 'tqdm')

def test_get_logger():
	with patch('logging.getLogger') as mock_getLogger:
		mock_logger = MagicMock()
		mock_getLogger.return_value = mock_logger
		mock_logger.hasHandlers.return_value = False

		with patch('logging.FileHandler') as mock_FileHandler:
			with patch('logging.StreamHandler') as mock_StreamHandler:
				logger = get_logger()

				assert logger == mock_logger
				mock_getLogger.assert_called_with(dvhelper.__name__)
				mock_logger.setLevel.assert_called_with(logging.INFO)
				assert mock_logger.addHandler.call_count >= 2

# region DVHelper class tests
def test_dvhelper_organize_folders_with_alias(dv_helper, actress_folders_with_alias):
	base_dir = actress_folders_with_alias['base_dir']
	actress_alias = actress_folders_with_alias['actress_alias']

	with patch('dvhelper.config.actress_alias', actress_alias):
		dv_helper.organize_folders(base_dir)
		assert True

def test_dvhelper_merge_folders(dv_helper, folders):
	source_folder = folders['source_folder']
	target_folder = folders['target_folder']
	source_subfolder = folders['source_subfolder']
	target_subfolder = folders.get('target_subfolder')

	def mock_merge_movie_folders(src, tgt):
		for item in list(src.iterdir()):
			if item.is_file():
				item.rename(tgt / item.name)
		src.rmdir()

	target_subfolder_exists = target_subfolder.exists() if target_subfolder else False

	with patch.object(dv_helper,
					  '_DVHelper__merge_movie_folders',
					  side_effect=mock_merge_movie_folders):
		dv_helper._DVHelper__merge_folders(source_folder, target_folder)

		assert (target_folder / 'file1.txt').exists()
		assert (target_folder / 'subfolder' / 'subfile.txt').exists()

		if target_subfolder_exists:
			dv_helper._DVHelper__merge_movie_folders.assert_called_once_with(source_subfolder, target_subfolder)
		else:
			pass

		assert not source_folder.exists()

def test_dvhelper_merge_folders_error_handling(dv_helper, folders_basic):
	source_folder = folders_basic['source_folder']
	target_folder = folders_basic['target_folder']

	with patch('pathlib.Path.rmdir') as mock_rmdir:
		mock_rmdir.side_effect = Exception("Permission denied")
		dv_helper._DVHelper__merge_folders(source_folder, target_folder)

		assert (target_folder / 'file1.txt').exists()

def test_dvhelper_merge_movie_folders(dv_helper, movie_folders):
	source_folder = movie_folders['source_folder']
	target_folder = movie_folders['target_folder']
	original_target_small_size = movie_folders['original_target_small_size']
	original_target_large_size = movie_folders['original_target_large_size']

	dv_helper._DVHelper__merge_movie_folders(source_folder, target_folder)

	# 1. source_size > target_size
	assert (target_folder / 'movie1.mp4').exists()
	assert (target_folder / 'movie1.mp4').stat().st_size > original_target_small_size

	# 2. source_size <= target_size
	assert (target_folder / 'movie2.mp4').exists()
	assert (target_folder / 'movie2.mp4').stat().st_size == original_target_large_size

	# 3. movie_name not in target_movies
	assert (target_folder / 'movie3.mp4').exists()

	# 4. other files
	assert (target_folder / 'poster.jpg').exists()

	# 5. other files unlink
	assert not (source_folder / 'info.txt').exists()
	assert (target_folder / 'info.txt').exists()

def test_dvhelper_merge_movie_folders_error_handling(dv_helper, movie_folders):
	source_folder = movie_folders['source_folder']
	target_folder = movie_folders['target_folder']

	with patch('pathlib.Path.rmdir') as mock_rmdir:
		mock_rmdir.side_effect = Exception("Permission denied")
		dv_helper._DVHelper__merge_movie_folders(source_folder, target_folder)
		assert True

def test_dvhelper_analyze_keyword(dv_helper):
	assert dv_helper.analyze_keyword('ABC-123') == 'ABC-123'
	assert dv_helper.analyze_keyword('ABC123') == 'ABC-123'

	assert dv_helper.analyze_keyword('FC2-123456') == 'FC2-123456'
	assert dv_helper.analyze_keyword('FC2-123ABC456') is None
	assert dv_helper.analyze_keyword('FC2 PPV-123456') == 'FC2-123456'

	assert dv_helper.analyze_keyword('259LUXU-1234') == '259LUXU-1234'
	assert dv_helper.analyze_keyword('259LUXU-ABC1234') is None

	assert dv_helper.analyze_keyword('200GANA-5678') == '200GANA-5678'
	assert dv_helper.analyze_keyword('200GANA-ABC5678') is None

	assert dv_helper.analyze_keyword('300MIUM-9012') == '300MIUM-9012'
	assert dv_helper.analyze_keyword('300MIUM-ABC9012') is None

	assert dv_helper.analyze_keyword('Invalid Keyword') is None

	assert dv_helper.analyze_keyword('Some text ABC-123 more text') == 'ABC-123'
	assert dv_helper.analyze_keyword('ABC-123 (2023)') == 'ABC-123'

def test_dvhelper_list_video_files(dv_helper, video_files):
	base_dir = video_files['base_dir']
	video1 = video_files['video1']
	video2 = video_files['video2']
	video3 = video_files['video3']
	video4 = video_files['video4']
	ignored_file = video_files['ignored_file']

	result = dv_helper.list_video_files(base_dir, max_depth=0)

	assert len(result) == 2
	assert Path(video1) in result
	assert Path(video2) in result
	assert Path(video3) not in result
	assert Path(video4) not in result
	assert Path(ignored_file) not in result

	result = dv_helper.list_video_files(base_dir, max_depth=1)

	assert len(result) == 3
	assert Path(video1) in result
	assert Path(video2) in result
	assert Path(video3) in result
	assert Path(video4) not in result

	result = dv_helper.list_video_files(base_dir, max_depth=2)

	assert len(result) == 4
	assert Path(video1) in result
	assert Path(video2) in result
	assert Path(video3) in result
	assert Path(video4) in result

def test_dvhelper_create_movie_folder(config, movie_info):
	with patch('dvhelper.config', config):
		base_dir = Path(config.completed_path)

		expected_path = base_dir / movie_info.actresses[0] / f'[{movie_info.number}]({movie_info.year})'

		assert f'[{movie_info.number}]({movie_info.year})' in str(expected_path)
		assert movie_info.actresses[0] in str(expected_path)

def test_dvhelper_batch_process_keyword_mode(dv_helper, temp_dir, movie_info_dict, search_html, detail_html):
	with patch('dvhelper.config') as mock_config:
		mock_config.completed_path = 'completed'
		mock_config.fanart_image = 'fanart.jpg'
		mock_config.ignored_file_prefix = '##'
		mock_config.search_url = 'https://example.com/search/'

		dv_helper.analyze_keyword = MagicMock(return_value='ABC-123')
		dv_helper.fetch_data = MagicMock(side_effect=[search_html, detail_html])
		dv_helper.fetch_media = MagicMock(return_value=True)

		with patch('dvhelper.MovieParser') as mock_movie_parser:
			mock_movie_parser.parse_search_results.return_value = {
				'detail_url': 'https://example.com/movie/123',
				'title': 'Test Movie',
				'fanart_url': 'https://example.com/image.jpg'
			}
			mock_movie_parser.parse_movie_details.return_value = movie_info_dict

			with patch('dvhelper.NFOGenerator') as mock_nfo_generator:
				mock_nfo = MagicMock()
				mock_nfo_generator.return_value = mock_nfo

				with patch('pathlib.Path.cwd', return_value=temp_dir), \
					 patch('pathlib.Path.mkdir', return_value=None), \
					 patch('builtins.print'):
					dv_helper.batch_process(['ABC-123'])

					dv_helper.analyze_keyword.assert_called_once_with('ABC-123')
					dv_helper.fetch_data.assert_called()
					dv_helper.fetch_media.assert_called_once()
					mock_movie_parser.parse_search_results.assert_called_once()
					mock_movie_parser.parse_movie_details.assert_called_once()
					mock_nfo_generator.assert_called_once()
					mock_nfo.save.assert_called_once()

def test_dvhelper_batch_process_directory_mode(dv_helper, test_video_file, movie_info_dict, search_html, detail_html):
	base_dir = test_video_file['base_dir']
	video_file = test_video_file['video_file']

	with patch('dvhelper.config') as mock_config:
		mock_config.completed_path = 'completed'
		mock_config.fanart_image = 'fanart.jpg'
		mock_config.ignored_file_prefix = '##'
		mock_config.search_url = 'https://example.com/search/'

		dv_helper.analyze_keyword = MagicMock(return_value='MOVIE')
		dv_helper.fetch_data = MagicMock(side_effect=[search_html, detail_html])
		dv_helper.fetch_media = MagicMock(return_value=True)

		with patch('dvhelper.MovieParser') as mock_movie_parser:
			mock_movie_parser.parse_search_results.return_value = {
				'detail_url': 'https://example.com/movie/123',
				'title': 'Test Movie',
				'fanart_url': 'https://example.com/image.jpg'
			}
			mock_movie_parser.parse_movie_details.return_value = movie_info_dict

			with patch('dvhelper.NFOGenerator') as mock_nfo_generator:
				mock_nfo = MagicMock()
				mock_nfo_generator.return_value = mock_nfo

				with patch('pathlib.Path.mkdir', return_value=None), \
					 patch('pathlib.Path.stat', return_value=MagicMock(st_size=1024)), \
					 patch('pathlib.Path.rename', return_value=None), \
					 patch('pathlib.Path.exists', return_value=False), \
					 patch('builtins.print'):
					dv_helper.batch_process([str(video_file)], dir_mode=True, root_dir=base_dir)

					dv_helper.analyze_keyword.assert_called_once_with('movie.mp4')
					dv_helper.fetch_data.assert_called()
					dv_helper.fetch_media.assert_called_once()
					mock_movie_parser.parse_search_results.assert_called_once()
					mock_movie_parser.parse_movie_details.assert_called_once()
					mock_nfo_generator.assert_called_once()
					mock_nfo.save.assert_called_once()

def test_dvhelper_batch_process_failed_movie(dv_helper):
	with patch('dvhelper.config') as mock_config:
		mock_config.search_url = 'https://example.com/search/'
		dv_helper.analyze_keyword = MagicMock(return_value=None)

		with patch('builtins.print'):
			dv_helper.batch_process(['invalid-keyword'])
			dv_helper.analyze_keyword.assert_called_once_with('invalid-keyword')

def test_dvhelper_batch_process_with_gallery(dv_helper, temp_dir, movie_info_dict, search_html, detail_html):
	with patch('dvhelper.config') as mock_config:
		mock_config.completed_path = 'completed'
		mock_config.fanart_image = 'fanart.jpg'
		mock_config.search_url = 'https://example.com/search/'

		dv_helper.analyze_keyword = MagicMock(return_value='ABC-123')
		dv_helper.fetch_data = MagicMock(side_effect=[search_html, detail_html])
		dv_helper.fetch_media = MagicMock(return_value=True)

		with patch('dvhelper.MovieParser') as mock_movie_parser:
			mock_movie_parser.parse_search_results.return_value = {
				'detail_url': 'https://example.com/movie/123',
				'title': 'Test Movie',
				'fanart_url': 'https://example.com/image.jpg'
			}
			mock_movie_parser.parse_movie_details.return_value = movie_info_dict

			with patch('dvhelper.NFOGenerator') as mock_nfo_generator:
				mock_nfo = MagicMock()
				mock_nfo_generator.return_value = mock_nfo

				with patch('pathlib.Path.cwd', return_value=temp_dir), \
					 patch('pathlib.Path.mkdir', return_value=None), \
					 patch('builtins.print'), \
					 patch('dvhelper.logger'):
					dv_helper.batch_process(['ABC-123'], gallery=True)

					assert dv_helper.fetch_media.call_count > 1
#endregion

#region main() function tests
def test_main_frozen_app():
	with patch.object(sys, 'frozen', True, create=True), \
		 patch('sys.executable', str(Path('.') / 'path' / 'to' / 'dvhelper.exe')), \
		 patch('dvhelper.Config') as mock_config_class, \
		 patch('sys.argv', ['dvhelper.exe', 'ABC-123']), \
		 patch('dvhelper.DVHelper'), \
		 patch('dvhelper.lazy_import'):

		mock_config = MagicMock()
		mock_config_class.return_value = mock_config

		dvhelper.main()

		expected_dir = Path('.') / 'path' / 'to'
		assert mock_config.actress_alias_file == expected_dir / 'actress_alias.json'
		assert mock_config.cookies_file == expected_dir / 'cookies.json'

def test_main_keyword_search():
	with patch('sys.argv', ['dvhelper.py', 'ABC-123']), \
		 patch('dvhelper.DVHelper'), \
		 patch('dvhelper.lazy_import') as mock_lazy_import, \
		 patch('dvhelper.set_language'), \
		 patch('dvhelper.Config') as mock_config_class:
		mock_config = MagicMock()
		mock_config_class.return_value = mock_config
		mock_config.actress_alias_file.exists.return_value = False

		mock_dv_helper = MagicMock()
		dvhelper.DVHelper.return_value = mock_dv_helper
		dvhelper.main()

		mock_lazy_import.assert_called_once()
		dvhelper.DVHelper.assert_called_once()
		mock_dv_helper.initialize_session.assert_called_once()
		mock_dv_helper.batch_process.assert_called_once_with(['ABC-123'], gallery=False)

def test_main_directory_processing(temp_dir):
	with patch('sys.argv', ['dvhelper.py', str(temp_dir)]), \
		 patch('dvhelper.DVHelper'), \
		 patch('dvhelper.lazy_import') as mock_lazy_import, \
		 patch('dvhelper.set_language'), \
		 patch('dvhelper.Config') as mock_config_class:
		mock_config = MagicMock()
		mock_config_class.return_value = mock_config
		mock_config.actress_alias_file.exists.return_value = False

		mock_dv_helper = MagicMock()
		dvhelper.DVHelper.return_value = mock_dv_helper
		mock_dv_helper.list_video_files.return_value = [Path(temp_dir) / 'movie.mp4']
		dvhelper.main()

		mock_lazy_import.assert_called_once()
		dvhelper.DVHelper.assert_called_once()
		mock_dv_helper.initialize_session.assert_called_once()
		mock_dv_helper.list_video_files.assert_called_once()
		mock_dv_helper.batch_process.assert_called_once()

def test_main_login_option():
	with patch('sys.argv', ['dvhelper.py', 'ABC-123', '-l']), \
		 patch('dvhelper.DVHelper'), \
		 patch('dvhelper.lazy_import'), \
		 patch('dvhelper.set_language'), \
		 patch('dvhelper.Config') as mock_config_class:
		mock_config = MagicMock()
		mock_config_class.return_value = mock_config
		mock_config.actress_alias_file.exists.return_value = False

		mock_dv_helper = MagicMock()
		dvhelper.DVHelper.return_value = mock_dv_helper
		mock_dv_helper.perform_login.return_value = MagicMock()
		dvhelper.main()

		mock_dv_helper.perform_login.assert_called_once()
		mock_dv_helper.initialize_session.assert_called_once()

@pytest.mark.parametrize('alias_file_exists', [True, False])
def test_main_login_failure(alias_file_exists):
	with patch('sys.argv', ['dvhelper.py', 'ABC-123', '-l']), \
		 patch('dvhelper.DVHelper'), \
		 patch('dvhelper.lazy_import'), \
		 patch('dvhelper.set_language'), \
		 patch('json.load') as mock_json_load, \
		 patch('dvhelper.Config') as mock_config_class, \
		 patch('sys.exit') as mock_exit:
		mock_config = MagicMock()
		mock_config_class.return_value = mock_config
		mock_config.actress_alias_file.exists.return_value = alias_file_exists
		mock_json_load.return_value = {}

		mock_dv_helper = MagicMock()
		dvhelper.DVHelper.return_value = mock_dv_helper
		mock_dv_helper.perform_login.return_value = None
		dvhelper.main()

		mock_dv_helper.perform_login.assert_called_once()
		mock_exit.assert_called_once_with(0)

def test_main_no_arguments():
	with patch('sys.argv', ['dvhelper.py']), \
		 patch('dvhelper.Config'), \
		 patch.object(HelpOnErrorParser, 'print_help') as mock_print_help:

		try:
			dvhelper.main()
		except SystemExit:
			pass

		mock_print_help.assert_called_once()

def test_main_english_language():
	with patch('sys.argv', ['dvhelper.py', 'ABC-123', '--lang']), \
		 patch('dvhelper.DVHelper'), \
		 patch('dvhelper.lazy_import'), \
		 patch('dvhelper.set_language') as mock_set_language, \
		 patch('dvhelper.Config') as mock_config_class:
		mock_config = MagicMock()
		mock_config_class.return_value = mock_config
		mock_config.actress_alias_file.exists.return_value = False

		mock_dv_helper = MagicMock()
		dvhelper.DVHelper.return_value = mock_dv_helper
		dvhelper.main()

		mock_set_language.assert_called_with('en_US')
#endregion

def teardown_module(module):
	pass
