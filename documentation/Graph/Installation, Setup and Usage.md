# Blazegraph Installation
Here are the most important sources for installing Blazegraph on your machine:
- Installation Guide (including Java info): https://github.com/blazegraph/database/wiki/Installation_guide
- Quickstart for Blazegraph: https://github.com/blazegraph/database/wiki/Quick_Start
- Using Blazegraph in Python: https://github.com/blazegraph/blazegraph-python 
- If you have already completed the "Installation, Setup and Usage" guide for the python code project, then you should not be required to do any more actions in terms of using Blazegraph and Python together, because every necessary package should already be installed.

For more information see also:
- https://blazegraph.com/
- https://github.com/blazegraph/database

# Using Blazegraph for this Project:
- After succesfully installing (and testing) Blazegraph you can use the "start-blazegraph-server.bat" to start the server. You have to start the server before opening the project and especially before running the application.
- after running the bat-file or this command 'java -server -Xmx4g -jar D:\Programme\Blazegraph\blazegraph.jar' in the Windows CMD you will see "Go to http://192.168.2.100:9999/blazegraph/ to get started." (or a similar address) in your console. Copy the address and safe it in an environment variable named "Blazegraph_Address"
- in a second environment variable named "Graph_File" safe the path where you put your "Eich-created.ttl" file. This could f.e. be next to the main.exe file. The Path should look something like this "D:/Your/Path/Eich-Created.ttl"
