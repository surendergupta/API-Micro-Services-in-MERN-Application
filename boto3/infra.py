import boto3
import csv
import base64
import uuid

random_uuid = uuid.uuid4()
random_name = str(random_uuid)[-4:]
# Define AWS region
aws_region = 'us-east-1'

# Create AWS clients
ec2_client = boto3.client('ec2', region_name=aws_region)
asg_client = boto3.client('autoscaling', region_name=aws_region)
elb_client = boto3.client('elbv2', region_name=aws_region)
ec2_resource = boto3.resource('ec2', region_name=aws_region)
# Define VPC parameters
vpc_cidr_block = '10.0.0.0/16'
vpc_name = 'orchestration-scaling-vpc'

# Define Key-Pair Name
key_pair_name = f"orchestration-scaling-key-{random_name}"

# Define subnet Block of 3 Zone
subnet_cidr_blocks = ['10.0.1.0/24', '10.0.2.0/24', '10.0.3.0/24']

# Define availability zones
availability_zones = ['us-east-1a', 'us-east-1b', 'us-east-1c']

# Define Security Group Parameters
security_group_name = 'orchestration-scaling-sg'
security_group_description = 'Project on Orchestration and Scaling'

# Other Parameters
target_group_name_s1 = 'orchestration-scaling-s1-tg'
target_group_name_s2 = 'orchestration-scaling-s2-tg'

elb_name_be_s1 = 'orchestration-scaling-s1-lb'
elb_name_be_s2 = 'orchestration-scaling-s2-lb'

launch_template_name = f"orchestration-scaling-{random_name}-lt"

asg_name_be_s1 = 'orchestration-scaling-s1-asg'
asg_name_be_s2 = 'orchestration-scaling-s2-asg'

min_size = 1
max_size = 3
desired_capacity = 2

instance_be_s1 = 'orchestration-scaling-be-hello-service'
instance_be_s2 = 'orchestration-scaling-be-profile-service'
instance_fe_app = 'orchestration-scaling-fe-app'
ami_id = 'ami-080e1f13689e07408'
instance_type = 't2.micro'

listener_port = 80
instance_port_s1 = 3001
instance_port_s2 = 3002

launch_template = {
    'LaunchTemplateName': launch_template_name,
    'Version': '1'
}

def create_security_group(vpc_id):
    try:
        # Create security group
        security_group_response = ec2_client.create_security_group(
            GroupName=security_group_name,
            Description=security_group_description,
            VpcId=vpc_id
        )
        security_group_id = security_group_response['GroupId']
        print(f"Security group ID: ", security_group_id)

        # Authorize inbound rules
        authorize_ingress(security_group_id, 'tcp', 80, 80, '0.0.0.0/0')
        authorize_ingress(security_group_id, 'tcp', 443, 443, '0.0.0.0/0')
        authorize_ingress(security_group_id, 'tcp', 22, 22, '0.0.0.0/0')
        authorize_ingress(security_group_id, 'tcp', 3000, 3000, '0.0.0.0/0')
        authorize_ingress(security_group_id, 'tcp', 3001, 3001, '0.0.0.0/0')
        authorize_ingress(security_group_id, 'tcp', 3002, 3002, '0.0.0.0/0')

        print("Inbound rules for ports 80, 443, 22, 3001, and 3002 added to the security group.")
        return security_group_id
    except Exception as e:
        print(f"Error while creating security group: {str(e)}")

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
        print(f"Error while authorizing ingress: {str(e)}")

def create_key_pair():
    try:
        
        response = ec2_client.create_key_pair(
            KeyName=key_pair_name,
            KeyType='rsa',
            KeyFormat='pem' 
        )
        print(f"Key pair '{key_pair_name}' created successfully.")
        
        # Save the private key to a file
        with open(f"{key_pair_name}.pem", "w") as key_file:
            key_file.write(response['KeyMaterial'])
        print(f"Private key saved to {key_pair_name}.pem")

        return response
    except Exception as e:
        print(f"Error while creating key pair: {str(e)}")

