import boto3

# Initialize Boto3 client
sns_client = boto3.client('sns')

# Create SNS topics
topics = ['deployment_success', 'deployment_failure']

for topic_name in topics:
    response = sns_client.create_topic(Name=topic_name)
    topic_arn = response['TopicArn']
    print(f"Created SNS topic '{topic_name}' with ARN: {topic_arn}")
