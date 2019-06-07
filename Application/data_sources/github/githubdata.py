import socket
#https://github.com/josegonzalez/python-github-backup/blob/master/bin/github-backup
import argparse
import base64
import calendar
import codecs
import errno
import getpass
import json
import logging
import os
import re
import select
import subprocess
import sys
import time
import platform
from urllib.parse import urlparse
from urllib.parse import quote as urlquote
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from urllib.request import Request
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)
FNULL = open(os.devnull, 'w')

def logging_subprocess(popenargs,
                       logger,
                       stdout_log_level=logging.DEBUG,
                       stderr_log_level=logging.ERROR,
                       **kwargs):
    """
    Variant of subprocess.call that accepts a logger instead of stdout/stderr,
    and logs stdout messages via logger.debug and stderr messages via
    logger.error.
    """
    child = subprocess.Popen(popenargs, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, **kwargs)
    if sys.platform == 'win32':
        log_info("Windows operating system detected - no subprocess logging will be returned")

    log_level = {child.stdout: stdout_log_level,
                 child.stderr: stderr_log_level}

    def check_io():
        if sys.platform == 'win32':
            return
        ready_to_read = select.select([child.stdout, child.stderr],
                                      [],
                                      [],
                                      1000)[0]
        for io in ready_to_read:
            line = io.readline()
            if not logger:
                continue
            if not (io == child.stderr and not line):
                logger.log(log_level[io], line[:-1])

    # keep checking stdout/stderr until the child exits
    while child.poll() is None:
        check_io()

    check_io()  # check again to catch anything after the process exits

    rc = child.wait()

    if rc != 0:
        print('{} returned {}:'.format(popenargs[0], rc), file=sys.stderr)
        print('\t', ' '.join(popenargs), file=sys.stderr)

    return rc

def get_query_args(query_args=None):
    if not query_args:
        query_args = {}
    return query_args


def _request_url_error(template, retry_timeout):
    # Incase of a connection timing out, we can retry a few time
    # But we won't crash and not back-up the rest now
    logging.info('{} timed out'.format(template))
    retry_timeout -= 1

    if retry_timeout >= 0:
        return True

    log_error('{} timed out to much, skipping!')
    return False

def _request_http_error(exc, auth, errors):
    # HTTPError behaves like a Response so we can
    # check the status code and headers to see exactly
    # what failed.

    should_continue = False
    headers = exc.headers
    limit_remaining = int(headers.get('x-ratelimit-remaining', 0))

    if exc.code == 403 and limit_remaining < 1:
        # The X-RateLimit-Reset header includes a
        # timestamp telling us when the limit will reset
        # so we can calculate how long to wait rather
        # than inefficiently polling:
        gm_now = calendar.timegm(time.gmtime())
        reset = int(headers.get('x-ratelimit-reset', 0)) or gm_now
        # We'll never sleep for less than 10 seconds:
        delta = max(10, reset - gm_now)

        limit = headers.get('x-ratelimit-limit')
        logging.error('Exceeded rate limit of {} requests; waiting {} seconds to reset'.format(limit, delta))

        if auth is None:
            logging.warning('Hint: Authenticate to raise your GitHub rate limit')

        time.sleep(delta)
        should_continue = True
    return errors, should_continue

def _get_response(request, auth, template):
    retry_timeout = 3
    errors = []
    # We'll make requests in a loop so we can
    # delay and retry in the case of rate-limiting
    while True:
        should_continue = False
        try:
            r = urlopen(request)
        except HTTPError as exc:
            errors, should_continue = _request_http_error(exc, auth, errors)  # noqa
            r = exc
        except URLError as e:
            logging.warning(e.reason)
            should_continue = _request_url_error(template, retry_timeout)
            if not should_continue:
                raise
        except socket.error as e:
            logger.warning(e.strerror)
            should_continue = _request_url_error(template, retry_timeout)
            if not should_continue:
                raise

        if should_continue:
            continue

        break
    return r, errors