def create_ec2_instances(security_group_id, subnet_ids, user_data_script, instance_name):
    try:
        # Create EC2 instance
        response = ec2_client.run_instances (
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/sdh',
                    'Ebs': {
                        'VolumeSize': 8,
                    },
                },
            ],
            ImageId=ami_id,
            InstanceType=instance_type,
            KeyName=key_pair_name,
            SecurityGroupIds=[security_group_id],
            UserData=user_data_script,
            SubnetId=subnet_ids[0],
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': instance_name}]
                }
            ],
        )
        instance_id = response['Instances'][0]['InstanceId']
        print(f'EC2 {instance_name} instance id "{instance_id}" launched successfully.')
        
        return instance_id
    
    except Exception as e:
        print(f"Error while creating EC2 instances: {str(e)}")

def create_target_group(vpc_id, target_group_name, instance_port):
    try:
        target_group_response = elb_client.create_target_group(
            Name=target_group_name,
            Protocol='HTTP',
            Port=instance_port,
            VpcId= vpc_id,  # Replace with your VPC ID
            HealthCheckProtocol='HTTP',
            HealthCheckPort=str(instance_port),
            HealthCheckPath='/',
            TargetType='instance',
            Tags = [{'Key': 'Name', 'Value': target_group_name}]
        )
        target_group_arn = target_group_response['TargetGroups'][0]['TargetGroupArn']
        return target_group_arn
    except Exception as e:
        print(f"Error while create target group: {str(e)}")

def create_load_balancer(elb_name, subnet_ids, security_group_ids):
    try:
        elb_response = elb_client.create_load_balancer(
            Name=elb_name,
            Subnets=subnet_ids,  # Specify your subnets
            SecurityGroups=[security_group_ids],  # Specify your security groups
            Scheme='internet-facing',
            Type='application',
            IpAddressType='ipv4',
            Tags=[{'Key': 'Name', 'Value': elb_name}]
        )
        elb_arn = elb_response['LoadBalancers'][0]['LoadBalancerArn']
        return elb_arn
    except Exception as e:
            print(f"Error while create load balance: {str(e)}")

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
        print(f"Error while create listener: {str(e)}")

def register_targets(target_group_arn, instance_id):
    try:
        elb_client.register_targets(TargetGroupArn=target_group_arn, Targets=[{'Id': instance_id}])
        
    except Exception as e:
        print(f"Error while register instance : {str(e)}")

