import os
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get variables
project = os.getenv('GOOGLE_CLOUD_PROJECT')
region = os.getenv('GOOGLE_CLOUD_LOCATION')
agent_path = os.getenv('AGENT_PATH')
service_name = os.getenv('SERVICE_NAME')
app_name = os.getenv('APP_NAME')
api_key = os.getenv('GOOGLE_API_KEY')

# Run deploy command
cmd = f'gcloud run deploy capital-agent-service --source . --region {region} --project {project} --allow-unauthenticated --set-env-vars="GOOGLE_CLOUD_PROJECT={project},GOOGLE_CLOUD_LOCATION={region},GOOGLE_GENAI_USE_VERTEXAI=false,SSL_CERT_FILE=$(python -m certifi),GOOGLE_API_KEY={api_key}"'
subprocess.run(cmd, shell=True)