def get_auth(username, password, encode=True):
    auth = None
    """
    if args.osx_keychain_item_name:
        if not args.osx_keychain_item_account:
            logging.error('You must specify both name and account fields for osx keychain password items')
        else:
            if platform.system() != 'Darwin':
                logging.error("Keychain arguments are only supported on Mac OSX")
            try:
                with open(os.devnull, 'w') as devnull:
                    token = (subprocess.check_output([
                        'security', 'find-generic-password',
                        '-s', args.osx_keychain_item_name,
                        '-a', args.osx_keychain_item_account,
                        '-w'], stderr=devnull).strip())
                auth = token + ':' + 'x-oauth-basic'
            except:
                logging.error('No password item matching the provided name and account could be found in the osx keychain.')
    elif args.osx_keychain_item_account:
        logging.error('You must specify both name and account fields for osx keychain password items')
    elif args.token:
        _path_specifier = 'file://'
        if args.token.startswith(_path_specifier):
            args.token = open(args.token[len(_path_specifier):],
                              'rt').readline().strip()
        auth = args.token + ':' + 'x-oauth-basic'
    """
    password = urlquote(password)
    auth = username + ':' + password
    if not auth:
        return None

    if not encode:
        return auth

    return base64.b64encode(auth.encode('ascii'))


def _construct_request(per_page, page, query_args, template, auth):
    querystring = urlencode(dict(list({
        'per_page': per_page,
        'page': page
    }.items()) + list(query_args.items())))

    request = Request(template + '?' + querystring)
    if auth is not None:
        request.add_header('Authorization', 'Basic '.encode('ascii') + auth)
    logger.info('Requesting {}?{}'.format(template, querystring))
    return request


def get_github_api_host(args=None):
    if args:
        if args.github_host:
            host = args.github_host + '/api/v3'
    else:
        host = 'api.github.com'

    return host


def get_github_host(args=None):
    if args:
        if args.github_host:
            host = args.github_host
    else:
        host = 'github.com'

    return host


def get_github_repo_url(username, password, repository):
    # if args.prefer_ssh:
    #     return repository['ssh_url']

    if repository.get('is_gist'):
        return repository['git_pull_url']

    auth = get_auth(username, password, False)
    if auth:
        repo_url = 'https://{0}@{1}/{2}/{3}.git'.format(
            auth,
            get_github_host(),
            repository['owner']['login'],
            repository['name'])
    else:
        repo_url = repository['clone_url']

    return repo_url


def retrieve_repositories(username,  password, authenticated_user):
    logger.info('Retrieving repositories')
    single_request = False
    # template = 'https://{0}/user/repos'.format(
    #         get_github_api_host())


    # # if args.user == authenticated_user['login']:
    # #     # we must use the /user/repos API to be able to access private repos
        
    # # else:
    # #     if args.private and not args.organization:
    # #         log_warning('Authenticated user is different from user being backed up, thus private repositories cannot be accessed')
    # #     template = 'https://{0}/users/{1}/repos'.format(
    # #         get_github_api_host(args),
    # #         args.user)

    # if args.organization:
    #     template = 'https://{0}/orgs/{1}/repos'.format(
    #         get_github_api_host(args),
    #         args.user)

    # if args.repository:
    #     
    single_request = True
    template = 'https://{0}/users/{1}/repos'.format(
            get_github_api_host(), username)

    repos = retrieve_data(username, password, template, single_request=single_request)
    logging.info(repos)

    """
    if args.all_starred:
        starred_template = 'https://{0}/users/{1}/starred'.format(get_github_api_host(), username)
        starred_repos = retrieve_data(username, password, starred_template, single_request=False)
        # flag each repo as starred for downstream processing
        for item in starred_repos:
            item.update({'is_starred': True})
        repos.extend(starred_repos)

    if args.include_gists:
        gists_template = 'https://{0}/users/{1}/gists'.format(get_github_api_host(), username)
        gists = retrieve_data(username, password,, gists_template, single_request=False)
        # flag each repo as a gist for downstream processing
        for item in gists:
            item.update({'is_gist': True})
        repos.extend(gists)

    if args.include_starred_gists:
        starred_gists_template = 'https://{0}/gists/starred'.format(get_github_api_host())
        starred_gists = retrieve_data(username, password, starred_gists_template, single_request=False)
        # flag each repo as a starred gist for downstream processing
        for item in starred_gists:
            item.update({'is_gist': True,
                         'is_starred': True})
        repos.extend(starred_gists)
    """
    return repos


