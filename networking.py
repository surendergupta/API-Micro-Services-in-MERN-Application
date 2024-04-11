import boto3

# Initialize Boto3 clients
elb_client = boto3.client('elbv2')
route53_client = boto3.client('route53')

# Define Load Balancer parameters
elb_name = 'my-load-balancer'
asg_name = 'my-auto-scaling-group'
listener_port = 80
target_group_name = 'my-target-group'

# Create a target group
target_group_response = elb_client.create_target_group(
    Name=target_group_name,
    Protocol='HTTP',
    Port=listener_port,
    VpcId='your-vpc-id',  # Replace with your VPC ID
    HealthCheckProtocol='HTTP',
    HealthCheckPort=str(listener_port),
    HealthCheckPath='/',
    TargetType='instance'
)
target_group_arn = target_group_response['TargetGroups'][0]['TargetGroupArn']

# Create a load balancer
elb_response = elb_client.create_load_balancer(
    Name=elb_name,
    Subnets=['subnet-1234567890abcdef0', 'subnet-abcdef1234567890'],  # Specify your subnets
    SecurityGroups=['sg-1234567890abcdef0'],  # Specify your security groups
    Scheme='internet-facing',
    Type='application',
    IpAddressType='ipv4'
)
elb_arn = elb_response['LoadBalancers'][0]['LoadBalancerArn']

# Create a listener
elb_client.create_listener(
    LoadBalancerArn=elb_arn,
    Protocol='HTTP',
    Port=listener_port,
    DefaultActions=[
        {
            'Type': 'forward',
            'TargetGroupArn': target_group_arn
        }
    ]
)

# Register ASG with the target group
elb_client.register_targets(
    TargetGroupArn=target_group_arn,
    Targets=[
        {
            'Id': 'instance-id-1'  # Replace with your instance IDs
        },
        {
            'Id': 'instance-id-2'
        }
    ]
)

# Configure DNS with Route 53 (example)
route53_client.change_resource_record_sets(
    HostedZoneId='your-hosted-zone-id',  # Replace with your Route 53 hosted zone ID
    ChangeBatch={
        'Changes': [
            {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': 'example.com',  # Your domain name
                    'Type': 'A',
                    'AliasTarget': {
                        'HostedZoneId': 'your-elb-hosted-zone-id',  # ELB hosted zone ID
                        'DNSName': elb_name + '.us-east-1.elb.amazonaws.com',  # ELB DNS name
                        'EvaluateTargetHealth': False
                    }
                }
            }
        ]
    }
)

print("Load balancer setup complete:")
print("Load Balancer ARN:", elb_arn)
print("Target Group ARN:", target_group_arn)
    