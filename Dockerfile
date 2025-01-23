# Usa uma imagem base específica do Python 3.11.7
FROM python:3.11.7-slim

# Define o diretório de trabalho
WORKDIR /app

# Atualiza os pacotes e instala dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
  build-essential \
  libffi-dev \
  libssl-dev \
  libxml2-dev \
  libxslt-dev \
  libz-dev \
  libjpeg-dev \
  tesseract-ocr \
  poppler-utils \
  default-jdk \
  python3-dev \
  && rm -rf /var/lib/apt/lists/*

# Instala o Chromium 131.0.6778.264-1
RUN apt-get update && apt-get install -y \
  chromium \
  fonts-liberation \
  libasound2 \
  libatk-bridge2.0-0 \
  libatspi2.0-0 \
  libnss3 \
  libxcomposite1 \
  libxcursor1 \
  libxdamage1 \
  libxrandr2 \
  libgbm-dev \
  xdg-utils \
  libu2f-udev \
  libvulkan1 \
  wget \
  gnupg \
  unzip \
  --no-install-recommends && \
  rm -rf /var/lib/apt/lists/*

# Instala o ChromeDriver correspondente ao Chromium
#RUN wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/131.0.6778.264/chromedriver_linux64.zip \
#  && unzip /tmp/chromedriver.zip -d /usr/bin/ \
#  && chmod +x /usr/bin/chromedriver \
#  && rm /tmp/chromedriver.zip

# Instalar o webdriver-manager
#RUN pip install --no-cache-dir selenium webdriver-manager gunicorn

# Instalar e configurar o fuso horário
RUN apt-get update && apt-get install -y tzdata && \
  ln -sf /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && \
  dpkg-reconfigure -f noninteractive tzdata

# Instala o Cython antes de outras dependências
RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir Cython

# Instala os pacotes necessários para o psycopg2
RUN apt-get update && apt-get install -y \
  libpq-dev gcc \
  && rm -rf /var/lib/apt/lists/*

# Copia os arquivos do projeto para o contêiner
COPY . .

# Instala as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Exponha a porta para a aplicação Flask
EXPOSE 5000

# Comando para iniciar o aplicativo
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "--timeout", "600", "runServer:app"]