def retrieve_data(username, password, template, query_args=None, single_request=False):
    auth = get_auth(username, password)
    logging.info(f"This is the auth {auth}")
    query_args = get_query_args(query_args)
    logging.info(f"This is the query_args {query_args}")
    per_page = 100
    page = 0
    data = []

    while True:
        page = page + 1
        request = _construct_request(per_page, page, query_args, template, auth)  # noqa
        r, errors = _get_response(request, auth, template)

        status_code = int(r.getcode())

        retries = 0
        while retries < 3 and status_code == 502:
            print('API request returned HTTP 502: Bad Gateway. Retrying in 5 seconds')
            retries += 1
            time.sleep(5)
            request = _construct_request(per_page, page, query_args, template, auth)  # noqa
            r, errors = _get_response(request, auth, template)

            status_code = int(r.getcode())

        if status_code != 200:
            template = 'API request returned HTTP {0}: {1}'
            errors.append(template.format(status_code, r.reason))
            logging.error(errors)

        response = json.loads(r.read().decode('utf-8'))
        if len(errors) == 0:
            if type(response) == list:
                data.extend(response)
                if len(response) < per_page:
                    break
            elif type(response) == dict and single_request:
                data.append(response)

        if len(errors) > 0:
            logging.error(errors)

        if single_request:
            break

    return data


def get_authenticated_user(username, password):
    #template = 'https://{0}/user'.format(get_github_api_host(args))
    template = 'https://api.github.com/user'
    data = retrieve_data(username, password, template, single_request=True)
    return data[0]


def mkdir_p(*args):
    for path in args:
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

def mask_password(url, secret='*****'):
    parsed = urlparse(url)

    if not parsed.password:
        return url
    elif parsed.password == 'x-oauth-basic':
        return url.replace(parsed.username, secret)

    return url.replace(parsed.password, secret)

def backup_repositories(username, password, output_directory, repositories):
    logging.info('Backing up repositories')
    repos_template = 'https://{0}/repos'.format(get_github_api_host())

    # if args.incremental:
    #     last_update = max(list(repository['updated_at'] for repository in repositories) or [time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime())])  # noqa
    #     last_update_path = os.path.join(output_directory, 'last_update')
    #     if os.path.exists(last_update_path):
    #         args.since = open(last_update_path).read().strip()
    #     else:
    #         args.since = None
    # else:
    #     args.since = None

    for repository in repositories:
        if repository.get('is_gist'):
            repo_cwd = os.path.join(output_directory, 'gists', repository['id'])
        elif repository.get('is_starred'):
            # put starred repos in -o/starred/${owner}/${repo} to prevent collision of
            # any repositories with the same name
            repo_cwd = os.path.join(output_directory, 'starred', repository['owner']['login'], repository['name'])
        else:
            repo_cwd = os.path.join(output_directory, 'repositories', repository['name'])

        repo_dir = os.path.join(repo_cwd, 'repository')
        repo_url = get_github_repo_url(username, password, repository)

        logger.info(f"This is the repo url {repo_url}")
        #include_gists = (args.include_gists or args.include_starred_gists)
        # if (args.include_repository or args.include_everything) \
        #         or (include_gists and repository.get('is_gist')):
        repo_name = repository.get('name') if not repository.get('is_gist') else repository.get('id')
        fetch_repository(repo_name,
                            repo_url,
                            repo_dir,
                            skip_existing=False,
                            bare_clone=False,
                            lfs_clone=False) #clone LFS repositories (requires Git LFS to be installed, https://git-lfs.github.com) [*])

        if repository.get('is_gist'):
            # dump gist information to a file as well
            output_file = '{0}/gist.json'.format(repo_cwd)
            with codecs.open(output_file, 'w', encoding='utf-8') as f:
                json_dump(repository, f)

                continue  # don't try to back anything else for a gist; it doesn't exist

        #download_wiki = (args.include_wiki or args.include_everything)
        # download_wiki = True
        # if repository['has_wiki'] and download_wiki:
        #     fetch_repository(repository['name'],
        #                      repo_url.replace('.git', '.wiki.git'),
        #                      os.path.join(repo_cwd, 'wiki'),
        #                      skip_existing=args.skip_existing,
        #                      bare_clone=args.bare_clone,
        #                      lfs_clone=args.lfs_clone)

        # if args.include_issues or args.include_everything:
        #     backup_issues(args, repo_cwd, repository, repos_template)

        # if args.include_pulls or args.include_everything:
        #     backup_pulls(args, repo_cwd, repository, repos_template)

        # if args.include_milestones or args.include_everything:
        #     backup_milestones(args, repo_cwd, repository, repos_template)

        # if args.include_labels or args.include_everything:
        #     backup_labels(args, repo_cwd, repository, repos_template)

        """
        backup_hooks(args, repo_cwd, repository, repos_template)
        backup_issues(args, repo_cwd, repository, repos_template)
        backup_pulls(args, repo_cwd, repository, repos_template)
        backup_milestones(args, repo_cwd, repository, repos_template)
        backup_labels(args, repo_cwd, repository, repos_template)
        backup_hooks(args, repo_cwd, repository, repos_template)
        """


    # if args.incremental:
    #     open(last_update_path, 'w').write(last_update)


