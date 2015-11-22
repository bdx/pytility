#!/usr/bin/python3

import requests
import sys



def get_cookie_jar(profile_folder):
	"""
	Original Author: Noah Fontes nfontes AT cynigram DOT com
	Original URL: http://blog.mithis.net/archives/python/90-firefox3-cookies-in-python
	License: MIT

	Maintainer: Dotan Cohen
	* Ported to Python 3
	* Support cookies from recovery.js
	* Accept profile folder as input parameter instead of sqlite filename
	"""

	import http.cookiejar
	import json
	import os
	import sqlite3
	import time
	from io import StringIO

	sql_file = os.path.join(profile_folder, 'cookies.sqlite')
	sessions_file = os.path.join(profile_folder, 'sessionstore-backups/recovery.js')
 
	try:
		con = sqlite3.connect(sql_file)
	except sqlite3.OperationalError:
		print("Cannot open cookies database.")
		return False

	cur = con.cursor()
	cur.execute("SELECT host, path, isSecure, expiry, name, value FROM moz_cookies")

	ftstr = ["FALSE","TRUE"]

	s = StringIO()
	s.write("""\
# Netscape HTTP Cookie File
# http://www.netscape.com/newsref/std/cookie_spec.html
# This is a generated file!  Do not edit.
""")

	for item in cur.fetchall():
		s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
			item[0], ftstr[item[0].startswith('.')], item[1],
			ftstr[item[2]], item[3], item[4], item[5])
		)

	sessions_input = open(sessions_file, 'r')
	sessions_data = json.loads(sessions_input.read())

	for win in sessions_data['windows']:
		for item in win['cookies']:

			# Required Keys: host, path, value, name
			# Optional keys: httponly
			# Missing Keys: expiry, secure

			# This does not seem to be used in the output file format
			item['httponly'] = 0
			if 'httponly' in item and item['httponly']==True:
				item['httponly'] = 1

			# I could find no instance of this actually being used, I am only guessing that it exists
			item['secure'] = 0
			if 'secure' in item and item['secure']==True:
				item['secure'] = 1

			# This field is needed, even though it doesn't seem to be available in the JSON
			item['expiry'] = int(time.time()+84600)

			s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
				item['host'], ftstr[item['host'].startswith('.')], item['path'],
				ftstr[item['secure']], item['expiry'], item['name'], item['value'])
			)

	s.seek(0)
	cookie_jar = http.cookiejar.MozillaCookieJar()
	cookie_jar._really_load(s, '', True, True)

	return cookie_jar



def get_profile_folder():

	"""
	Return the Firefox profile folder

	Based upon Tim Ansell's code from here:
	http://blog.mithis.net/archives/python/94-reading-cookies-firefox
	"""

	import os
	import ConfigParser

	firefoxdir=os.path.expanduser('~/.mozilla/firefox')
	config = ConfigParser.ConfigParser()
	config.read(firefoxdir + '/profiles.ini')

	for profile in config.sections():
	    if (profile == 'General'):
	        continue
	    if config.has_option(profile, 'default'):
	        if (config.get(profile, 'default') == '1'):
	            defaultprofile=profile
	            break

	profile_folder=config.get(defaultprofile, 'path')
	if (config.get(defaultprofile, 'isrelative')):
	    profile_folder=firefoxdir + '/' + profile_folder

	return profile_folder

# Test the script, see if we are logged into Github

firefox_profile_folder = get_profile_folder()
cj = get_cookie_jar(firefox_profile_folder)

if cj==False:
	sys.exit()

response = requests.get('http://github.com', cookies=cj)

if 'Signed in as' in response.text:
	print('Confirmed signed into Github!')
else:
	print('Cannot confirmed that you are signed into Github.')
	print('Please ensure that you are singed into Github in Firefox before testing.')

