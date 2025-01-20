# Test file to test and demonstrate the API for the vcs module.



from vcs import app_repo

print('Debugging the git module')
print('List of remotes:')
print(app_repo.remotes())
print('List of branches (local):')
print(app_repo.branches())
print('List of branches(incl. remotes):')
print(app_repo.branches(False))
print()
print('List of branches with tracked remotes:')
for branch in app_repo.branches():
    print(branch, app_repo.tracked_remote_label(branch))
print('Current branch:')
print(app_repo.current_branch())
if app_repo.has_branch('master'):
    if app_repo.has_remote_branch('master'):
        remote, rem_branch = app_repo.tracked_remote('master')
        print('master has remote: ', remote, rem_branch)
    else:
        print('master doesn\'t have a remote branch')
print('has remote dummy:', app_repo.has_remote('dummy'))
print('has remote origin:', app_repo.has_remote('origin'))
print('has remote upstream:', app_repo.has_remote('upstream'))
