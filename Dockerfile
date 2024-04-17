FROM python:3.9.2
RUN apt-get update || : && apt-get install python -y
RUN apt-get install -y python-dev

ENV PYTHONUNBUFFERED=1

# If running in Docker you will need to tell Flask what domain and port you are connecting with
#ENV DOMAIN=imws.ngrok.io
#ENV PORT=443

ENV DOMAIN=localhost
ENV PORT=55000

RUN mkdir /app
WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN python /app/keys/build_config.py
ENV PYTHONPATH "${PYTHONPATH}:./app"
EXPOSE 55000
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
ENTRYPOINT ["gunicorn", "--config", "gunicorn_config.py", "wsgi:app"]