def backup_issues(args, repo_cwd, repository, repos_template):
    has_issues_dir = os.path.isdir('{0}/issues/.git'.format(repo_cwd))
    if args.skip_existing and has_issues_dir:
        return

    log_info('Retrieving {0} issues'.format(repository['full_name']))
    issue_cwd = os.path.join(repo_cwd, 'issues')
    mkdir_p(repo_cwd, issue_cwd)

    issues = {}
    issues_skipped = 0
    issues_skipped_message = ''
    _issue_template = '{0}/{1}/issues'.format(repos_template,
                                              repository['full_name'])

    should_include_pulls = args.include_pulls or args.include_everything
    issue_states = ['open', 'closed']
    for issue_state in issue_states:
        query_args = {
            'filter': 'all',
            'state': issue_state
        }
        if args.since:
            query_args['since'] = args.since

        _issues = retrieve_data(args,
                                _issue_template,
                                query_args=query_args)
        for issue in _issues:
            # skip pull requests which are also returned as issues
            # if retrieving pull requests is requested as well
            if 'pull_request' in issue and should_include_pulls:
                issues_skipped += 1
                continue

            issues[issue['number']] = issue

    if issues_skipped:
        issues_skipped_message = ' (skipped {0} pull requests)'.format(
            issues_skipped)

    log_info('Saving {0} issues to disk{1}'.format(
        len(list(issues.keys())), issues_skipped_message))
    comments_template = _issue_template + '/{0}/comments'
    events_template = _issue_template + '/{0}/events'
    for number, issue in list(issues.items()):
        if args.include_issue_comments or args.include_everything:
            template = comments_template.format(number)
            issues[number]['comment_data'] = retrieve_data(args, template)
        if args.include_issue_events or args.include_everything:
            template = events_template.format(number)
            issues[number]['event_data'] = retrieve_data(args, template)

        issue_file = '{0}/{1}.json'.format(issue_cwd, number)
        with codecs.open(issue_file, 'w', encoding='utf-8') as f:
            json_dump(issue, f)


