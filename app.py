from os import environ as env
from os.path import exists
from json import loads
import requests

# Configs
LANG_SKIP_COUNTING = ['Jupyter Notebook']
PERCENTAGE_ROUND = 2
TEMPLATE = 'template.md' # If blank, it will be disabled.
OUTPUT = 'OUTPUT.md'

# Constants
API_BASES = 'https://api.github.com'
API_GET_USER = API_BASES + '/user'
HEADER_BASES = {
    'User-Agent': 'Mozilla/5.0'
}
# Secrets
SECRETS_OAUTH_TOKEN_NAME = 'OAUTH_TOKEN'
SECRETS_OAUTH_TOKEN = ''

# Module Functions
def get_json_resources_using_url(url, ver='2022-11-28', params={}):
    headers = HEADER_BASES.copy()
    headers['Accept'] = 'application/vnd.github+json'
    headers['X-GitHub-Api-Version'] = ver
    return loads(requests.get(url=url, headers=headers, params=params).text)

def get_token():
    headers = HEADER_BASES.copy()
    headers['Authorization'] = 'Bearer {}'.format(SECRETS_OAUTH_TOKEN)
    return loads(requests.get(url=API_BASES, headers=headers).text)

def get_user():
    headers = HEADER_BASES.copy()
    headers['Authorization'] = 'Bearer {}'.format(SECRETS_OAUTH_TOKEN)
    return loads(requests.get(url=API_GET_USER, headers=headers).text)

# Processes
def init():
    global SECRETS_OAUTH_TOKEN
    global HEADER_BASES
    if SECRETS_OAUTH_TOKEN_NAME in env:
        SECRETS_OAUTH_TOKEN = env[SECRETS_OAUTH_TOKEN_NAME]
        HEADER_BASES['Authorization'] = 'Bearer {}'.format(SECRETS_OAUTH_TOKEN)
    else:
        print('No environment variables.')
        exit(1)

def load_repo_lang_urls():
    user = get_user()
    targeted_repos = 1
    language_urls = []
    # Todo: reimplementing required
    # https://docs.github.com/ko/enterprise-cloud@latest/rest/guides/using-pagination-in-the-rest-api?apiVersion=2022-11-28
    page, per_page = 0, 100
    while targeted_repos < user['public_repos']:
        params = {'page': page, 'per_page': per_page}
        repos = get_json_resources_using_url(user['repos_url'], params=params)
        for repo in repos:
            language_urls.append(repo['languages_url'])
        targeted_repos += len(language_urls)
        page += 1
    return language_urls

def sum_repository_language_statistics(language_urls: list):
    repos_langs = {}
    for language_url in language_urls:
        repo_langs = get_json_resources_using_url(language_url)
        for repo_lang in repo_langs:
            if repo_lang in repos_langs:
                repos_langs[repo_lang] += repo_langs[repo_lang]
            else:
                repos_langs[repo_lang] = repo_langs[repo_lang]
    return repos_langs

def calc_percentage_lang_stats(lang_stats: dict):
    for skip_lang in LANG_SKIP_COUNTING:
        if skip_lang in lang_stats:
            del lang_stats[skip_lang]
    sums = sum(lang_stats.values())
    lang_percentage = {}
    for lang in lang_stats:
        lang_percentage[lang] = lang_stats[lang] / sums
    lang_percentage = sorted(lang_percentage.items(), key=lambda x:x[1], reverse=True)
    return lang_percentage

def write_result_to_string(lang_stats_list_tupled: list, lang_stats: dict):
    lang_name_len = max([len(tupled[0]) for tupled in lang_stats_list_tupled])
    string_left_width = lang_name_len + 5
    string_body = ''
    for lang in lang_stats_list_tupled:
        string_body += lang[0].ljust(string_left_width, '.') + '{}% ({})'.format(format(lang[1] * 100, f'.{PERCENTAGE_ROUND}f'), lang_stats[lang[0]])
        string_body += '\n'
    return string_body

def write_to_local_file(string_result: str):
    puts = ''
    if TEMPLATE:
        puts = open(TEMPLATE).read()
        puts = puts.replace('{{ LANG_STATS }}', string_result)
    else:
        puts = string_result
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(puts)

if __name__ == '__main__':
    init()
    repo_lang_urls = load_repo_lang_urls()
    lang_stats = sum_repository_language_statistics(repo_lang_urls)
    lang_stats_filtered = calc_percentage_lang_stats(lang_stats)
    string_result = write_result_to_string(lang_stats_filtered, lang_stats)
    write_to_local_file(string_result)
