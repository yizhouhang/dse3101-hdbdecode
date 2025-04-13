# Use a lightweight Python base image
FROM python:3.9

# Set working directory
WORKDIR /HDB-Decode

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app 
COPY . .

# Expose the port that Streamlit uses
EXPOSE 8501

# Run the Streamlit app from the frontend folder
CMD ["streamlit", "run", "frontend.py", "--server.port=8501", "--server.enableCORS=false"]

