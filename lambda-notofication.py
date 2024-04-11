import boto3

# Initialize Boto3 client
sns_client = boto3.client('sns')

def lambda_handler(event, context):
    # Determine deployment status (success/failure) from event
    deployment_status = event.get('status')

    # Publish message to the appropriate SNS topic
    if deployment_status == 'success':
        topic_name = 'deployment_success'
        message = 'Deployment was successful.'
    else:
        topic_name = 'deployment_failure'
        message = 'Deployment failed.'

    response = sns_client.publish(
        TopicArn=f"arn:aws:sns:your-region:your-account-id:{topic_name}",
        Message=message
    )

    print(f"Published message to '{topic_name}' SNS topic.")
