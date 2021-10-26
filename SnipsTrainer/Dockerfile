FROM public.ecr.aws/lambda/python:3.8

RUN pip install snips-nlu
RUN snips-nlu download es
RUN pip list
COPY app.py   ./
CMD ["app.handler"]      