def create_launch_tempate(security_group_id):
    user_data = """#!/bin/bash
    sudo apt-get update
    sudo apt install docker.io -y
    sudo usermod -aG docker $USER
    sudo chmod 666 /var/run/docker.sock

    docker pull public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-hello-service
    docker run -dp 3001:3001 -e "PORT=3001" public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-hello-service

    docker pull public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-profile-service
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
        print(f"Error while launch template creating : {str(e)}")

def create_auto_scaling_group(asg_name, subnet_ids, target_group_arn):
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
        print(f"Error while create auto scaling group : {str(e)}")

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
        
        # Iterate over CIDR blocks and availability zones
        for i, cidr_block in enumerate(subnet_cidr_blocks):
            # Get the availability zone for this subnet
            availability_zone = availability_zones[i]
            # Create the subnet in the specified availability zone
            subnet_response = ec2_client.create_subnet(
                VpcId=vpc_id,
                CidrBlock=cidr_block,
                AvailabilityZone=availability_zone,
                # MapPublicIpOnLaunch=True
            )
            # Append the subnet ID to the list
            subnet_id = subnet_response['Subnet']['SubnetId']
            subnet_ids.append(subnet_id)            
            
        for subnet_id in subnet_ids:
            ec2_client.modify_subnet_attribute(
                SubnetId=subnet_id,
                MapPublicIpOnLaunch={'Value': True}
            )
        # Print the subnet IDs
        print(f"Subnets created: {subnet_ids}")

        # Create route table
        route_table_response = ec2_client.create_route_table(VpcId=vpc_id)
        route_table_id = route_table_response['RouteTable']['RouteTableId']
        print(f"Route Table created with ID: {route_table_id}")
        

        ec2_client.associate_route_table(RouteTableId=route_table_id, SubnetId=subnet_ids[0])
        print("Subnet attached to route table.")

        # Create internet gateway
        ig_response = ec2_client.create_internet_gateway()
        ig_id = ig_response['InternetGateway']['InternetGatewayId']
        print(f"Internet Gateway created with ID: {ig_id}")

        # Attach internet gateway to VPC
        ec2_client.attach_internet_gateway(InternetGatewayId=ig_id, VpcId=vpc_id)
        print("Internet Gateway attached to VPC")

        # Create route pointing to the internet gateway
        ec2_client.create_route(
            RouteTableId=route_table_id,
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=ig_id
        )
        print("Route added to the route table pointing to the internet gateway.")

        # Create security group
        security_group_id = create_security_group(vpc_id)

        # Craete Key PAir
        create_key_pair()

        # Create EC2 instances
        user_data_script_be_s1 = """#!/bin/bash
        sudo apt-get update -y
        sudo apt install docker.io -y
        sudo usermod -aG docker $USER
        sudo chmod 666 /var/run/docker.sock
        docker pull public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-hello-service
        docker run -dp 3001:3001 -e "PORT=3001" public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-hello-service
        """

        user_data_script_be_s2 = """#!/bin/bash
        sudo apt-get update -y
        sudo apt install docker.io -y
        sudo usermod -aG docker $USER
        sudo chmod 666 /var/run/docker.sock
        docker pull public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-profile-service
        docker run -dp 3002:3002 -e "PORT=3002" -e "MONGO_URL=mongodb+srv://surendergupta:abcd4321A@cluster0.tyk2d2k.mongodb.net/SimpleMicroService" public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-profile-service        
        """
        user_data_encoded_be_s1 = base64.b64encode(user_data_script_be_s1.encode()).decode('utf-8')
        user_data_encoded_be_s2 = base64.b64encode(user_data_script_be_s2.encode()).decode('utf-8')

        be_s1_instance_id = create_ec2_instances(security_group_id, subnet_ids, user_data_encoded_be_s1, instance_be_s1)
        be_s2_instance_id = create_ec2_instances(security_group_id, subnet_ids, user_data_encoded_be_s2, instance_be_s2)
        
        instance_s1 = ec2_resource.Instance(be_s1_instance_id)
        instance_s1.wait_until_running()
        print(f"Instance s1 {instance_s1.instance_id} is now running of ip {instance_s1.public_ip_address}.")
        
        instance_s2 = ec2_resource.Instance(be_s2_instance_id)
        instance_s2.wait_until_running()
        print(f"Instance s2 {instance_s2.instance_id} is now running of ip {instance_s2.public_ip_address}.")

        # Create Target Group:
        target_group_arn_s1 = create_target_group(vpc_id, target_group_name_s1, instance_port_s1)
        target_group_arn_s2 = create_target_group(vpc_id, target_group_name_s2, instance_port_s2)

        print(f"Target Group S1: {target_group_arn_s1}")
        print(f"Target Group S2: {target_group_arn_s2}")

        register_targets(target_group_arn_s1, be_s1_instance_id)
        register_targets(target_group_arn_s2, be_s2_instance_id)

        # Create Load Balancer:
        elb_arn_s1 = create_load_balancer(elb_name_be_s1, subnet_ids, security_group_id)
        elb_arn_s2 = create_load_balancer(elb_name_be_s2, subnet_ids, security_group_id)

        print(f"Load Balancer S1: {elb_arn_s1}")
        print(f"Load Balancer S2: {elb_arn_s2}")

        create_listener(elb_arn_s1, target_group_arn_s1)
        create_listener(elb_arn_s2, target_group_arn_s2)

        create_launch_tempate(security_group_id)

        asg_be_s1_response = create_auto_scaling_group(asg_name_be_s1, subnet_ids, target_group_arn_s1)
        asg_be_s2_response = create_auto_scaling_group(asg_name_be_s2, subnet_ids, target_group_arn_s2)

        print(f"Auto Scaling Group S1: {asg_be_s1_response}")
        print(f"Auto Scaling Group S2: {asg_be_s2_response}")
        
        # Configure DNS
        # API_LINK_HELLO_SERVICE: http://hello-service.cloudcrypto.in/
        # API_LINK_PROFIE_SERVICE: http://profile-service.cloudcrypto.in/
        
        # user_data_script_fe = """#!/bin/bash
        # sudo apt-get update -y
        # sudo apt install docker.io -y
        # sudo usermod -aG docker $USER
        # sudo chmod 666 /var/run/docker.sock
        # docker pull public.ecr.aws/t5n9y4h0/suri-simple-mern-fe
        # docker run -dp 3000:3000 public.ecr.aws/t5n9y4h0/suri-simple-mern-fe
        # """
        # user_data_encoded_fe = base64.b64encode(user_data_script_fe.encode()).decode('utf-8')

        # fe_app_instance_ids = create_ec2_instances(security_group_id, subnet_ids, user_data_encoded_fe, instance_fe_app)        
        # print(f"React App Frontend instance: {fe_app_instance_ids}")
        # instance_app = ec2_resource.Instance(fe_app_instance_ids)
        # instance_app.wait_until_running()
        # print(f"Instance s1 {instance_app.instance_id} is now running of ip {instance_app.public_ip_address}.")

        print("EC2 instances created")
    except Exception as e:
        print(f"Error creating resource infrastructure: {str(e)}")

