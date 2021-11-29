import os
import subprocess

import mock
from mock import patch
from nose.tools import eq_, ok_
from hamcrest import *
	
from generate import android_tasks, utils, lib
from generate.tests.lib import assert_raises_regexp

class TestLookForJava(object):
	@patch('generate.android_tasks.os.path.isdir')
	def test_first_there(self, isdir):
		isdir.return_value = True
		eq_(android_tasks._look_for_java('a b c d'.split()), os.path.join('a', 'bin'))

	@patch('generate.android_tasks.os.path.isdir')
	def test_none_there(self, isdir):
		isdir.return_value = False
		assert_raises_regexp(android_tasks.AndroidError, "Java was not available",
				android_tasks._look_for_java, 'a b c d'.split())

class TestDownloadForWindows(object):
	@patch('generate.android_tasks.zipfile')
	@patch('generate.android_tasks.lib.download_with_progress_bar')
	def test_normal(self, download, zipfile):
		with patch('generate.android_tasks.sys.platform', new='win32'):
			res = android_tasks._download_sdk_for_windows('temp dir')
		
		eq_(download.call_args[0][1], "https://trigger.io/redirect/android/windows")
		
		zipfile.ZipFile.assert_called_once()
		zipfile.ZipFile.return_value.extractall.assert_called_once()
		zipfile.ZipFile.return_value.close.assert_called_once()
		
		eq_(res.android, r"C:\android-sdk-windows\tools\android.bat")
		eq_(res.adb, r"C:\android-sdk-windows\platform-tools\adb")

class TestDownloadForMac(object):
	@patch('generate.android_tasks.lib.PopenWithoutNewConsole')
	@patch('generate.android_tasks.lib.download_with_progress_bar')
	def test_normal(self, download, Popen):
		Popen.return_value.communicate.return_value = ('', '')
		with patch('generate.android_tasks.sys.platform', new='darwin'):
			res = android_tasks._download_sdk_for_mac('temp dir')
		
		eq_(download.call_args[0][1], "https://trigger.io/redirect/android/macosx")
		
		Popen.assert_called_once()
		
		eq_(res.android, r"/Applications/android-sdk-macosx/tools/android")
		eq_(res.adb, r"/Applications/android-sdk-macosx/platform-tools/adb")

class TestDownloadForLinux(object):
	@patch('generate.android_tasks.lib.PopenWithoutNewConsole')
	@patch('generate.android_tasks.lib.download_with_progress_bar')
	@patch('generate.android_tasks.os')
	@patch('generate.android_tasks.path')
	def test_normal(self, path, os, download, Popen):
		path.isdir.return_value = False
		Popen.return_value.communicate.return_value = ('', '')
		with patch('generate.android_tasks.sys.platform', new='linux'):
			res = android_tasks._download_sdk_for_linux('temp dir')
		
		eq_(download.call_args[0][1], "https://trigger.io/redirect/android/linux")
		
		os.mkdir.assert_called_once()
		Popen.assert_called_once()
		
		ok_(res.android.endswith("/android-sdk-macosx/tools/android"))
		ok_(res.adb.endswith("/android-sdk-macosx/platform-tools/adb"))
		
	@patch('generate.android_tasks.lib.PopenWithoutNewConsole')
	@patch('generate.android_tasks.lib.download_with_progress_bar')
	@patch('generate.android_tasks.os')
	@patch('generate.android_tasks.path')
	def test_already_exists(self, path, os, download, Popen):
		path.isdir.return_value = True
		Popen.return_value.communicate.return_value = ('', '')
		android_tasks._download_sdk_for_linux('temp dir')
		
		eq_(os.mkdir.call_count, 0)
		
class TestInstallSdk(object):
	@patch('generate.android_tasks._update_sdk')
	@patch('generate.android_tasks._download_sdk_for_windows')
	@patch('generate.android_tasks.tempfile.mkdtemp')
	@patch('generate.android_tasks.shutil.rmtree')
	@patch('generate.android_tasks.sys')
	def test_win(self, sys, rmtree, mkdtemp, _download_sdk_for_windows, _update_sdk):
		sys.platform = 'windows'
		
		res = android_tasks._install_sdk_automatically(_mock_build())
		
		_download_sdk_for_windows.assert_called_once()
		_update_sdk.assert_called_once_with(android_tasks._download_sdk_for_windows.return_value)
		eq_(res, _download_sdk_for_windows.return_value)
		rmtree.assert_called_once_with(mkdtemp.return_value, ignore_errors=True)

	@patch('generate.android_tasks._update_sdk')
	@patch('generate.android_tasks._download_sdk_for_mac')
	@patch('generate.android_tasks.tempfile.mkdtemp')
	@patch('generate.android_tasks.shutil.rmtree')
	@patch('generate.android_tasks.sys')
	def test_mac(self, sys, rmtree, mkdtemp, _download_sdk_for_mac, _update_sdk):
		sys.platform = 'darwin'
		
		android_tasks._install_sdk_automatically(_mock_build())
		
		_download_sdk_for_mac.assert_called_once()
		_update_sdk.assert_called_once_with(_download_sdk_for_mac.return_value)

	@patch('generate.android_tasks._update_sdk')
	@patch('generate.android_tasks._download_sdk_for_linux')
	@patch('generate.android_tasks.tempfile.mkdtemp')
	@patch('generate.android_tasks.shutil.rmtree')
	@patch('generate.android_tasks.sys')
	def test_linux(self, sys, rmtree, mkdtemp, _download_sdk_for_linux, _update_sdk):
		sys.platform = 'linux'
		
		android_tasks._install_sdk_automatically(_mock_build())
		
		_download_sdk_for_linux.assert_called_once()
		_update_sdk.assert_called_once_with(_download_sdk_for_linux.return_value)

