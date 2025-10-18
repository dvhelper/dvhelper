"""测试 Config 类的功能"""

def test_config_initialize(config):
	assert config.base_url == 'https://avfan.com'
	assert config.sign_in_url == 'https://avfan.com/zh-CN/sign_in'
	assert config.search_url == 'https://avfan.com/search?q='
	assert isinstance(config.movie_file_extensions, tuple)
	assert '.mp4' in config.movie_file_extensions

def test_config_regex_patterns(config):
	assert config.normal_movie_pattern.match('ABC-123')
	assert config.normal_movie_pattern.match('XYZ-4567')

	assert config.fc2_movie_pattern.match('FC2-123456')
	assert config.fc2_movie_pattern.match('FC2 PPV-123456')

	assert config._259luxu_movie_pattern.match('259LUXU-1234')
	assert config._200gana_movie_pattern.match('200GANA-5678')
	assert config._300mium_movie_pattern.match('300MIUM-9012')
