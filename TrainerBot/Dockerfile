FROM public.ecr.aws/lambda/python:3.8

RUN pip install snips-nlu
RUN snips-nlu download es
RUN pip list
COPY lambda_function.py   ./
CMD ["lambda_function.lambda_handler"]      
