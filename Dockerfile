FROM python:alpine3.6
WORKDIR /usr/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN adduser -u 1000 -D -h /usr/app -s /sbin/nologin app && \
    chmod 755 /usr/app
USER app
ENV PYTHONPATH $PYTHONPATH:/usr/src/app
CMD [ "python", "./server/cleanup/remove_old_tags.py" ]
#CMD [ "python"]
