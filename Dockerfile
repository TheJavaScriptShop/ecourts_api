# To enable ssh & remote debugging on app service change the base image to the one below
# FROM mcr.microsoft.com/azure-functions/python:4-python3.9-appservice
FROM mcr.microsoft.com/azure-functions/python:4-python3.9

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools

# 0. Install essential packages
RUN apt-get update \
    && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    unzip \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update; \
    apt-get -y upgrade; \
    apt-get install -y gnupg2 wget lsb-release
RUN apt-get remove libpq5
RUN apt-get install libpq-dev
RUN apt-get install postgresql-dev

COPY requirements.txt /
RUN pip install -r /requirements.txt

# 1. Install Chrome (root image is debian)
# See https://stackoverflow.com/questions/49132615/installing-chrome-in-docker-file
ARG CHROME_VERSION="google-chrome-stable"
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update -qqy \
        && apt-get -qqy install \
    ${CHROME_VERSION:-google-chrome-stable} \
    && rm /etc/apt/sources.list.d/google-chrome.list \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# 2. Install Chrome driver used by Selenium
RUN LATEST=$(wget -q -O - http://chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget http://chromedriver.storage.googleapis.com/$LATEST/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && ln -s $PWD/chromedriver /usr/local/bin/chromedriver

ENV PATH="/usr/local/bin/chromedriver:${PATH}"

# 3. Install selenium in Python
RUN pip install -U selenium

# 4. Finally, copy python code to image
COPY . /home/site/wwwroot

# 5. Install other packages in requirements.txt
RUN cd /home/site/wwwroot && \
    pip install -r requirements.txt