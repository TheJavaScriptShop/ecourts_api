# Use virtual env

Python version 3.9

## Installation
To install virtualenv run:
pip3 install virtualenv

## Usage
cd ecourts_api/
virtualenv venv

These commands create a venv/ directory in your project where all dependencies are installed. You need to activate it first though (in every terminal instance where you are working on your project):

source venv/bin/activate

You should see a (venv) appear at the beginning of your terminal prompt indicating that you are working inside the virtualenv. Now when you install something like this:

pip3 install -r requirements.txt 

It will get installed in the venv/ folder, and not conflict with other projects.

## To leave the virtual environment run:

deactivate

Important: Remember to add venv to your project's .gitignore file so you don't include all of that in your source code.

