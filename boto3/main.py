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
security_group_description = 'Security group for my sample MERN Micro Architechture'

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
launch_template = {
    'LaunchTemplateName': launch_template_name,
    'Version': '1'
}

target_group_name = 'simple-mern-tg'
listener_port = 80





def create_vpc():
    try:
        vpc_response = ec2_client.create_vpc(
            CidrBlock=vpc_cidr_block,
            TagSpecifications=[
                {
                    'ResourceType': 'vpc',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': vpc_name,
                        },
                    ],
                },
            ],
        )
        vpc_id = vpc_response['Vpc']['VpcId']
        return vpc_id
    except Exception as e:
        print(f"Error authorizing ingress: {str(e)}")

def create_subnet(vpc_id):
    try:
        availability_zones = ec2_client.describe_availability_zones()
        zone_names = [zone['ZoneName'] for zone in availability_zones['AvailabilityZones']]
        subnet_ids = []
        for i, cidr_block in enumerate(subnet_cidr_blocks):
            az = zone_names[i]  # Use the AZ name from the list
            subnet_response = ec2_client.create_subnet(
                VpcId=vpc_id,
                CidrBlock=cidr_block,
                AvailabilityZone=az
            )
            subnet_ids.append(subnet_response['Subnet']['SubnetId'])
        return subnet_ids
    except Exception as e:
        print(f"Error authorizing ingress: {str(e)}")

def create_internet_gateway():
    try:
        ig_response = ec2_client.create_internet_gateway()
        ig_id = ig_response['InternetGateway']['InternetGatewayId']
        return ig_id
    except Exception as e:
        print(f"Error authorizing ingress: {str(e)}")

def attach_internet_gateway(vpc_id, ig_id):
    try:
        ec2_client.attach_internet_gateway(
            InternetGatewayId=ig_id,
            VpcId=vpc_id
        )
    except Exception as e:
        print(f"Error authorizing ingress: {str(e)}")

def create_route_table(vpc_id):
    try:
        route_table_response = ec2_client.create_route_table(
            VpcId=vpc_id
            )
        route_table_id = route_table_response['RouteTable']['RouteTableId']
        return route_table_id
    except Exception as e:
        print(f"Error authorizing ingress: {str(e)}")

def create_route(route_table_id, ig_id):
    try:
        ec2_client.create_route(
            RouteTableId=route_table_id,
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=ig_id
        )
    except Exception as e:
        print(f"Error authorizing ingress: {str(e)}")

def create_security_group(vpc_id):
    try:
        # Create security group
        security_group_response = ec2_client.create_security_group(
            GroupName=security_group_name,
            Description=security_group_description,
            VpcId=vpc_id
        )
        security_group_id = security_group_response['GroupId']
        
        # Authorize inbound rules for ports 80, 443, 22, 3001, and 3002
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

def create_key_pair():
    try:
        ec2 = boto3.client('ec2')
        response = ec2.create_key_pair(KeyName=key_pair_name)
        print(f"Key pair '{key_pair_name}' created successfully.")
        # Save the private key to a file
        with open(f"{key_pair_name}.pem", "w") as key_file:
            key_file.write(response['KeyMaterial'])
        print(f"Private key saved to {key_pair_name}.pem")
        return response
    except Exception as e:
        print(f"Error creating key pair: {str(e)}")

def create_launch_tempate(security_group_id):
    user_data = """#!/bin/bash
    sudo apt-get update
    sudo apt install docker.io -y
    sudo usermod -aG docker $USER
    sudo chmod 666 /var/run/docker.sock
    docker run -dp 3001:3001 -e "PORT=3001" public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-hello-service
    docker run -dp 3002:3002 -e "PORT=3002" -e "MONGO_URL=mongodb+srv://surendergupta:abcd4321A@cluster0.tyk2d2k.mongodb.net/SimpleMicroService" public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-profile-service
    """
    encoded_user_data = base64.b64encode(user_data.encode('utf-8')).decode('utf-8')
    
    try:
        lt_response = ec2_client.create_launch_template(
            LaunchTemplateName=launch_template_name,
            VersionDescription='Initial version',
            LaunchTemplateData={
                'InstanceType': instance_type,
                'ImageId': ami_id,
                'KeyName': key_pair_name,
                'SecurityGroupIds': [security_group_id],
                'UserData': encoded_user_data
            }            
        )
        print(f'Launch template created successfully. {lt_response}')
        return lt_response
    except Exception as e:
        print(f"Error authorizing ingress: {str(e)}")

