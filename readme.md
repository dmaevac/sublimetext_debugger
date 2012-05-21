Chrome Developer Tools Sublime Text Plugin
=====

*Live edit and debug javascript from Sublime Text 2*

*STILL IN DEVELOPMENT*

1. Make it work     <-- We are here!
2. Make it stable
3. Make it fast
4. Make it pretty


Aims
=====

This package aims to add the following functionality to Sublime Text 2:

a) allow live editing of javascript running in Google Chrome

b) provide basic debugging funtionality


Usage
=====

- Install plugin package in the usual manner
- ctrl + shift + c to connect a project foler to an instance of Chrome
(Chrome must have been started with the argument  --remote-debugging-port=9222 )
- ctrl + shift + t to toggle a breakpoint at the current line
- f8 to resume from a pause
- f10 to 'step over'

- When save is triggered the script is replaced live inside the browser (no need to refresh!)
