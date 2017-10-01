# Contributing to RocketMap

## Table Of Contents

[I just have a question/need help](#i-just-have-a-questionneed-help)

[Project Managers](#project-managers)

[How do I get started?](#how-do-i-get-started)
* [Python Packages](#python-packages)
* [NodeJS Packages](#nodejs-packages)

[Reporting code issues](#reporting-code-issues)
* [Before you report](#before-you-report)
* [Submitting a helpful bug report](#submitting-a-helpful-bug-report)

[Contributing Code](#contributing-code)
* [Basic Knowledge](#basic-knowledge)
* [Styleguides](#styleguides)
* [Submitting a helpful pull request](#submitting-a-helpful-pull-request)
* [Collaborating with other contributors](#collaborating-with-other-contributors)
* [Third Party Applications](#third-party-applications)

## I just have a question/need help.

Please do not open a GitHub issue for support or questions. They are best answered via [Discord](https://discord.gg/RocketMap). GitHub issues are for RocketMap code issues *only*.

## Project Managers

Management of the RocketMap project is handled by Seb ([@sebastienvercammen](https://github.com/sebastienvercammen)) and Thunderfox ([@FrostTheFox](https://github.com/FrostTheFox)) and can be reached via [Discord](https://discord.gg/RocketMap) should there be any questions regarding the contribution guidelines or RocketMap development.

## How do I get started?

RocketMap has two main dependencies to get started:

1. RocketMap is a Python2 project, therefore, you need [Python 2](https://www.python.org/downloads/)!
2. RocketMap also requires [NodeJS](https://nodejs.org/en/download/) in order to build frontend assets.

### Python Packages

All the required packages to operate RocketMap are found in requirements.txt in the project root, and can easily be installed by executing `pip install --upgrade -r requirements.txt`.

### NodeJS Packages

NodeJS packages are found in package.json in the project root, and can be easily installed by simply executing `npm install`.

## Reporting code issues

### Before you report

1. **Make sure you are on the latest version!** When in doubt, `git pull`.
2. Ensure it is an actual issue with the project itself. Confirm that you do not have a faulty config, and that you have properly installed all the required dependencies. ***READ THE ERROR OUTPUT YOU ARE GIVEN!*** It may have the solution readily printed for you!
3. Reproduce. Confirm the circumstances required to reproduce the bug. If specific configuration is required, include the required configuration in your report. Find a friend, spin up a virtual machine or use a different computer and test the issue there. If you do not have the issue on the new machine, it may be indicative that something is wrong with your configuration.
4. *USE GITHUB SEARCH.* Search open issues and look for any open issues that already address the problem. Duplicate issues will be closed.

### Submitting a helpful bug report

When you begin the process of opening an issue, you will be given a template in the text box that should help guide you through the process. Please fill in as much detail as you can.

* **Expected Behavior** - What did you expect to happen? Should the map have handled an exception, or have done something different?
* **Current Behavior** - What actually happened? Did the map crash? Did a function behave in a way it was not intended? Include any logs or stack traces here.
* **Possible Solution** - If you know how this issue is caused and have a possible solution, please include it.
* **Steps to reproduce** - Here is where your “Reproduce” stage comes in. Provide the specific configuration that you used. Frontend issue? Provide instructions on what to click or do on the frontend to cause the issue.
* **Context** - Why is this an issue?
* **Your environment** - Operating system, `python --version`, `pip --version`, etc.

If you are asked for more details, *please provide details*. Any issues not following the above layout or that is not detailed enough to determine the issue may be subject to closure.

## Contributing code

### Basic Knowledge

To contribute code to RocketMap, it is heavily advised that you are knowledgeable in Git. At a minimum, you should know how to commit, push, pull and do basic rebasing.

### Styleguides

RocketMap follows and adheres to the [pep8 standards](https://www.python.org/dev/peps/pep-0008/) for Python code, and has established rules for JavaScript in the .eslintrc.json file in the project root. Automatic checks of these standards are performed when pull requests are opened, however you can save some time by running these checks on your local machine. 

To check if your Python code conforms to PEP8, you can use the flake8 package (`pip install flake8`). After making changes, open a terminal in the project root and run `flake8 --statistics --show-source --disable-noqa`.

To check if your JavaScript code conforms to the eslint rules, you can run `npm run lint`.

### Submitting a helpful pull request

* **Description** - Describe in detail the changes you made. If you add or remove specific libraries, frameworks, etc, please list the specific frameworks. Any movements between files, e.g. moving code from runserver.py to utils.py, should be noted as such.
* **Motivation and Context** - What’s the need for this change? What issue does it solve? If there’s an open issue, please write this exact phrase: “Fixes #prnumber” This will automatically close the issue when the pull request is merged.
* **How has this been tested?** - Please include the details of your test. Scan area, configuration, operating system, python version, any other relevant details.
* **Screenshots** - If you have made frontend changes, screenshots are highly advised to give context.
* **Types of changes & Checklist** - Please put a x in boxes that apply. Make sure it looks like [x], instead of [x ] or [ x], so you get a nice checkbox.

### Collaborating with other contributors

When you have an open pull request and wish to collaborate with other contributors, you may request access to the #pr channel in the [RocketMap Discord](https://discord.gg/rocketmap). To request access, you may send a message to Seb or Thunderfox. Please provide a link to your open pull request with your message.

### Third Party Applications

We welcome third parties to create tools to extend the functionality and user experience of RocketMap (e.g. mobile clients, extended platforms like [PokéAlarm](https://github.com/RocketMap/PokeAlarm)), provided they follow the 3rd party project policies:

* 3rd party projects that wish to use RocketMap or any RM-hosted websites need to contact the RM project managers before release of their tool in order to be approved. We love innovation and improvement of RM, but we need to protect the interests of the RM community. If your project isn't doing anything shady and isn't violating the privacy of others, you'll likely be approved without hassle.
* Any 3rd party project that uses RM users' websites needs to be opt-in for the website's owner. Any website that hasn't explicitly opted in should be blocked in your project. In exchange for your cooperation, and to help with growth, RM-approved projects may receive their own Thunderbot command (e.g. !pokealarm), have your GitHub link excluded from link filtering, and receive a "3rd party" role in the [RM Discord](https://discord.gg/RocketMap). A common way of adding an opt-in is to host a file *"myProjectName.txt"* similar to [robots.txt](http://www.robotstxt.org/) that explicitly allows the website to be used in the project.
* Unapproved projects will not be supported on RM's Discord and links to the project will automatically be removed. 
* Projects that do not provide an opt-in method (where applicable) may find themselves blocked from all RM instances at discretion of the project managers.
