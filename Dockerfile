FROM python:3.11-slim
RUN apt-get update || : && apt-get install python3.11 -y
#RUN apt-get install python-pip -y
RUN apt-get install -y python-dev-is-python3

ENV PYTHONUNBUFFERED=True

# If running in Docker you will need to tell Flask what domain and port you are connecting with
#ENV DOMAIN=imws.ngrok.io
#ENV PORT=443

#ENV DOMAIN=localhost
#ENV PORT=55000

ENV DOMAIN=box-lti-fs2l2gquzq-uc.a.run.app/
ENV PORT=8080

RUN mkdir /app
WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN python ./keys/build_config.py
ENV PYTHONPATH "${PYTHONPATH}:./app"
EXPOSE $PORT
ENTRYPOINT ["./scripts/entrypoint.sh"]
ENTRYPOINT ["gunicorn", "--config", "gunicorn_config.py", "wsgi:app"]