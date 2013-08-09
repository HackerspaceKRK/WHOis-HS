# -*- coding: utf-8 -*-

# Appplication that monitors users being currently in hackerspace. Running on Raspberry PI.
# Copyright (C) 2013 Tadeusz Magura-Witkowski
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from web import form
from threading import Timer
import web
import json
import binascii
import sqlite3
import time
import hashlib
import string
import random
import datetime
import time
import re
import ConfigParser

config = ConfigParser.ConfigParser()
config.read(('config.cfg', 'localconfig.cfg'))

web.config.debug = config.getboolean('application', 'debug')

def mac_to_binary(mac):
	return binascii.unhexlify(mac.replace(':', ''))

def binary_to_mac(binary):
	s = binascii.hexlify(binary)
	return ':'.join( (s[i:i+2] for i in range(0, len(s), 2)) )

def convert_date_to_fucking_human_readable_format_the_hell_cause_unix_timestamp_is_fucking_bad_for_peoples_eyes(timestamp):
	return datetime.datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M')

db = web.database(dbn='sqlite', db=config.get('database', 'db_file'))
render = web.template.render('templates', base='base', globals={'binary_to_mac': binary_to_mac,
	'BASE_URL': config.get('application', 'base_url'),
	'date': convert_date_to_fucking_human_readable_format_the_hell_cause_unix_timestamp_is_fucking_bad_for_peoples_eyes,})

urls = (
	'/', 'index',
	'/whois', 'who_is',
	r'^/r/(\d+)/(.{10})$', 'register_device',
	'/register', 'register_user',
	'/panel', 'user_panel',
	'/logout', 'user_logout',
	'/panel/editprofile', 'user_edit_profile',
	r'/panel/removedevice/(.{17})', 'user_remove_device',
)

app = web.application(urls, globals())

if web.config.get('_session') is None:
	session = web.session.Session(app, web.session.DiskStore('sessions'), {'user_id': 0})
	web.config._session = session
else:
	session = web.config._session

def hash_password(username, password):
	hash = '%s%s%s' % (username, password, config.get('application', 'hash_secret'))
	for i in range(20):
		hash = hashlib.sha256(hash).digest()

	return hash

def generate_access_key():
	return ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for x in range(10))

def get_current_users():
	# final version - parses /var/lib/dhcp/dhcp.leases

	data = ''
	with file(config.get('database', 'leases_file'), 'r') as f:
		data = f.read()

	# matches = re.findall(r'lease ([^\s]*) {\n  starts \d \d\d\d\d/\d\d/\d\d \d\d:\d\d:\d\d;\n  ends \d \d\d\d\d/\d\d/\d\d \d\d:\d\d:\d\d;\n  cltt \d \d\d\d\d/\d\d/\d\d \d\d:\d\d:\d\d;\n  binding state active;[\s\S]*?hardware ethernet (.{17});', data)
	# return [(ip, mac_to_binary(mac)) for ip, mac in matches]

	# fuck regexp (which actually works well), lets try to parse it manually (in really ugly way!)
	ipnow = ''
	macaddr = ''
	inblock = False

	matches = []

	utcnow = datetime.datetime.utcnow()

	for line in data.split('\n'):
		line = line.strip()

		if not len(line) or line[0] == '#':
			continue

		if line.startswith('lease '):
			ipnow = line[6:-2]
			inblock = True
		elif inblock:
			if line[0] == '}':
				matches.append( (ipnow, mac_to_binary(macaddr)) )
				inblock = False
			elif line.startswith('binding state free') or (line.startswith('ends') and datetime.datetime.strptime(line[7:-1], "%Y/%m/%d %H:%M:%S") < utcnow): # skip entry
				inblock = False
			elif line.startswith('hardware ethernet'):
				macaddr = line[18:-1]

	return matches

# from PEP0318
def singleton(cls):
	instances = {}
	def getinstance():
		if cls not in instances:
			instances[cls] = cls()
		return instances[cls]
	return getinstance

def get_users_in_hs(current_leases=None):
	dhcp_leases = get_current_users() if current_leases is None else current_leases
	query_for = [sqlite3.Binary(lease[1]) for lease in dhcp_leases]
	users = {}

	if len(dhcp_leases):
		db.query('UPDATE whois_devices SET last_seen = strftime(\'%s\',\'now\') WHERE mac_addr IN $mac_list', vars=
			{'mac_list': query_for})

		results = db.query('SELECT DISTINCT id, display_name FROM whois_users WHERE id IN (SELECT user_id FROM whois_devices WHERE mac_addr IN $macs)', vars=
			{'macs': query_for})

		for user in results:
			users[user['id']] = user['display_name']

	return users

