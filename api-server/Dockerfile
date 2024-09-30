FROM python:3.12-slim

RUN apt -y update && apt install -y
RUN apt -y install curl
RUN apt -y install g++
RUN apt -y install make
RUN apt -y install git

WORKDIR /app

RUN git clone https://github.com/pCarmonaa/StockfishTraces.git
RUN cd StockfishTraces/src && make build
RUN mkdir stockfish
RUN cp StockfishTraces/src/stockfish stockfish/stockfish
RUN rm -R StockfishTraces

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src .
COPY ./data ./data

EXPOSE 5000

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]
