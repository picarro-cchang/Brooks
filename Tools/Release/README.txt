1. Run newReleaseStep1.bat and newReleaseStep2.bat for the very first time to create new branches in repository

2. Verify "C:\Python25\Lib\site-packages\Picarro.pth" before making new .exe package

3. Make .exe package by running "makeExe.bat" and copy host exe (dist) to R drive

4. Modify the new version number and release branch in: tagOnly.bat, makeConfig.bat, compInstallers.bat and all the .iss files

5. Update the config files on S drive before compiling installers: "makeConfig.bat"

6. (Optional) Update the local config files: "pullConfig.bat"

7. (Optional) Tag the most current version on each branch: "tagOnly.bat"

8. Compile all the installers: "compInstallers.bat"

9. After relase, run "afterRelease.bat" to update the parent repository in C