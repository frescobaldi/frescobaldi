# Test file to test and demonstrate the API for the vcs module.

import app
import vcs

print 'Debugging the git module'
print 'List of remotes:'
print app.repo.remotes()
print 'List of branches (local):'
print app.repo.branches()
print 'List of branches(incl. remotes):'
print app.repo.branches(False)
print
print 'List of branches with tracked remotes:'
for branch in app.repo.branches():
    print branch, app.repo.tracked_remote_label(branch.lstrip('* '))
print 'Current branch:'
print app.repo.current_branch()
if app.repo.has_branch('master'):
    if app.repo.has_remote_branch('master'):
        remote, rem_branch = app.repo.tracked_remote('master')
        print 'master has remote: ', remote, rem_branch
    else:
        print 'master doesn\'t have a remote branch'
print 'has remote dummy:', app.repo.has_remote('dummy')
print 'has remote origin:', app.repo.has_remote('origin')
print 'has remote upstream:', app.repo.has_remote('upstream')

upstream = app.repo.upstream_remote()
print
print 'remote tracking the official repo:', upstream
print 'URL:', app.repo.config['remote'][upstream]['url']
