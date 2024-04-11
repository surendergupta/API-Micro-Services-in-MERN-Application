import boto3

# Initialize Boto3 clients
ec2_client = boto3.client('ec2')
asg_client = boto3.client('autoscaling')
elb_client = boto3.client('elbv2')
route53_client = boto3.client('route53')
lambda_client = boto3.client('lambda')

# Define VPC parameters
vpc_cidr_block = '10.0.0.0/16'
subnet_cidr_blocks = ['10.0.1.0/24', '10.0.2.0/24']
security_group_name = 'suri-smma-group'
security_group_description = 'Security group for my sample MERN Micro Architechture'

# Create VPC
vpc_response = ec2_client.create_vpc(
    CidrBlock=vpc_cidr_block
)
vpc_id = vpc_response['Vpc']['VpcId']

# Create subnets
subnet_ids = []
for cidr_block in subnet_cidr_blocks:
    subnet_response = ec2_client.create_subnet(
        CidrBlock=cidr_block,
        VpcId=vpc_id
    )
    subnet_ids.append(subnet_response['Subnet']['SubnetId'])

# Create internet gateway
ig_response = ec2_client.create_internet_gateway()
ig_id = ig_response['InternetGateway']['InternetGatewayId']

# Attach internet gateway to VPC
ec2_client.attach_internet_gateway(
    InternetGatewayId=ig_id,
    VpcId=vpc_id
)

# Create route table
route_table_response = ec2_client.create_route_table(
    VpcId=vpc_id
)
route_table_id = route_table_response['RouteTable']['RouteTableId']

# Create route to internet gateway
ec2_client.create_route(
    RouteTableId=route_table_id,
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=ig_id
)

# Create Elastic IP (EIP)
eip_response = ec2_client.allocate_address(
    Domain='vpc'  # Specify 'vpc' for VPC Elastic IP, 'standard' for EC2 Classic
)
eip_allocation_id = eip_response['AllocationId']
eip_public_ip = eip_response.get('PublicIp', 'No Public IP')  # Get the assigned public IP if applicable


# Create NAT gateway
nat_response = ec2_client.create_nat_gateway(
    SubnetId=subnet_ids[0],  # Choose one of the subnets for NAT gateway
    AllocationId= eip_allocation_id  # Replace with your EIP allocation ID
)
nat_gateway_id = nat_response['NatGateway']['NatGatewayId']

# Create security group
security_group_response = ec2_client.create_security_group(
    GroupName=security_group_name,
    Description=security_group_description,
    VpcId=vpc_id
)
security_group_id = security_group_response['GroupId']

# Define launch configuration parameters
ami_id = 'ami-080e1f13689e07408'  # Specify your AMI ID for the EC2 instance with Docker installed
instance_type = 't2.micro'
security_group_ids = [security_group_id]  # Specify your security group IDs
backend_user_data = """
#!/bin/bash
docker run -dp 3001:3001 -e "PORT=3001" public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-hello-service
docker run -dp 3002:3002 -e "PORT=3002" -e "MONGO_URL=mongodb+srv://surendergupta:abcd4321A@cluster0.tyk2d2k.mongodb.net/SimpleMicroService" public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-profile-service

"""

frontend_user_data = """
#!/bin/bash
docker run -dp 80:3000 public.ecr.aws/t5n9y4h0/suri-simple-mern-fe
"""

lc_response = asg_client.create_launch_template(
    LaunchTemplateName='BackendSimpleMernASGLaunchConfig',
    Version='1',
    LaunchTemplateData={
        'ImageId': ami_id,
        'InstanceType': instance_type,
        'SecurityGroups': security_group_ids,
        'UserData': backend_user_data
    }
)

lc_response = asg_client.create_launch_template(
    LaunchTemplateName='FrontendSimpleMernASGLaunchConfig',
    Version='1',
    LaunchTemplateData={
        'ImageId': ami_id,
        'InstanceType': instance_type,
        'SecurityGroups': security_group_ids,
        'UserData': frontend_user_data
    }
)


# Define Auto Scaling Group parameters
asg_name = 'suri-mern-micro-asg'
launch_template = {
    'LaunchTemplateName': {
        'BackendSimpleMernASGLaunchConfig',
        'FrontendSimpleMernASGLaunchConfig'
    },
    'Version': '1'
}
subnet_ids_for_asg = subnet_ids
min_size = 1
max_size = 3
desired_capacity = 2

# Create Auto Scaling Group
asg_response = asg_client.create_auto_scaling_group(
    AutoScalingGroupName=asg_name,
    LaunchTemplate=launch_template,
    MinSize=min_size,
    MaxSize=max_size,
    DesiredCapacity=desired_capacity,
    VPCZoneIdentifier=','.join(subnet_ids_for_asg)
)

# Define your Lambda function code
lambda_function_code = """
def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }
"""

# Define Lambda function configuration
lambda_function_name = 'simple_mern_micro_lambda'
lambda_runtime = 'python3.8'
lambda_role_arn = 'arn:aws:iam::060095847722:role/simple_mern_microservice'  # Replace with your Lambda execution role ARN
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

elb_name = 'simple-loadbalancer'
listener_port = 80
target_group_name = 'simple-mern-tg'

# Create a target group
target_group_response = elb_client.create_target_group(
    Name=target_group_name,
    Protocol='HTTP',
    Port=listener_port,
    VpcId= vpc_id,  # Replace with your VPC ID
    HealthCheckProtocol='HTTP',
    HealthCheckPort=str(listener_port),
    HealthCheckPath='/',
    TargetType='instance'
)
target_group_arn = target_group_response['TargetGroups'][0]['TargetGroupArn']

# Create a load balancer
elb_response = elb_client.create_load_balancer(
    Name=elb_name,
    Subnets=subnet_ids,  # Specify your subnets
    SecurityGroups=security_group_ids,  # Specify your security groups
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

#Register ASG with the target group
elb_client.register_targets(
    TargetGroupArn=target_group_arn,
    Targets=[
        {
            'Id': 'instance-id-1'  # Replace with your instance IDs
        },
        {
            'Id': 'instance-id-2'
        }
        ,
        {
            'Id': 'instance-id-2'
        }
    ]
)

print("Infrastructure setup complete:")
print("VPC ID:", vpc_id)
print("Subnet IDs:", subnet_ids)
print("Security Group ID:", security_group_id)
print("Auto Scaling Group Name:", asg_name)
print("Internet Gateway ID:", ig_id)
print("Route Table ID:", route_table_id)
print("Elastic IP Allocation ID:", eip_allocation_id)
print("Elastic IP Public IP:", eip_public_ip)
print("Lambda function ARN:", lambda_response['FunctionArn'])
print("Load Balancer ARN:", elb_arn)
print("Target Group ARN:", target_group_arn)