@singleton
class ClientMonitor(object):
	def __init__(self):
		# mapping USER ID -> FIRST SEEN TIMESTAMP
		self._lastUsers = {}
		self._lastUsersSet = set([])

	def update_data(self, users_now):
		users_now_ids = set(users_now.keys())

		current_timestamp = time.time()

		new_users = users_now_ids - self._lastUsersSet
		for user_id in new_users:
				db.query('INSERT INTO whois_history (user_id, date_from, date_to) VALUES ($user_id ,$date_from, 0)', vars={'user_id': user_id, 'date_from': current_timestamp})
				self._lastUsers[user_id] = current_timestamp

		users_left = self._lastUsersSet - users_now_ids
		if len(users_left):
			db.query('UPDATE whois_history SET date_to = $date_to WHERE user_id IN $user_ids', vars={'user_ids': list(users_left), 'date_to': current_timestamp})
		# we do not need to track them any more
		for user_id in users_left:
			del self._lastUsers[user_id]

		self._lastUsersSet = users_now_ids

def timer_update_history():
	users_now = get_users_in_hs()

	ClientMonitor().update_data(users_now)

	Timer(120, timer_update_history).start()

class who_is:
	last_seen_updated = 0
	last_seen_list = []
	total_devices_count = 0

	def GET(self):
		web.header('Content-type', 'application/json')

		dhcp_leases = get_current_users()
		users = get_users_in_hs(dhcp_leases).values()

		who_is.last_seen_updated = int(time.time()) + 60*1
		who_is.total_devices_count = len(dhcp_leases)
		who_is.last_seen_list = list(users)

		return json.dumps({'date': who_is.last_seen_updated, 'users': who_is.last_seen_list, 'total_devices_count': who_is.total_devices_count})
		
class register_device:
	def GET(self, uid, access_key):
		uid = int(uid)

		result = db.query('SELECT * FROM whois_users WHERE id == $uid AND access_key == $access_key', vars={'uid': uid, 'access_key': access_key})
		
		if not result:
			raise web.badrequest(u'Zły uid lub access_key. Sprawdź czy wszedłeś pod poprawy adres URL. Jeżeli tak, to pamiętaj, że przy każdym logowaniu Twój adres jest generowany na nowo. Spróbuj zatem zalogować się ponownie i użyć nowego adresu.')

		user_ip = web.ctx.env.get('REMOTE_ADDR')
		user_mac = None
		dhcp_leases = get_current_users()

		for lease in dhcp_leases:
			if lease[0] == user_ip:
				user_mac = lease[1]

				break

		if not user_mac:
			raise web.badrequest(u'Czy jesteś pewien, że korzystasz z HS-owego WIFI? Jeżeli tak, to powiadom kogoś o tym błędzie!')

		result = db.query('SELECT * FROM whois_devices WHERE mac_addr == $mac_addr', vars={'mac_addr': sqlite3.Binary(user_mac)})

		if result:
			raise web.badrequest(u'Twoje urządzenie jest już zarejestrowane!')

		db.insert('whois_devices', mac_addr=sqlite3.Binary(user_mac), user_id=uid, last_seen=int(time.time()))

		return u'Brawo! Właśnie dokonałeś rejestracji swojego urządzenia w systemie :) Od tej chwili jego obecność będzie oznaczało również Twoją.'

password_validator = form.regexp(r'.{3,100}$', u'od 3 do 100 znaków')
display_name_validator = form.regexp(r'.{3,100}$', u'od 3 do 100 znaków')
unique_username_validator = form.Validator(u'Podana nazwa użytkownika jest już zajęta', lambda f: 
						db.query('SELECT COUNT(id) AS cnt FROM whois_users WHERE login == $login', vars={'login': f.login})[0]['cnt'] == 0)
password_match_validator = form.Validator(u'Hasła w dwóch polach się nie zgadzają', lambda i: i.password == i.password2)
unique_display_name_validator = form.Validator(u'Ktoś już używa takiej nazwy...', lambda f: 
						db.query('SELECT COUNT(id) AS cnt FROM whois_users WHERE display_name == $display_name', vars={'display_name': f.display_name})[0]['cnt'] == 0)
login_validator = form.regexp(r'[a-zA-Z0-9_]{3,32}$', u'od 3 do 32 znaków, alfanumeryczny')

class register_user:
	register_form = form.Form(
		form.Textbox('login', login_validator, description='Login'),
		form.Textbox('display_name', display_name_validator, description=u'Nazwa wyświetlana'),
		form.Password('password', password_validator, description=u'Hasło'),
		form.Password('password2', description=u'Powtórz hasło'),
		form.Button('submit', type='submit', html='Zarejestruj'),
		validators = [password_match_validator, unique_username_validator, unique_display_name_validator])

	def GET(self):
		f = register_user.register_form()

		return render.register(f)

	def POST(self):
		f = register_user.register_form()

		if not f.validates():
			f.password.value = f.password2.value = ''
			return render.register(f)
		else:
			data = f.d
			del data['password2']
			del data['submit']
			data['password'] = sqlite3.Binary(hash_password(data['login'], data['password']))
			data['registered_at'] = int(time.time())
			data['access_key'] = generate_access_key()

			session.user_id = db.insert('whois_users', **data)

			raise web.seeother('/panel')

