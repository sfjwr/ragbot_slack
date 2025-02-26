FROM public.ecr.aws/lambda/python:3.12-arm64

ENV AWS_DEFAULT_REGION ap-northeast-1

RUN pip3 install --upgrade pip
RUN pip3 install pipenv

COPY app.py ${LAMBDA_TASK_ROOT}
COPY config.json ${LAMBDA_TASK_ROOT}

COPY Pipfile* /
RUN pipenv install --system --deploy

CMD [ "app.handler" ]
