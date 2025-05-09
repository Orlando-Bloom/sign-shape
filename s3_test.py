import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

# Replace with your actual credentials and endpoint
AWS_ACCESS_KEY_ID = '0053e9bbf768ee80000000002'
AWS_SECRET_ACCESS_KEY = 'K005XEEbTzGy5qpqkvd0fuyildauiew'
AWS_S3_ENDPOINT_URL = 'https://objects-us-east-1.dream.io'
AWS_S3_BUCKET = 'sign-shape-new'

# Initialize client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url=AWS_S3_ENDPOINT_URL,
    region_name='us-east-1'
)

try:
    print("✅ Attempting to list buckets...")
    response = s3.list_buckets()
    bucket_names = [bucket['Name'] for bucket in response['Buckets']]
    print("Available buckets:", bucket_names)

    if AWS_S3_BUCKET in bucket_names:
        print(f"✅ Bucket '{AWS_S3_BUCKET}' exists and is accessible.")
    else:
        print(f"❌ Bucket '{AWS_S3_BUCKET}' does NOT exist or is not accessible.")

except NoCredentialsError:
    print("❌ Missing credentials.")
except PartialCredentialsError:
    print("❌ Incomplete credentials provided.")
except ClientError as e:
    print(f"❌ ClientError: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")