def backup_pulls(args, repo_cwd, repository, repos_template):
    has_pulls_dir = os.path.isdir('{0}/pulls/.git'.format(repo_cwd))
    if args.skip_existing and has_pulls_dir:
        return

    log_info('Retrieving {0} pull requests'.format(repository['full_name']))  # noqa
    pulls_cwd = os.path.join(repo_cwd, 'pulls')
    mkdir_p(repo_cwd, pulls_cwd)

    pulls = {}
    _pulls_template = '{0}/{1}/pulls'.format(repos_template,
                                             repository['full_name'])
    query_args = {
        'filter': 'all',
        'state': 'all',
        'sort': 'updated',
        'direction': 'desc',
    }

    if not args.include_pull_details:
        pull_states = ['open', 'closed']
        for pull_state in pull_states:
            query_args['state'] = pull_state
            # It'd be nice to be able to apply the args.since filter here...
            _pulls = retrieve_data(args,
                                   _pulls_template,
                                   query_args=query_args)
            for pull in _pulls:
                if not args.since or pull['updated_at'] >= args.since:
                    pulls[pull['number']] = pull
    else:
        _pulls = retrieve_data(args,
                               _pulls_template,
                               query_args=query_args)
        for pull in _pulls:
            if not args.since or pull['updated_at'] >= args.since:
                pulls[pull['number']] = retrieve_data(
                    args,
                    _pulls_template + '/{}'.format(pull['number']),
                    single_request=True
                )

    log_info('Saving {0} pull requests to disk'.format(
        len(list(pulls.keys()))))
    comments_template = _pulls_template + '/{0}/comments'
    commits_template = _pulls_template + '/{0}/commits'
    for number, pull in list(pulls.items()):
        if args.include_pull_comments or args.include_everything:
            template = comments_template.format(number)
            pulls[number]['comment_data'] = retrieve_data(args, template)
        if args.include_pull_commits or args.include_everything:
            template = commits_template.format(number)
            pulls[number]['commit_data'] = retrieve_data(args, template)

        pull_file = '{0}/{1}.json'.format(pulls_cwd, number)
        with codecs.open(pull_file, 'w', encoding='utf-8') as f:
            json_dump(pull, f)


def backup_milestones(args, repo_cwd, repository, repos_template):
    milestone_cwd = os.path.join(repo_cwd, 'milestones')
    if args.skip_existing and os.path.isdir(milestone_cwd):
        return

    log_info('Retrieving {0} milestones'.format(repository['full_name']))
    mkdir_p(repo_cwd, milestone_cwd)

    template = '{0}/{1}/milestones'.format(repos_template,
                                           repository['full_name'])

    query_args = {
        'state': 'all'
    }

    _milestones = retrieve_data(args, template, query_args=query_args)

    milestones = {}
    for milestone in _milestones:
        milestones[milestone['number']] = milestone

    log_info('Saving {0} milestones to disk'.format(
        len(list(milestones.keys()))))
    for number, milestone in list(milestones.items()):
        milestone_file = '{0}/{1}.json'.format(milestone_cwd, number)
        with codecs.open(milestone_file, 'w', encoding='utf-8') as f:
            json_dump(milestone, f)


def backup_labels(args, repo_cwd, repository, repos_template):
    label_cwd = os.path.join(repo_cwd, 'labels')
    output_file = '{0}/labels.json'.format(label_cwd)
    template = '{0}/{1}/labels'.format(repos_template,
                                       repository['full_name'])
    _backup_data(args,
                 'labels',
                 template,
                 output_file,
                 label_cwd)


def backup_hooks(args, repo_cwd, repository, repos_template):
    auth = get_auth(args)
    if not auth:
        log_info("Skipping hooks since no authentication provided")
        return
    hook_cwd = os.path.join(repo_cwd, 'hooks')
    output_file = '{0}/hooks.json'.format(hook_cwd)
    template = '{0}/{1}/hooks'.format(repos_template,
                                      repository['full_name'])
    try:
        _backup_data(args,
                     'hooks',
                     template,
                     output_file,
                     hook_cwd)
    except SystemExit:
        log_info("Unable to read hooks, skipping")

