# Use official Python image
FROM python:3.13

# Set working directory
WORKDIR /app

# Copy necessary files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port used by FastMCP (from your settings)
EXPOSE 7999

# Run the MCP tool server
CMD ["python", "tools.py"]