def create_target_group(vpc_id):
    try:
        target_group_response = elb_client.create_target_group(
            Name=target_group_name,
            Protocol='HTTP',
            Port=3001,
            VpcId= vpc_id,  # Replace with your VPC ID
            HealthCheckProtocol='HTTP',
            HealthCheckPort=str(listener_port),
            HealthCheckPath='/',
            TargetType='instance',
            Tags = [{'Key': 'Name', 'Value': target_group_name}]
        )
        target_group_arn = target_group_response['TargetGroups'][0]['TargetGroupArn']
        return target_group_arn
    except Exception as e:
        print(f"Error authorizing ingress: {str(e)}")

def create_auto_scaling_group(subnet_ids, target_group_arn):
    try:
        subnet_ids_for_asg = subnet_ids
        asg_be_response = asg_client.create_auto_scaling_group(
            AutoScalingGroupName = asg_name,
            LaunchTemplate = launch_template,
            MinSize = min_size,
            MaxSize = max_size,
            DesiredCapacity = desired_capacity,
            VPCZoneIdentifier = ','.join(subnet_ids_for_asg),
            Tags=[{'Key': 'Name', 'Value': asg_name}],
            HealthCheckType='ELB',
            HealthCheckGracePeriod=300,
            TargetGroupARNs=[target_group_arn]
        )    
        return asg_be_response
    except Exception as e:
        print(f"Error authorizing ingress: {str(e)}")

def create_load_balancer(subnet_ids, security_group_ids):
    try:
        elb_response = elb_client.create_load_balancer(
            Name=alb_name,
            Subnets=subnet_ids,  # Specify your subnets
            SecurityGroups=[security_group_ids],  # Specify your security groups
            Scheme='internet-facing',
            Type='application',
            IpAddressType='ipv4',
            Tags=[{'Key': 'Name', 'Value': alb_name}]
        )
        elb_arn = elb_response['LoadBalancers'][0]['LoadBalancerArn']
        return elb_arn
    except Exception as e:
            print(f"Error retrieving instances: {str(e)}")

def create_listener(elb_arn, target_group_arn):
    try:
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
    except Exception as e:
        print(f"Error retrieving instances: {str(e)}")

def register_targets(target_group_arn, ec2_instance_ids):
    try:
        for instance_id in ec2_instance_ids:
            elb_client.register_targets(
                TargetGroupArn=target_group_arn,
                Targets=[{'Id': instance_id}]
            )
    except Exception as e:
        print(f"Error retrieving instances: {str(e)}")