def fetch_repository(name,
                     remote_url,
                     local_dir,
                     skip_existing=False,
                     bare_clone=False,
                     lfs_clone=False):
    if bare_clone:
        if os.path.exists(local_dir):
            clone_exists = subprocess.check_output(['git',
                                                    'rev-parse',
                                                    '--is-bare-repository'],
                                                   cwd=local_dir) == b"true\n"
        else:
            clone_exists = False
    else:
        clone_exists = os.path.exists(os.path.join(local_dir, '.git'))

    if clone_exists and skip_existing:
        return

    masked_remote_url = mask_password(remote_url)

    initialized = subprocess.call('git ls-remote ' + remote_url,
                                  stdout=FNULL,
                                  stderr=FNULL,
                                  shell=True)
    if initialized == 128:
        logging.info("Skipping {0} ({1}) since it's not initialized".format(
            name, masked_remote_url))
        return

    if clone_exists:
        logging.info('Updating {0} in {1}'.format(name, local_dir))

        remotes = subprocess.check_output(['git', 'remote', 'show'],
                                          cwd=local_dir)
        remotes = [i.strip() for i in remotes.decode('utf-8').splitlines()]

        if 'origin' not in remotes:
            git_command = ['git', 'remote', 'rm', 'origin']
            logging_subprocess(git_command, None, cwd=local_dir)
            git_command = ['git', 'remote', 'add', 'origin', remote_url]
            logging_subprocess(git_command, None, cwd=local_dir)
        else:
            git_command = ['git', 'remote', 'set-url', 'origin', remote_url]
            logging_subprocess(git_command, None, cwd=local_dir)

        if lfs_clone:
            git_command = ['git', 'lfs', 'fetch', '--all', '--force', '--tags', '--prune']
        else:
            git_command = ['git', 'fetch', '--all', '--force', '--tags', '--prune']
        logging_subprocess(git_command, None, cwd=local_dir)
    else:
        logging.info('Cloning {0} repository from {1} to {2}'.format(
            name,
            masked_remote_url,
            local_dir))
        if bare_clone:
            if lfs_clone:
                git_command = ['git', 'lfs', 'clone', '--mirror', remote_url, local_dir]
            else:
                git_command = ['git', 'clone', '--mirror', remote_url, local_dir]
        else:
            if lfs_clone:
                git_command = ['git', 'lfs', 'clone', remote_url, local_dir]
            else:
                git_command = ['git', 'clone', remote_url, local_dir]
        logging_subprocess(git_command, None)


def backup_account(args, output_directory):
    account_cwd = os.path.join(output_directory, 'account')

    if args.include_starred or args.include_everything:
        output_file = "{0}/starred.json".format(account_cwd)
        template = "https://{0}/users/{1}/starred".format(get_github_api_host(args), args.user)
        _backup_data(args,
                     "starred repositories",
                     template,
                     output_file,
                     account_cwd)

    if args.include_watched or args.include_everything:
        output_file = "{0}/watched.json".format(account_cwd)
        template = "https://{0}/users/{1}/subscriptions".format(get_github_api_host(args), args.user)
        _backup_data(args,
                     "watched repositories",
                     template,
                     output_file,
                     account_cwd)

    if args.include_followers or args.include_everything:
        output_file = "{0}/followers.json".format(account_cwd)
        template = "https://{0}/users/{1}/followers".format(get_github_api_host(args), args.user)
        _backup_data(args,
                     "followers",
                     template,
                     output_file,
                     account_cwd)

    if args.include_following or args.include_everything:
        output_file = "{0}/following.json".format(account_cwd)
        template = "https://{0}/users/{1}/following".format(get_github_api_host(args), args.user)
        _backup_data(args,
                     "following",
                     template,
                     output_file,
                     account_cwd)


def _backup_data(args, name, template, output_file, output_directory):
    skip_existing = args.skip_existing
    if not skip_existing or not os.path.exists(output_file):
        logging.info('Retrieving {0} {1}'.format(args.user, name))
        mkdir_p(output_directory)
        data = retrieve_data(args, template)

        logging.info('Writing {0} {1} to disk'.format(len(data), name))
        with codecs.open(output_file, 'w', encoding='utf-8') as f:
            json_dump(data, f)


def json_dump(data, output_file):
    json.dump(data,
              output_file,
              ensure_ascii=False,
              sort_keys=True,
              indent=4,
              separators=(',', ': '))



def main():
    username = "graphicaldot"
    password = "mitthuparishweta"
    home = os.path.expanduser("~")

    output_directory = f"{home}/.datapod/github"
    output_directory = os.path.realpath(output_directory)
    if not os.path.isdir(output_directory):
        logging.info('Create output directory {0}'.format(output_directory))
        mkdir_p(output_directory)

    # if args.lfs_clone:
    #     check_git_lfs_install()

    logging.info('Backing up user {0} to {1}'.format(username, output_directory))

    authenticated_user = get_authenticated_user(username, password)
    logging.info(authenticated_user)
    repositories = retrieve_repositories(username, password, authenticated_user)
    backup_repositories(username, password, output_directory, repositories)

    """

    repositories = filter_repositories(args, repositories)
    backup_account(args, output_directory)
    """

if __name__ == '__main__':
    main()