class TestUpdateSdk(object):
	@patch('generate.android_tasks.time')
	@patch('generate.android_tasks.lib.PopenWithoutNewConsole')
	@patch('generate.android_tasks._kill_adb')
	def test_normal(self, _kill_adb, Popen, time):
		Popen.return_value.stdout.readline.return_value = ''
		
		android_tasks._update_sdk(android_tasks.PathInfo(adb='adb', android='android', sdk='sdk', aapt='aapt'))
		Popen.assert_called_once_with(['android', "update", "sdk", "--no-ui", "--filter", "platform-tool,tool,android-8"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		assert_that(_kill_adb.call_count, greater_than(1))

def _mock_build():
	m = mock.Mock()
	m.tool_config = {}
	m.orig_wd = 'dummy original working directory'
	return m

class TestFindOrInstallSdk(object):
	@patch('generate.android_tasks.path.isdir')
	@patch('generate.android_tasks._ask_user_if_should_install_sdk')
	def test_found_user_provided_sdk_no_slash(self, _ask_user_if_should_install_sdk, isdir):
		build = _mock_build()
		build.tool_config['android.sdk'] = 'manual sdk'
		user_provided_sdk = lib.expand_relative_path(build, 'manual sdk/') + '/'
		isdir = lambda pth: pth == user_provided_sdk

		res = android_tasks._find_or_install_sdk(build)

		assert_that(res, has_property('sdk', user_provided_sdk))
		assert_that(_ask_user_if_should_install_sdk, has_property('call_count', 0))

	@patch('generate.android_tasks.path')
	@patch('generate.android_tasks._ask_user_if_should_install_sdk')
	def test_found_user_provided_sdk_with_slash(self, _ask_user_if_should_install_sdk, path):
		build = _mock_build()
		build.tool_config['android.sdk'] = 'manual sdk/'
		user_provided_sdk = lib.expand_relative_path(build, 'manual sdk/') + '/'
		isdir = lambda pth: pth == user_provided_sdk

		res = android_tasks._find_or_install_sdk(build)

		assert_that(res, has_property('sdk', user_provided_sdk))
		assert_that(_ask_user_if_should_install_sdk, has_property('call_count', 0))

	@patch('generate.android_tasks.path')
	@patch('generate.android_tasks._ask_user_if_should_install_sdk')
	def test_found_default(self, _ask_user_if_should_install_sdk, path):
		path.isdir = lambda pth: pth == "C:/android-sdk-windows/"
		res = android_tasks._find_or_install_sdk(_mock_build())
		eq_(res.sdk, "C:/android-sdk-windows/")
		assert_that(_ask_user_if_should_install_sdk, has_property('call_count', 0))
	
	@patch('generate.android_tasks._ask_user_if_should_install_sdk')
	@patch('generate.android_tasks.path.isdir')
	def test_choose_manual(self, isdir, _should_install_sdk):
		isdir.return_value = False
		_should_install_sdk.return_value = False
		
		assert_raises_regexp(lib.BASE_EXCEPTION, "please set this in your local config", android_tasks._find_or_install_sdk, _mock_build())
		
	@patch('generate.android_tasks.sys')
	@patch('generate.android_tasks.path')
	def test_funny_platform(self, path, sys):
		path.isdir.return_value = False
		sys.platform = 'mismatch'
		
		assert_raises_regexp(lib.CouldNotLocate, "please specify with", android_tasks._find_or_install_sdk, _mock_build())
		
	@patch('generate.android_tasks._install_sdk_automatically')
	@patch('generate.android_tasks._ask_user_if_should_install_sdk')
	@patch('generate.android_tasks.path')
	def test_choose_auto(self, path, _should_install_sdk, _install_sdk_automatically):
		path.isdir.return_value = False
		_should_install_sdk.return_value = True
		
		android_tasks._find_or_install_sdk(_mock_build())

		_install_sdk_automatically.assert_called_once()

class TestScrapeDevices(object):
	def test_normal(self):
		text = '''\
List of devices attached 
012345A	device
012345B	device
'''
		eq_(android_tasks._scrape_available_devices(text), ["012345A", "012345B"])

class TestCreateAvdIfNecessary(object):
	@patch('generate.android_tasks._have_avd')
	@patch('generate.android_tasks._have_android_8_available')
	@patch('generate.android_tasks._update_sdk')
	@patch('generate.android_tasks._create_avd')
	def test_should_not_create_avd_if_already_exists(self, _create_avd, _update_sdk, _have_android_8_available, _have_avd):
		_have_avd.return_value = True
		android_tasks._create_avd_if_necessary(path_info=None)
		assert_that(_create_avd, has_property('call_count', 0))

	@patch('generate.android_tasks._have_avd')
	@patch('generate.android_tasks._have_android_8_available')
	@patch('generate.android_tasks._update_sdk')
	@patch('generate.android_tasks._create_avd')
	def test_should_update_sdk_if_creation_fails_and_dont_have_android_8(self, _create_avd, _update_sdk, _have_android_8_available, _have_avd):
		_have_avd.return_value = False
		_have_android_8_available.return_value = False

		succeed = []
		def raise_shell_error(*args):
			if succeed:
				return
			else:
				raise utils.ShellError("Dummy error", output="dummy output")

		def allow_create_to_succeed(*args):
			succeed.append(None)

		_create_avd.side_effect = raise_shell_error
		_update_sdk.side_effect = allow_create_to_succeed

		android_tasks._create_avd_if_necessary(path_info=None)

		assert_that(_create_avd, has_property('call_count', 2))
		_update_sdk.assert_called_once()

	@patch('generate.android_tasks._have_avd')
	@patch('generate.android_tasks._have_android_8_available')
	@patch('generate.android_tasks._update_sdk')
	@patch('generate.android_tasks._create_avd')
	def test_should_not_catch_error_from_second_attempt_to_create(self, _create_avd, _update_sdk, _have_android_8_available, _have_avd):
		_have_avd.return_value = False
		_have_android_8_available.return_value = False

		def raise_shell_error(*args):
			raise utils.ShellError("Dummy error", output="dummy output")

		_create_avd.side_effect = raise_shell_error

		try:
			android_tasks._create_avd_if_necessary(path_info=None)
		except utils.ShellError as e:
			assert_that(_create_avd, has_property('call_count', 2))
			_update_sdk.assert_called_once()
		else:
			ok_(False, "Should have allowed error from the second attempt to create an AVD propagate")

	@patch('generate.android_tasks._have_avd')
	@patch('generate.android_tasks._have_android_8_available')
	@patch('generate.android_tasks._update_sdk')
	@patch('generate.android_tasks._create_avd')
	def test_should_reraise_if_android_8_available(self, _create_avd, _update_sdk, _have_android_8_available, _have_avd):
		_have_avd.return_value = False
		_have_android_8_available.return_value = True

		def raise_shell_error(*args):
			raise utils.ShellError("Dummy error", output="dummy output")

		_create_avd.side_effect = raise_shell_error

		try:
			android_tasks._create_avd_if_necessary(path_info=None)
		except utils.ShellError as e:
			assert_that(_create_avd, has_property('call_count', 1))
			_update_sdk.assert_called_once()
		else:
			ok_(False, "Should have allowed error from the first attempt to create an AVD propagate")

class TestRunAndroid(object):
	@patch('generate.android_tasks._get_jre')
	@patch('generate.android_tasks._find_or_install_sdk')
	def test_should_not_try_to_install_android_sdk_if_no_jre_available(self, _find_or_install_sdk, _get_jre):
		_get_jre.side_effect = android_tasks.AndroidError
		try:
			android_tasks.run_android(None, None, None, None, None, None)
		except android_tasks.AndroidError as e:
			_get_jre.assert_called_once()
			assert_that(_find_or_install_sdk, has_property('call_count', 0))
		else:
			ok_(False, "Should have thrown AndroidError")

class TestPackageAndroid(object):
	@patch('generate.android_tasks._get_jre')
	@patch('generate.android_tasks._find_or_install_sdk')
	def test_should_not_try_to_install_android_sdk_if_no_jre_available(self, _find_or_install_sdk, _get_jre):
		_get_jre.side_effect = android_tasks.AndroidError
		try:
			android_tasks.package_android(None)
		except android_tasks.AndroidError as e:
			_get_jre.assert_called_once()
			assert_that(_find_or_install_sdk, has_property('call_count', 0))
		else:
			ok_(False, "Should have thrown AndroidError")
