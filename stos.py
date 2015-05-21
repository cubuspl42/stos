import configparser
import getpass
import html
import logging
import os
from os import path
import re
import sys
import time

from bs4 import BeautifulSoup
import colorama
import html2text
import requests
from tabulate import tabulate

logging.captureWarnings(True)

_stos_url = 'https://kaims.pl/~kmocet/stos/index.php'

def _fatal(message):
    print('fatal: ' + message, file=sys.stderr)
    sys.exit(1)

def _debug(html_text):
    debug_file = os.environ.get('STOS_DEBUG_FILE')
    if debug_file :
        with open(debug_file, 'w') as file:
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

def _print_results(soup) :
    result = soup.find(id='result')
    if result :
        print("**** Wyniki ****\n")
        rows = []
        trs = result.find_all('tr')[1:-1]
        for tr in trs :
            tds = tr.find_all('td')[:-3]
            style = colorama.Fore.RED
            if tr['class'][0] == 'testacc':
                style = colorama.Fore.GREEN
            style_reset = colorama.Fore.RESET
            rows.append([style + str(td.string or '') + style_reset for td in tds])
        if rows :
            uwagi = ['Uwagi'] if 'Uwagi' in soup else []
            print(tabulate(rows, headers=['Test', 'Wynik'] + uwagi + ['Punkty', 'Czas [s]']))
            print()
        else:
            print(result.get_text())
            print()

def _print_infofile(soup) :
    info = soup.find(id='infofile')
    if info :
        print("**** Dodatkowe informacje ****")

        compileroutput = info.find(id='compileroutput')
        if compileroutput :
            print(compileroutput.get_text())

        for element in info.children :
            if element.name == 'table':
                table = element
                tds = table.find_all('td')
                wrong_lines = tds[0].get_text().splitlines();
                if not wrong_lines[-1] :
                    wrong_lines.pop()
                correct_lines = tds[1].get_text().splitlines();
                if not correct_lines[-1] :
                    correct_lines.pop()
                rows = []
                i = 0
                while(i < len(wrong_lines) or i < len(correct_lines)) :
                    rows.append([wrong_lines[i] if i < len(wrong_lines) else '',
                                 correct_lines[i] if i < len(correct_lines) else ''])
                    i += 1
                headers = [str(th.string) for th in table.find_all('th')]
                print(tabulate(rows, headers=headers))
            else :
                try :
                    if element['class'][0] == 'trace' :
                        print(re.sub("\n+" , "\n", html2text.html2text(str(element))))
                except (KeyError, TypeError):
                    pass

def _print_status(session, config) :
    status_html = _get_status_html(session, config)
    while any(s in status_html for s in ('przetwarzane', 'oczekuje', 'kolejce')) :
        time.sleep(2)
        status_html = _get_status_html(session, config)

    #_debug(status_html)
    soup = BeautifulSoup(html.unescape(status_html))
    _print_results(soup)
    _print_infofile(soup)

def push(repo_path) :
    config = _read_config(repo_path)
    username, password = _get_username_password(repo_path, config)
    session = requests.Session()
    _login_to_stos(session, username, password)
    _put_files(repo_path, session, config)
    _print_status(session, config)

def status(repo_path) :
    config = _read_config(repo_path)
    username, password = _get_username_password(repo_path, config)
    session = requests.Session()
    _login_to_stos(session, username, password)
    _print_status(session, config)

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
        print("example: stos init 365 # initialize problem with id 365", file=sys.stderr)
        print("example: stos push # send sources to STOS and show status", file=sys.stderr)
        print("example: stos status # show status of the problem", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        _fatal("Connection error")
