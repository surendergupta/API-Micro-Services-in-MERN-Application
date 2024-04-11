import boto3

# Initialize Boto3 clients
ec2_client = boto3.client('ec2')
asg_client = boto3.client('autoscaling')

# Define VPC parameters
vpc_cidr_block = '10.0.0.0/16'
subnet_cidr_blocks = ['10.0.1.0/24', '10.0.2.0/24']
security_group_name = 'backend-security-group'
security_group_description = 'Security group for my backend application'

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
user_data = """
#!/bin/bash
docker run -dp 3001:3001 -e "PORT=3001" public.ecr.aws/s7f2n3x3/suri-simple-mern-be-micro-hello-service
docker run -dp 3002:3002 -e "PORT=3002" -e "MONGO_URL=mongodb+srv://surendergupta:abcd4321A@cluster0.tyk2d2k.mongodb.net/SimpleMicroService" public.ecr.aws/s7f2n3x3/suri-simple-mern-be-micro-profile-service

"""  # Specify your Docker image name and any additional Docker run options

# Create launch configuration
lc_response = asg_client.create_launch_template(
    LaunchTemplateName='BackendSimpleMernASGLaunchConfig',
    Version='1',
    LaunchTemplateData={
        'ImageId': ami_id,
        'InstanceType': instance_type,
        'SecurityGroups': security_group_ids,
        'UserData': user_data
    }
)

# Define Auto Scaling Group parameters
asg_name = 'backend-asg'
launch_template = {
    'LaunchTemplateName': 'BackendSimpleMernASGLaunchConfig',
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

print("Backend deployment setup complete:")
print("VPC ID:", vpc_id)
print("Subnet IDs:", subnet_ids)
print("Security Group ID:", security_group_id)
print("Auto Scaling Group Name:", asg_name)
