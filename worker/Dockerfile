FROM python:3.11-slim
RUN pip install --no-cache-dir numpy==1.26.4 scipy==1.11.4 nibabel==5.2.1 pandas==2.2.2
WORKDIR /app
COPY run_job.py /app/run_job.py
ENTRYPOINT ["python","/app/run_job.py"]
