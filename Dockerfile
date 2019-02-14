FROM python:3.6

MAINTAINER hongjoo.lee@glowmee.com

WORKDIR /usr/src/app

RUN pip install --upgrade pip
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN mkdir -p /var/log/uwsgi
# to be removed with revising common.py
RUN mkdir -p /app/logs

RUN python manage.py collectstatic --no-input
EXPOSE 8000
#ENTRYPOINT ["uwsgi", "--ini", "/usr/src/app/backends/api/wsgi.ini"]
