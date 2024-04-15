import boto3
import base64

# Define AWS region
aws_region = 'us-east-1'

# Create AWS clients
ec2_client = boto3.client('ec2', region_name=aws_region)
ec2_resource = boto3.resource('ec2', region_name=aws_region)

ami_id = 'ami-080e1f13689e07408'
instance_type = 't2.micro'
key_pair_name = 'orchestration-scaling-key-2068'
security_group_id = 'sg-00f0ad424716607b9'
subnet_ids = ['subnet-0867e4b8a4ecf26f8', 'subnet-0db60c3d3efc51a9f', 'subnet-042248a77ac7cf215']
instance_fe_app = 'orchestration-scaling-fe-app'

API_LINK_HELLO_SERVICE = 'http://hello-service.cloudcrypto.in/'
API_LINK_PROFIE_SERVICE = 'http://profile-service.cloudcrypto.in/'

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


if __name__ == "__main__":
    user_data_script_fe = """#!/bin/bash
    sudo apt-get update -y
    sudo apt install docker.io -y
    sudo usermod -aG docker $USER
    sudo chmod 666 /var/run/docker.sock
    docker pull public.ecr.aws/t5n9y4h0/suri-simple-mern-fe:17
    docker run -dp 3000:3000 -e "REACT_APP_SERVICE1_URL={}" -e "REACT_APP_SERVICE2_URL={}" public.ecr.aws/t5n9y4h0/suri-simple-mern-fe:17
    """.format(API_LINK_HELLO_SERVICE, API_LINK_PROFIE_SERVICE)
    user_data_encoded_fe = base64.b64encode(user_data_script_fe.encode()).decode('utf-8')

    fe_app_instance_ids = create_ec2_instances(security_group_id, subnet_ids, user_data_encoded_fe, instance_fe_app)        
    print(f"React App Frontend instance: {fe_app_instance_ids}")
    instance_app = ec2_resource.Instance(fe_app_instance_ids)
    instance_app.wait_until_running()
    print(f"Instance s1 {instance_app.instance_id} is now running of ip {instance_app.public_ip_address}.")