def get_instances_running_by_name():
    try:
        # Get instances with specific name
        response = ec2_client.describe_instances(
            Filters=[
                {'Name': 'tag:Name', 'Values': [asg_name]},
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

def create_ec2_instances(security_group_id):
    try:
        # Create EC2 instance
        user_data_script = """#!/bin/bash
            sudo apt-get update
            sudo apt install docker.io -y
            sudo usermod -aG docker $USER
            sudo chmod 666 /var/run/docker.sock
            service docker start
            docker run -dp 3000:3000 public.ecr.aws/t5n9y4h0/suri-simple-mern-fe
        """
        user_data_encoded = base64.b64encode(user_data_script.encode()).decode('utf-8')

        response = ec2_client.run_instances (
            ImageId=ami_id,
            InstanceType=instance_type,
            KeyName=key_pair_name,
            SecurityGroupIds=[security_group_id],
            UserData=user_data_encoded,
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': instance_name_fe
                        }
                    ]
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
        vpc_id = create_vpc()
        print(f"Create VPC id : {vpc_id}")
        
        # Create Subnet
        subnet_ids = create_subnet(vpc_id)
        print(f"Create Subnet ids : {subnet_ids}")
        
        # Create Internet Gateway
        ig_id = create_internet_gateway()
        print(f"Create Internet Gateway id : {ig_id}")
        
        # Attach Internet Gateway
        attach_internet_gateway(vpc_id, ig_id)
        
        # Create Route Table
        route_table_id = create_route_table(vpc_id)
        print(f"Create Route Table id : {route_table_id}")
        
        # Attach Route Table to Internet Gateway
        create_route(route_table_id, ig_id)
        
        # Create Security Group
        security_group_id = create_security_group(vpc_id)    
        print(f"Create Security Group id : {security_group_id}")
        
        # Create Key Pair
        key_response = create_key_pair()
        print(f"Create Key Pair : {key_response}")
        
        # Create Launch Template
        lt_response = create_launch_tempate(security_group_id)
        print(f"Create Launch Template : {lt_response}")
        
        # Create Target Group
        target_group_arn = create_target_group(vpc_id)
        print(f"Create Target group : {target_group_arn}")
        
        # Create Auto Scaling Group
        asg_be_response = create_auto_scaling_group(subnet_ids, target_group_arn)
        print(f"Create Auto Scalling Group : {asg_be_response}")
        
        # Create Load Balancer
        elb_arn = create_load_balancer(subnet_ids, security_group_id)
        print(f"Create Load Balancer : {elb_arn}")
        
        # Get Running Instance List By Name
        ec2_instance_ids = get_instances_running_by_name()

        # Register Instance In Target Group
        register_targets(target_group_arn, ec2_instance_ids)
        
        # Add Listener Target Group
        create_listener(elb_arn, target_group_arn)
        
        # Create Frontend EC2 Instance
        fe_instance_id = create_ec2_instances(security_group_id)
        print(f"Create Frontend Instance : {fe_instance_id}")
        
        # Storing Data into File
        fields = ['VPC_NAME', 'VPC_ID', 'ROUTE_TABLE_ID', 'SUBNET_ID', 'INTERNET_GATEWAY_ID', 'SECURITY_GROUP_ID', 'KEY_PAIR', 'LAUNCH_TEMPLATE' 'ASG_GROUP_BE']
        rows = [[vpc_name, vpc_id, route_table_id, subnet_ids, ig_id, security_group_id, key_response, lt_response,  asg_be_response]]
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(fields)
            csvwriter.writerows(rows)
        
        print('Resource Crated Successfully.')
    except Exception as e:
        print(f"Error creating EC2 instances: {str(e)}")

def delete_vpc(vpc_id):
    try:
        # Detach and delete internet gateway
        response = ec2_client.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])
        for igw in response['InternetGateways']:
            for attachment in igw['Attachments']:
                if attachment['VpcId'] == vpc_id:
                    ec2_client.detach_internet_gateway(InternetGatewayId=igw['InternetGatewayId'], VpcId=vpc_id)
                    ec2_client.delete_internet_gateway(InternetGatewayId=igw['InternetGatewayId'])
                    break

        # Delete subnets
        response = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        for subnet in response['Subnets']:
            ec2_client.delete_subnet(SubnetId=subnet['SubnetId'])
        
        # Delete route tables
        response = ec2_client.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        for route_table in response['RouteTables']:
            for association in route_table['Associations']:
                if not association['Main']:
                    ec2_client.disassociate_route_table(AssociationId=association['RouteTableAssociationId'])
                    ec2_client.delete_route_table(RouteTableId=route_table['RouteTableId'])

        # Delete security groups
        response = ec2_client.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        for security_group in response['SecurityGroups']:
            if security_group['GroupName'] != 'default':
                ec2_client.delete_security_group(GroupId=security_group['GroupId'])

        # Retry deleting VPC
        ec2_client.delete_vpc(VpcId=vpc_id)
        print(f"VPC {vpc_id} deleted successfully.")
    except Exception as e:
        print(f"Error deleting VPC: {str(e)}")

def delete_asg():    
    try:
        # Delete Auto Scaling Group
        asg_client.delete_auto_scaling_group(AutoScalingGroupName=asg_name, ForceDelete=True)
        print(f"Auto Scaling Group {asg_name} deleted successfully.")
    except Exception as e:
        print(f"Error deleting Auto Scaling Group: {str(e)}")

def delete_resource_infra():
    with open(filename, 'r') as read_obj:   
        # Return a reader object which will 
        # iterate over lines in the given csvfile 
        csv_reader = csv.reader(read_obj)   
        # convert string to list 
        list_of_csv = list(csv_reader) 
        print(list_of_csv)
        vpc_id = list_of_csv[1][1]
        delete_vpc(vpc_id)
        delete_asg()

def main():
    choice = input("Enter 1 to call create Resource, 2 to call delete resource: ")
    if choice == '1':
        create_resource_infra()        
    elif choice == '2':
        delete_resource_infra()
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
    # create_resource_infra()