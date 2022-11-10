# To enable ssh & remote debugging on app service change the base image to the one below
# FROM mcr.microsoft.com/azure-functions/python:4-python3.9-appservice
FROM mcr.microsoft.com/azure-functions/python:4-python3.9

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip3 install --upgrade pip

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

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

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
    wget http://chromedriver.storage.googleapis.com/107.0.5304.62/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && ln -s $PWD/chromedriver /usr/local/bin/chromedriver

ENV PATH="/usr/local/bin/chromedriver:${PATH}"

# 3. Install selenium in Python
RUN pip install -U selenium


# 4. Finally, copy python code to image
COPY . /home/site/wwwroot

WORKDIR /home/site/wwwroot
EXPOSE 3000 80 443 22

CMD ["gunicorn", "--workers", "4", "--timeout", "3600", "--capture-output", "--bind", "0.0.0.0:80", "-m", "007", "wsgi:application", "--reload"]
