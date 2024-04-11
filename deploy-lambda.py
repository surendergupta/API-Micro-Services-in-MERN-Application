import boto3
import time

# Initialize Boto3 clients
lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')

# Define your Lambda function code for database backup
lambda_function_code = """
import boto3
import time

def lambda_handler(event, context):
    # Define your database backup logic here
    # For example, if you are using MongoDB, you can use 'mongodump'
    # Replace 'your_database_name' with your actual database name
    db_backup_command = f'mongodump --db your_database_name'

    # Execute the database backup command
    backup_result = os.system(db_backup_command)

    if backup_result == 0:
        # Backup successful, generate timestamp for S3 object key
        timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        s3_client = boto3.client('s3')
        s3_bucket_name = 'your-s3-bucket-name'
        s3_object_key = f'db_backup_{timestamp}.zip'  # Adjust the file extension if needed

        # Upload the backup file to S3 bucket
        s3_client.upload_file('backup.zip', s3_bucket_name, s3_object_key)

        return {
            'statusCode': 200,
            'body': f'Database backup completed and uploaded to S3 bucket: {s3_bucket_name}/{s3_object_key}'
        }
    else:
        # Backup failed
        return {
            'statusCode': 500,
            'body': 'Database backup failed'
        }
"""

# Define Lambda function configuration
lambda_function_name = 'backup_db_lambda_function'
lambda_runtime = 'python3.8'
lambda_role_arn = 'arn:aws:iam::your-account-id:role/your-lambda-role'  # Replace with your Lambda execution role ARN
lambda_handler = 'lambda_function.lambda_handler'

# Create Lambda function
lambda_response = lambda_client.create_function(
    FunctionName=lambda_function_name,
    Runtime=lambda_runtime,
    Role=lambda_role_arn,
    Handler=lambda_handler,
    Code={
        'ZipFile': lambda_function_code.encode()
    }
)

print("Lambda function created successfully:")
print("Function ARN:", lambda_response['FunctionArn'])
