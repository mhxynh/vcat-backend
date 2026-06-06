FROM public.ecr.aws/sam/build-python3.12:1.161.0

WORKDIR /app

RUN dnf install -y docker && dnf clean all

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3001

CMD ["sh", "/app/docker-entrypoint.sh"]
