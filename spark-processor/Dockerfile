FROM python:3.9-slim-bullseye

# Install Java 11 and other dependencies (bullseye has openjdk-11)
RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless wget procps && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$PATH:$JAVA_HOME/bin

# Download and install Spark
ENV SPARK_VERSION=3.4.1
ENV HADOOP_VERSION=3
ENV SPARK_HOME=/opt/spark

RUN wget -q https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz && \
    tar -xzf spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz && \
    mv spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} ${SPARK_HOME} && \
    rm spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz

ENV PATH=$PATH:${SPARK_HOME}/bin:${SPARK_HOME}/sbin
ENV PYTHONPATH=${SPARK_HOME}/python:${SPARK_HOME}/python/lib/py4j-0.10.9.7-src.zip

WORKDIR /app

# Copy and install Python packages
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Note: spark_processor.py will be mounted via volume in docker-compose.yml
CMD ["python3", "spark_processor.py"]
