Debugger/Live Script Editor for Sublime Text 2
=====

*Debug from Sublime Text 2*

1. **Make it work**
2. Make it stable
3. Make it fast
4. Make it pretty

Aims
-----
This package aims to add the following functionality to Sublime Text 2:

a) provide common, basic debugging interface with adapters for:

a-1) javascript running in google chrome (chromeconnector) - partially working

a-2) javascript running in a node process (v8connector) - barely working

a-3) python & others (maybe)

b) allow live editing of javascript running in Google Chrome


Usage
----
- Install plugin package in the usual manner
- Start Chrome with the argument  --remote-debugging-port=9222
- Add the website folder to SublimeText - Project > Add Folder to Project
- ctrl + shift + c to connect the project folder to the instance of Chrome


Breakpoint Navigation
---
- ctrl + shift + t to toggle a breakpoint at the current line
- f8 to resume from a pause
- f10 to 'step over'
- f11 to 'step into'
- shift+f11 to 'step out'


Notes
-----
- This will most likely error if and when you try and use it.
- chromeconnector is very shabby
- v8connector (based on twisted) could be more promising