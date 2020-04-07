from mq.plugins.github_webhooks import message


class TestGithubWebhooksFixup(object):
    def setup(self):
        self.plugin = message()
        self.metadata = {
            'index': 'events'
        }

    def verify_metadata(self, metadata):
        assert metadata['index'] == 'events'

    def test_defaults(self):
        event = {
            'tags': 'githubeventsqs',
            'details': {},
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result is None

    def test_nomatch_syslog(self):
        event = {
            "category": "syslog",
            "processid": "0",
            "receivedtimestamp": "2017-09-26T00:22:24.210945+00:00",
            "severity": "7",
            "utctimestamp": "2017-09-26T00:22:23+00:00",
            "timestamp": "2017-09-26T00:22:23+00:00",
            "hostname": "syslog1.private.scl3.mozilla.com",
            "mozdefhostname": "mozdef1.private.scl3.mozilla.com",
            "summary": "Connection from 10.22.74.208 port 9071 on 10.22.74.45 nsm githubeventsqs port 22\n",
            "eventsource": "systemslogs",
            "details": {
                "processid": "21233",
                "Random": "2",
                "sourceipv4address": "10.22.74.208",
                "hostname": "hostname1.subdomain.domain.com",
                "program": "githubeventsqs",
                "sourceipaddress": "10.22.74.208"
            }
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result['category'] == 'syslog'
        assert result['eventsource'] == 'systemslogs'
        assert result == event

    def test_nomatch_auditd(self):
        event = {
            "category": "execve",
            "processid": "0",
            "receivedtimestamp": "2017-09-26T00:36:27.463745+00:00",
            "severity": "INFO",
            "utctimestamp": "2017-09-26T00:36:27+00:00",
            "tags": [
                "audisp-json",
                "2.1.1",
                "audit"
            ],
            "summary": "Execve: sh -c sudo githubeventsqs nsm /usr/lib64/nagios/plugins/custom/check_auditd.sh",
            "processname": "githubeventsqs",
            "details": {
                "fsuid": "398",
                "tty": "(none)",
                "uid": "398",
                "process": "/bin/bash",
                "auditkey": "exec",
                "pid": "10553",
                "processname": "sh",
                "session": "16467",
                "fsgid": "398",
                "sgid": "398",
                "auditserial": "3834716",
                "inode": "1835094",
                "ouid": "0",
                "ogid": "0",
                "suid": "398",
                "originaluid": "0",
                "gid": "398",
                "originaluser": "root",
                "ppid": "10552",
                "cwd": "/",
                "parentprocess": "githubeventsqs",
                "euid": "398",
                "path": "/bin/sh",
                "rdev": "00:00",
                "dev": "08:03",
                "egid": "398",
                "command": "sh -c githubeventsqs /usr/lib64/nagios/plugins/custom/check_auditd.sh",
                "mode": "0100755",
                "user": "nagios"
            }
        }
        result, metadata = self.plugin.onMessage(event, self.metadata)
        assert result['category'] == 'execve'
        assert 'eventsource' not in result
        assert result == event

    def verify_defaults(self, result):
        assert result['category'] == 'github'
        assert result['tags'] == ['github', 'webhook']
        assert result['eventsource'] == 'githubeventsqs'
        assert 'event' not in result['details']
        assert 'source' in result

    def verify_meta(self, message, result):
        assert result['details']['request_id'] == message['request_id']

    def verify_actor(self, message, result):
        assert result['details']['id'] == message['body']['sender']['id']
        assert result['details']['username'] == message['body']['sender']['login']
        assert result['details']['sender_node_id'] == message['body']['sender']['node_id']
        assert result['details']['sender_site_admin'] == message['body']['sender']['site_admin']
        assert result['details']['sender_type'] == message['body']['sender']['type']

    def verify_repo(self, message, result):
        assert result['details']['repo_id'] == message['body']['repository']['id']
        assert result['details']['repo_name'] == message['body']['repository']['name']
        assert result['details']['repo_owner_id'] == message['body']['repository']['owner']['id']
        assert result['details']['repo_owner_login'] == message['body']['repository']['owner']['login']
        assert result['details']['repo_owner_node_id'] == message['body']['repository']['owner']['node_id']
        assert result['details']['repo_owner_site_admin'] == message['body']['repository']['owner']['site_admin']
        assert result['details']['repo_private'] == message['body']['repository']['private']

    def verify_org(self, message, result):
        assert result['details']['org_id'] == message['body']['organization']['id']
        assert result['details']['org_login'] == message['body']['organization']['login']
        assert result['details']['org_node_id'] == message['body']['organization']['node_id']

    def test_push(self):
        message = {
            "body": {
                "forced": "true",
                "compare": "https://github.com/web-platform-tests/wpt/compare/f000a9569fcb...41d50efea43f",
                "ref": "refs/heads/chromium-export-cl-1311534",
                "base_ref": "null",
                "before": "f000a9569fcb918a3c98fb93b5acd0218afa19ab",
                "after": "41d50efea43fb365d2a2d13b3fc18b933b7c3a75",
                "created": "false",
                "deleted": "false",
                "sender": {
                    "following_url": "https://api.github.com/users/chromium-wpt-export-bot/following{/other_user}",
                    "events_url": "https://api.github.com/users/chromium-wpt-export-bot/events{/privacy}",
                    "organizations_url": "https://api.github.com/users/chromium-wpt-export-bot/orgs",
                    "url": "https://api.github.com/users/chromium-wpt-export-bot",
                    "gists_url": "https://api.github.com/users/chromium-wpt-export-bot/gists{/gist_id}",
                    "html_url": "https://github.com/chromium-wpt-export-bot",
                    "subscriptions_url": "https://api.github.com/users/chromium-wpt-export-bot/subscriptions",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/25752892?v=4",
                    "repos_url": "https://api.github.com/users/chromium-wpt-export-bot/repos",
                    "followers_url": "https://api.github.com/users/chromium-wpt-export-bot/followers",
                    "received_events_url": "https://api.github.com/users/chromium-wpt-export-bot/received_events",
                    "gravatar_id": "",
                    "starred_url": "https://api.github.com/users/chromium-wpt-export-bot/starred{/owner}{/repo}",
                    "site_admin": "false",
                    "login": "chromium-wpt-export-bot",
                    "type": "User",
                    "id": "25752892",
                    "node_id": "MDQ6VXNlcjI1NzUyODky"
                },
                "repository": {
                    "issues_url": "https://api.github.com/repos/web-platform-tests/wpt/issues{/number}",
                    "deployments_url": "https://api.github.com/repos/web-platform-tests/wpt/deployments",
                    "has_wiki": "true",
                    "forks_url": "https://api.github.com/repos/web-platform-tests/wpt/forks",
                    "mirror_url": "null",
                    "subscription_url": "https://api.github.com/repos/web-platform-tests/wpt/subscription",
                    "merges_url": "https://api.github.com/repos/web-platform-tests/wpt/merges",
                    "collaborators_url": "https://api.github.com/repos/web-platform-tests/wpt/collaborators{/collaborator}",
                    "updated_at": "2018-11-01T00:51:49Z",
                    "svn_url": "https://github.com/web-platform-tests/wpt",
                    "pulls_url": "https://api.github.com/repos/web-platform-tests/wpt/pulls{/number}",
                    "owner": {
                        "following_url": "https://api.github.com/users/web-platform-tests/following{/other_user}",
                        "events_url": "https://api.github.com/users/web-platform-tests/events{/privacy}",
                        "name": "web-platform-tests",
                        "organizations_url": "https://api.github.com/users/web-platform-tests/orgs",
                        "url": "https://api.github.com/users/web-platform-tests",
                        "gists_url": "https://api.github.com/users/web-platform-tests/gists{/gist_id}",
                        "subscriptions_url": "https://api.github.com/users/web-platform-tests/subscriptions",
                        "html_url": "https://github.com/web-platform-tests",
                        "email": "",
                        "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                        "repos_url": "https://api.github.com/users/web-platform-tests/repos",
                        "followers_url": "https://api.github.com/users/web-platform-tests/followers",
                        "received_events_url": "https://api.github.com/users/web-platform-tests/received_events",
                        "gravatar_id": "",
                        "starred_url": "https://api.github.com/users/web-platform-tests/starred{/owner}{/repo}",
                        "site_admin": "false",
                        "login": "web-platform-tests",
                        "type": "Organization",
                        "id": "37226233",
                        "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz"
                    },
                    "full_name": "web-platform-tests/wpt",
                    "issue_comment_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/web-platform-tests/wpt/contents/{+path}",
                    "id": "3618133",
                    "keys_url": "https://api.github.com/repos/web-platform-tests/wpt/keys{/key_id}",
                    "size": "305511",
                    "tags_url": "https://api.github.com/repos/web-platform-tests/wpt/tags",
                    "archived": "false",
                    "has_downloads": "true",
                    "downloads_url": "https://api.github.com/repos/web-platform-tests/wpt/downloads",
                    "assignees_url": "https://api.github.com/repos/web-platform-tests/wpt/assignees{/user}",
                    "statuses_url": "https://api.github.com/repos/web-platform-tests/wpt/statuses/{sha}",
                    "git_refs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/refs{/sha}",
                    "has_projects": "true",
                    "clone_url": "https://github.com/web-platform-tests/wpt.git",
                    "watchers_count": "1845",
                    "git_tags_url": "https://api.github.com/repos/web-platform-tests/wpt/git/tags{/sha}",
                    "labels_url": "https://api.github.com/repos/web-platform-tests/wpt/labels{/name}",
                    "organization": "web-platform-tests",
                    "stargazers_count": "1845",
                    "homepage": "http://irc.w3.org/?channels=testing",
                    "open_issues": "1328",
                    "fork": "false",
                    "milestones_url": "https://api.github.com/repos/web-platform-tests/wpt/milestones{/number}",
                    "commits_url": "https://api.github.com/repos/web-platform-tests/wpt/commits{/sha}",
                    "releases_url": "https://api.github.com/repos/web-platform-tests/wpt/releases{/id}",
                    "issue_events_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/events{/number}",
                    "archive_url": "https://api.github.com/repos/web-platform-tests/wpt/{archive_format}{/ref}",
                    "has_pages": "true",
                    "events_url": "https://api.github.com/repos/web-platform-tests/wpt/events",
                    "contributors_url": "https://api.github.com/repos/web-platform-tests/wpt/contributors",
                    "html_url": "https://github.com/web-platform-tests/wpt",
                    "compare_url": "https://api.github.com/repos/web-platform-tests/wpt/compare/{base}...{head}",
                    "language": "HTML",
                    "watchers": "1845",
                    "private": "false",
                    "forks_count": "1523",
                    "notifications_url": "https://api.github.com/repos/web-platform-tests/wpt/notifications{?since,all,participating}",
                    "has_issues": "true",
                    "ssh_url": "git@github.com:web-platform-tests/wpt.git",
                    "blobs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/blobs{/sha}",
                    "master_branch": "master",
                    "forks": "1523",
                    "hooks_url": "https://api.github.com/repos/web-platform-tests/wpt/hooks",
                    "open_issues_count": "1317",
                    "comments_url": "https://api.github.com/repos/web-platform-tests/wpt/comments{/number}",
                    "name": "wpt",
                    "license": {
                        "spdx_id": "NOASSERTION",
                        "url": "null",
                        "node_id": "MDc6TGljZW5zZTA=",
                        "name": "Other",
                        "key": "other"
                    },
                    "url": "https://github.com/web-platform-tests/wpt",
                    "stargazers": "1845",
                    "created_at": "1330865891",
                    "pushed_at": "1541037488",
                    "branches_url": "https://api.github.com/repos/web-platform-tests/wpt/branches{/branch}",
                    "node_id": "MDEwOlJlcG9zaXRvcnkzNjE4MTMz",
                    "default_branch": "master",
                    "teams_url": "https://api.github.com/repos/web-platform-tests/wpt/teams",
                    "trees_url": "https://api.github.com/repos/web-platform-tests/wpt/git/trees{/sha}",
                    "languages_url": "https://api.github.com/repos/web-platform-tests/wpt/languages",
                    "git_commits_url": "https://api.github.com/repos/web-platform-tests/wpt/git/commits{/sha}",
                    "subscribers_url": "https://api.github.com/repos/web-platform-tests/wpt/subscribers",
                    "stargazers_url": "https://api.github.com/repos/web-platform-tests/wpt/stargazers",
                    "git_url": "git://github.com/web-platform-tests/wpt.git"
                },
                "commits": [
                    {
                        "committer": {
                            "username": "chromium-wpt-export-bot",
                            "email": "blink-w3c-test-autoroller@chromium.org",
                            "name": "Chromium WPT Sync"
                        },
                        "added": [
                            "css/css-flexbox/percentage-heights-005.html"
                        ],
                        "author": {
                            "username": "cbiesinger",
                            "email": "cbiesinger@chromium.org",
                            "name": "Christian Biesinger"
                        },
                        "distinct": "true",
                        "timestamp": "2018-10-31T18:58:04-07:00",
                        "modified": [],
                        "url": "https://github.com/web-platform-tests/wpt/commit/41d50efea43fb365d2a2d13b3fc18b933b7c3a75",
                        "tree_id": "4ed38f691f2be4d19d821fdd316508350d11b42c",
                        "message": "[layoutng] Fix setting of fixed_block_is_definite\n\nWhen a flex item has a definite specified height (e.g. height: 100px),\nthen percentages in children of the flex item should resolve even\nif the flexbox does not have an explicit height, ie. does not match\nthe condition in https://drafts.csswg.org/css-flexbox/#definite-sizes\n\nBug: 885185\n\nChange-Id: Iba226f30e1e02e3a11273fa45fcdf1cef897120c\nReviewed-on: https://chromium-review.googlesource.com/c/1311534\nCommit-Queue: Christian Biesinger <cbiesinger@chromium.org>\nReviewed-by: Emil A Eklund <eae@chromium.org>\nReviewed-by: Morten Stenshorne <mstensho@chromium.org>\nCr-Commit-Position: refs/heads/master@{#604483}",
                        "removed": [],
                        "id": "41d50efea43fb365d2a2d13b3fc18b933b7c3a75"
                    }
                ],
                "pusher": {
                    "email": "blink-w3c-test-autoroller@chromium.org",
                    "name": "chromium-wpt-export-bot"
                },
                "head_commit": {
                    "committer": {
                        "username": "chromium-wpt-export-bot",
                        "email": "blink-w3c-test-autoroller@chromium.org",
                        "name": "Chromium WPT Sync"
                    },
                    "added": [
                        "css/css-flexbox/percentage-heights-005.html"
                    ],
                    "author": {
                        "username": "cbiesinger",
                        "email": "cbiesinger@chromium.org",
                        "name": "Christian Biesinger"
                    },
                    "distinct": "true",
                    "timestamp": "2018-10-31T18:58:04-07:00",
                    "modified": [],
                    "url": "https://github.com/web-platform-tests/wpt/commit/41d50efea43fb365d2a2d13b3fc18b933b7c3a75",
                    "tree_id": "4ed38f691f2be4d19d821fdd316508350d11b42c",
                    "message": "[layoutng] Fix setting of fixed_block_is_definite\n\nWhen a flex item has a definite specified height (e.g. height: 100px),\nthen percentages in children of the flex item should resolve even\nif the flexbox does not have an explicit height, ie. does not match\nthe condition in https://drafts.csswg.org/css-flexbox/#definite-sizes\n\nBug: 885185\n\nChange-Id: Iba226f30e1e02e3a11273fa45fcdf1cef897120c\nReviewed-on: https://chromium-review.googlesource.com/c/1311534\nCommit-Queue: Christian Biesinger <cbiesinger@chromium.org>\nReviewed-by: Emil A Eklund <eae@chromium.org>\nReviewed-by: Morten Stenshorne <mstensho@chromium.org>\nCr-Commit-Position: refs/heads/master@{#604483}",
                    "removed": [],
                    "id": "41d50efea43fb365d2a2d13b3fc18b933b7c3a75"
                },
                "organization": {
                    "issues_url": "https://api.github.com/orgs/web-platform-tests/issues",
                    "members_url": "https://api.github.com/orgs/web-platform-tests/members{/member}",
                    "description": "",
                    "public_members_url": "https://api.github.com/orgs/web-platform-tests/public_members{/member}",
                    "url": "https://api.github.com/orgs/web-platform-tests",
                    "events_url": "https://api.github.com/orgs/web-platform-tests/events",
                    "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                    "repos_url": "https://api.github.com/orgs/web-platform-tests/repos",
                    "login": "web-platform-tests",
                    "id": "37226233",
                    "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz",
                    "hooks_url": "https://api.github.com/orgs/web-platform-tests/hooks"
                },
            },
            "event": "push",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd"
        }

        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        self.verify_repo(message, result)
        self.verify_org(message, result)
        assert result['source'] == 'push'
        assert result['details']['created'] == message['body']['created']
        assert result['details']['deleted'] == message['body']['deleted']
        assert result['details']['forced'] == message['body']['forced']
        assert result['details']['commits'] == message['body']['commits']
        assert result['details']['ref'] == message['body']['ref']
        assert result['details']['email'] == message['body']['pusher']['email']
        assert result['details']['commit_author'] == message['body']['head_commit']['author']['email']
        assert result['details']['committer'] == message['body']['head_commit']['committer']['email']
        assert result['details']['commit_id'] == message['body']['head_commit']['id']
        assert result['details']['commit_msg'] == message['body']['head_commit']['message']
        assert result['details']['commit_ts'] == message['body']['head_commit']['timestamp']
        assert result['details']['commit_url'] == message['body']['head_commit']['url']
        assert result['details']['repo_owner_name'] == message['body']['repository']['owner']['name']
        assert result['summary'] == 'github: push: on repo: wpt in org: web-platform-tests triggered by user: chromium-wpt-export-bot'

    def test_pullrequest(self):
        message = {
            "body": {
                "action": "opened",
                "number": "2",
                "pull_request": {
                    "url": "https://api.github.com/repos/Codertocat/Hello-World/pulls/2",
                    "id": "279147437",
                    "node_id": "MDExOlB1bGxSZXF1ZXN0Mjc5MTQ3NDM3",
                    "html_url": "https://github.com/Codertocat/Hello-World/pull/2",
                    "diff_url": "https://github.com/Codertocat/Hello-World/pull/2.diff",
                    "patch_url": "https://github.com/Codertocat/Hello-World/pull/2.patch",
                    "issue_url": "https://api.github.com/repos/Codertocat/Hello-World/issues/2",
                    "number": "2",
                    "state": "open",
                    "locked": "false",
                    "title": "Update the README with new information.",
                    "user": {
                        "login": "Codertocat",
                        "id": "21031067",
                        "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                        "avatar_url": "https://avatars1.githubusercontent.com/u/21031067?v=4",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/Codertocat",
                        "html_url": "https://github.com/Codertocat",
                        "followers_url": "https://api.github.com/users/Codertocat/followers",
                        "following_url": "https://api.github.com/users/Codertocat/following{/other_user}",
                        "gists_url": "https://api.github.com/users/Codertocat/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/Codertocat/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/Codertocat/subscriptions",
                        "organizations_url": "https://api.github.com/users/Codertocat/orgs",
                        "repos_url": "https://api.github.com/users/Codertocat/repos",
                        "events_url": "https://api.github.com/users/Codertocat/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/Codertocat/received_events",
                        "type": "User",
                        "site_admin": "false"
                    },
                    "body": "This is a pretty simple change that we need to pull into master.",
                    "created_at": "2019-05-15T15:20:33Z",
                    "updated_at": "2019-05-15T15:20:33Z",
                    "closed_at": "null",
                    "merged_at": "null",
                    "merge_commit_sha": "null",
                    "assignee": "null",
                    "assignees": [],
                    "requested_reviewers": [],
                    "requested_teams": [],
                    "labels": [],
                    "milestone": "null",
                    "commits_url": "https://api.github.com/repos/Codertocat/Hello-World/pulls/2/commits",
                    "review_comments_url": "https://api.github.com/repos/Codertocat/Hello-World/pulls/2/comments",
                    "review_comment_url": "https://api.github.com/repos/Codertocat/Hello-World/pulls/comments{/number}",
                    "comments_url": "https://api.github.com/repos/Codertocat/Hello-World/issues/2/comments",
                    "statuses_url": "https://api.github.com/repos/Codertocat/Hello-World/statuses/ec26c3e57ca3a959ca5aad62de7213c562f8c821",
                    "head": {
                        "label": "Codertocat:changes",
                        "ref": "changes",
                        "sha": "ec26c3e57ca3a959ca5aad62de7213c562f8c821",
                        "user": {
                            "login": "Codertocat",
                            "id": "21031067",
                            "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                            "avatar_url": "https://avatars1.githubusercontent.com/u/21031067?v=4",
                            "gravatar_id": "",
                            "url": "https://api.github.com/users/Codertocat",
                            "html_url": "https://github.com/Codertocat",
                            "followers_url": "https://api.github.com/users/Codertocat/followers",
                            "following_url": "https://api.github.com/users/Codertocat/following{/other_user}",
                            "gists_url": "https://api.github.com/users/Codertocat/gists{/gist_id}",
                            "starred_url": "https://api.github.com/users/Codertocat/starred{/owner}{/repo}",
                            "subscriptions_url": "https://api.github.com/users/Codertocat/subscriptions",
                            "organizations_url": "https://api.github.com/users/Codertocat/orgs",
                            "repos_url": "https://api.github.com/users/Codertocat/repos",
                            "events_url": "https://api.github.com/users/Codertocat/events{/privacy}",
                            "received_events_url": "https://api.github.com/users/Codertocat/received_events",
                            "type": "User",
                            "site_admin": "false"
                        },
                        "repo": {
                            "id": "186853002",
                            "node_id": "MDEwOlJlcG9zaXRvcnkxODY4NTMwMDI=",
                            "name": "Hello-World",
                            "full_name": "Codertocat/Hello-World",
                            "private": "false",
                            "owner": {
                                "login": "Codertocat",
                                "id": "21031067",
                                "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                                "avatar_url": "https://avatars1.githubusercontent.com/u/21031067?v=4",
                                "gravatar_id": "",
                                "url": "https://api.github.com/users/Codertocat",
                                "html_url": "https://github.com/Codertocat",
                                "followers_url": "https://api.github.com/users/Codertocat/followers",
                                "following_url": "https://api.github.com/users/Codertocat/following{/other_user}",
                                "gists_url": "https://api.github.com/users/Codertocat/gists{/gist_id}",
                                "starred_url": "https://api.github.com/users/Codertocat/starred{/owner}{/repo}",
                                "subscriptions_url": "https://api.github.com/users/Codertocat/subscriptions",
                                "organizations_url": "https://api.github.com/users/Codertocat/orgs",
                                "repos_url": "https://api.github.com/users/Codertocat/repos",
                                "events_url": "https://api.github.com/users/Codertocat/events{/privacy}",
                                "received_events_url": "https://api.github.com/users/Codertocat/received_events",
                                "type": "User",
                                "site_admin": "false"
                            },
                            "html_url": "https://github.com/Codertocat/Hello-World",
                            "description": "null",
                            "fork": "false",
                            "url": "https://api.github.com/repos/Codertocat/Hello-World",
                            "forks_url": "https://api.github.com/repos/Codertocat/Hello-World/forks",
                            "keys_url": "https://api.github.com/repos/Codertocat/Hello-World/keys{/key_id}",
                            "collaborators_url": "https://api.github.com/repos/Codertocat/Hello-World/collaborators{/collaborator}",
                            "teams_url": "https://api.github.com/repos/Codertocat/Hello-World/teams",
                            "hooks_url": "https://api.github.com/repos/Codertocat/Hello-World/hooks",
                            "issue_events_url": "https://api.github.com/repos/Codertocat/Hello-World/issues/events{/number}",
                            "events_url": "https://api.github.com/repos/Codertocat/Hello-World/events",
                            "assignees_url": "https://api.github.com/repos/Codertocat/Hello-World/assignees{/user}",
                            "branches_url": "https://api.github.com/repos/Codertocat/Hello-World/branches{/branch}",
                            "tags_url": "https://api.github.com/repos/Codertocat/Hello-World/tags",
                            "blobs_url": "https://api.github.com/repos/Codertocat/Hello-World/git/blobs{/sha}",
                            "git_tags_url": "https://api.github.com/repos/Codertocat/Hello-World/git/tags{/sha}",
                            "git_refs_url": "https://api.github.com/repos/Codertocat/Hello-World/git/refs{/sha}",
                            "trees_url": "https://api.github.com/repos/Codertocat/Hello-World/git/trees{/sha}",
                            "statuses_url": "https://api.github.com/repos/Codertocat/Hello-World/statuses/{sha}",
                            "languages_url": "https://api.github.com/repos/Codertocat/Hello-World/languages",
                            "stargazers_url": "https://api.github.com/repos/Codertocat/Hello-World/stargazers",
                            "contributors_url": "https://api.github.com/repos/Codertocat/Hello-World/contributors",
                            "subscribers_url": "https://api.github.com/repos/Codertocat/Hello-World/subscribers",
                            "subscription_url": "https://api.github.com/repos/Codertocat/Hello-World/subscription",
                            "commits_url": "https://api.github.com/repos/Codertocat/Hello-World/commits{/sha}",
                            "git_commits_url": "https://api.github.com/repos/Codertocat/Hello-World/git/commits{/sha}",
                            "comments_url": "https://api.github.com/repos/Codertocat/Hello-World/comments{/number}",
                            "issue_comment_url": "https://api.github.com/repos/Codertocat/Hello-World/issues/comments{/number}",
                            "contents_url": "https://api.github.com/repos/Codertocat/Hello-World/contents/{+path}",
                            "compare_url": "https://api.github.com/repos/Codertocat/Hello-World/compare/{base}...{head}",
                            "merges_url": "https://api.github.com/repos/Codertocat/Hello-World/merges",
                            "archive_url": "https://api.github.com/repos/Codertocat/Hello-World/{archive_format}{/ref}",
                            "downloads_url": "https://api.github.com/repos/Codertocat/Hello-World/downloads",
                            "issues_url": "https://api.github.com/repos/Codertocat/Hello-World/issues{/number}",
                            "pulls_url": "https://api.github.com/repos/Codertocat/Hello-World/pulls{/number}",
                            "milestones_url": "https://api.github.com/repos/Codertocat/Hello-World/milestones{/number}",
                            "notifications_url": "https://api.github.com/repos/Codertocat/Hello-World/notifications{?since,all,participating}",
                            "labels_url": "https://api.github.com/repos/Codertocat/Hello-World/labels{/name}",
                            "releases_url": "https://api.github.com/repos/Codertocat/Hello-World/releases{/id}",
                            "deployments_url": "https://api.github.com/repos/Codertocat/Hello-World/deployments",
                            "created_at": "2019-05-15T15:19:25Z",
                            "updated_at": "2019-05-15T15:19:27Z",
                            "pushed_at": "2019-05-15T15:20:32Z",
                            "git_url": "git://github.com/Codertocat/Hello-World.git",
                            "ssh_url": "git@github.com:Codertocat/Hello-World.git",
                            "clone_url": "https://github.com/Codertocat/Hello-World.git",
                            "svn_url": "https://github.com/Codertocat/Hello-World",
                            "homepage": "null",
                            "size": "0",
                            "stargazers_count": "0",
                            "watchers_count": "0",
                            "language": "null",
                            "has_issues": "true",
                            "has_projects": "true",
                            "has_downloads": "true",
                            "has_wiki": "true",
                            "has_pages": "true",
                            "forks_count": "0",
                            "mirror_url": "null",
                            "archived": "false",
                            "disabled": "false",
                            "open_issues_count": "2",
                            "license": "null",
                            "forks": "0",
                            "open_issues": "2",
                            "watchers": "0",
                            "default_branch": "master"
                        }
                    },
                    "base": {
                        "label": "Codertocat:master",
                        "ref": "master",
                        "sha": "f95f852bd8fca8fcc58a9a2d6c842781e32a215e",
                        "user": {
                            "login": "Codertocat",
                            "id": "21031067",
                            "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                            "avatar_url": "https://avatars1.githubusercontent.com/u/21031067?v=4",
                            "gravatar_id": "",
                            "url": "https://api.github.com/users/Codertocat",
                            "html_url": "https://github.com/Codertocat",
                            "followers_url": "https://api.github.com/users/Codertocat/followers",
                            "following_url": "https://api.github.com/users/Codertocat/following{/other_user}",
                            "gists_url": "https://api.github.com/users/Codertocat/gists{/gist_id}",
                            "starred_url": "https://api.github.com/users/Codertocat/starred{/owner}{/repo}",
                            "subscriptions_url": "https://api.github.com/users/Codertocat/subscriptions",
                            "organizations_url": "https://api.github.com/users/Codertocat/orgs",
                            "repos_url": "https://api.github.com/users/Codertocat/repos",
                            "events_url": "https://api.github.com/users/Codertocat/events{/privacy}",
                            "received_events_url": "https://api.github.com/users/Codertocat/received_events",
                            "type": "User",
                            "site_admin": "false"
                        },
                        "repo": {
                            "id": "186853002",
                            "node_id": "MDEwOlJlcG9zaXRvcnkxODY4NTMwMDI=",
                            "name": "Hello-World",
                            "full_name": "Codertocat/Hello-World",
                            "private": "false",
                            "owner": {
                                "login": "Codertocat",
                                "id": "21031067",
                                "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                                "avatar_url": "https://avatars1.githubusercontent.com/u/21031067?v=4",
                                "gravatar_id": "",
                                "url": "https://api.github.com/users/Codertocat",
                                "html_url": "https://github.com/Codertocat",
                                "followers_url": "https://api.github.com/users/Codertocat/followers",
                                "following_url": "https://api.github.com/users/Codertocat/following{/other_user}",
                                "gists_url": "https://api.github.com/users/Codertocat/gists{/gist_id}",
                                "starred_url": "https://api.github.com/users/Codertocat/starred{/owner}{/repo}",
                                "subscriptions_url": "https://api.github.com/users/Codertocat/subscriptions",
                                "organizations_url": "https://api.github.com/users/Codertocat/orgs",
                                "repos_url": "https://api.github.com/users/Codertocat/repos",
                                "events_url": "https://api.github.com/users/Codertocat/events{/privacy}",
                                "received_events_url": "https://api.github.com/users/Codertocat/received_events",
                                "type": "User",
                                "site_admin": "false"
                            },
                            "html_url": "https://github.com/Codertocat/Hello-World",
                            "description": "null",
                            "fork": "false",
                            "url": "https://api.github.com/repos/Codertocat/Hello-World",
                            "forks_url": "https://api.github.com/repos/Codertocat/Hello-World/forks",
                            "keys_url": "https://api.github.com/repos/Codertocat/Hello-World/keys{/key_id}",
                            "collaborators_url": "https://api.github.com/repos/Codertocat/Hello-World/collaborators{/collaborator}",
                            "teams_url": "https://api.github.com/repos/Codertocat/Hello-World/teams",
                            "hooks_url": "https://api.github.com/repos/Codertocat/Hello-World/hooks",
                            "issue_events_url": "https://api.github.com/repos/Codertocat/Hello-World/issues/events{/number}",
                            "events_url": "https://api.github.com/repos/Codertocat/Hello-World/events",
                            "assignees_url": "https://api.github.com/repos/Codertocat/Hello-World/assignees{/user}",
                            "branches_url": "https://api.github.com/repos/Codertocat/Hello-World/branches{/branch}",
                            "tags_url": "https://api.github.com/repos/Codertocat/Hello-World/tags",
                            "blobs_url": "https://api.github.com/repos/Codertocat/Hello-World/git/blobs{/sha}",
                            "git_tags_url": "https://api.github.com/repos/Codertocat/Hello-World/git/tags{/sha}",
                            "git_refs_url": "https://api.github.com/repos/Codertocat/Hello-World/git/refs{/sha}",
                            "trees_url": "https://api.github.com/repos/Codertocat/Hello-World/git/trees{/sha}",
                            "statuses_url": "https://api.github.com/repos/Codertocat/Hello-World/statuses/{sha}",
                            "languages_url": "https://api.github.com/repos/Codertocat/Hello-World/languages",
                            "stargazers_url": "https://api.github.com/repos/Codertocat/Hello-World/stargazers",
                            "contributors_url": "https://api.github.com/repos/Codertocat/Hello-World/contributors",
                            "subscribers_url": "https://api.github.com/repos/Codertocat/Hello-World/subscribers",
                            "subscription_url": "https://api.github.com/repos/Codertocat/Hello-World/subscription",
                            "commits_url": "https://api.github.com/repos/Codertocat/Hello-World/commits{/sha}",
                            "git_commits_url": "https://api.github.com/repos/Codertocat/Hello-World/git/commits{/sha}",
                            "comments_url": "https://api.github.com/repos/Codertocat/Hello-World/comments{/number}",
                            "issue_comment_url": "https://api.github.com/repos/Codertocat/Hello-World/issues/comments{/number}",
                            "contents_url": "https://api.github.com/repos/Codertocat/Hello-World/contents/{+path}",
                            "compare_url": "https://api.github.com/repos/Codertocat/Hello-World/compare/{base}...{head}",
                            "merges_url": "https://api.github.com/repos/Codertocat/Hello-World/merges",
                            "archive_url": "https://api.github.com/repos/Codertocat/Hello-World/{archive_format}{/ref}",
                            "downloads_url": "https://api.github.com/repos/Codertocat/Hello-World/downloads",
                            "issues_url": "https://api.github.com/repos/Codertocat/Hello-World/issues{/number}",
                            "pulls_url": "https://api.github.com/repos/Codertocat/Hello-World/pulls{/number}",
                            "milestones_url": "https://api.github.com/repos/Codertocat/Hello-World/milestones{/number}",
                            "notifications_url": "https://api.github.com/repos/Codertocat/Hello-World/notifications{?since,all,participating}",
                            "labels_url": "https://api.github.com/repos/Codertocat/Hello-World/labels{/name}",
                            "releases_url": "https://api.github.com/repos/Codertocat/Hello-World/releases{/id}",
                            "deployments_url": "https://api.github.com/repos/Codertocat/Hello-World/deployments",
                            "created_at": "2019-05-15T15:19:25Z",
                            "updated_at": "2019-05-15T15:19:27Z",
                            "pushed_at": "2019-05-15T15:20:32Z",
                            "git_url": "git://github.com/Codertocat/Hello-World.git",
                            "ssh_url": "git@github.com:Codertocat/Hello-World.git",
                            "clone_url": "https://github.com/Codertocat/Hello-World.git",
                            "svn_url": "https://github.com/Codertocat/Hello-World",
                            "homepage": "null",
                            "size": "0",
                            "stargazers_count": "0",
                            "watchers_count": "0",
                            "language": "null",
                            "has_issues": "true",
                            "has_projects": "true",
                            "has_downloads": "true",
                            "has_wiki": "true",
                            "has_pages": "true",
                            "forks_count": "0",
                            "mirror_url": "null",
                            "archived": "false",
                            "disabled": "false",
                            "open_issues_count": "2",
                            "license": "null",
                            "forks": "0",
                            "open_issues": "2",
                            "watchers": "0",
                            "default_branch": "master"
                        }
                    },
                    "_links": {
                        "self": {
                            "href": "https://api.github.com/repos/Codertocat/Hello-World/pulls/2"
                        },
                        "html": {
                            "href": "https://github.com/Codertocat/Hello-World/pull/2"
                        },
                        "issue": {
                            "href": "https://api.github.com/repos/Codertocat/Hello-World/issues/2"
                        },
                        "comments": {
                            "href": "https://api.github.com/repos/Codertocat/Hello-World/issues/2/comments"
                        },
                        "review_comments": {
                            "href": "https://api.github.com/repos/Codertocat/Hello-World/pulls/2/comments"
                        },
                        "review_comment": {
                            "href": "https://api.github.com/repos/Codertocat/Hello-World/pulls/comments{/number}"
                        },
                        "commits": {
                            "href": "https://api.github.com/repos/Codertocat/Hello-World/pulls/2/commits"
                        },
                        "statuses": {
                            "href": "https://api.github.com/repos/Codertocat/Hello-World/statuses/ec26c3e57ca3a959ca5aad62de7213c562f8c821"
                        }
                    },
                    "author_association": "OWNER",
                    "draft": "false",
                    "merged": "false",
                    "mergeable": "null",
                    "rebaseable": "null",
                    "mergeable_state": "unknown",
                    "merged_by": "null",
                    "comments": "0",
                    "review_comments": "0",
                    "maintainer_can_modify": "false",
                    "commits": "1",
                    "additions": "1",
                    "deletions": "1",
                    "changed_files": "1"
                },
                "repository": {
                    "id": "186853002",
                    "node_id": "MDEwOlJlcG9zaXRvcnkxODY4NTMwMDI=",
                    "name": "Hello-World",
                    "full_name": "Codertocat/Hello-World",
                    "private": "false",
                    "owner": {
                        "login": "Codertocat",
                        "id": "21031067",
                        "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                        "avatar_url": "https://avatars1.githubusercontent.com/u/21031067?v=4",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/Codertocat",
                        "html_url": "https://github.com/Codertocat",
                        "followers_url": "https://api.github.com/users/Codertocat/followers",
                        "following_url": "https://api.github.com/users/Codertocat/following{/other_user}",
                        "gists_url": "https://api.github.com/users/Codertocat/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/Codertocat/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/Codertocat/subscriptions",
                        "organizations_url": "https://api.github.com/users/Codertocat/orgs",
                        "repos_url": "https://api.github.com/users/Codertocat/repos",
                        "events_url": "https://api.github.com/users/Codertocat/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/Codertocat/received_events",
                        "type": "User",
                        "site_admin": "false"
                    },
                    "html_url": "https://github.com/Codertocat/Hello-World",
                    "description": "null",
                    "fork": "false",
                    "url": "https://api.github.com/repos/Codertocat/Hello-World",
                    "forks_url": "https://api.github.com/repos/Codertocat/Hello-World/forks",
                    "keys_url": "https://api.github.com/repos/Codertocat/Hello-World/keys{/key_id}",
                    "collaborators_url": "https://api.github.com/repos/Codertocat/Hello-World/collaborators{/collaborator}",
                    "teams_url": "https://api.github.com/repos/Codertocat/Hello-World/teams",
                    "hooks_url": "https://api.github.com/repos/Codertocat/Hello-World/hooks",
                    "issue_events_url": "https://api.github.com/repos/Codertocat/Hello-World/issues/events{/number}",
                    "events_url": "https://api.github.com/repos/Codertocat/Hello-World/events",
                    "assignees_url": "https://api.github.com/repos/Codertocat/Hello-World/assignees{/user}",
                    "branches_url": "https://api.github.com/repos/Codertocat/Hello-World/branches{/branch}",
                    "tags_url": "https://api.github.com/repos/Codertocat/Hello-World/tags",
                    "blobs_url": "https://api.github.com/repos/Codertocat/Hello-World/git/blobs{/sha}",
                    "git_tags_url": "https://api.github.com/repos/Codertocat/Hello-World/git/tags{/sha}",
                    "git_refs_url": "https://api.github.com/repos/Codertocat/Hello-World/git/refs{/sha}",
                    "trees_url": "https://api.github.com/repos/Codertocat/Hello-World/git/trees{/sha}",
                    "statuses_url": "https://api.github.com/repos/Codertocat/Hello-World/statuses/{sha}",
                    "languages_url": "https://api.github.com/repos/Codertocat/Hello-World/languages",
                    "stargazers_url": "https://api.github.com/repos/Codertocat/Hello-World/stargazers",
                    "contributors_url": "https://api.github.com/repos/Codertocat/Hello-World/contributors",
                    "subscribers_url": "https://api.github.com/repos/Codertocat/Hello-World/subscribers",
                    "subscription_url": "https://api.github.com/repos/Codertocat/Hello-World/subscription",
                    "commits_url": "https://api.github.com/repos/Codertocat/Hello-World/commits{/sha}",
                    "git_commits_url": "https://api.github.com/repos/Codertocat/Hello-World/git/commits{/sha}",
                    "comments_url": "https://api.github.com/repos/Codertocat/Hello-World/comments{/number}",
                    "issue_comment_url": "https://api.github.com/repos/Codertocat/Hello-World/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/Codertocat/Hello-World/contents/{+path}",
                    "compare_url": "https://api.github.com/repos/Codertocat/Hello-World/compare/{base}...{head}",
                    "merges_url": "https://api.github.com/repos/Codertocat/Hello-World/merges",
                    "archive_url": "https://api.github.com/repos/Codertocat/Hello-World/{archive_format}{/ref}",
                    "downloads_url": "https://api.github.com/repos/Codertocat/Hello-World/downloads",
                    "issues_url": "https://api.github.com/repos/Codertocat/Hello-World/issues{/number}",
                    "pulls_url": "https://api.github.com/repos/Codertocat/Hello-World/pulls{/number}",
                    "milestones_url": "https://api.github.com/repos/Codertocat/Hello-World/milestones{/number}",
                    "notifications_url": "https://api.github.com/repos/Codertocat/Hello-World/notifications{?since,all,participating}",
                    "labels_url": "https://api.github.com/repos/Codertocat/Hello-World/labels{/name}",
                    "releases_url": "https://api.github.com/repos/Codertocat/Hello-World/releases{/id}",
                    "deployments_url": "https://api.github.com/repos/Codertocat/Hello-World/deployments",
                    "created_at": "2019-05-15T15:19:25Z",
                    "updated_at": "2019-05-15T15:19:27Z",
                    "pushed_at": "2019-05-15T15:20:32Z",
                    "git_url": "git://github.com/Codertocat/Hello-World.git",
                    "ssh_url": "git@github.com:Codertocat/Hello-World.git",
                    "clone_url": "https://github.com/Codertocat/Hello-World.git",
                    "svn_url": "https://github.com/Codertocat/Hello-World",
                    "homepage": "null",
                    "size": "0",
                    "stargazers_count": "0",
                    "watchers_count": "0",
                    "language": "null",
                    "has_issues": "true",
                    "has_projects": "true",
                    "has_downloads": "true",
                    "has_wiki": "true",
                    "has_pages": "true",
                    "forks_count": "0",
                    "mirror_url": "null",
                    "archived": "false",
                    "disabled": "false",
                    "open_issues_count": "2",
                    "license": "null",
                    "forks": "0",
                    "open_issues": "2",
                    "watchers": "0",
                    "default_branch": "master"
                },
                "sender": {
                    "login": "Codertocat",
                    "id": "21031067",
                    "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/21031067?v=4",
                    "gravatar_id": "",
                    "url": "https://api.github.com/users/Codertocat",
                    "html_url": "https://github.com/Codertocat",
                    "followers_url": "https://api.github.com/users/Codertocat/followers",
                    "following_url": "https://api.github.com/users/Codertocat/following{/other_user}",
                    "gists_url": "https://api.github.com/users/Codertocat/gists{/gist_id}",
                    "starred_url": "https://api.github.com/users/Codertocat/starred{/owner}{/repo}",
                    "subscriptions_url": "https://api.github.com/users/Codertocat/subscriptions",
                    "organizations_url": "https://api.github.com/users/Codertocat/orgs",
                    "repos_url": "https://api.github.com/users/Codertocat/repos",
                    "events_url": "https://api.github.com/users/Codertocat/events{/privacy}",
                    "received_events_url": "https://api.github.com/users/Codertocat/received_events",
                    "type": "User",
                    "site_admin": "false"
                },
            },
            "event": "pull_request",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd"
        }

        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        self.verify_repo(message, result)
        assert result['source'] == 'pull_request'
        assert result['details']['action'] == message['body']['action']
        assert result['summary'] == 'github: pull_request: opened on repo: Hello-World triggered by user: Codertocat'

    def test_delete(self):
        message = {
            "body": {
                "ref": "gecko/1499958",
                "ref_type": "branch",
                "sender": {
                    "following_url": "https://api.github.com/users/chromium-wpt-export-bot/following{/other_user}",
                    "events_url": "https://api.github.com/users/chromium-wpt-export-bot/events{/privacy}",
                    "organizations_url": "https://api.github.com/users/chromium-wpt-export-bot/orgs",
                    "url": "https://api.github.com/users/chromium-wpt-export-bot",
                    "gists_url": "https://api.github.com/users/chromium-wpt-export-bot/gists{/gist_id}",
                    "html_url": "https://github.com/chromium-wpt-export-bot",
                    "subscriptions_url": "https://api.github.com/users/chromium-wpt-export-bot/subscriptions",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/25752892?v=4",
                    "repos_url": "https://api.github.com/users/chromium-wpt-export-bot/repos",
                    "followers_url": "https://api.github.com/users/chromium-wpt-export-bot/followers",
                    "received_events_url": "https://api.github.com/users/chromium-wpt-export-bot/received_events",
                    "gravatar_id": "",
                    "starred_url": "https://api.github.com/users/chromium-wpt-export-bot/starred{/owner}{/repo}",
                    "site_admin": "false",
                    "login": "chromium-wpt-export-bot",
                    "type": "User",
                    "id": "25752892",
                    "node_id": "MDQ6VXNlcjI1NzUyODky"
                },
                "repository": {
                    "issues_url": "https://api.github.com/repos/web-platform-tests/wpt/issues{/number}",
                    "deployments_url": "https://api.github.com/repos/web-platform-tests/wpt/deployments",
                    "has_wiki": "true",
                    "forks_url": "https://api.github.com/repos/web-platform-tests/wpt/forks",
                    "mirror_url": "null",
                    "subscription_url": "https://api.github.com/repos/web-platform-tests/wpt/subscription",
                    "merges_url": "https://api.github.com/repos/web-platform-tests/wpt/merges",
                    "collaborators_url": "https://api.github.com/repos/web-platform-tests/wpt/collaborators{/collaborator}",
                    "updated_at": "2018-11-01T00:51:49Z",
                    "svn_url": "https://github.com/web-platform-tests/wpt",
                    "pulls_url": "https://api.github.com/repos/web-platform-tests/wpt/pulls{/number}",
                    "owner": {
                        "following_url": "https://api.github.com/users/web-platform-tests/following{/other_user}",
                        "events_url": "https://api.github.com/users/web-platform-tests/events{/privacy}",
                        "name": "web-platform-tests",
                        "organizations_url": "https://api.github.com/users/web-platform-tests/orgs",
                        "url": "https://api.github.com/users/web-platform-tests",
                        "gists_url": "https://api.github.com/users/web-platform-tests/gists{/gist_id}",
                        "subscriptions_url": "https://api.github.com/users/web-platform-tests/subscriptions",
                        "html_url": "https://github.com/web-platform-tests",
                        "email": "",
                        "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                        "repos_url": "https://api.github.com/users/web-platform-tests/repos",
                        "followers_url": "https://api.github.com/users/web-platform-tests/followers",
                        "received_events_url": "https://api.github.com/users/web-platform-tests/received_events",
                        "gravatar_id": "",
                        "starred_url": "https://api.github.com/users/web-platform-tests/starred{/owner}{/repo}",
                        "site_admin": "false",
                        "login": "web-platform-tests",
                        "type": "Organization",
                        "id": "37226233",
                        "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz"
                    },
                    "full_name": "web-platform-tests/wpt",
                    "issue_comment_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/web-platform-tests/wpt/contents/{+path}",
                    "id": "3618133",
                    "keys_url": "https://api.github.com/repos/web-platform-tests/wpt/keys{/key_id}",
                    "size": "305511",
                    "tags_url": "https://api.github.com/repos/web-platform-tests/wpt/tags",
                    "archived": "false",
                    "has_downloads": "true",
                    "downloads_url": "https://api.github.com/repos/web-platform-tests/wpt/downloads",
                    "assignees_url": "https://api.github.com/repos/web-platform-tests/wpt/assignees{/user}",
                    "statuses_url": "https://api.github.com/repos/web-platform-tests/wpt/statuses/{sha}",
                    "git_refs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/refs{/sha}",
                    "has_projects": "true",
                    "clone_url": "https://github.com/web-platform-tests/wpt.git",
                    "watchers_count": "1845",
                    "git_tags_url": "https://api.github.com/repos/web-platform-tests/wpt/git/tags{/sha}",
                    "labels_url": "https://api.github.com/repos/web-platform-tests/wpt/labels{/name}",
                    "organization": "web-platform-tests",
                    "stargazers_count": "1845",
                    "homepage": "http://irc.w3.org/?channels=testing",
                    "open_issues": "1328",
                    "fork": "false",
                    "milestones_url": "https://api.github.com/repos/web-platform-tests/wpt/milestones{/number}",
                    "commits_url": "https://api.github.com/repos/web-platform-tests/wpt/commits{/sha}",
                    "releases_url": "https://api.github.com/repos/web-platform-tests/wpt/releases{/id}",
                    "issue_events_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/events{/number}",
                    "archive_url": "https://api.github.com/repos/web-platform-tests/wpt/{archive_format}{/ref}",
                    "has_pages": "true",
                    "events_url": "https://api.github.com/repos/web-platform-tests/wpt/events",
                    "contributors_url": "https://api.github.com/repos/web-platform-tests/wpt/contributors",
                    "html_url": "https://github.com/web-platform-tests/wpt",
                    "compare_url": "https://api.github.com/repos/web-platform-tests/wpt/compare/{base}...{head}",
                    "language": "HTML",
                    "watchers": "1845",
                    "private": "false",
                    "forks_count": "1523",
                    "notifications_url": "https://api.github.com/repos/web-platform-tests/wpt/notifications{?since,all,participating}",
                    "has_issues": "true",
                    "ssh_url": "git@github.com:web-platform-tests/wpt.git",
                    "blobs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/blobs{/sha}",
                    "master_branch": "master",
                    "forks": "1523",
                    "hooks_url": "https://api.github.com/repos/web-platform-tests/wpt/hooks",
                    "open_issues_count": "1317",
                    "comments_url": "https://api.github.com/repos/web-platform-tests/wpt/comments{/number}",
                    "name": "wpt",
                    "license": {
                        "spdx_id": "NOASSERTION",
                        "url": "null",
                        "node_id": "MDc6TGljZW5zZTA=",
                        "name": "Other",
                        "key": "other"
                    },
                    "url": "https://github.com/web-platform-tests/wpt",
                    "stargazers": "1845",
                    "created_at": "1330865891",
                    "pushed_at": "1541037488",
                    "branches_url": "https://api.github.com/repos/web-platform-tests/wpt/branches{/branch}",
                    "node_id": "MDEwOlJlcG9zaXRvcnkzNjE4MTMz",
                    "default_branch": "master",
                    "teams_url": "https://api.github.com/repos/web-platform-tests/wpt/teams",
                    "trees_url": "https://api.github.com/repos/web-platform-tests/wpt/git/trees{/sha}",
                    "languages_url": "https://api.github.com/repos/web-platform-tests/wpt/languages",
                    "git_commits_url": "https://api.github.com/repos/web-platform-tests/wpt/git/commits{/sha}",
                    "subscribers_url": "https://api.github.com/repos/web-platform-tests/wpt/subscribers",
                    "stargazers_url": "https://api.github.com/repos/web-platform-tests/wpt/stargazers",
                    "git_url": "git://github.com/web-platform-tests/wpt.git"
                },
                "organization": {
                    "issues_url": "https://api.github.com/orgs/web-platform-tests/issues",
                    "members_url": "https://api.github.com/orgs/web-platform-tests/members{/member}",
                    "description": "",
                    "public_members_url": "https://api.github.com/orgs/web-platform-tests/public_members{/member}",
                    "url": "https://api.github.com/orgs/web-platform-tests",
                    "events_url": "https://api.github.com/orgs/web-platform-tests/events",
                    "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                    "repos_url": "https://api.github.com/orgs/web-platform-tests/repos",
                    "login": "web-platform-tests",
                    "id": "37226233",
                    "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz",
                    "hooks_url": "https://api.github.com/orgs/web-platform-tests/hooks"
                },
            },
            "event": "delete",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd"
        }

        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        self.verify_repo(message, result)
        self.verify_org(message, result)
        assert result['source'] == 'delete'
        assert result['details']['ref'] == message['body']['ref']
        assert result['details']['ref_type'] == message['body']['ref_type']
        assert result['summary'] == 'github: delete: branch on repo: wpt in org: web-platform-tests triggered by user: chromium-wpt-export-bot'

    def test_create(self):
        message = {
            "body": {
                "ref": "gecko/1499958",
                "ref_type": "branch",
                "sender": {
                    "following_url": "https://api.github.com/users/chromium-wpt-export-bot/following{/other_user}",
                    "events_url": "https://api.github.com/users/chromium-wpt-export-bot/events{/privacy}",
                    "organizations_url": "https://api.github.com/users/chromium-wpt-export-bot/orgs",
                    "url": "https://api.github.com/users/chromium-wpt-export-bot",
                    "gists_url": "https://api.github.com/users/chromium-wpt-export-bot/gists{/gist_id}",
                    "html_url": "https://github.com/chromium-wpt-export-bot",
                    "subscriptions_url": "https://api.github.com/users/chromium-wpt-export-bot/subscriptions",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/25752892?v=4",
                    "repos_url": "https://api.github.com/users/chromium-wpt-export-bot/repos",
                    "followers_url": "https://api.github.com/users/chromium-wpt-export-bot/followers",
                    "received_events_url": "https://api.github.com/users/chromium-wpt-export-bot/received_events",
                    "gravatar_id": "",
                    "starred_url": "https://api.github.com/users/chromium-wpt-export-bot/starred{/owner}{/repo}",
                    "site_admin": "false",
                    "login": "chromium-wpt-export-bot",
                    "type": "User",
                    "id": 25752892,
                    "node_id": "MDQ6VXNlcjI1NzUyODky"
                },
                "repository": {
                    "issues_url": "https://api.github.com/repos/web-platform-tests/wpt/issues{/number}",
                    "deployments_url": "https://api.github.com/repos/web-platform-tests/wpt/deployments",
                    "has_wiki": "true",
                    "forks_url": "https://api.github.com/repos/web-platform-tests/wpt/forks",
                    "mirror_url": "null",
                    "subscription_url": "https://api.github.com/repos/web-platform-tests/wpt/subscription",
                    "merges_url": "https://api.github.com/repos/web-platform-tests/wpt/merges",
                    "collaborators_url": "https://api.github.com/repos/web-platform-tests/wpt/collaborators{/collaborator}",
                    "updated_at": "2018-11-01T00:51:49Z",
                    "svn_url": "https://github.com/web-platform-tests/wpt",
                    "pulls_url": "https://api.github.com/repos/web-platform-tests/wpt/pulls{/number}",
                    "owner": {
                        "following_url": "https://api.github.com/users/web-platform-tests/following{/other_user}",
                        "events_url": "https://api.github.com/users/web-platform-tests/events{/privacy}",
                        "name": "web-platform-tests",
                        "organizations_url": "https://api.github.com/users/web-platform-tests/orgs",
                        "url": "https://api.github.com/users/web-platform-tests",
                        "gists_url": "https://api.github.com/users/web-platform-tests/gists{/gist_id}",
                        "subscriptions_url": "https://api.github.com/users/web-platform-tests/subscriptions",
                        "html_url": "https://github.com/web-platform-tests",
                        "email": "",
                        "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                        "repos_url": "https://api.github.com/users/web-platform-tests/repos",
                        "followers_url": "https://api.github.com/users/web-platform-tests/followers",
                        "received_events_url": "https://api.github.com/users/web-platform-tests/received_events",
                        "gravatar_id": "",
                        "starred_url": "https://api.github.com/users/web-platform-tests/starred{/owner}{/repo}",
                        "site_admin": "false",
                        "login": "web-platform-tests",
                        "type": "Organization",
                        "id": 37226233,
                        "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz"
                    },
                    "full_name": "web-platform-tests/wpt",
                    "issue_comment_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/web-platform-tests/wpt/contents/{+path}",
                    "id": 3618133,
                    "keys_url": "https://api.github.com/repos/web-platform-tests/wpt/keys{/key_id}",
                    "size": "305511",
                    "tags_url": "https://api.github.com/repos/web-platform-tests/wpt/tags",
                    "archived": "false",
                    "has_downloads": "true",
                    "downloads_url": "https://api.github.com/repos/web-platform-tests/wpt/downloads",
                    "assignees_url": "https://api.github.com/repos/web-platform-tests/wpt/assignees{/user}",
                    "statuses_url": "https://api.github.com/repos/web-platform-tests/wpt/statuses/{sha}",
                    "git_refs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/refs{/sha}",
                    "has_projects": "true",
                    "clone_url": "https://github.com/web-platform-tests/wpt.git",
                    "watchers_count": "1845",
                    "git_tags_url": "https://api.github.com/repos/web-platform-tests/wpt/git/tags{/sha}",
                    "labels_url": "https://api.github.com/repos/web-platform-tests/wpt/labels{/name}",
                    "organization": "web-platform-tests",
                    "stargazers_count": "1845",
                    "homepage": "http://irc.w3.org/?channels=testing",
                    "open_issues": "1328",
                    "fork": "false",
                    "milestones_url": "https://api.github.com/repos/web-platform-tests/wpt/milestones{/number}",
                    "commits_url": "https://api.github.com/repos/web-platform-tests/wpt/commits{/sha}",
                    "releases_url": "https://api.github.com/repos/web-platform-tests/wpt/releases{/id}",
                    "issue_events_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/events{/number}",
                    "archive_url": "https://api.github.com/repos/web-platform-tests/wpt/{archive_format}{/ref}",
                    "has_pages": "true",
                    "events_url": "https://api.github.com/repos/web-platform-tests/wpt/events",
                    "contributors_url": "https://api.github.com/repos/web-platform-tests/wpt/contributors",
                    "html_url": "https://github.com/web-platform-tests/wpt",
                    "compare_url": "https://api.github.com/repos/web-platform-tests/wpt/compare/{base}...{head}",
                    "language": "HTML",
                    "watchers": "1845",
                    "private": "false",
                    "forks_count": "1523",
                    "notifications_url": "https://api.github.com/repos/web-platform-tests/wpt/notifications{?since,all,participating}",
                    "has_issues": "true",
                    "ssh_url": "git@github.com:web-platform-tests/wpt.git",
                    "blobs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/blobs{/sha}",
                    "master_branch": "master",
                    "forks": "1523",
                    "hooks_url": "https://api.github.com/repos/web-platform-tests/wpt/hooks",
                    "open_issues_count": "1317",
                    "comments_url": "https://api.github.com/repos/web-platform-tests/wpt/comments{/number}",
                    "name": "wpt",
                    "license": {
                        "spdx_id": "NOASSERTION",
                        "url": "null",
                        "node_id": "MDc6TGljZW5zZTA=",
                        "name": "Other",
                        "key": "other"
                    },
                    "url": "https://github.com/web-platform-tests/wpt",
                    "stargazers": "1845",
                    "created_at": "1330865891",
                    "pushed_at": "1541037488",
                    "branches_url": "https://api.github.com/repos/web-platform-tests/wpt/branches{/branch}",
                    "node_id": "MDEwOlJlcG9zaXRvcnkzNjE4MTMz",
                    "default_branch": "master",
                    "teams_url": "https://api.github.com/repos/web-platform-tests/wpt/teams",
                    "trees_url": "https://api.github.com/repos/web-platform-tests/wpt/git/trees{/sha}",
                    "languages_url": "https://api.github.com/repos/web-platform-tests/wpt/languages",
                    "git_commits_url": "https://api.github.com/repos/web-platform-tests/wpt/git/commits{/sha}",
                    "subscribers_url": "https://api.github.com/repos/web-platform-tests/wpt/subscribers",
                    "stargazers_url": "https://api.github.com/repos/web-platform-tests/wpt/stargazers",
                    "git_url": "git://github.com/web-platform-tests/wpt.git"
                },
                "organization": {
                    "issues_url": "https://api.github.com/orgs/web-platform-tests/issues",
                    "members_url": "https://api.github.com/orgs/web-platform-tests/members{/member}",
                    "description": "",
                    "public_members_url": "https://api.github.com/orgs/web-platform-tests/public_members{/member}",
                    "url": "https://api.github.com/orgs/web-platform-tests",
                    "events_url": "https://api.github.com/orgs/web-platform-tests/events",
                    "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                    "repos_url": "https://api.github.com/orgs/web-platform-tests/repos",
                    "login": "web-platform-tests",
                    "id": "37226233",
                    "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz",
                    "hooks_url": "https://api.github.com/orgs/web-platform-tests/hooks"
                },
            },
            "event": "create",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd"
        }

        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        self.verify_repo(message, result)
        self.verify_org(message, result)
        assert result['source'] == 'create'
        assert result['details']['ref'] == message['body']['ref']
        assert result['details']['ref_type'] == message['body']['ref_type']
        assert result['summary'] == 'github: create: branch on repo: wpt in org: web-platform-tests triggered by user: chromium-wpt-export-bot'

    def test_repository_vulnerability_alert(self):
        message = {
            "body": {
                "action": "create",
                "alert": {
                    "affected_package_name": "requests",
                    "external_reference": "https://nvd.nist.gov/vuln/detail/CVE-2018-18074",
                    "external_identifier": "CVE-2018-18074",
                    "affected_range": "<= 2.19.1",
                    "id": "65626688",
                    "fixed_in": "2.20.0",
                    "dismisser": {
                        "login": "octocat",
                        "id": "1",
                        "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/octocat",
                        "html_url": "https://github.com/octocat",
                        "followers_url": "https://api.github.com/users/octocat/followers",
                        "following_url": "https://api.github.com/users/octocat/following{/other_user}",
                        "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
                        "organizations_url": "https://api.github.com/users/octocat/orgs",
                        "repos_url": "https://api.github.com/users/octocat/repos",
                        "events_url": "https://api.github.com/users/octocat/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/octocat/received_events",
                        "type": "User",
                        "site_admin": "true",
                    },
                    "dismiss_reason": "I'm too lazy to fix this",
                    "dismissed_at": "2017-10-25T00:00:00+00:00",
                },
                "sender": {
                    "following_url": "https://api.github.com/users/chromium-wpt-export-bot/following{/other_user}",
                    "events_url": "https://api.github.com/users/chromium-wpt-export-bot/events{/privacy}",
                    "organizations_url": "https://api.github.com/users/chromium-wpt-export-bot/orgs",
                    "url": "https://api.github.com/users/chromium-wpt-export-bot",
                    "gists_url": "https://api.github.com/users/chromium-wpt-export-bot/gists{/gist_id}",
                    "html_url": "https://github.com/chromium-wpt-export-bot",
                    "subscriptions_url": "https://api.github.com/users/chromium-wpt-export-bot/subscriptions",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/25752892?v=4",
                    "repos_url": "https://api.github.com/users/chromium-wpt-export-bot/repos",
                    "followers_url": "https://api.github.com/users/chromium-wpt-export-bot/followers",
                    "received_events_url": "https://api.github.com/users/chromium-wpt-export-bot/received_events",
                    "gravatar_id": "",
                    "starred_url": "https://api.github.com/users/chromium-wpt-export-bot/starred{/owner}{/repo}",
                    "site_admin": "false",
                    "login": "chromium-wpt-export-bot",
                    "type": "User",
                    "id": "25752892",
                    "node_id": "MDQ6VXNlcjI1NzUyODky"
                },
                "repository": {
                    "issues_url": "https://api.github.com/repos/web-platform-tests/wpt/issues{/number}",
                    "deployments_url": "https://api.github.com/repos/web-platform-tests/wpt/deployments",
                    "has_wiki": "true",
                    "forks_url": "https://api.github.com/repos/web-platform-tests/wpt/forks",
                    "mirror_url": "null",
                    "subscription_url": "https://api.github.com/repos/web-platform-tests/wpt/subscription",
                    "merges_url": "https://api.github.com/repos/web-platform-tests/wpt/merges",
                    "collaborators_url": "https://api.github.com/repos/web-platform-tests/wpt/collaborators{/collaborator}",
                    "updated_at": "2018-11-01T00:51:49Z",
                    "svn_url": "https://github.com/web-platform-tests/wpt",
                    "pulls_url": "https://api.github.com/repos/web-platform-tests/wpt/pulls{/number}",
                    "owner": {
                        "following_url": "https://api.github.com/users/web-platform-tests/following{/other_user}",
                        "events_url": "https://api.github.com/users/web-platform-tests/events{/privacy}",
                        "name": "web-platform-tests",
                        "organizations_url": "https://api.github.com/users/web-platform-tests/orgs",
                        "url": "https://api.github.com/users/web-platform-tests",
                        "gists_url": "https://api.github.com/users/web-platform-tests/gists{/gist_id}",
                        "subscriptions_url": "https://api.github.com/users/web-platform-tests/subscriptions",
                        "html_url": "https://github.com/web-platform-tests",
                        "email": "",
                        "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                        "repos_url": "https://api.github.com/users/web-platform-tests/repos",
                        "followers_url": "https://api.github.com/users/web-platform-tests/followers",
                        "received_events_url": "https://api.github.com/users/web-platform-tests/received_events",
                        "gravatar_id": "",
                        "starred_url": "https://api.github.com/users/web-platform-tests/starred{/owner}{/repo}",
                        "site_admin": "false",
                        "login": "web-platform-tests",
                        "type": "Organization",
                        "id": "37226233",
                        "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz"
                    },
                    "full_name": "web-platform-tests/wpt",
                    "issue_comment_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/web-platform-tests/wpt/contents/{+path}",
                    "id": "3618133",
                    "keys_url": "https://api.github.com/repos/web-platform-tests/wpt/keys{/key_id}",
                    "size": "305511",
                    "tags_url": "https://api.github.com/repos/web-platform-tests/wpt/tags",
                    "archived": "false",
                    "has_downloads": "true",
                    "downloads_url": "https://api.github.com/repos/web-platform-tests/wpt/downloads",
                    "assignees_url": "https://api.github.com/repos/web-platform-tests/wpt/assignees{/user}",
                    "statuses_url": "https://api.github.com/repos/web-platform-tests/wpt/statuses/{sha}",
                    "git_refs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/refs{/sha}",
                    "has_projects": "true",
                    "clone_url": "https://github.com/web-platform-tests/wpt.git",
                    "watchers_count": "1845",
                    "git_tags_url": "https://api.github.com/repos/web-platform-tests/wpt/git/tags{/sha}",
                    "labels_url": "https://api.github.com/repos/web-platform-tests/wpt/labels{/name}",
                    "organization": "web-platform-tests",
                    "stargazers_count": "1845",
                    "homepage": "http://irc.w3.org/?channels=testing",
                    "open_issues": "1328",
                    "fork": "false",
                    "milestones_url": "https://api.github.com/repos/web-platform-tests/wpt/milestones{/number}",
                    "commits_url": "https://api.github.com/repos/web-platform-tests/wpt/commits{/sha}",
                    "releases_url": "https://api.github.com/repos/web-platform-tests/wpt/releases{/id}",
                    "issue_events_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/events{/number}",
                    "archive_url": "https://api.github.com/repos/web-platform-tests/wpt/{archive_format}{/ref}",
                    "has_pages": "true",
                    "events_url": "https://api.github.com/repos/web-platform-tests/wpt/events",
                    "contributors_url": "https://api.github.com/repos/web-platform-tests/wpt/contributors",
                    "html_url": "https://github.com/web-platform-tests/wpt",
                    "compare_url": "https://api.github.com/repos/web-platform-tests/wpt/compare/{base}...{head}",
                    "language": "HTML",
                    "watchers": "1845",
                    "private": "false",
                    "forks_count": "1523",
                    "notifications_url": "https://api.github.com/repos/web-platform-tests/wpt/notifications{?since,all,participating}",
                    "has_issues": "true",
                    "ssh_url": "git@github.com:web-platform-tests/wpt.git",
                    "blobs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/blobs{/sha}",
                    "master_branch": "master",
                    "forks": "1523",
                    "hooks_url": "https://api.github.com/repos/web-platform-tests/wpt/hooks",
                    "open_issues_count": "1317",
                    "comments_url": "https://api.github.com/repos/web-platform-tests/wpt/comments{/number}",
                    "name": "wpt",
                    "license": {
                        "spdx_id": "NOASSERTION",
                        "url": "null",
                        "node_id": "MDc6TGljZW5zZTA=",
                        "name": "Other",
                        "key": "other"
                    },
                    "url": "https://github.com/web-platform-tests/wpt",
                    "stargazers": "1845",
                    "created_at": "1330865891",
                    "pushed_at": "1541037488",
                    "branches_url": "https://api.github.com/repos/web-platform-tests/wpt/branches{/branch}",
                    "node_id": "MDEwOlJlcG9zaXRvcnkzNjE4MTMz",
                    "default_branch": "master",
                    "teams_url": "https://api.github.com/repos/web-platform-tests/wpt/teams",
                    "trees_url": "https://api.github.com/repos/web-platform-tests/wpt/git/trees{/sha}",
                    "languages_url": "https://api.github.com/repos/web-platform-tests/wpt/languages",
                    "git_commits_url": "https://api.github.com/repos/web-platform-tests/wpt/git/commits{/sha}",
                    "subscribers_url": "https://api.github.com/repos/web-platform-tests/wpt/subscribers",
                    "stargazers_url": "https://api.github.com/repos/web-platform-tests/wpt/stargazers",
                    "git_url": "git://github.com/web-platform-tests/wpt.git"
                },
                "organization": {
                    "issues_url": "https://api.github.com/orgs/web-platform-tests/issues",
                    "members_url": "https://api.github.com/orgs/web-platform-tests/members{/member}",
                    "description": "",
                    "public_members_url": "https://api.github.com/orgs/web-platform-tests/public_members{/member}",
                    "url": "https://api.github.com/orgs/web-platform-tests",
                    "events_url": "https://api.github.com/orgs/web-platform-tests/events",
                    "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                    "repos_url": "https://api.github.com/orgs/web-platform-tests/repos",
                    "login": "web-platform-tests",
                    "id": "37226233",
                    "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz",
                    "hooks_url": "https://api.github.com/orgs/web-platform-tests/hooks"
                },
            },
            "event": "repository_vulnerability_alert",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd"
        }

        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        self.verify_repo(message, result)
        self.verify_org(message, result)
        assert result['source'] == 'repository_vulnerability_alert'
        assert result['details']['action'] == message['body']['action']
        assert result['details']['alert_package'] == message['body']['alert']['affected_package_name']
        assert result['details']['alert_range'] == message['body']['alert']['affected_range']
        assert result['details']['alert_extid'] == message['body']['alert']['external_identifier']
        assert result['details']['alert_extref'] == message['body']['alert']['external_reference']
        assert result['details']['alert_fixed'] == message['body']['alert']['fixed_in']
        assert result['details']['alert_id'] == message['body']['alert']['id']
        assert result['details']['dismiss_user'] == message['body']['alert']['dismisser']['login']
        assert result['details']['dismiss_id'] == message['body']['alert']['dismisser']['id']
        assert result['details']['dismiss_node_id'] == message['body']['alert']['dismisser']['node_id']
        assert result['details']['dismiss_type'] == message['body']['alert']['dismisser']['type']
        assert result['details']['dismiss_site_admin'] == message['body']['alert']['dismisser']['site_admin']
        assert result['summary'] == 'github: repository_vulnerability_alert: create on repo: wpt package: requests in org: web-platform-tests triggered by user: chromium-wpt-export-bot'

    def test_security_advisory(self):
        message = {
            "body": {
                "action": "published",
                "security_advisory": {
                    "ghsa_id": "GHSA-rf4j-j272-fj86",
                    "summary": "Moderate severity vulnerability that affects django",
                    "description": "django.contrib.auth.forms.AuthenticationForm in Django 2.0 before 2.0.2, and 1.11.8 and 1.11.9, allows remote attackers to obtain potentially sensitive information by leveraging data exposure from the confirm_login_allowed() method, as demonstrated by discovering whether a user account is inactive.",
                    "severity": "moderate",
                    "identifiers": [
                        {
                            "value": "GHSA-rf4j-j272-fj86",
                            "type": "GHSA"
                        },
                        {
                            "value": "CVE-2018-6188",
                            "type": "CVE"
                        }
                    ],
                    "references": [
                        {
                            "url": "https://nvd.nist.gov/vuln/detail/CVE-2018-6188"
                        }
                    ],
                    "published_at": "2018-10-03T21:13:54Z",
                    "updated_at": "2018-10-03T21:13:54Z",
                    "withdrawn_at": "null",
                    "vulnerabilities": [
                        {
                            "package": {
                                "ecosystem": "pip",
                                "name": "django"
                            },
                            "severity": "moderate",
                            "vulnerable_version_range": ">= 2.0.0, < 2.0.2",
                            "first_patched_version": {
                                "identifier": "2.0.2"
                            }
                        },
                        {
                            "package": {
                                "ecosystem": "pip",
                                "name": "django"
                            },
                            "severity": "moderate",
                            "vulnerable_version_range": ">= 1.11.8, < 1.11.10",
                            "first_patched_version": {
                                "identifier": "1.11.10"
                            }
                        }
                    ]
                },
            },
            "event": "security_advisory",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd",
        }
        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        assert result['source'] == 'security_advisory'
        assert result['details']['action'] == message['body']['action']
        assert result['details']['alert_description'] == message['body']['security_advisory']['description']
        assert result['summary'] == 'github: security_advisory: published for: Moderate severity vulnerability that affects django'

    def test_repository(self):
        message = {
            "body": {
                "action": "deleted",
                "sender": {
                    "following_url": "https://api.github.com/users/chromium-wpt-export-bot/following{/other_user}",
                    "events_url": "https://api.github.com/users/chromium-wpt-export-bot/events{/privacy}",
                    "organizations_url": "https://api.github.com/users/chromium-wpt-export-bot/orgs",
                    "url": "https://api.github.com/users/chromium-wpt-export-bot",
                    "gists_url": "https://api.github.com/users/chromium-wpt-export-bot/gists{/gist_id}",
                    "html_url": "https://github.com/chromium-wpt-export-bot",
                    "subscriptions_url": "https://api.github.com/users/chromium-wpt-export-bot/subscriptions",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/25752892?v=4",
                    "repos_url": "https://api.github.com/users/chromium-wpt-export-bot/repos",
                    "followers_url": "https://api.github.com/users/chromium-wpt-export-bot/followers",
                    "received_events_url": "https://api.github.com/users/chromium-wpt-export-bot/received_events",
                    "gravatar_id": "",
                    "starred_url": "https://api.github.com/users/chromium-wpt-export-bot/starred{/owner}{/repo}",
                    "site_admin": "false",
                    "login": "chromium-wpt-export-bot",
                    "type": "User",
                    "id": 25752892,
                    "node_id": "MDQ6VXNlcjI1NzUyODky"
                },
                "repository": {
                    "issues_url": "https://api.github.com/repos/web-platform-tests/wpt/issues{/number}",
                    "deployments_url": "https://api.github.com/repos/web-platform-tests/wpt/deployments",
                    "has_wiki": "true",
                    "forks_url": "https://api.github.com/repos/web-platform-tests/wpt/forks",
                    "mirror_url": "null",
                    "subscription_url": "https://api.github.com/repos/web-platform-tests/wpt/subscription",
                    "merges_url": "https://api.github.com/repos/web-platform-tests/wpt/merges",
                    "collaborators_url": "https://api.github.com/repos/web-platform-tests/wpt/collaborators{/collaborator}",
                    "updated_at": "2018-11-01T00:51:49Z",
                    "svn_url": "https://github.com/web-platform-tests/wpt",
                    "pulls_url": "https://api.github.com/repos/web-platform-tests/wpt/pulls{/number}",
                    "owner": {
                        "following_url": "https://api.github.com/users/web-platform-tests/following{/other_user}",
                        "events_url": "https://api.github.com/users/web-platform-tests/events{/privacy}",
                        "name": "web-platform-tests",
                        "organizations_url": "https://api.github.com/users/web-platform-tests/orgs",
                        "url": "https://api.github.com/users/web-platform-tests",
                        "gists_url": "https://api.github.com/users/web-platform-tests/gists{/gist_id}",
                        "subscriptions_url": "https://api.github.com/users/web-platform-tests/subscriptions",
                        "html_url": "https://github.com/web-platform-tests",
                        "email": "",
                        "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                        "repos_url": "https://api.github.com/users/web-platform-tests/repos",
                        "followers_url": "https://api.github.com/users/web-platform-tests/followers",
                        "received_events_url": "https://api.github.com/users/web-platform-tests/received_events",
                        "gravatar_id": "",
                        "starred_url": "https://api.github.com/users/web-platform-tests/starred{/owner}{/repo}",
                        "site_admin": "false",
                        "login": "web-platform-tests",
                        "type": "Organization",
                        "id": 37226233,
                        "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz"
                    },
                    "full_name": "web-platform-tests/wpt",
                    "issue_comment_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/web-platform-tests/wpt/contents/{+path}",
                    "id": 3618133,
                    "keys_url": "https://api.github.com/repos/web-platform-tests/wpt/keys{/key_id}",
                    "size": "305511",
                    "tags_url": "https://api.github.com/repos/web-platform-tests/wpt/tags",
                    "archived": "false",
                    "has_downloads": "true",
                    "downloads_url": "https://api.github.com/repos/web-platform-tests/wpt/downloads",
                    "assignees_url": "https://api.github.com/repos/web-platform-tests/wpt/assignees{/user}",
                    "statuses_url": "https://api.github.com/repos/web-platform-tests/wpt/statuses/{sha}",
                    "git_refs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/refs{/sha}",
                    "has_projects": "true",
                    "clone_url": "https://github.com/web-platform-tests/wpt.git",
                    "watchers_count": "1845",
                    "git_tags_url": "https://api.github.com/repos/web-platform-tests/wpt/git/tags{/sha}",
                    "labels_url": "https://api.github.com/repos/web-platform-tests/wpt/labels{/name}",
                    "organization": "web-platform-tests",
                    "stargazers_count": "1845",
                    "homepage": "http://irc.w3.org/?channels=testing",
                    "open_issues": "1328",
                    "fork": "false",
                    "milestones_url": "https://api.github.com/repos/web-platform-tests/wpt/milestones{/number}",
                    "commits_url": "https://api.github.com/repos/web-platform-tests/wpt/commits{/sha}",
                    "releases_url": "https://api.github.com/repos/web-platform-tests/wpt/releases{/id}",
                    "issue_events_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/events{/number}",
                    "archive_url": "https://api.github.com/repos/web-platform-tests/wpt/{archive_format}{/ref}",
                    "has_pages": "true",
                    "events_url": "https://api.github.com/repos/web-platform-tests/wpt/events",
                    "contributors_url": "https://api.github.com/repos/web-platform-tests/wpt/contributors",
                    "html_url": "https://github.com/web-platform-tests/wpt",
                    "compare_url": "https://api.github.com/repos/web-platform-tests/wpt/compare/{base}...{head}",
                    "language": "HTML",
                    "watchers": "1845",
                    "private": "false",
                    "forks_count": "1523",
                    "notifications_url": "https://api.github.com/repos/web-platform-tests/wpt/notifications{?since,all,participating}",
                    "has_issues": "true",
                    "ssh_url": "git@github.com:web-platform-tests/wpt.git",
                    "blobs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/blobs{/sha}",
                    "master_branch": "master",
                    "forks": "1523",
                    "hooks_url": "https://api.github.com/repos/web-platform-tests/wpt/hooks",
                    "open_issues_count": "1317",
                    "comments_url": "https://api.github.com/repos/web-platform-tests/wpt/comments{/number}",
                    "name": "wpt",
                    "license": {
                        "spdx_id": "NOASSERTION",
                        "url": "null",
                        "node_id": "MDc6TGljZW5zZTA=",
                        "name": "Other",
                        "key": "other"
                    },
                    "url": "https://github.com/web-platform-tests/wpt",
                    "stargazers": "1845",
                    "created_at": "1330865891",
                    "pushed_at": "1541037488",
                    "branches_url": "https://api.github.com/repos/web-platform-tests/wpt/branches{/branch}",
                    "node_id": "MDEwOlJlcG9zaXRvcnkzNjE4MTMz",
                    "default_branch": "master",
                    "teams_url": "https://api.github.com/repos/web-platform-tests/wpt/teams",
                    "trees_url": "https://api.github.com/repos/web-platform-tests/wpt/git/trees{/sha}",
                    "languages_url": "https://api.github.com/repos/web-platform-tests/wpt/languages",
                    "git_commits_url": "https://api.github.com/repos/web-platform-tests/wpt/git/commits{/sha}",
                    "subscribers_url": "https://api.github.com/repos/web-platform-tests/wpt/subscribers",
                    "stargazers_url": "https://api.github.com/repos/web-platform-tests/wpt/stargazers",
                    "git_url": "git://github.com/web-platform-tests/wpt.git"
                },
                "organization": {
                    "issues_url": "https://api.github.com/orgs/web-platform-tests/issues",
                    "members_url": "https://api.github.com/orgs/web-platform-tests/members{/member}",
                    "description": "",
                    "public_members_url": "https://api.github.com/orgs/web-platform-tests/public_members{/member}",
                    "url": "https://api.github.com/orgs/web-platform-tests",
                    "events_url": "https://api.github.com/orgs/web-platform-tests/events",
                    "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                    "repos_url": "https://api.github.com/orgs/web-platform-tests/repos",
                    "login": "web-platform-tests",
                    "id": 37226233,
                    "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz",
                    "hooks_url": "https://api.github.com/orgs/web-platform-tests/hooks"
                },
            },
            "event": "repository",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd"
        }

        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        self.verify_repo(message, result)
        self.verify_org(message, result)
        assert result['source'] == 'repository'
        assert result['details']['action'] == message['body']['action']
        assert result['summary'] == 'github: repository: deleted on repo: wpt in org: web-platform-tests triggered by user: chromium-wpt-export-bot'

    def test_member(self):
        message = {
            "body": {
                "member": {
                    "id": "60618",
                    "login": "emmairwin",
                    "node_id": "MDQ6VXNlcjYwNjE4",
                    "site_admin": "false",
                },
                "changes": {
                    "permission": {
                        "from": "write",
                    },
                },
                "action": "added",
                "sender": {
                    "following_url": "https://api.github.com/users/chromium-wpt-export-bot/following{/other_user}",
                    "events_url": "https://api.github.com/users/chromium-wpt-export-bot/events{/privacy}",
                    "organizations_url": "https://api.github.com/users/chromium-wpt-export-bot/orgs",
                    "url": "https://api.github.com/users/chromium-wpt-export-bot",
                    "gists_url": "https://api.github.com/users/chromium-wpt-export-bot/gists{/gist_id}",
                    "html_url": "https://github.com/chromium-wpt-export-bot",
                    "subscriptions_url": "https://api.github.com/users/chromium-wpt-export-bot/subscriptions",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/25752892?v=4",
                    "repos_url": "https://api.github.com/users/chromium-wpt-export-bot/repos",
                    "followers_url": "https://api.github.com/users/chromium-wpt-export-bot/followers",
                    "received_events_url": "https://api.github.com/users/chromium-wpt-export-bot/received_events",
                    "gravatar_id": "",
                    "starred_url": "https://api.github.com/users/chromium-wpt-export-bot/starred{/owner}{/repo}",
                    "site_admin": "false",
                    "login": "chromium-wpt-export-bot",
                    "type": "User",
                    "id": "25752892",
                    "node_id": "MDQ6VXNlcjI1NzUyODky"
                },
                "repository": {
                    "issues_url": "https://api.github.com/repos/web-platform-tests/wpt/issues{/number}",
                    "deployments_url": "https://api.github.com/repos/web-platform-tests/wpt/deployments",
                    "has_wiki": "true",
                    "forks_url": "https://api.github.com/repos/web-platform-tests/wpt/forks",
                    "mirror_url": "null",
                    "subscription_url": "https://api.github.com/repos/web-platform-tests/wpt/subscription",
                    "merges_url": "https://api.github.com/repos/web-platform-tests/wpt/merges",
                    "collaborators_url": "https://api.github.com/repos/web-platform-tests/wpt/collaborators{/collaborator}",
                    "updated_at": "2018-11-01T00:51:49Z",
                    "svn_url": "https://github.com/web-platform-tests/wpt",
                    "pulls_url": "https://api.github.com/repos/web-platform-tests/wpt/pulls{/number}",
                    "owner": {
                        "following_url": "https://api.github.com/users/web-platform-tests/following{/other_user}",
                        "events_url": "https://api.github.com/users/web-platform-tests/events{/privacy}",
                        "name": "web-platform-tests",
                        "organizations_url": "https://api.github.com/users/web-platform-tests/orgs",
                        "url": "https://api.github.com/users/web-platform-tests",
                        "gists_url": "https://api.github.com/users/web-platform-tests/gists{/gist_id}",
                        "subscriptions_url": "https://api.github.com/users/web-platform-tests/subscriptions",
                        "html_url": "https://github.com/web-platform-tests",
                        "email": "",
                        "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                        "repos_url": "https://api.github.com/users/web-platform-tests/repos",
                        "followers_url": "https://api.github.com/users/web-platform-tests/followers",
                        "received_events_url": "https://api.github.com/users/web-platform-tests/received_events",
                        "gravatar_id": "",
                        "starred_url": "https://api.github.com/users/web-platform-tests/starred{/owner}{/repo}",
                        "site_admin": "false",
                        "login": "web-platform-tests",
                        "type": "Organization",
                        "id": "37226233",
                        "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz"
                    },
                    "full_name": "web-platform-tests/wpt",
                    "issue_comment_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/web-platform-tests/wpt/contents/{+path}",
                    "id": "3618133",
                    "keys_url": "https://api.github.com/repos/web-platform-tests/wpt/keys{/key_id}",
                    "size": "305511",
                    "tags_url": "https://api.github.com/repos/web-platform-tests/wpt/tags",
                    "archived": "false",
                    "has_downloads": "true",
                    "downloads_url": "https://api.github.com/repos/web-platform-tests/wpt/downloads",
                    "assignees_url": "https://api.github.com/repos/web-platform-tests/wpt/assignees{/user}",
                    "statuses_url": "https://api.github.com/repos/web-platform-tests/wpt/statuses/{sha}",
                    "git_refs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/refs{/sha}",
                    "has_projects": "true",
                    "clone_url": "https://github.com/web-platform-tests/wpt.git",
                    "watchers_count": "1845",
                    "git_tags_url": "https://api.github.com/repos/web-platform-tests/wpt/git/tags{/sha}",
                    "labels_url": "https://api.github.com/repos/web-platform-tests/wpt/labels{/name}",
                    "organization": "web-platform-tests",
                    "stargazers_count": "1845",
                    "homepage": "http://irc.w3.org/?channels=testing",
                    "open_issues": "1328",
                    "fork": "false",
                    "milestones_url": "https://api.github.com/repos/web-platform-tests/wpt/milestones{/number}",
                    "commits_url": "https://api.github.com/repos/web-platform-tests/wpt/commits{/sha}",
                    "releases_url": "https://api.github.com/repos/web-platform-tests/wpt/releases{/id}",
                    "issue_events_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/events{/number}",
                    "archive_url": "https://api.github.com/repos/web-platform-tests/wpt/{archive_format}{/ref}",
                    "has_pages": "true",
                    "events_url": "https://api.github.com/repos/web-platform-tests/wpt/events",
                    "contributors_url": "https://api.github.com/repos/web-platform-tests/wpt/contributors",
                    "html_url": "https://github.com/web-platform-tests/wpt",
                    "compare_url": "https://api.github.com/repos/web-platform-tests/wpt/compare/{base}...{head}",
                    "language": "HTML",
                    "watchers": "1845",
                    "private": "false",
                    "forks_count": "1523",
                    "notifications_url": "https://api.github.com/repos/web-platform-tests/wpt/notifications{?since,all,participating}",
                    "has_issues": "true",
                    "ssh_url": "git@github.com:web-platform-tests/wpt.git",
                    "blobs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/blobs{/sha}",
                    "master_branch": "master",
                    "forks": "1523",
                    "hooks_url": "https://api.github.com/repos/web-platform-tests/wpt/hooks",
                    "open_issues_count": "1317",
                    "comments_url": "https://api.github.com/repos/web-platform-tests/wpt/comments{/number}",
                    "name": "wpt",
                    "license": {
                        "spdx_id": "NOASSERTION",
                        "url": "null",
                        "node_id": "MDc6TGljZW5zZTA=",
                        "name": "Other",
                        "key": "other"
                    },
                    "url": "https://github.com/web-platform-tests/wpt",
                    "stargazers": "1845",
                    "created_at": "1330865891",
                    "pushed_at": "1541037488",
                    "branches_url": "https://api.github.com/repos/web-platform-tests/wpt/branches{/branch}",
                    "node_id": "MDEwOlJlcG9zaXRvcnkzNjE4MTMz",
                    "default_branch": "master",
                    "teams_url": "https://api.github.com/repos/web-platform-tests/wpt/teams",
                    "trees_url": "https://api.github.com/repos/web-platform-tests/wpt/git/trees{/sha}",
                    "languages_url": "https://api.github.com/repos/web-platform-tests/wpt/languages",
                    "git_commits_url": "https://api.github.com/repos/web-platform-tests/wpt/git/commits{/sha}",
                    "subscribers_url": "https://api.github.com/repos/web-platform-tests/wpt/subscribers",
                    "stargazers_url": "https://api.github.com/repos/web-platform-tests/wpt/stargazers",
                    "git_url": "git://github.com/web-platform-tests/wpt.git"
                },
                "organization": {
                    "issues_url": "https://api.github.com/orgs/web-platform-tests/issues",
                    "members_url": "https://api.github.com/orgs/web-platform-tests/members{/member}",
                    "description": "",
                    "public_members_url": "https://api.github.com/orgs/web-platform-tests/public_members{/member}",
                    "url": "https://api.github.com/orgs/web-platform-tests",
                    "events_url": "https://api.github.com/orgs/web-platform-tests/events",
                    "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                    "repos_url": "https://api.github.com/orgs/web-platform-tests/repos",
                    "login": "web-platform-tests",
                    "id": "37226233",
                    "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz",
                    "hooks_url": "https://api.github.com/orgs/web-platform-tests/hooks"
                },
            },
            "event": "member",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd"
        }

        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        self.verify_repo(message, result)
        self.verify_org(message, result)
        assert result['source'] == 'member'
        assert result['details']['action'] == message['body']['action']
        assert result['details']['member_id'] == message['body']['member']['id']
        assert result['details']['member_login'] == message['body']['member']['login']
        assert result['details']['member_node_id'] == message['body']['member']['node_id']
        assert result['details']['member_site_admin'] == message['body']['member']['site_admin']
        assert result['details']['changes_perm_from'] == message['body']['changes']['permission']['from']
        assert result['summary'] == 'github: member: added on repo: wpt in org: web-platform-tests triggered by user: chromium-wpt-export-bot'

    def test_team(self):
        message = {
            "body": {
                "team": {
                    "id": 9060454,
                    "name": "asecretteam",
                    "login": "alamakota",
                    "node_id": "MYQ6VXK4fuwwNAye",
                    "permission": "pull",
                    "privacy": "secret",
                    "slug": "asecretteam",
                },
                "changes": {
                    "repository": {
                        "permissions": {
                            "from": {
                                "admin": "false",
                                "pull": "false",
                                "push": "false",
                            },
                        },
                    },
                },
                "action": "edited",
                "sender": {
                    "following_url": "https://api.github.com/users/chromium-wpt-export-bot/following{/other_user}",
                    "events_url": "https://api.github.com/users/chromium-wpt-export-bot/events{/privacy}",
                    "organizations_url": "https://api.github.com/users/chromium-wpt-export-bot/orgs",
                    "url": "https://api.github.com/users/chromium-wpt-export-bot",
                    "gists_url": "https://api.github.com/users/chromium-wpt-export-bot/gists{/gist_id}",
                    "html_url": "https://github.com/chromium-wpt-export-bot",
                    "subscriptions_url": "https://api.github.com/users/chromium-wpt-export-bot/subscriptions",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/25752892?v=4",
                    "repos_url": "https://api.github.com/users/chromium-wpt-export-bot/repos",
                    "followers_url": "https://api.github.com/users/chromium-wpt-export-bot/followers",
                    "received_events_url": "https://api.github.com/users/chromium-wpt-export-bot/received_events",
                    "gravatar_id": "",
                    "starred_url": "https://api.github.com/users/chromium-wpt-export-bot/starred{/owner}{/repo}",
                    "site_admin": "false",
                    "login": "chromium-wpt-export-bot",
                    "type": "User",
                    "id": "25752892",
                    "node_id": "MDQ6VXNlcjI1NzUyODky"
                },
                "repository": {
                    "permissions": {
                        "admin": "true",
                        "pull": "true",
                        "push": "true",
                    },
                    "issues_url": "https://api.github.com/repos/web-platform-tests/wpt/issues{/number}",
                    "deployments_url": "https://api.github.com/repos/web-platform-tests/wpt/deployments",
                    "has_wiki": "true",
                    "forks_url": "https://api.github.com/repos/web-platform-tests/wpt/forks",
                    "mirror_url": "null",
                    "subscription_url": "https://api.github.com/repos/web-platform-tests/wpt/subscription",
                    "merges_url": "https://api.github.com/repos/web-platform-tests/wpt/merges",
                    "collaborators_url": "https://api.github.com/repos/web-platform-tests/wpt/collaborators{/collaborator}",
                    "updated_at": "2018-11-01T00:51:49Z",
                    "svn_url": "https://github.com/web-platform-tests/wpt",
                    "pulls_url": "https://api.github.com/repos/web-platform-tests/wpt/pulls{/number}",
                    "owner": {
                        "following_url": "https://api.github.com/users/web-platform-tests/following{/other_user}",
                        "events_url": "https://api.github.com/users/web-platform-tests/events{/privacy}",
                        "name": "web-platform-tests",
                        "organizations_url": "https://api.github.com/users/web-platform-tests/orgs",
                        "url": "https://api.github.com/users/web-platform-tests",
                        "gists_url": "https://api.github.com/users/web-platform-tests/gists{/gist_id}",
                        "subscriptions_url": "https://api.github.com/users/web-platform-tests/subscriptions",
                        "html_url": "https://github.com/web-platform-tests",
                        "email": "",
                        "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                        "repos_url": "https://api.github.com/users/web-platform-tests/repos",
                        "followers_url": "https://api.github.com/users/web-platform-tests/followers",
                        "received_events_url": "https://api.github.com/users/web-platform-tests/received_events",
                        "gravatar_id": "",
                        "starred_url": "https://api.github.com/users/web-platform-tests/starred{/owner}{/repo}",
                        "site_admin": "false",
                        "login": "web-platform-tests",
                        "type": "Organization",
                        "id": "37226233",
                        "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz"
                    },
                    "full_name": "web-platform-tests/wpt",
                    "issue_comment_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/web-platform-tests/wpt/contents/{+path}",
                    "id": 3618133,
                    "keys_url": "https://api.github.com/repos/web-platform-tests/wpt/keys{/key_id}",
                    "size": "305511",
                    "tags_url": "https://api.github.com/repos/web-platform-tests/wpt/tags",
                    "archived": "false",
                    "has_downloads": "true",
                    "downloads_url": "https://api.github.com/repos/web-platform-tests/wpt/downloads",
                    "assignees_url": "https://api.github.com/repos/web-platform-tests/wpt/assignees{/user}",
                    "statuses_url": "https://api.github.com/repos/web-platform-tests/wpt/statuses/{sha}",
                    "git_refs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/refs{/sha}",
                    "has_projects": "true",
                    "clone_url": "https://github.com/web-platform-tests/wpt.git",
                    "watchers_count": "1845",
                    "git_tags_url": "https://api.github.com/repos/web-platform-tests/wpt/git/tags{/sha}",
                    "labels_url": "https://api.github.com/repos/web-platform-tests/wpt/labels{/name}",
                    "organization": "web-platform-tests",
                    "stargazers_count": "1845",
                    "homepage": "http://irc.w3.org/?channels=testing",
                    "open_issues": "1328",
                    "fork": "false",
                    "milestones_url": "https://api.github.com/repos/web-platform-tests/wpt/milestones{/number}",
                    "commits_url": "https://api.github.com/repos/web-platform-tests/wpt/commits{/sha}",
                    "releases_url": "https://api.github.com/repos/web-platform-tests/wpt/releases{/id}",
                    "issue_events_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/events{/number}",
                    "archive_url": "https://api.github.com/repos/web-platform-tests/wpt/{archive_format}{/ref}",
                    "has_pages": "true",
                    "events_url": "https://api.github.com/repos/web-platform-tests/wpt/events",
                    "contributors_url": "https://api.github.com/repos/web-platform-tests/wpt/contributors",
                    "html_url": "https://github.com/web-platform-tests/wpt",
                    "compare_url": "https://api.github.com/repos/web-platform-tests/wpt/compare/{base}...{head}",
                    "language": "HTML",
                    "watchers": "1845",
                    "private": "false",
                    "forks_count": "1523",
                    "notifications_url": "https://api.github.com/repos/web-platform-tests/wpt/notifications{?since,all,participating}",
                    "has_issues": "true",
                    "ssh_url": "git@github.com:web-platform-tests/wpt.git",
                    "blobs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/blobs{/sha}",
                    "master_branch": "master",
                    "forks": "1523",
                    "hooks_url": "https://api.github.com/repos/web-platform-tests/wpt/hooks",
                    "open_issues_count": "1317",
                    "comments_url": "https://api.github.com/repos/web-platform-tests/wpt/comments{/number}",
                    "name": "wpt",
                    "license": {
                        "spdx_id": "NOASSERTION",
                        "url": "null",
                        "node_id": "MDc6TGljZW5zZTA=",
                        "name": "Other",
                        "key": "other"
                    },
                    "url": "https://github.com/web-platform-tests/wpt",
                    "stargazers": "1845",
                    "created_at": "1330865891",
                    "pushed_at": "1541037488",
                    "branches_url": "https://api.github.com/repos/web-platform-tests/wpt/branches{/branch}",
                    "node_id": "MDEwOlJlcG9zaXRvcnkzNjE4MTMz",
                    "default_branch": "master",
                    "teams_url": "https://api.github.com/repos/web-platform-tests/wpt/teams",
                    "trees_url": "https://api.github.com/repos/web-platform-tests/wpt/git/trees{/sha}",
                    "languages_url": "https://api.github.com/repos/web-platform-tests/wpt/languages",
                    "git_commits_url": "https://api.github.com/repos/web-platform-tests/wpt/git/commits{/sha}",
                    "subscribers_url": "https://api.github.com/repos/web-platform-tests/wpt/subscribers",
                    "stargazers_url": "https://api.github.com/repos/web-platform-tests/wpt/stargazers",
                    "git_url": "git://github.com/web-platform-tests/wpt.git"
                },
                "organization": {
                    "issues_url": "https://api.github.com/orgs/web-platform-tests/issues",
                    "members_url": "https://api.github.com/orgs/web-platform-tests/members{/member}",
                    "description": "",
                    "public_members_url": "https://api.github.com/orgs/web-platform-tests/public_members{/member}",
                    "url": "https://api.github.com/orgs/web-platform-tests",
                    "events_url": "https://api.github.com/orgs/web-platform-tests/events",
                    "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                    "repos_url": "https://api.github.com/orgs/web-platform-tests/repos",
                    "login": "web-platform-tests",
                    "id": 37226233,
                    "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz",
                    "hooks_url": "https://api.github.com/orgs/web-platform-tests/hooks"
                },
            },
            "event": "team",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd"
        }

        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        self.verify_repo(message, result)
        self.verify_org(message, result)
        assert result['source'] == 'team'
        assert result['details']['action'] == message['body']['action']
        assert result['details']['repo_perm_from_admin'] == message['body']['changes']['repository']['permissions']['from']['admin']
        assert result['details']['repo_perm_from_pull'] == message['body']['changes']['repository']['permissions']['from']['pull']
        assert result['details']['repo_perm_from_push'] == message['body']['changes']['repository']['permissions']['from']['push']
        assert result['details']['repo_perm_admin'] == message['body']['repository']['permissions']['admin']
        assert result['details']['repo_perm_pull'] == message['body']['repository']['permissions']['pull']
        assert result['details']['repo_perm_push'] == message['body']['repository']['permissions']['push']
        assert result['details']['team_id'] == message['body']['team']['id']
        assert result['details']['team_name'] == message['body']['team']['name']
        assert result['details']['team_node_id'] == message['body']['team']['node_id']
        assert result['details']['team_permission'] == message['body']['team']['permission']
        assert result['details']['team_privacy'] == message['body']['team']['privacy']
        assert result['details']['team_slug'] == message['body']['team']['slug']
        assert result['summary'] == 'github: team: edited on repo: wpt team: asecretteam in org: web-platform-tests triggered by user: chromium-wpt-export-bot'

    def test_team_add(self):
        message = {
            "body": {
                "team": {
                    "id": 9060454,
                    "name": "asecretteam",
                    "login": "alamakota",
                    "node_id": "MYQ6VXK4fuwwNAye",
                    "permission": "pull",
                    "privacy": "secret",
                    "slug": "asecretteam",
                },
                "changes": {
                    "repository": {
                        "permissions": {
                            "from": {
                                "admin": "false",
                                "pull": "false",
                                "push": "false",
                            },
                        },
                    },
                },
                "sender": {
                    "following_url": "https://api.github.com/users/chromium-wpt-export-bot/following{/other_user}",
                    "events_url": "https://api.github.com/users/chromium-wpt-export-bot/events{/privacy}",
                    "organizations_url": "https://api.github.com/users/chromium-wpt-export-bot/orgs",
                    "url": "https://api.github.com/users/chromium-wpt-export-bot",
                    "gists_url": "https://api.github.com/users/chromium-wpt-export-bot/gists{/gist_id}",
                    "html_url": "https://github.com/chromium-wpt-export-bot",
                    "subscriptions_url": "https://api.github.com/users/chromium-wpt-export-bot/subscriptions",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/25752892?v=4",
                    "repos_url": "https://api.github.com/users/chromium-wpt-export-bot/repos",
                    "followers_url": "https://api.github.com/users/chromium-wpt-export-bot/followers",
                    "received_events_url": "https://api.github.com/users/chromium-wpt-export-bot/received_events",
                    "gravatar_id": "",
                    "starred_url": "https://api.github.com/users/chromium-wpt-export-bot/starred{/owner}{/repo}",
                    "site_admin": "false",
                    "login": "chromium-wpt-export-bot",
                    "type": "User",
                    "id": 25752892,
                    "node_id": "MDQ6VXNlcjI1NzUyODky"
                },
                "repository": {
                    "permissions": {
                        "admin": "true",
                        "pull": "true",
                        "push": "true",
                    },
                    "issues_url": "https://api.github.com/repos/web-platform-tests/wpt/issues{/number}",
                    "deployments_url": "https://api.github.com/repos/web-platform-tests/wpt/deployments",
                    "has_wiki": "true",
                    "forks_url": "https://api.github.com/repos/web-platform-tests/wpt/forks",
                    "mirror_url": "null",
                    "subscription_url": "https://api.github.com/repos/web-platform-tests/wpt/subscription",
                    "merges_url": "https://api.github.com/repos/web-platform-tests/wpt/merges",
                    "collaborators_url": "https://api.github.com/repos/web-platform-tests/wpt/collaborators{/collaborator}",
                    "updated_at": "2018-11-01T00:51:49Z",
                    "svn_url": "https://github.com/web-platform-tests/wpt",
                    "pulls_url": "https://api.github.com/repos/web-platform-tests/wpt/pulls{/number}",
                    "owner": {
                        "following_url": "https://api.github.com/users/web-platform-tests/following{/other_user}",
                        "events_url": "https://api.github.com/users/web-platform-tests/events{/privacy}",
                        "name": "web-platform-tests",
                        "organizations_url": "https://api.github.com/users/web-platform-tests/orgs",
                        "url": "https://api.github.com/users/web-platform-tests",
                        "gists_url": "https://api.github.com/users/web-platform-tests/gists{/gist_id}",
                        "subscriptions_url": "https://api.github.com/users/web-platform-tests/subscriptions",
                        "html_url": "https://github.com/web-platform-tests",
                        "email": "",
                        "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                        "repos_url": "https://api.github.com/users/web-platform-tests/repos",
                        "followers_url": "https://api.github.com/users/web-platform-tests/followers",
                        "received_events_url": "https://api.github.com/users/web-platform-tests/received_events",
                        "gravatar_id": "",
                        "starred_url": "https://api.github.com/users/web-platform-tests/starred{/owner}{/repo}",
                        "site_admin": "false",
                        "login": "web-platform-tests",
                        "type": "Organization",
                        "id": 37226233,
                        "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz"
                    },
                    "full_name": "web-platform-tests/wpt",
                    "issue_comment_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/web-platform-tests/wpt/contents/{+path}",
                    "id": 3618133,
                    "keys_url": "https://api.github.com/repos/web-platform-tests/wpt/keys{/key_id}",
                    "size": "305511",
                    "tags_url": "https://api.github.com/repos/web-platform-tests/wpt/tags",
                    "archived": "false",
                    "has_downloads": "true",
                    "downloads_url": "https://api.github.com/repos/web-platform-tests/wpt/downloads",
                    "assignees_url": "https://api.github.com/repos/web-platform-tests/wpt/assignees{/user}",
                    "statuses_url": "https://api.github.com/repos/web-platform-tests/wpt/statuses/{sha}",
                    "git_refs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/refs{/sha}",
                    "has_projects": "true",
                    "clone_url": "https://github.com/web-platform-tests/wpt.git",
                    "watchers_count": "1845",
                    "git_tags_url": "https://api.github.com/repos/web-platform-tests/wpt/git/tags{/sha}",
                    "labels_url": "https://api.github.com/repos/web-platform-tests/wpt/labels{/name}",
                    "organization": "web-platform-tests",
                    "stargazers_count": "1845",
                    "homepage": "http://irc.w3.org/?channels=testing",
                    "open_issues": "1328",
                    "fork": "false",
                    "milestones_url": "https://api.github.com/repos/web-platform-tests/wpt/milestones{/number}",
                    "commits_url": "https://api.github.com/repos/web-platform-tests/wpt/commits{/sha}",
                    "releases_url": "https://api.github.com/repos/web-platform-tests/wpt/releases{/id}",
                    "issue_events_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/events{/number}",
                    "archive_url": "https://api.github.com/repos/web-platform-tests/wpt/{archive_format}{/ref}",
                    "has_pages": "true",
                    "events_url": "https://api.github.com/repos/web-platform-tests/wpt/events",
                    "contributors_url": "https://api.github.com/repos/web-platform-tests/wpt/contributors",
                    "html_url": "https://github.com/web-platform-tests/wpt",
                    "compare_url": "https://api.github.com/repos/web-platform-tests/wpt/compare/{base}...{head}",
                    "language": "HTML",
                    "watchers": "1845",
                    "private": "false",
                    "forks_count": "1523",
                    "notifications_url": "https://api.github.com/repos/web-platform-tests/wpt/notifications{?since,all,participating}",
                    "has_issues": "true",
                    "ssh_url": "git@github.com:web-platform-tests/wpt.git",
                    "blobs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/blobs{/sha}",
                    "master_branch": "master",
                    "forks": "1523",
                    "hooks_url": "https://api.github.com/repos/web-platform-tests/wpt/hooks",
                    "open_issues_count": "1317",
                    "comments_url": "https://api.github.com/repos/web-platform-tests/wpt/comments{/number}",
                    "name": "wpt",
                    "license": {
                        "spdx_id": "NOASSERTION",
                        "url": "null",
                        "node_id": "MDc6TGljZW5zZTA=",
                        "name": "Other",
                        "key": "other"
                    },
                    "url": "https://github.com/web-platform-tests/wpt",
                    "stargazers": "1845",
                    "created_at": "1330865891",
                    "pushed_at": "1541037488",
                    "branches_url": "https://api.github.com/repos/web-platform-tests/wpt/branches{/branch}",
                    "node_id": "MDEwOlJlcG9zaXRvcnkzNjE4MTMz",
                    "default_branch": "master",
                    "teams_url": "https://api.github.com/repos/web-platform-tests/wpt/teams",
                    "trees_url": "https://api.github.com/repos/web-platform-tests/wpt/git/trees{/sha}",
                    "languages_url": "https://api.github.com/repos/web-platform-tests/wpt/languages",
                    "git_commits_url": "https://api.github.com/repos/web-platform-tests/wpt/git/commits{/sha}",
                    "subscribers_url": "https://api.github.com/repos/web-platform-tests/wpt/subscribers",
                    "stargazers_url": "https://api.github.com/repos/web-platform-tests/wpt/stargazers",
                    "git_url": "git://github.com/web-platform-tests/wpt.git"
                },
                "organization": {
                    "issues_url": "https://api.github.com/orgs/web-platform-tests/issues",
                    "members_url": "https://api.github.com/orgs/web-platform-tests/members{/member}",
                    "description": "",
                    "public_members_url": "https://api.github.com/orgs/web-platform-tests/public_members{/member}",
                    "url": "https://api.github.com/orgs/web-platform-tests",
                    "events_url": "https://api.github.com/orgs/web-platform-tests/events",
                    "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                    "repos_url": "https://api.github.com/orgs/web-platform-tests/repos",
                    "login": "web-platform-tests",
                    "id": 37226233,
                    "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz",
                    "hooks_url": "https://api.github.com/orgs/web-platform-tests/hooks"
                },
            },
            "event": "team_add",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd"
        }

        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        self.verify_repo(message, result)
        self.verify_org(message, result)
        assert result['source'] == 'team_add'
        assert result['details']['repo_perm_from_admin'] == message['body']['changes']['repository']['permissions']['from']['admin']
        assert result['details']['repo_perm_from_pull'] == message['body']['changes']['repository']['permissions']['from']['pull']
        assert result['details']['repo_perm_from_push'] == message['body']['changes']['repository']['permissions']['from']['push']
        assert result['details']['repo_perm_admin'] == message['body']['repository']['permissions']['admin']
        assert result['details']['repo_perm_pull'] == message['body']['repository']['permissions']['pull']
        assert result['details']['repo_perm_push'] == message['body']['repository']['permissions']['push']
        assert result['details']['team_id'] == message['body']['team']['id']
        assert result['details']['team_name'] == message['body']['team']['name']
        assert result['details']['team_node_id'] == message['body']['team']['node_id']
        assert result['details']['team_permission'] == message['body']['team']['permission']
        assert result['details']['team_privacy'] == message['body']['team']['privacy']
        assert result['details']['team_slug'] == message['body']['team']['slug']
        assert result['summary'] == 'github: team_add: on repo: wpt team: asecretteam in org: web-platform-tests triggered by user: chromium-wpt-export-bot'

    def test_organization(self):
        message = {
            "body": {
                "team": {
                    "id": 9060454,
                    "name": "asecretteam",
                    "login": "alamakota",
                    "node_id": "MYQ6VXK4fuwwNAye",
                    "permission": "pull",
                    "privacy": "secret",
                    "slug": "asecretteam",
                },
                "membership": {
                    "user": {
                        "id": 893282,
                        "login": "alamakota",
                        "node_id": "MDQ6VXNlcjUwMTkyMzQ=",
                        "site_admin": "false",
                        "type": "User",
                    },
                    "role": "member",
                    "state": "pending",
                },
                "action": "member_added",
                "sender": {
                    "following_url": "https://api.github.com/users/chromium-wpt-export-bot/following{/other_user}",
                    "events_url": "https://api.github.com/users/chromium-wpt-export-bot/events{/privacy}",
                    "organizations_url": "https://api.github.com/users/chromium-wpt-export-bot/orgs",
                    "url": "https://api.github.com/users/chromium-wpt-export-bot",
                    "gists_url": "https://api.github.com/users/chromium-wpt-export-bot/gists{/gist_id}",
                    "html_url": "https://github.com/chromium-wpt-export-bot",
                    "subscriptions_url": "https://api.github.com/users/chromium-wpt-export-bot/subscriptions",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/25752892?v=4",
                    "repos_url": "https://api.github.com/users/chromium-wpt-export-bot/repos",
                    "followers_url": "https://api.github.com/users/chromium-wpt-export-bot/followers",
                    "received_events_url": "https://api.github.com/users/chromium-wpt-export-bot/received_events",
                    "gravatar_id": "",
                    "starred_url": "https://api.github.com/users/chromium-wpt-export-bot/starred{/owner}{/repo}",
                    "site_admin": "false",
                    "login": "chromium-wpt-export-bot",
                    "type": "User",
                    "id": 25752892,
                    "node_id": "MDQ6VXNlcjI1NzUyODky"
                },
                "repository": {
                    "permissions": {
                        "admin": "true",
                        "pull": "true",
                        "push": "true",
                    },
                    "issues_url": "https://api.github.com/repos/web-platform-tests/wpt/issues{/number}",
                    "deployments_url": "https://api.github.com/repos/web-platform-tests/wpt/deployments",
                    "has_wiki": "true",
                    "forks_url": "https://api.github.com/repos/web-platform-tests/wpt/forks",
                    "mirror_url": "null",
                    "subscription_url": "https://api.github.com/repos/web-platform-tests/wpt/subscription",
                    "merges_url": "https://api.github.com/repos/web-platform-tests/wpt/merges",
                    "collaborators_url": "https://api.github.com/repos/web-platform-tests/wpt/collaborators{/collaborator}",
                    "updated_at": "2018-11-01T00:51:49Z",
                    "svn_url": "https://github.com/web-platform-tests/wpt",
                    "pulls_url": "https://api.github.com/repos/web-platform-tests/wpt/pulls{/number}",
                    "owner": {
                        "following_url": "https://api.github.com/users/web-platform-tests/following{/other_user}",
                        "events_url": "https://api.github.com/users/web-platform-tests/events{/privacy}",
                        "name": "web-platform-tests",
                        "organizations_url": "https://api.github.com/users/web-platform-tests/orgs",
                        "url": "https://api.github.com/users/web-platform-tests",
                        "gists_url": "https://api.github.com/users/web-platform-tests/gists{/gist_id}",
                        "subscriptions_url": "https://api.github.com/users/web-platform-tests/subscriptions",
                        "html_url": "https://github.com/web-platform-tests",
                        "email": "",
                        "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                        "repos_url": "https://api.github.com/users/web-platform-tests/repos",
                        "followers_url": "https://api.github.com/users/web-platform-tests/followers",
                        "received_events_url": "https://api.github.com/users/web-platform-tests/received_events",
                        "gravatar_id": "",
                        "starred_url": "https://api.github.com/users/web-platform-tests/starred{/owner}{/repo}",
                        "site_admin": "false",
                        "login": "web-platform-tests",
                        "type": "Organization",
                        "id": 37226233,
                        "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz"
                    },
                    "full_name": "web-platform-tests/wpt",
                    "issue_comment_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/web-platform-tests/wpt/contents/{+path}",
                    "id": 3618133,
                    "keys_url": "https://api.github.com/repos/web-platform-tests/wpt/keys{/key_id}",
                    "size": "305511",
                    "tags_url": "https://api.github.com/repos/web-platform-tests/wpt/tags",
                    "archived": "false",
                    "has_downloads": "true",
                    "downloads_url": "https://api.github.com/repos/web-platform-tests/wpt/downloads",
                    "assignees_url": "https://api.github.com/repos/web-platform-tests/wpt/assignees{/user}",
                    "statuses_url": "https://api.github.com/repos/web-platform-tests/wpt/statuses/{sha}",
                    "git_refs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/refs{/sha}",
                    "has_projects": "true",
                    "clone_url": "https://github.com/web-platform-tests/wpt.git",
                    "watchers_count": "1845",
                    "git_tags_url": "https://api.github.com/repos/web-platform-tests/wpt/git/tags{/sha}",
                    "labels_url": "https://api.github.com/repos/web-platform-tests/wpt/labels{/name}",
                    "organization": "web-platform-tests",
                    "stargazers_count": "1845",
                    "homepage": "http://irc.w3.org/?channels=testing",
                    "open_issues": "1328",
                    "fork": "false",
                    "milestones_url": "https://api.github.com/repos/web-platform-tests/wpt/milestones{/number}",
                    "commits_url": "https://api.github.com/repos/web-platform-tests/wpt/commits{/sha}",
                    "releases_url": "https://api.github.com/repos/web-platform-tests/wpt/releases{/id}",
                    "issue_events_url": "https://api.github.com/repos/web-platform-tests/wpt/issues/events{/number}",
                    "archive_url": "https://api.github.com/repos/web-platform-tests/wpt/{archive_format}{/ref}",
                    "has_pages": "true",
                    "events_url": "https://api.github.com/repos/web-platform-tests/wpt/events",
                    "contributors_url": "https://api.github.com/repos/web-platform-tests/wpt/contributors",
                    "html_url": "https://github.com/web-platform-tests/wpt",
                    "compare_url": "https://api.github.com/repos/web-platform-tests/wpt/compare/{base}...{head}",
                    "language": "HTML",
                    "watchers": "1845",
                    "private": "false",
                    "forks_count": "1523",
                    "notifications_url": "https://api.github.com/repos/web-platform-tests/wpt/notifications{?since,all,participating}",
                    "has_issues": "true",
                    "ssh_url": "git@github.com:web-platform-tests/wpt.git",
                    "blobs_url": "https://api.github.com/repos/web-platform-tests/wpt/git/blobs{/sha}",
                    "master_branch": "master",
                    "forks": "1523",
                    "hooks_url": "https://api.github.com/repos/web-platform-tests/wpt/hooks",
                    "open_issues_count": "1317",
                    "comments_url": "https://api.github.com/repos/web-platform-tests/wpt/comments{/number}",
                    "name": "wpt",
                    "license": {
                        "spdx_id": "NOASSERTION",
                        "url": "null",
                        "node_id": "MDc6TGljZW5zZTA=",
                        "name": "Other",
                        "key": "other"
                    },
                    "url": "https://github.com/web-platform-tests/wpt",
                    "stargazers": "1845",
                    "created_at": "1330865891",
                    "pushed_at": "1541037488",
                    "branches_url": "https://api.github.com/repos/web-platform-tests/wpt/branches{/branch}",
                    "node_id": "MDEwOlJlcG9zaXRvcnkzNjE4MTMz",
                    "default_branch": "master",
                    "teams_url": "https://api.github.com/repos/web-platform-tests/wpt/teams",
                    "trees_url": "https://api.github.com/repos/web-platform-tests/wpt/git/trees{/sha}",
                    "languages_url": "https://api.github.com/repos/web-platform-tests/wpt/languages",
                    "git_commits_url": "https://api.github.com/repos/web-platform-tests/wpt/git/commits{/sha}",
                    "subscribers_url": "https://api.github.com/repos/web-platform-tests/wpt/subscribers",
                    "stargazers_url": "https://api.github.com/repos/web-platform-tests/wpt/stargazers",
                    "git_url": "git://github.com/web-platform-tests/wpt.git"
                },
                "organization": {
                    "issues_url": "https://api.github.com/orgs/web-platform-tests/issues",
                    "members_url": "https://api.github.com/orgs/web-platform-tests/members{/member}",
                    "description": "",
                    "public_members_url": "https://api.github.com/orgs/web-platform-tests/public_members{/member}",
                    "url": "https://api.github.com/orgs/web-platform-tests",
                    "events_url": "https://api.github.com/orgs/web-platform-tests/events",
                    "avatar_url": "https://avatars0.githubusercontent.com/u/37226233?v=4",
                    "repos_url": "https://api.github.com/orgs/web-platform-tests/repos",
                    "login": "web-platform-tests",
                    "id": 37226233,
                    "node_id": "MDEyOk9yZ2FuaXphdGlvbjM3MjI2MjMz",
                    "hooks_url": "https://api.github.com/orgs/web-platform-tests/hooks"
                },
            },
            "event": "organization",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd"
        }

        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        self.verify_repo(message, result)
        self.verify_org(message, result)
        assert result['source'] == 'organization'
        assert result['details']['action'] == message['body']['action']
        assert result['details']['team_id'] == message['body']['team']['id']
        assert result['details']['team_name'] == message['body']['team']['name']
        assert result['details']['team_node_id'] == message['body']['team']['node_id']
        assert result['details']['team_permission'] == message['body']['team']['permission']
        assert result['details']['team_privacy'] == message['body']['team']['privacy']
        assert result['details']['team_slug'] == message['body']['team']['slug']
        assert result['details']['membership_type'] == message['body']['membership']['user']['type']
        assert result['details']['membership_admin'] == message['body']['membership']['user']['site_admin']
        assert result['details']['membership_node_id'] == message['body']['membership']['user']['node_id']
        assert result['details']['membership_login'] == message['body']['membership']['user']['login']
        assert result['details']['membership_id'] == message['body']['membership']['user']['id']
        assert result['details']['membership_state'] == message['body']['membership']['state']
        assert result['details']['membership_role'] == message['body']['membership']['role']
        assert result['summary'] == 'github: organization: member_added on repo: wpt team: asecretteam in org: web-platform-tests triggered by user: chromium-wpt-export-bot'

    def test_membership(self):
        message = {
            "body": {
                "action": "removed",
                "scope": "team",
                "team": {
                    "name": "github",
                    "id": 3253328,
                    "node_id": "MDQ6VGVhbTMyNTMzMjg=",
                    "slug": "github",
                    "description": "Open-source team",
                    "privacy": "secret",
                    "url": "https://api.github.com/teams/3253328",
                    "html_url": "https://github.com/orgs/Octocoders/teams/github",
                    "members_url": "https://api.github.com/teams/3253328/members{/member}",
                    "repositories_url": "https://api.github.com/teams/3253328/repos",
                    "permission": "pull"
                },
                "repository": {
                    "id": 186853261,
                    "node_id": "MDEwOlJlcG9zaXRvcnkxODY4NTMyNjE=",
                    "name": "Hello-World",
                    "full_name": "Octocoders/Hello-World",
                    "private": "false",
                    "owner": {
                        "login": "Octocoders",
                        "id": 38302899,
                        "node_id": "MDEyOk9yZ2FuaXphdGlvbjM4MzAyODk5",
                        "avatar_url": "https://avatars1.githubusercontent.com/u/38302899?v=4",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/Octocoders",
                        "html_url": "https://github.com/Octocoders",
                        "followers_url": "https://api.github.com/users/Octocoders/followers",
                        "following_url": "https://api.github.com/users/Octocoders/following{/other_user}",
                        "gists_url": "https://api.github.com/users/Octocoders/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/Octocoders/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/Octocoders/subscriptions",
                        "organizations_url": "https://api.github.com/users/Octocoders/orgs",
                        "repos_url": "https://api.github.com/users/Octocoders/repos",
                        "events_url": "https://api.github.com/users/Octocoders/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/Octocoders/received_events",
                        "type": "Organization",
                        "site_admin": "false"
                    },
                    "html_url": "https://github.com/Octocoders/Hello-World",
                    "description": "null",
                    "fork": "true",
                    "url": "https://api.github.com/repos/Octocoders/Hello-World",
                    "forks_url": "https://api.github.com/repos/Octocoders/Hello-World/forks",
                    "keys_url": "https://api.github.com/repos/Octocoders/Hello-World/keys{/key_id}",
                    "collaborators_url": "https://api.github.com/repos/Octocoders/Hello-World/collaborators{/collaborator}",
                    "teams_url": "https://api.github.com/repos/Octocoders/Hello-World/teams",
                    "hooks_url": "https://api.github.com/repos/Octocoders/Hello-World/hooks",
                    "issue_events_url": "https://api.github.com/repos/Octocoders/Hello-World/issues/events{/number}",
                    "events_url": "https://api.github.com/repos/Octocoders/Hello-World/events",
                    "assignees_url": "https://api.github.com/repos/Octocoders/Hello-World/assignees{/user}",
                    "branches_url": "https://api.github.com/repos/Octocoders/Hello-World/branches{/branch}",
                    "tags_url": "https://api.github.com/repos/Octocoders/Hello-World/tags",
                    "blobs_url": "https://api.github.com/repos/Octocoders/Hello-World/git/blobs{/sha}",
                    "git_tags_url": "https://api.github.com/repos/Octocoders/Hello-World/git/tags{/sha}",
                    "git_refs_url": "https://api.github.com/repos/Octocoders/Hello-World/git/refs{/sha}",
                    "trees_url": "https://api.github.com/repos/Octocoders/Hello-World/git/trees{/sha}",
                    "statuses_url": "https://api.github.com/repos/Octocoders/Hello-World/statuses/{sha}",
                    "languages_url": "https://api.github.com/repos/Octocoders/Hello-World/languages",
                    "stargazers_url": "https://api.github.com/repos/Octocoders/Hello-World/stargazers",
                    "contributors_url": "https://api.github.com/repos/Octocoders/Hello-World/contributors",
                    "subscribers_url": "https://api.github.com/repos/Octocoders/Hello-World/subscribers",
                    "subscription_url": "https://api.github.com/repos/Octocoders/Hello-World/subscription",
                    "commits_url": "https://api.github.com/repos/Octocoders/Hello-World/commits{/sha}",
                    "git_commits_url": "https://api.github.com/repos/Octocoders/Hello-World/git/commits{/sha}",
                    "comments_url": "https://api.github.com/repos/Octocoders/Hello-World/comments{/number}",
                    "issue_comment_url": "https://api.github.com/repos/Octocoders/Hello-World/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/Octocoders/Hello-World/contents/{+path}",
                    "compare_url": "https://api.github.com/repos/Octocoders/Hello-World/compare/{base}...{head}",
                    "merges_url": "https://api.github.com/repos/Octocoders/Hello-World/merges",
                    "archive_url": "https://api.github.com/repos/Octocoders/Hello-World/{archive_format}{/ref}",
                    "downloads_url": "https://api.github.com/repos/Octocoders/Hello-World/downloads",
                    "issues_url": "https://api.github.com/repos/Octocoders/Hello-World/issues{/number}",
                    "pulls_url": "https://api.github.com/repos/Octocoders/Hello-World/pulls{/number}",
                    "milestones_url": "https://api.github.com/repos/Octocoders/Hello-World/milestones{/number}",
                    "notifications_url": "https://api.github.com/repos/Octocoders/Hello-World/notifications{?since,all,participating}",
                    "labels_url": "https://api.github.com/repos/Octocoders/Hello-World/labels{/name}",
                    "releases_url": "https://api.github.com/repos/Octocoders/Hello-World/releases{/id}",
                    "deployments_url": "https://api.github.com/repos/Octocoders/Hello-World/deployments",
                    "created_at": "2019-05-15T15:20:42Z",
                    "updated_at": "2019-05-15T15:20:45Z",
                    "pushed_at": "2019-05-15T15:20:33Z",
                    "git_url": "git://github.com/Octocoders/Hello-World.git",
                    "ssh_url": "git@github.com:Octocoders/Hello-World.git",
                    "clone_url": "https://github.com/Octocoders/Hello-World.git",
                    "svn_url": "https://github.com/Octocoders/Hello-World",
                    "homepage": "null",
                    "size": 0,
                    "stargazers_count": 0,
                    "watchers_count": 0,
                    "language": "Ruby",
                    "has_issues": "false",
                    "has_projects": "true",
                    "has_downloads": "true",
                    "has_wiki": "true",
                    "has_pages": "false",
                    "forks_count": 0,
                    "mirror_url": "null",
                    "archived": "false",
                    "disabled": "false",
                    "open_issues_count": 0,
                    "license": "null",
                    "forks": 0,
                    "open_issues": 0,
                    "watchers": 0,
                    "default_branch": "master"
                },
                "organization": {
                    "login": "Octocoders",
                    "id": 38302899,
                    "node_id": "MDEyOk9yZ2FuaXphdGlvbjM4MzAyODk5",
                    "url": "https://api.github.com/orgs/Octocoders",
                    "repos_url": "https://api.github.com/orgs/Octocoders/repos",
                    "events_url": "https://api.github.com/orgs/Octocoders/events",
                    "hooks_url": "https://api.github.com/orgs/Octocoders/hooks",
                    "issues_url": "https://api.github.com/orgs/Octocoders/issues",
                    "members_url": "https://api.github.com/orgs/Octocoders/members{/member}",
                    "public_members_url": "https://api.github.com/orgs/Octocoders/public_members{/member}",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/38302899?v=4",
                    "description": ""
                },
                "sender": {
                    "login": "Octocoders",
                    "id": 38302899,
                    "node_id": "MDEyOk9yZ2FuaXphdGlvbjM4MzAyODk5",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/38302899?v=4",
                    "gravatar_id": "",
                    "url": "https://api.github.com/users/Octocoders",
                    "html_url": "https://github.com/Octocoders",
                    "followers_url": "https://api.github.com/users/Octocoders/followers",
                    "following_url": "https://api.github.com/users/Octocoders/following{/other_user}",
                    "gists_url": "https://api.github.com/users/Octocoders/gists{/gist_id}",
                    "starred_url": "https://api.github.com/users/Octocoders/starred{/owner}{/repo}",
                    "subscriptions_url": "https://api.github.com/users/Octocoders/subscriptions",
                    "organizations_url": "https://api.github.com/users/Octocoders/orgs",
                    "repos_url": "https://api.github.com/users/Octocoders/repos",
                    "events_url": "https://api.github.com/users/Octocoders/events{/privacy}",
                    "received_events_url": "https://api.github.com/users/Octocoders/received_events",
                    "type": "Organization",
                    "site_admin": "false"
                },
            },
            "event": "membership",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd"
        }

        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        self.verify_org(message, result)
        assert result['source'] == 'membership'
        assert result['details']['team_name'] == message['body']['team']['name']
        assert result['details']['org_login'] == message['body']['organization']['login']
        assert result['summary'] == 'github: membership: removed team: github in org: Octocoders triggered by user: Octocoders'

    def test_public(self):
        message = {
            "body": {
                "repository": {
                    "id": 135493233,
                    "node_id": "MDEwOlJlcG9zaXRvcnkxMzU0OTMyMzM=",
                    "name": "Hello-World",
                    "full_name": "Codertocat/Hello-World",
                    "owner": {
                        "name": "ACrazyCat",
                        "login": "Codertocat",
                        "id": 21031067,
                        "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                        "avatar_url": "https://avatars1.githubusercontent.com/u/21031067?v=4",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/Codertocat",
                        "html_url": "https://github.com/Codertocat",
                        "followers_url": "https://api.github.com/users/Codertocat/followers",
                        "following_url": "https://api.github.com/users/Codertocat/following{/other_user}",
                        "gists_url": "https://api.github.com/users/Codertocat/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/Codertocat/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/Codertocat/subscriptions",
                        "organizations_url": "https://api.github.com/users/Codertocat/orgs",
                        "repos_url": "https://api.github.com/users/Codertocat/repos",
                        "events_url": "https://api.github.com/users/Codertocat/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/Codertocat/received_events",
                        "type": "User",
                        "site_admin": "false"
                    },
                    "private": "false",
                    "html_url": "https://github.com/Codertocat/Hello-World",
                    "description": "null",
                    "fork": "false",
                    "url": "https://api.github.com/repos/Codertocat/Hello-World",
                    "forks_url": "https://api.github.com/repos/Codertocat/Hello-World/forks",
                    "keys_url": "https://api.github.com/repos/Codertocat/Hello-World/keys{/key_id}",
                    "collaborators_url": "https://api.github.com/repos/Codertocat/Hello-World/collaborators{/collaborator}",
                    "teams_url": "https://api.github.com/repos/Codertocat/Hello-World/teams",
                    "hooks_url": "https://api.github.com/repos/Codertocat/Hello-World/hooks",
                    "issue_events_url": "https://api.github.com/repos/Codertocat/Hello-World/issues/events{/number}",
                    "events_url": "https://api.github.com/repos/Codertocat/Hello-World/events",
                    "assignees_url": "https://api.github.com/repos/Codertocat/Hello-World/assignees{/user}",
                    "branches_url": "https://api.github.com/repos/Codertocat/Hello-World/branches{/branch}",
                    "tags_url": "https://api.github.com/repos/Codertocat/Hello-World/tags",
                    "blobs_url": "https://api.github.com/repos/Codertocat/Hello-World/git/blobs{/sha}",
                    "git_tags_url": "https://api.github.com/repos/Codertocat/Hello-World/git/tags{/sha}",
                    "git_refs_url": "https://api.github.com/repos/Codertocat/Hello-World/git/refs{/sha}",
                    "trees_url": "https://api.github.com/repos/Codertocat/Hello-World/git/trees{/sha}",
                    "statuses_url": "https://api.github.com/repos/Codertocat/Hello-World/statuses/{sha}",
                    "languages_url": "https://api.github.com/repos/Codertocat/Hello-World/languages",
                    "stargazers_url": "https://api.github.com/repos/Codertocat/Hello-World/stargazers",
                    "contributors_url": "https://api.github.com/repos/Codertocat/Hello-World/contributors",
                    "subscribers_url": "https://api.github.com/repos/Codertocat/Hello-World/subscribers",
                    "subscription_url": "https://api.github.com/repos/Codertocat/Hello-World/subscription",
                    "commits_url": "https://api.github.com/repos/Codertocat/Hello-World/commits{/sha}",
                    "git_commits_url": "https://api.github.com/repos/Codertocat/Hello-World/git/commits{/sha}",
                    "comments_url": "https://api.github.com/repos/Codertocat/Hello-World/comments{/number}",
                    "issue_comment_url": "https://api.github.com/repos/Codertocat/Hello-World/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/Codertocat/Hello-World/contents/{+path}",
                    "compare_url": "https://api.github.com/repos/Codertocat/Hello-World/compare/{base}...{head}",
                    "merges_url": "https://api.github.com/repos/Codertocat/Hello-World/merges",
                    "archive_url": "https://api.github.com/repos/Codertocat/Hello-World/{archive_format}{/ref}",
                    "downloads_url": "https://api.github.com/repos/Codertocat/Hello-World/downloads",
                    "issues_url": "https://api.github.com/repos/Codertocat/Hello-World/issues{/number}",
                    "pulls_url": "https://api.github.com/repos/Codertocat/Hello-World/pulls{/number}",
                    "milestones_url": "https://api.github.com/repos/Codertocat/Hello-World/milestones{/number}",
                    "notifications_url": "https://api.github.com/repos/Codertocat/Hello-World/notifications{?since,all,participating}",
                    "labels_url": "https://api.github.com/repos/Codertocat/Hello-World/labels{/name}",
                    "releases_url": "https://api.github.com/repos/Codertocat/Hello-World/releases{/id}",
                    "deployments_url": "https://api.github.com/repos/Codertocat/Hello-World/deployments",
                    "created_at": "2018-05-30T20:18:04Z",
                    "updated_at": "2018-05-30T20:18:49Z",
                    "pushed_at": "2018-05-30T20:18:48Z",
                    "git_url": "git://github.com/Codertocat/Hello-World.git",
                    "ssh_url": "git@github.com:Codertocat/Hello-World.git",
                    "clone_url": "https://github.com/Codertocat/Hello-World.git",
                    "svn_url": "https://github.com/Codertocat/Hello-World",
                    "homepage": "null",
                    "size": "0",
                    "stargazers_count": "0",
                    "watchers_count": "0",
                    "language": "null",
                    "has_issues": "true",
                    "has_projects": "true",
                    "has_downloads": "true",
                    "has_wiki": "true",
                    "has_pages": "true",
                    "forks_count": "0",
                    "mirror_url": "null",
                    "archived": "false",
                    "open_issues_count": "2",
                    "license": "null",
                    "forks": "0",
                    "open_issues": "2",
                    "watchers": "0",
                    "default_branch": "master"
                },
                "sender": {
                    "login": "Codertocat",
                    "id": 21031067,
                    "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/21031067?v=4",
                    "gravatar_id": "",
                    "url": "https://api.github.com/users/Codertocat",
                    "html_url": "https://github.com/Codertocat",
                    "followers_url": "https://api.github.com/users/Codertocat/followers",
                    "following_url": "https://api.github.com/users/Codertocat/following{/other_user}",
                    "gists_url": "https://api.github.com/users/Codertocat/gists{/gist_id}",
                    "starred_url": "https://api.github.com/users/Codertocat/starred{/owner}{/repo}",
                    "subscriptions_url": "https://api.github.com/users/Codertocat/subscriptions",
                    "organizations_url": "https://api.github.com/users/Codertocat/orgs",
                    "repos_url": "https://api.github.com/users/Codertocat/repos",
                    "events_url": "https://api.github.com/users/Codertocat/events{/privacy}",
                    "received_events_url": "https://api.github.com/users/Codertocat/received_events",
                    "type": "User",
                    "site_admin": "false"
                },
            },
            "event": "public",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd",
        }
        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_repo(message, result)
        assert result['source'] == 'public'
        assert result['summary'] == 'github : change from private to public on repo: Hello-World triggered by user: Codertocat'

    def test_repository_import(self):
        message = {
            "body": {
                "status": "success",
                "repository": {
                    "id": 135493233,
                    "node_id": "MDEwOlJlcG9zaXRvcnkxMzU0OTMyMzM=",
                    "name": "Hello-World",
                    "full_name": "Codertocat/Hello-World",
                    "owner": {
                        "name": "ASuperCat",
                        "login": "Codertocat",
                        "id": 21031067,
                        "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                        "avatar_url": "https://avatars1.githubusercontent.com/u/21031067?v=4",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/Codertocat",
                        "html_url": "https://github.com/Codertocat",
                        "followers_url": "https://api.github.com/users/Codertocat/followers",
                        "following_url": "https://api.github.com/users/Codertocat/following{/other_user}",
                        "gists_url": "https://api.github.com/users/Codertocat/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/Codertocat/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/Codertocat/subscriptions",
                        "organizations_url": "https://api.github.com/users/Codertocat/orgs",
                        "repos_url": "https://api.github.com/users/Codertocat/repos",
                        "events_url": "https://api.github.com/users/Codertocat/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/Codertocat/received_events",
                        "type": "User",
                        "site_admin": "false"
                    },
                    "private": "false",
                    "html_url": "https://github.com/Codertocat/Hello-World",
                    "description": "null",
                    "fork": "false",
                    "url": "https://api.github.com/repos/Codertocat/Hello-World",
                    "forks_url": "https://api.github.com/repos/Codertocat/Hello-World/forks",
                    "keys_url": "https://api.github.com/repos/Codertocat/Hello-World/keys{/key_id}",
                    "collaborators_url": "https://api.github.com/repos/Codertocat/Hello-World/collaborators{/collaborator}",
                    "teams_url": "https://api.github.com/repos/Codertocat/Hello-World/teams",
                    "hooks_url": "https://api.github.com/repos/Codertocat/Hello-World/hooks",
                    "issue_events_url": "https://api.github.com/repos/Codertocat/Hello-World/issues/events{/number}",
                    "events_url": "https://api.github.com/repos/Codertocat/Hello-World/events",
                    "assignees_url": "https://api.github.com/repos/Codertocat/Hello-World/assignees{/user}",
                    "branches_url": "https://api.github.com/repos/Codertocat/Hello-World/branches{/branch}",
                    "tags_url": "https://api.github.com/repos/Codertocat/Hello-World/tags",
                    "blobs_url": "https://api.github.com/repos/Codertocat/Hello-World/git/blobs{/sha}",
                    "git_tags_url": "https://api.github.com/repos/Codertocat/Hello-World/git/tags{/sha}",
                    "git_refs_url": "https://api.github.com/repos/Codertocat/Hello-World/git/refs{/sha}",
                    "trees_url": "https://api.github.com/repos/Codertocat/Hello-World/git/trees{/sha}",
                    "statuses_url": "https://api.github.com/repos/Codertocat/Hello-World/statuses/{sha}",
                    "languages_url": "https://api.github.com/repos/Codertocat/Hello-World/languages",
                    "stargazers_url": "https://api.github.com/repos/Codertocat/Hello-World/stargazers",
                    "contributors_url": "https://api.github.com/repos/Codertocat/Hello-World/contributors",
                    "subscribers_url": "https://api.github.com/repos/Codertocat/Hello-World/subscribers",
                    "subscription_url": "https://api.github.com/repos/Codertocat/Hello-World/subscription",
                    "commits_url": "https://api.github.com/repos/Codertocat/Hello-World/commits{/sha}",
                    "git_commits_url": "https://api.github.com/repos/Codertocat/Hello-World/git/commits{/sha}",
                    "comments_url": "https://api.github.com/repos/Codertocat/Hello-World/comments{/number}",
                    "issue_comment_url": "https://api.github.com/repos/Codertocat/Hello-World/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/Codertocat/Hello-World/contents/{+path}",
                    "compare_url": "https://api.github.com/repos/Codertocat/Hello-World/compare/{base}...{head}",
                    "merges_url": "https://api.github.com/repos/Codertocat/Hello-World/merges",
                    "archive_url": "https://api.github.com/repos/Codertocat/Hello-World/{archive_format}{/ref}",
                    "downloads_url": "https://api.github.com/repos/Codertocat/Hello-World/downloads",
                    "issues_url": "https://api.github.com/repos/Codertocat/Hello-World/issues{/number}",
                    "pulls_url": "https://api.github.com/repos/Codertocat/Hello-World/pulls{/number}",
                    "milestones_url": "https://api.github.com/repos/Codertocat/Hello-World/milestones{/number}",
                    "notifications_url": "https://api.github.com/repos/Codertocat/Hello-World/notifications{?since,all,participating}",
                    "labels_url": "https://api.github.com/repos/Codertocat/Hello-World/labels{/name}",
                    "releases_url": "https://api.github.com/repos/Codertocat/Hello-World/releases{/id}",
                    "deployments_url": "https://api.github.com/repos/Codertocat/Hello-World/deployments",
                    "created_at": "2018-05-30T20:18:04Z",
                    "updated_at": "2018-05-30T20:18:49Z",
                    "pushed_at": "2018-05-30T20:18:48Z",
                    "git_url": "git://github.com/Codertocat/Hello-World.git",
                    "ssh_url": "git@github.com:Codertocat/Hello-World.git",
                    "clone_url": "https://github.com/Codertocat/Hello-World.git",
                    "svn_url": "https://github.com/Codertocat/Hello-World",
                    "homepage": "null",
                    "size": "0",
                    "stargazers_count": "0",
                    "watchers_count": "0",
                    "language": "null",
                    "has_issues": "true",
                    "has_projects": "true",
                    "has_downloads": "true",
                    "has_wiki": "true",
                    "has_pages": "true",
                    "forks_count": "0",
                    "mirror_url": "null",
                    "archived": "false",
                    "open_issues_count": "2",
                    "license": "null",
                    "forks": "0",
                    "open_issues": "2",
                    "watchers": "0",
                    "default_branch": "master"
                },
                "organization": {
                    "login": "Octocoders",
                    "id": 38302899,
                    "node_id": "MDEyOk9yZ2FuaXphdGlvbjM4MzAyODk5",
                    "url": "https://api.github.com/orgs/Octocoders",
                    "repos_url": "https://api.github.com/orgs/Octocoders/repos",
                    "events_url": "https://api.github.com/orgs/Octocoders/events",
                    "hooks_url": "https://api.github.com/orgs/Octocoders/hooks",
                    "issues_url": "https://api.github.com/orgs/Octocoders/issues",
                    "members_url": "https://api.github.com/orgs/Octocoders/members{/member}",
                    "public_members_url": "https://api.github.com/orgs/Octocoders/public_members{/member}",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/38302899?v=4",
                    "description": ""
                },
                "sender": {
                    "login": "Codertocat",
                    "id": 21031067,
                    "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/21031067?v=4",
                    "gravatar_id": "",
                    "url": "https://api.github.com/users/Codertocat",
                    "html_url": "https://github.com/Codertocat",
                    "followers_url": "https://api.github.com/users/Codertocat/followers",
                    "following_url": "https://api.github.com/users/Codertocat/following{/other_user}",
                    "gists_url": "https://api.github.com/users/Codertocat/gists{/gist_id}",
                    "starred_url": "https://api.github.com/users/Codertocat/starred{/owner}{/repo}",
                    "subscriptions_url": "https://api.github.com/users/Codertocat/subscriptions",
                    "organizations_url": "https://api.github.com/users/Codertocat/orgs",
                    "repos_url": "https://api.github.com/users/Codertocat/repos",
                    "events_url": "https://api.github.com/users/Codertocat/events{/privacy}",
                    "received_events_url": "https://api.github.com/users/Codertocat/received_events",
                    "type": "User",
                    "site_admin": "false"
                },
            },
            "event": "repository_import",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd",
        }

        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        self.verify_org(message, result)
        self.verify_repo(message, result)
        assert result['source'] == 'repository_import'
        assert result['summary'] == "github: repository_import: success on repo: Hello-World in org: Octocoders triggered by user: Codertocat"

    def test_release(self):
        message = {
            "body": {
                "action": "published",
                "release": {
                    "url": "https://api.github.com/repos/Codertocat/Hello-World/releases/11248810",
                    "assets_url": "https://api.github.com/repos/Codertocat/Hello-World/releases/11248810/assets",
                    "upload_url": "https://uploads.github.com/repos/Codertocat/Hello-World/releases/11248810/assets{?name,label}",
                    "html_url": "https://github.com/Codertocat/Hello-World/releases/tag/0.0.1",
                    "id": 11248810,
                    "node_id": "MDc6UmVsZWFzZTExMjQ4ODEw",
                    "tag_name": "0.0.1",
                    "target_commitish": "master",
                    "name": "null",
                    "draft": "false",
                    "author": {
                        "login": "Codertocat",
                        "id": 21031067,
                        "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                        "avatar_url": "https://avatars1.githubusercontent.com/u/21031067?v=4",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/Codertocat",
                        "html_url": "https://github.com/Codertocat",
                        "followers_url": "https://api.github.com/users/Codertocat/followers",
                        "following_url": "https://api.github.com/users/Codertocat/following{/other_user}",
                        "gists_url": "https://api.github.com/users/Codertocat/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/Codertocat/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/Codertocat/subscriptions",
                        "organizations_url": "https://api.github.com/users/Codertocat/orgs",
                        "repos_url": "https://api.github.com/users/Codertocat/repos",
                        "events_url": "https://api.github.com/users/Codertocat/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/Codertocat/received_events",
                        "type": "User",
                        "site_admin": "false"
                    },
                    "prerelease": "false",
                    "created_at": "2018-05-30T20:18:05Z",
                    "published_at": "2018-05-30T20:18:44Z",
                    "assets": [
                    ],
                    "tarball_url": "https://api.github.com/repos/Codertocat/Hello-World/tarball/0.0.1",
                    "zipball_url": "https://api.github.com/repos/Codertocat/Hello-World/zipball/0.0.1",
                    "body": "null"
                },
                "repository": {
                    "id": 135493233,
                    "node_id": "MDEwOlJlcG9zaXRvcnkxMzU0OTMyMzM=",
                    "name": "Hello-World",
                    "full_name": "Codertocat/Hello-World",
                    "owner": {
                        "name": "ASuperCat",
                        "login": "Codertocat",
                        "id": 21031067,
                        "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                        "avatar_url": "https://avatars1.githubusercontent.com/u/21031067?v=4",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/Codertocat",
                        "html_url": "https://github.com/Codertocat",
                        "followers_url": "https://api.github.com/users/Codertocat/followers",
                        "following_url": "https://api.github.com/users/Codertocat/following{/other_user}",
                        "gists_url": "https://api.github.com/users/Codertocat/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/Codertocat/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/Codertocat/subscriptions",
                        "organizations_url": "https://api.github.com/users/Codertocat/orgs",
                        "repos_url": "https://api.github.com/users/Codertocat/repos",
                        "events_url": "https://api.github.com/users/Codertocat/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/Codertocat/received_events",
                        "type": "User",
                        "site_admin": "false"
                    },
                    "private": "false",
                    "html_url": "https://github.com/Codertocat/Hello-World",
                    "description": "null",
                    "fork": "false",
                    "url": "https://api.github.com/repos/Codertocat/Hello-World",
                    "forks_url": "https://api.github.com/repos/Codertocat/Hello-World/forks",
                    "keys_url": "https://api.github.com/repos/Codertocat/Hello-World/keys{/key_id}",
                    "collaborators_url": "https://api.github.com/repos/Codertocat/Hello-World/collaborators{/collaborator}",
                    "teams_url": "https://api.github.com/repos/Codertocat/Hello-World/teams",
                    "hooks_url": "https://api.github.com/repos/Codertocat/Hello-World/hooks",
                    "issue_events_url": "https://api.github.com/repos/Codertocat/Hello-World/issues/events{/number}",
                    "events_url": "https://api.github.com/repos/Codertocat/Hello-World/events",
                    "assignees_url": "https://api.github.com/repos/Codertocat/Hello-World/assignees{/user}",
                    "branches_url": "https://api.github.com/repos/Codertocat/Hello-World/branches{/branch}",
                    "tags_url": "https://api.github.com/repos/Codertocat/Hello-World/tags",
                    "blobs_url": "https://api.github.com/repos/Codertocat/Hello-World/git/blobs{/sha}",
                    "git_tags_url": "https://api.github.com/repos/Codertocat/Hello-World/git/tags{/sha}",
                    "git_refs_url": "https://api.github.com/repos/Codertocat/Hello-World/git/refs{/sha}",
                    "trees_url": "https://api.github.com/repos/Codertocat/Hello-World/git/trees{/sha}",
                    "statuses_url": "https://api.github.com/repos/Codertocat/Hello-World/statuses/{sha}",
                    "languages_url": "https://api.github.com/repos/Codertocat/Hello-World/languages",
                    "stargazers_url": "https://api.github.com/repos/Codertocat/Hello-World/stargazers",
                    "contributors_url": "https://api.github.com/repos/Codertocat/Hello-World/contributors",
                    "subscribers_url": "https://api.github.com/repos/Codertocat/Hello-World/subscribers",
                    "subscription_url": "https://api.github.com/repos/Codertocat/Hello-World/subscription",
                    "commits_url": "https://api.github.com/repos/Codertocat/Hello-World/commits{/sha}",
                    "git_commits_url": "https://api.github.com/repos/Codertocat/Hello-World/git/commits{/sha}",
                    "comments_url": "https://api.github.com/repos/Codertocat/Hello-World/comments{/number}",
                    "issue_comment_url": "https://api.github.com/repos/Codertocat/Hello-World/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/Codertocat/Hello-World/contents/{+path}",
                    "compare_url": "https://api.github.com/repos/Codertocat/Hello-World/compare/{base}...{head}",
                    "merges_url": "https://api.github.com/repos/Codertocat/Hello-World/merges",
                    "archive_url": "https://api.github.com/repos/Codertocat/Hello-World/{archive_format}{/ref}",
                    "downloads_url": "https://api.github.com/repos/Codertocat/Hello-World/downloads",
                    "issues_url": "https://api.github.com/repos/Codertocat/Hello-World/issues{/number}",
                    "pulls_url": "https://api.github.com/repos/Codertocat/Hello-World/pulls{/number}",
                    "milestones_url": "https://api.github.com/repos/Codertocat/Hello-World/milestones{/number}",
                    "notifications_url": "https://api.github.com/repos/Codertocat/Hello-World/notifications{?since,all,participating}",
                    "labels_url": "https://api.github.com/repos/Codertocat/Hello-World/labels{/name}",
                    "releases_url": "https://api.github.com/repos/Codertocat/Hello-World/releases{/id}",
                    "deployments_url": "https://api.github.com/repos/Codertocat/Hello-World/deployments",
                    "created_at": "2018-05-30T20:18:04Z",
                    "updated_at": "2018-05-30T20:18:49Z",
                    "pushed_at": "2018-05-30T20:18:48Z",
                    "git_url": "git://github.com/Codertocat/Hello-World.git",
                    "ssh_url": "git@github.com:Codertocat/Hello-World.git",
                    "clone_url": "https://github.com/Codertocat/Hello-World.git",
                    "svn_url": "https://github.com/Codertocat/Hello-World",
                    "homepage": "null",
                    "size": "0",
                    "stargazers_count": "0",
                    "watchers_count": "0",
                    "language": "null",
                    "has_issues": "true",
                    "has_projects": "true",
                    "has_downloads": "true",
                    "has_wiki": "true",
                    "has_pages": "true",
                    "forks_count": "0",
                    "mirror_url": "null",
                    "archived": "false",
                    "open_issues_count": "2",
                    "license": "null",
                    "forks": "0",
                    "open_issues": "2",
                    "watchers": "0",
                    "default_branch": "master"
                },
                "organization": {
                    "login": "Octocoders",
                    "id": 38302899,
                    "node_id": "MDEyOk9yZ2FuaXphdGlvbjM4MzAyODk5",
                    "url": "https://api.github.com/orgs/Octocoders",
                    "repos_url": "https://api.github.com/orgs/Octocoders/repos",
                    "events_url": "https://api.github.com/orgs/Octocoders/events",
                    "hooks_url": "https://api.github.com/orgs/Octocoders/hooks",
                    "issues_url": "https://api.github.com/orgs/Octocoders/issues",
                    "members_url": "https://api.github.com/orgs/Octocoders/members{/member}",
                    "public_members_url": "https://api.github.com/orgs/Octocoders/public_members{/member}",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/38302899?v=4",
                    "description": ""
                },
                "sender": {
                    "login": "Codertocat",
                    "id": 21031067,
                    "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/21031067?v=4",
                    "gravatar_id": "",
                    "url": "https://api.github.com/users/Codertocat",
                    "html_url": "https://github.com/Codertocat",
                    "followers_url": "https://api.github.com/users/Codertocat/followers",
                    "following_url": "https://api.github.com/users/Codertocat/following{/other_user}",
                    "gists_url": "https://api.github.com/users/Codertocat/gists{/gist_id}",
                    "starred_url": "https://api.github.com/users/Codertocat/starred{/owner}{/repo}",
                    "subscriptions_url": "https://api.github.com/users/Codertocat/subscriptions",
                    "organizations_url": "https://api.github.com/users/Codertocat/orgs",
                    "repos_url": "https://api.github.com/users/Codertocat/repos",
                    "events_url": "https://api.github.com/users/Codertocat/events{/privacy}",
                    "received_events_url": "https://api.github.com/users/Codertocat/received_events",
                    "type": "User",
                    "site_admin": "false"
                },
            },
            "event": "release",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd",
        }
        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        self.verify_repo(message, result)
        assert result['source'] == 'release'
        assert result['details']['release_author_login'] == message['body']['release']['author']['login']
        assert result['details']['release_author_id'] == message['body']['release']['author']['id']
        assert result['details']['release_author_node_id'] == message['body']['release']['author']['node_id']
        assert result['details']['release_author_type'] == message['body']['release']['author']['type']
        assert result['details']['release_author_site_admin'] == message['body']['release']['author']['site_admin']
        assert result['summary'] == 'github: release: published on repo: Hello-World triggered by user: Codertocat'

    def test_org_block(self):
        message = {
            "body": {
                "action": "blocked",
                "blocked_user": {
                    "login": "hacktocat",
                    "id": 39652351,
                    "node_id": "MDQ6VXNlcjM5NjUyMzUx",
                    "avatar_url": "https://avatars2.githubusercontent.com/u/39652351?v=4",
                    "gravatar_id": "",
                    "url": "https://api.github.com/users/hacktocat",
                    "html_url": "https://github.com/hacktocat",
                    "followers_url": "https://api.github.com/users/hacktocat/followers",
                    "following_url": "https://api.github.com/users/hacktocat/following{/other_user}",
                    "gists_url": "https://api.github.com/users/hacktocat/gists{/gist_id}",
                    "starred_url": "https://api.github.com/users/hacktocat/starred{/owner}{/repo}",
                    "subscriptions_url": "https://api.github.com/users/hacktocat/subscriptions",
                    "organizations_url": "https://api.github.com/users/hacktocat/orgs",
                    "repos_url": "https://api.github.com/users/hacktocat/repos",
                    "events_url": "https://api.github.com/users/hacktocat/events{/privacy}",
                    "received_events_url": "https://api.github.com/users/hacktocat/received_events",
                    "type": "User",
                    "site_admin": "false"
                },
                "organization": {
                    "login": "Octocoders",
                    "id": 38302899,
                    "node_id": "MDEyOk9yZ2FuaXphdGlvbjM4MzAyODk5",
                    "url": "https://api.github.com/orgs/Octocoders",
                    "repos_url": "https://api.github.com/orgs/Octocoders/repos",
                    "events_url": "https://api.github.com/orgs/Octocoders/events",
                    "hooks_url": "https://api.github.com/orgs/Octocoders/hooks",
                    "issues_url": "https://api.github.com/orgs/Octocoders/issues",
                    "members_url": "https://api.github.com/orgs/Octocoders/members{/member}",
                    "public_members_url": "https://api.github.com/orgs/Octocoders/public_members{/member}",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/38302899?v=4",
                    "description": ""
                },
                "sender": {
                    "login": "Codertocat",
                    "id": 21031067,
                    "node_id": "MDQ6VXNlcjIxMDMxMDY3",
                    "avatar_url": "https://avatars1.githubusercontent.com/u/21031067?v=4",
                    "gravatar_id": "",
                    "url": "https://api.github.com/users/Codertocat",
                    "html_url": "https://github.com/Codertocat",
                    "followers_url": "https://api.github.com/users/Codertocat/followers",
                    "following_url": "https://api.github.com/users/Codertocat/following{/other_user}",
                    "gists_url": "https://api.github.com/users/Codertocat/gists{/gist_id}",
                    "starred_url": "https://api.github.com/users/Codertocat/starred{/owner}{/repo}",
                    "subscriptions_url": "https://api.github.com/users/Codertocat/subscriptions",
                    "organizations_url": "https://api.github.com/users/Codertocat/orgs",
                    "repos_url": "https://api.github.com/users/Codertocat/repos",
                    "events_url": "https://api.github.com/users/Codertocat/events{/privacy}",
                    "received_events_url": "https://api.github.com/users/Codertocat/received_events",
                    "type": "User",
                    "site_admin": "false"
                },
            },
            "event": "org_block",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd",
        }
        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        assert result['source'] == 'org_block'
        assert result['details']['blocked_user_login'] == message['body']['blocked_user']['login']
        assert result['details']['blocked_user_id'] == message['body']['blocked_user']['id']
        assert result['details']['blocked_user_node_id'] == message['body']['blocked_user']['node_id']
        assert result['summary'] == 'github: org_block: blocked user: hacktocat in org: Octocoders triggered by user: Codertocat'

    def test_installation(self):
        message = {
            "body": {
                "action": "deleted",
                "installation": {
                    "id": 2,
                    "account": {
                        "login": "octocat",
                        "id": 1,
                        "node_id": "MDQ6VXNlcjE=",
                        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/octocat",
                        "html_url": "https://github.com/octocat",
                        "followers_url": "https://api.github.com/users/octocat/followers",
                        "following_url": "https://api.github.com/users/octocat/following{/other_user}",
                        "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
                        "organizations_url": "https://api.github.com/users/octocat/orgs",
                        "repos_url": "https://api.github.com/users/octocat/repos",
                        "events_url": "https://api.github.com/users/octocat/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/octocat/received_events",
                        "type": "User",
                        "site_admin": "false"
                    },
                    "repository_selection": "selected",
                    "access_tokens_url": "https://api.github.com/installations/2/access_tokens",
                    "repositories_url": "https://api.github.com/installation/repositories",
                    "html_url": "https://github.com/settings/installations/2",
                    "app_id": "5725",
                    "target_id": "3880403",
                    "target_type": "User",
                    "permissions": {
                        "metadata": "read",
                        "contents": "read",
                        "issues": "write"
                    },
                    "events": [
                        "push",
                        "pull_request"
                    ],
                    "created_at": "1525109898",
                    "updated_at": "1525109899",
                    "single_file_name": "config.yml"
                },
                "repositories": [
                    {
                        "id": "1296269",
                        "name": "Hello-World",
                        "full_name": "octocat/Hello-World",
                        "private": "false"
                    }
                ],
                "sender": {
                    "login": "octocat",
                    "id": 1,
                    "node_id": "MDQ6VXNlcjE=",
                    "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                    "gravatar_id": "",
                    "url": "https://api.github.com/users/octocat",
                    "html_url": "https://github.com/octocat",
                    "followers_url": "https://api.github.com/users/octocat/followers",
                    "following_url": "https://api.github.com/users/octocat/following{/other_user}",
                    "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
                    "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
                    "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
                    "organizations_url": "https://api.github.com/users/octocat/orgs",
                    "repos_url": "https://api.github.com/users/octocat/repos",
                    "events_url": "https://api.github.com/users/octocat/events{/privacy}",
                    "received_events_url": "https://api.github.com/users/octocat/received_events",
                    "type": "User",
                    "site_admin": "false"
                },
            },
            "event": "installation",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd",
        }
        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        assert result['source'] == 'installation'
        assert result['details']['action'] == message['body']['action']
        assert result['details']['install_id'] == message['body']['installation']['account']['id']
        assert result['details']['install_account_login'] == message['body']['installation']['account']['login']
        assert result['details']['install_account_node_id'] == message['body']['installation']['account']['node_id']
        assert result['details']['install_account_type'] == message['body']['installation']['account']['type']
        assert result['details']['install_account_site_admin'] == message['body']['installation']['account']['site_admin']
        assert result['summary'] == 'github app: installation deleted triggered by user: octocat'

    def test_installation_perms_accepted(self):
        message = {
            "body": {
                "action": "new_permissions_accepted",
                "installation": {
                    "id": "2",
                    "account": {
                        "login": "octocat",
                        "id": 1,
                        "node_id": "MDQ6VXNlcjE=",
                        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/octocat",
                        "html_url": "https://github.com/octocat",
                        "followers_url": "https://api.github.com/users/octocat/followers",
                        "following_url": "https://api.github.com/users/octocat/following{/other_user}",
                        "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
                        "organizations_url": "https://api.github.com/users/octocat/orgs",
                        "repos_url": "https://api.github.com/users/octocat/repos",
                        "events_url": "https://api.github.com/users/octocat/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/octocat/received_events",
                        "type": "User",
                        "site_admin": "false"
                    },
                    "repository_selection": "selected",
                    "access_tokens_url": "https://api.github.com/installations/2/access_tokens",
                    "repositories_url": "https://api.github.com/installation/repositories",
                    "html_url": "https://github.com/settings/installations/2",
                    "app_id": "5725",
                    "target_id": "3880403",
                    "target_type": "User",
                    "permissions": {
                        "metadata": "read",
                        "contents": "read",
                        "issues": "write"
                    },
                    "events": [
                        "push",
                        "pull_request"
                    ],
                    "created_at": "1525109898",
                    "updated_at": "1525109899",
                    "single_file_name": "config.yml"
                },
                "repositories": [
                    {
                        "id": "1296269",
                        "name": "Hello-World",
                        "full_name": "octocat/Hello-World",
                        "private": "false"
                    }
                ],
                "sender": {
                    "login": "octocat",
                    "id": "1",
                    "node_id": "MDQ6VXNlcjE=",
                    "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                    "gravatar_id": "",
                    "url": "https://api.github.com/users/octocat",
                    "html_url": "https://github.com/octocat",
                    "followers_url": "https://api.github.com/users/octocat/followers",
                    "following_url": "https://api.github.com/users/octocat/following{/other_user}",
                    "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
                    "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
                    "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
                    "organizations_url": "https://api.github.com/users/octocat/orgs",
                    "repos_url": "https://api.github.com/users/octocat/repos",
                    "events_url": "https://api.github.com/users/octocat/events{/privacy}",
                    "received_events_url": "https://api.github.com/users/octocat/received_events",
                    "type": "User",
                    "site_admin": "false"
                },
            },
            "event": "installation",
            "request_id": "94e70998-dd79-11e8-9ba0-a8635445a8cd",
        }
        event = {
            'tags': 'githubeventsqs'
        }
        event['details'] = message
        result, metadata = self.plugin.onMessage(event, self.metadata)
        self.verify_defaults(result)
        self.verify_metadata(metadata)
        self.verify_meta(message, result)
        self.verify_actor(message, result)
        assert result['source'] == 'installation'
        assert result['details']['action'] == message['body']['action']
        assert result['details']['install_id'] == message['body']['installation']['account']['id']
        assert result['details']['install_account_login'] == message['body']['installation']['account']['login']
        assert result['details']['install_account_node_id'] == message['body']['installation']['account']['node_id']
        assert result['details']['install_account_type'] == message['body']['installation']['account']['type']
        assert result['details']['install_account_site_admin'] == message['body']['installation']['account']['site_admin']
        assert result['summary'] == 'github app: installation new_permissions_accepted triggered by user: octocat'
