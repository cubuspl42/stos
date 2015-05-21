import configparser
import getpass
import os
from os import path
import sys
import time

from bs4 import BeautifulSoup
import colorama
import requests
from tabulate import tabulate

_stos_url = 'https://kaims.pl/~kmocet/stos/index.php'

def _fatal(message):
    print('fatal: ' + message, file=sys.stderr)
    sys.exit(1)

def _debug(html_text):
    with open('/tmp/stos_response.html', 'w') as file:
        file.write(html_text)

def _stos_path(repo_path):
    return path.join(repo_path, '.stos')

def _config_path(repo_path) :
    return path.join(_stos_path(repo_path), 'config')

def init(repo_path, problem_id) :
    os.makedirs(_stos_path(repo_path), exist_ok=True)
    with open(_config_path(repo_path), 'w') as configfile :
        config = configparser.ConfigParser()
        config['STOS'] = {'problem_id': problem_id}
        config.write(configfile)

def _read_config(repo_path) :
    config = configparser.ConfigParser()
    try:
        with open(_config_path(repo_path)) as configfile :
            config.read_file(configfile)
    except FileNotFoundError:
        _fatal('Not a STOS repository')
    return config

def _write_config(repo_path, config) :
    with open(_config_path(repo_path), 'w') as configfile :
        config.write(configfile)

def _get_username_password(repo_path, config) :
    stos_config = config['STOS']
    try :
        username = stos_config['username']
        password = stos_config['password']
    except KeyError:
        username = input('STOS username: ')
        password = getpass.getpass('STOS password: ')
        stos_config['username'] = username
        stos_config['password'] = password
        _write_config(repo_path, config)
    return username, password

def _login_to_stos(session, username, password) :
    params = {'p': 'login'}
    data = {'login': username, 'password': password}
    r = session.post(_stos_url, params=params, data=data, verify=False)
    if 'Wylogowanie' not in r.text:
        _fatal('Login unsucessful')

def _put_files(repo_path, session, config) :
    stos_config = config['STOS']
    problem_id = stos_config['problem_id']
    params = {'p': 'put'}
    data = {'code': problem_id, 'context': '84'}
    files = {}
    i = 1
    for filename in os.listdir(repo_path) :
        if any(filename.endswith(ext) for ext in ['.cpp', '.h', '.hpp']) :
            files.update({'afile' + str(i) : (filename, open(filename))})
            i += 1
    r = session.post(_stos_url, params=params, data=data, files=files, verify=False)
    if 'przetwarzane' not in r.text and 'oczekuje' not in r.text :
        _debug(r.text)
        _fatal('Failed to upload files to STOS')

def _get_status_html(session, config) :
    params = {'p': 'status', 'probid': config['STOS']['problem_id']}
    r = session.get(_stos_url, params=params, verify=False)
    return r.text

def _print_test_coverage(session, config) :
    status_html = _get_status_html(session, config)
    while 'przetwarzane' in status_html or 'oczekuje' in status_html:
        time.sleep(2)
        status_html = _get_status_html(session, config)
    _debug(status_html)
    soup = BeautifulSoup(status_html)
    result = soup.find(id='result')
    rows = []
    trs = result.find_all('tr')[1:-1]
    for tr in trs :
        tds = tr.find_all('td')[:-3]
        style = colorama.Fore.RED
        if tr['class'][0] == 'testacc':
            style = colorama.Fore.GREEN
        style_reset = colorama.Fore.RESET
        rows.append([style + str(td.string or '') + style_reset for td in tds])
    uwagi = ['Uwagi'] if 'Uwagi' in status_html else []
    print(tabulate(rows, headers=['Test', 'Wynik'] + uwagi + ['Punkty', 'Czas [s]']))

def push(repo_path) :
    config = _read_config(repo_path)
    username, password = _get_username_password(repo_path, config)
    session = requests.Session()
    _login_to_stos(session, username, password)
    _put_files(repo_path, session, config)
    _print_test_coverage(session, config)

def status(repo_path) :
    config = _read_config(repo_path)
    username, password = _get_username_password(repo_path, config)
    session = requests.Session()
    _login_to_stos(session, username, password)
    _print_test_coverage(session, config)

if __name__ == "__main__":
    colorama.init()
    try:
        command = sys.argv[1]
        cwd = os.getcwd()
        if command == 'init':
            init(cwd, sys.argv[2])
        elif command == 'push':
            push(cwd)
        elif command == 'status':
            status(cwd)
    except IndexError:
        print("usage: stos <command> <args>", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        _fatal("Connection error")
