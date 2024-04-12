import boto3
import csv
import base64
from botocore.exceptions import NoCredentialsError

# Define AWS region
aws_region = 'us-east-1'

# Create AWS clients
ec2_client = boto3.client('ec2', region_name=aws_region)
asg_client = boto3.client('autoscaling', region_name=aws_region)
elb_client = boto3.client('elbv2', region_name=aws_region)

# Define VPC parameters
vpc_cidr_block = '10.0.0.0/16'
vpc_name = 'boto3_orchestration_scaling_vpc'

# Other parameters
filename = f"{vpc_name}_records.csv"
key_pair_name = "boto3-orchestration-scaling-key"
subnet_cidr_blocks = ['10.0.1.0/24', '10.0.2.0/24', '10.0.3.0/24']
security_group_name = 'suri-smma-group'
security_group_description = 'Security group for my sample MERN Micro Architecture'

asg_name = 'backend-simple-mern-asg'
min_size = 1
max_size = 3
desired_capacity = 2
alb_name = 'Simple-mern-lb'
instance_name_be = 'Simple-Mern-BE'
instance_name_fe = 'Simple-Mern-FE'
instance_type = 't2.micro'
ami_id = 'ami-080e1f13689e07408'
launch_template_name = 'BackendSimpleMernASGLaunchConfig'

target_group_name = 'simple-mern-tg'
listener_port = 80

def create_security_group(vpc_id):
    try:
        # Create security group
        security_group_response = ec2_client.create_security_group(
            GroupName=security_group_name,
            Description=security_group_description,
            VpcId=vpc_id
        )
        security_group_id = security_group_response['GroupId']

        # Authorize inbound rules
        authorize_ingress(security_group_id, 'tcp', 80, 80, '0.0.0.0/0')
        authorize_ingress(security_group_id, 'tcp', 443, 443, '0.0.0.0/0')
        authorize_ingress(security_group_id, 'tcp', 22, 22, '0.0.0.0/0')
        authorize_ingress(security_group_id, 'tcp', 3001, 3001, '0.0.0.0/0')
        authorize_ingress(security_group_id, 'tcp', 3002, 3002, '0.0.0.0/0')

        print("Inbound rules for ports 80, 443, 22, 3001, and 3002 added to the security group.")
        return security_group_id
    except Exception as e:
        print(f"Error creating security group: {str(e)}")

def authorize_ingress(security_group_id, ip_protocol, from_port, to_port, cidr_ip):
    try:
        # Authorize inbound traffic
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': ip_protocol,
                    'FromPort': from_port,
                    'ToPort': to_port,
                    'IpRanges': [{'CidrIp': cidr_ip}]
                }
            ]
        )
    except Exception as e:
        print(f"Error authorizing ingress: {str(e)}")

def get_instances_running_by_name(name):
    try:
        # Get instances with specific name
        response = ec2_client.describe_instances(
            Filters=[
                {'Name': 'tag:Name', 'Values': [name]},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append(instance['InstanceId'])
        return instances
    except Exception as e:
        print(f"Error retrieving instances: {str(e)}")

def create_ec2_instances(security_group_id, user_data_script, instance_name):
    try:
        # Create EC2 instance
        response = ec2_client.run_instances (
            ImageId=ami_id,
            InstanceType=instance_type,
            KeyName=key_pair_name,
            SecurityGroupIds=[security_group_id],
            UserData=user_data_script,
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': instance_name}]
                }
            ]
        )
        instance_ids = [instance['InstanceId'] for instance in response['Instances']]
        return instance_ids
    except Exception as e:
        print(f"Error creating EC2 instances: {str(e)}")

def create_resource_infra():
    try:
        # Create VPC
        vpc_response = ec2_client.create_vpc(
            CidrBlock=vpc_cidr_block,
            TagSpecifications=[{'ResourceType': 'vpc', 'Tags': [{'Key': 'Name', 'Value': vpc_name}]}]
        )
        vpc_id = vpc_response['Vpc']['VpcId']
        print(f"VPC created with ID: {vpc_id}")

        # Create subnet
        subnet_ids = []
        for i, cidr_block in enumerate(subnet_cidr_blocks):
            az = f"{aws_region}a"  # Hardcoding AZ for simplicity
            subnet_response = ec2_client.create_subnet(
                VpcId=vpc_id,
                CidrBlock=cidr_block,
                AvailabilityZone=az
            )
            subnet_ids.append(subnet_response['Subnet']['SubnetId'])
        print(f"Subnets created: {subnet_ids}")

        # Create internet gateway
        ig_response = ec2_client.create_internet_gateway()
        ig_id = ig_response['InternetGateway']['InternetGatewayId']
        print(f"Internet Gateway created with ID: {ig_id}")

        # Attach internet gateway to VPC
        ec2_client.attach_internet_gateway(InternetGatewayId=ig_id, VpcId=vpc_id)
        print("Internet Gateway attached to VPC")

        # Create route table
        route_table_response = ec2_client.create_route_table(VpcId=vpc_id)
        route_table_id = route_table_response['RouteTable']['RouteTableId']
        print(f"Route Table created with ID: {route_table_id}")

        # Create route
        ec2_client.create_route(
            RouteTableId=route_table_id,
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=ig_id
        )
        print("Route created")

        # Create security group
        security_group_id = create_security_group(vpc_id)

        # Create EC2 instances
        user_data_script_be = """#!/bin/bash
        # User data script for backend instances
        """
        user_data_script_fe = """#!/bin/bash
        # User data script for frontend instances
        """
        fe_instance_ids = create_ec2_instances(security_group_id, user_data_script_fe, instance_name_fe)
        be_instance_ids = create_ec2_instances(security_group_id, user_data_script_be, instance_name_be)

        print("EC2 instances created")
    except Exception as e:
        print(f"Error creating resource infrastructure: {str(e)}")

def main():
    choice = input("Enter 1 to create resources, 2 to delete resources: ")
    if choice == '1':
        create_resource_infra()
    elif choice == '2':
        # Implement deletion logic here
        pass
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
