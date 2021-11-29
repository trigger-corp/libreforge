from os import path

import mock
from nose.tools import raises, eq_, assert_raises

from generate.ios_tasks import IOSRunner, IOSError

class TestIOSRunner(object):

	ios_runner = IOSRunner('dummy directory')
	appstore_non_wildcard    = "appstore_non-wildcard.mobileprovision"
	adhoc_wildcard           = "adhoc_wildcard.mobileprovision"
	development_expired      = "development_expired.mobileprovision"
	development_wildcard     = "development_wildcard.mobileprovision"

	def setup(self):
		def fixture_path(filename):
			return path.abspath(path.join(__file__, path.pardir, "fixtures", filename))
		self.appstore_non_wildcard = fixture_path(self.appstore_non_wildcard)
		self.adhoc_wildcard = fixture_path(self.adhoc_wildcard)
		self.development_expired = fixture_path(self.development_expired)
		self.development_wildcard = fixture_path(self.development_wildcard)

	@mock.patch('generate.ios_tasks.subprocess.Popen')
	def test_get_child_processes(self, Popen):
		ps_output = '''
 2  1
 3  2
 4  1
 5  11
'''.split('\n')
		Popen.return_value.stdout = ps_output

		result = IOSRunner.get_child_processes(1)

		eq_(result, [2, 4])

	@mock.patch('generate.ios_tasks.subprocess')
	def test_check_for_codesign(self, subprocess):
		runner = IOSRunner('path/to/build')

		subprocess.Popen.return_value.returncode = 0
		subprocess.Popen.return_value.communicate.return_value = ('stdout\n', 'stderr\n')

		result = runner._check_for_codesign()

		subprocess.Popen.assert_called_once_with(['which', 'codesign'], stdout=subprocess.PIPE)
		eq_(result, 'stdout')

		subprocess.Popen.return_value.returncode = 1
		assert_raises(IOError, runner._check_for_codesign)

	@mock.patch('generate.ios_tasks.IOSRunner.get_bundled_ai')
	def test_provisioning_profile(self, get_bundled_ai):
		iosr = self.ios_runner
		plist_string = iosr._grab_plist_from_binary_mess(self.development_wildcard)
		plist_dict   = iosr._parse_plist(plist_string)
		eq_(
			self.ios_runner.check_plist_dict(plist_dict, '0',),
			None
		)

	@raises(IOSError)
	def test_expired_profile(self):
		iosr = self.ios_runner
		plist_string = iosr._grab_plist_from_binary_mess(self.development_expired)
		plist_dict   = iosr._parse_plist(plist_string)
		self.ios_runner.check_plist_dict(plist_dict, '0',)

	@raises(IOSError)
	def test_adhoc_profile(self):
		iosr = self.ios_runner
		plist_string = iosr._grab_plist_from_binary_mess(self.adhoc_wildcard)
		plist_dict   = iosr._parse_plist(plist_string)
		self.ios_runner.check_plist_dict(plist_dict, '0',)

	@mock.patch('generate.ios_tasks.IOSRunner.get_bundled_ai')
	def test_distribution_profile(self, get_bundled_ai):
		iosr = self.ios_runner
		plist_string = iosr._grab_plist_from_binary_mess(self.appstore_non_wildcard)
		plist_dict   = iosr._parse_plist(plist_string)
		get_bundled_ai.return_value = "XXXXXXX.io.trigger.forge.followarzxxxxxxxxxxxxxxxxxxxxxxxxxx"

		iosr.check_plist_dict(plist_dict, '0')
