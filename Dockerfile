FROM python:3
WORKDIR /app
RUN pip install pipenv
ADD Pipfile Pipfile.lock /app/
RUN pipenv install
ADD . /app
CMD [ "pipenv", "run", "python", "-m", "unittest" ]
