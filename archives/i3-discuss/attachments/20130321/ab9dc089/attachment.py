# -*- coding: utf-8 -*-

class Py3status:
	"""
	Inspired by Fam Zheng request on mailing list [1]
	Thanks to Axel Wagner and Justus Jonas for their interesting replies

	This class renames the current workspace with the name of the focused window
	We do a small operation on the name for convenience which you can adapt ofc

	NOTE: my workspaces are named "1 NAME" with no ":" so you may want to change
	the NUM_SPLIT variable to your separator

	NOTE: you need i3-py [2] for this class to work

	TODO: this affects window assignment settings ;(

	[1] http://article.gmane.org/gmane.comp.window-managers.i3.general/918/
	[2] https://github.com/ziberna/i3-py | https://pypi.python.org/pypi/i3-py
	"""
	def rename_workspace(self, json, i3status_config):
		response = {'full_text' : '', 'name' : 'rename_workspace'}

		NUM_SPLIT = " "
		LONG_NAME_SPLIT = " - "
		LONG_NAME_INDEX = -1

		try:
			import i3
			from syslog import syslog
			from syslog import LOG_INFO
			nodes = i3.filter(nodes=[], focused=True)
			for node in nodes:
				# dont rename empty workspaces
				if 'num' in node : continue

				# NOTE: quick hack transformation for long named windows
				# 'Inbox - XXX account - Mozilla Thunderbird' becomes 'Mozilla Thunderbird'
				node['name'] = node['name'].split(LONG_NAME_SPLIT)[LONG_NAME_INDEX]

				current_workspace = [ws for ws in i3.get_workspaces() if ws['focused']][0]
				ws_num, ws_name = current_workspace['name'].split(NUM_SPLIT, 1)
				new_name = "%s %s" % (ws_num, node['name'])
				if new_name != current_workspace['name']:
					cmd = 'rename workspace "%s %s" to "%s"' % (ws_num, ws_name, new_name)
					i3.msg('command', cmd)
					syslog(LOG_INFO, cmd)
		except Exception, e:
			raise
		finally:
			# for maximum responsiveness, dont cache this class
			response.update({'cached_until': 10})
			return (0, response)

p = Py3status()
p.rename_workspace({}, {})