def get_userrow():
	return db.query('SELECT * FROM whois_users WHERE id = $id', vars={'id': session.user_id})[0]

class user_edit_profile:
	edit_form = web.form.Form(
		form.Textbox('display_name', description=u'Nazwa wyświetlana'),
		form.Password('password', description=u'Nowe hasło'),
		form.Password('password2', description=u'Powtórzenie nowego'),
		form.Password('old_password', description=u'Stare hasło'),
		form.Button('submit', type='submit', html=u'Zmień'),
		validators=[]
	)

	def GET(self):
		if not session.user_id:
			raise web.seeother('/panel')

		try:
			userrow = get_userrow()
		except:
			session.kill()

			raise web.seeother('/panel')

		f = user_edit_profile.edit_form()
		
		return render.editprofile(f)

	def POST(self):
		if not session.user_id:
			raise web.seeother('/panel')

		f = user_edit_profile.edit_form()

		if not f.validates():
			return render.editprofile(f)

		if f.d['password']:

			userrow = get_userrow()

			def check_old_password(i):
				return hash_password(userrow['login'], i) == bytes(userrow['password'])

			check_password_validator = form.Validator('is invalid', check_old_password)

			f.validators.append( password_match_validator )
			f.password.validators = [password_validator]
			f.old_password.validators = [password_validator, check_password_validator]

		if f.d['display_name']:
			f.validators.append( unique_display_name_validator )
			f.display_name.validators = [display_name_validator]

		if not f.validates():
			return render.editprofile(f)

		data_to_change = {'where': 'id = $id', 'vars': {'id': session.user_id}}

		if f.d['password']: # changing password
			data_to_change['password'] = sqlite3.Binary(hash_password(userrow['login'], f.d.password))

		if f.d['display_name']: # changing display name
			data_to_change['display_name'] = f.d['display_name']

		if len(data_to_change.keys()) > 2: # if changing anything
			db.update('whois_users', **data_to_change)

		raise web.seeother('/panel')

class user_panel:
	login_form = form.Form(
		form.Textbox('login', login_validator, description='Login'),
		form.Password('password', password_validator,description=u'Hasło'),
		form.Button('submit', type='submit', html=u'Zaloguj się'))

	def GET(self):
		if not session.user_id:
			return render.login(user_panel.login_form())

		try:
			userrow = get_userrow()
			devices = db.query('SELECT * FROM whois_devices WHERE user_id = $user_id', vars={'user_id': userrow['id']})
		except:
			session.kill()

			raise web.seeother('/panel')

		return render.panel(userrow, devices)

	def POST(self):
		if session.user_id:
			raise web.seeother('/panel')

		f = user_panel.login_form()

		if not f.validates():
			f.password.value = ''
			return render.login(f)

		result = db.query('SELECT id FROM whois_users WHERE login == $login AND password == $password', 
			vars={'login': f.d.login, 'password': sqlite3.Binary(hash_password(f.d.login, f.d.password))})

		try:
			uid = result[0]['id']
		except:
			time.sleep(5) # to slow down brute-force attemps
			f.password.value = ''
			return render.login(f, True)

		db.query('UPDATE whois_users SET last_login = strftime(\'%s\',\'now\'), access_key = $access_key WHERE id = $id', vars=
			{'access_key': generate_access_key(), 'id': uid})
	
		session.user_id = uid

		raise web.seeother('/panel')

class user_remove_device:
	def GET(self, device_mac):
		if not session.user_id:
			raise web.seeother('/panel')

		try:
			mac_addr = sqlite3.Binary(mac_to_binary(device_mac))

			devicerow = db.query('SELECT * FROM whois_devices WHERE mac_addr = $mac_addr', vars=
				{'mac_addr': mac_addr})[0]


			if devicerow.user_id != session.user_id:
				raise web.badrequest(u'To urządzenie nie jest Twoje!')

			db.delete('whois_devices', where='mac_addr = $mac_addr', vars=
				{'mac_addr': mac_addr})
		except web.badrequest as e:
			raise e
		except:
			pass

		raise web.seeother('/panel')

class index:
	def GET(self):
		return render.index()

class user_logout:
	def GET(self):
		session.kill()

		raise web.seeother('/panel')

if __name__ == '__main__':
	db.query('CREATE TABLE IF NOT EXISTS whois_users (id INTEGER PRIMARY KEY AUTOINCREMENT, display_name VARCHAR(100), login VARCHAR(32) UNIQUE, password BLOB(32), access_key VARCHAR(10), registered_at INTEGER, last_login INTEGER)')
	db.query('CREATE TABLE IF NOT EXISTS whois_devices (mac_addr BLOB(6) PRIMARY KEY UNIQUE, user_id INTEGER, last_seen INTEGER)')
	db.query('CREATE TABLE IF NOT EXISTS whois_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date_from INTEGER, date_to INTEGER)')

	timer_update_history()

	app.run()