def delete_resource_infra(asg_name, lb_arn, tg_arn, key_name, lt_id, ig_id, vpc_id):
    # Delete Auto Scaling groups
    print('Deleting Auto Scaling groups...')
    asg_client.delete_auto_scaling_group(AutoScalingGroupName=asg_name)
    # asg_response = asg_client.describe_auto_scaling_groups()
    # for group in asg_response['AutoScalingGroups']:
    #     asg_client.delete_auto_scaling_group(AutoScalingGroupName=group['AutoScalingGroupName'])

    # Delete Load balancers
    print('Deleting Load balancers...')
    elb_client.delete_load_balancer(LoadBalancerArn=lb_arn)
    # elb_response = elb_client.describe_load_balancers()
    # for lb in elb_response['LoadBalancers']:
    #     elb_client.delete_load_balancer(LoadBalancerArn=lb['LoadBalancerArn'])

    # Delete Target groups
    print('Deleting Target groups...')
    elb_client.delete_target_group(TargetGroupArn=tg_arn)
    # tg_response = elb_client.describe_target_groups()
    # for tg in tg_response['TargetGroups']:
    #     elb_client.delete_target_group(TargetGroupArn=tg['TargetGroupArn'])

    # Delete Key pairs
    print('Deleting Key pairs...')
    ec2_client.delete_key_pair(KeyName=key_name)
    # key_pairs = ec2_client.describe_key_pairs()
    # for key_pair in key_pairs['KeyPairs']:
    #     ec2_client.delete_key_pair(KeyName=key_pair['KeyName'])

    # Delete Launch Templates
    print('Deleting Launch Templates...')
    ec2_client.delete_launch_template(LaunchTemplateName=lt_id)
    # lt_response = ec2_client.describe_launch_templates()
    # for lt in lt_response['LaunchTemplates']:
    #     ec2_client.delete_launch_template(LaunchTemplateName=lt['LaunchTemplateName'])

    # Delete Instances
    print('Deleting Instances...')
    instances = ec2_client.describe_instances()
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            ec2_client.terminate_instances(InstanceIds=[instance['InstanceId']])

    # Detach Internet gateways from VPC
    print('Detaching Internet gateways from VPC...')
    ec2_client.detach_internet_gateway(InternetGatewayId=ig_id, VpcId=vpc_id)
    # vpc_response = ec2_client.describe_vpcs()
    # for vpc in vpc_response['Vpcs']:
    #     ig_response = ec2_client.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc['VpcId']]}])
    #     for ig in ig_response['InternetGateways']:
    #         ec2_client.detach_internet_gateway(InternetGatewayId=ig['InternetGatewayId'], VpcId=vpc['VpcId'])

    # Delete Internet gateways
    print('Deleting Internet gateways...')
    ec2_client.delete_internet_gateway(InternetGatewayId=ig_id)
    # ig_response = ec2_client.describe_internet_gateways()
    # for ig in ig_response['InternetGateways']:
    #     ec2_client.delete_internet_gateway(InternetGatewayId=ig['InternetGatewayId'])

    # Delete VPC
    print('Deleting VPC...')
    ec2_client.delete_vpc(VpcId=vpc_id)
    # for vpc in vpc_response['Vpcs']:
    #     ec2_client.delete_vpc(VpcId=vpc['VpcId'])
    print("success delete")

def main():
    choice = input("Enter 1 to call create Resource, 2 to call delete resource, 3 to call create instances: ")
    if choice == '1':
        create_resource_infra()        
    elif choice == '2':
        print("Invalid choice.")
        # delete_resource_infra(asg_name, lb_arn, tg_arn, key_name, lt_id, ig_id, vpc_id)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()