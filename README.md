This is the official dev/build/release repository for all Linux based I2000
analyzers starting with Rev. C (aka Kirchoff).  Rev. B with DCRDS and earlier
still reside in the repository picarro/host.

When cloning this repository you may find that some development and build
scripts don't work because they are assuming the path /home/picarro/git/host
is the location of the source code whereas a free clone will put the code
in /home/picarro/git/I2000-Host.  To fix this do one of the following:

* Change the path of the script.
* Make a softlink of I2000-Host to host.
* Clone with "git clone http://github.com/picarro/I2000-Host.git host.

Project Administration:

* We are using the formal branching model described here: https://nvie.com/posts/a-successful-git-branching-model/
* Do your work on a topic branch off of the main develop branch.
* Commit with meaningful messages.  If the commit fixes a bug already logged in Jira, put the issue number in the first line of the commit message. Use this write up as a guide https://chris.beams.io/posts/git-commit/ as well as the Jira guidelines.
* Use pull-requests to merge your topic branch back into develop.
* Before issuing a pull-request, pull and merge any recent changes in develop and make sure the code in your branch works!
* After a pull-request is accepted and merged delete the topic branch from the repo.  The repo should only contain active branches and fixed releases.

The only persons currently allowed to commit to this repo are 
* Chetan Vala
* Gerald Sornsen
* Patrick Pittier (administrator)
* Petr Khromov
