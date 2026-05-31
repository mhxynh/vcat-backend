FROM public.ecr.aws/sam/build-python3.12:latest

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3001

CMD ["sh", "/app/docker-entrypoint.sh"]
