# SampleMERNwithMicroservices

## Git fork and clone

1. Project Link: https://github.com/UnpredictablePrashant/SampleMERNwithMicroservices
2. Fork this repository. For the update from the main repository, you can follow these steps:
```
mkdir SampleMERNwithMicroservices
cd SampleMERNwithMicroservices
git init
git remote add upstream https://github.com/UnpredictablePrashant/SampleMERNwithMicroservices.git
git fetch upstream
git checkout main
git merge upstream/main main
git rebase upstream/main 

```

## Project Steps:
1. Set Up the AWS Environment

- Download AWS CLI below link as per your OS:

```
[ ASW CLI ](https://aws.amazon.com/cli/)

```

- Afers Installation check AWS version:

```
aws --version

```

- Output:

```
aws-cli/2.15.36 Python/3.11.8 Windows/10 exe/AMD64 prompt/off

```

- Now Configure your AWS:

```
aws configure 
AWS Access Key ID : <ACCESS_KEY> 
AWS Secret Access Key: <ACCESS_SECRET_KEY> 
Default region name [us-east-1]: us-east-1
Default output format [json]: json

```

- Now AWS CLI configure Successfully

- Move to BOTO 3

- In Windows you craete virtual envinorment on Linux Skip this.

```
python -m venv venv
venv\Scripts\activate

```

- Install Boto 3

```
pip install boto3

```

- To verify AWS CLI and BOTO 3 configure correctly create test.py file and put below code :

```
import boto3

# Create an S3 client
s3 = boto3.client('s3')

# List all S3 buckets
response = s3.list_buckets()

# Print bucket names
print('S3 Buckets:')
for bucket in response['Buckets']:
    print(f'  {bucket["Name"]}')

```

- To execute the test.py file

```
python .\test.py

```

- Output:

```
S3 Buckets:
  b3devlambda
  codepipeline-us-east-2-783934304898
  daniel-boto3-2
  daniel-boto3-29
  daniel-boto3-3
  daniel-boto3-4
  daniel-boto3-5
  darwinbox

```

- If you getting the S3 list from your AWS Account is show AWS CLI and BOTO 3 configure correctly.


2. Prepare the MERN Application

- Containerize the MERN Application: Create a Dockerfile for each component (frontend and backend).

- Dockerfile of frontend

```
FROM node:18
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]

```

- Dockerfile of backend micro 1

```
FROM node:18
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3001
CMD ["node", "index.js"]

```

- Dockerfile of backend micro 2

```
FROM node:20
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3002
CMD ["node", "index.js"]

```

- Build Docker images for the frontend and backend

```
docker build -t simple_mern_micro_fe .
docker build -t simple_mearn_be_micro_1 .
docker build -t simple_mearn_be_micro_2 .

```

- Check Doker image run

```
docker run -dp 3001:3001 -e "PORT=3001" simple_mearn_be_micro_1
docker run -dp 3002:3002 -e "PORT=3002" -e "MONGO_URL=mongodb+srv://surendergupta:abcd4321A@cluster0.tyk2d2k.mongodb.net/SimpleMicroService" simple_mearn_be_micro_2
docker run -dp 3000:3000 simple_mearn_micro_fe

```

![alt text](./screenshots/image.png)

![alt text](./screenshots/image-1.png)

![alt text](./screenshots/image-2.png)

![alt text](./screenshots/image-3.png)


- Docker Container Stop and Remove


```
docker stop d815e1c39071 7cdc746c44ee 4d9aa90ad51f
docker rm d815e1c39071 7cdc746c44ee 4d9aa90ad51f

```

![alt text](./screenshots/image-4.png)

- Push Docker Images to Amazon ECR:

- Created Amazon ECR repository for each image:

public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-hello-service
public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-profile-service
public.ecr.aws/t5n9y4h0/suri-simple-mern-fe

- Login to aws and local docker image tag and push

```
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/s7f2n3x3

docker tag simple_mearn_micro_fe:latest public.ecr.aws/t5n9y4h0/suri-simple-mern-fe:latest
docker push public.ecr.aws/t5n9y4h0/suri-simple-mern-fe:latest

docker tag simple_mearn_be_micro_1:latest public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-hello-service:latest
docker push public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-hello-service:latest

docker tag simple_mearn_be_micro_2:latest public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-profile-service:latest
docker push public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-profile-service:latest

```

- If you are facing error like:
- Error saving credentials: error storing credentials - err: exit status 1, out: `error storing credentials - err: exit status 1, out: `The stub received bad data.``

- C:\Users\<YOUR_USER>\.docker\config.json file open it in notepad remove `"credsStore": "desktop",` line fron config.json file
- Now login again in docker and then `aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/s7f2n3x3` run it.


![alt text](./screenshots/image-5.png)

![alt text](./screenshots/image-6.png)

![alt text](./screenshots/image-7.png)

3. Version Control
- Create a CodeCommit repository

![alt text](./screenshots/image-8.png)

![alt text](./screenshots/image-9.png)

![alt text](./screenshots/image-10.png)

- Create User IAM Permission ADD Policy

![alt text](./screenshots/image-11.png)

- Click on Add Permission

![alt text](./screenshots/image-12.png)

- I am already Attched Policy for my User

![alt text](./screenshots/image-13.png)

- Click on right side Quick Link -> My security credentials

![alt text](./screenshots/image-14.png)

- Under the AWS CodeCommit Credentials -> HTTPS Git credentials for AWS CodeCommit -> Generate Credentials -> Download Creditial -> DONE

![alt text](./screenshots/image-15.png)

- Push code to AWS CodeCommit

```
git init
git remote add codecommit https://git-codecommit.us-east-1.amazonaws.com/v1/repos/sample-mern-with-microservices
git add .
git commit -m "first codecommit "
git push codecommit main <Ask username and password above we download after policy attached>

```

![alt text](./screenshots/image-16.png)

4. Create EC2 Instance and install java jdk, docker, jenkins

- Create EC2 Instance with Machine: ubuntu, Instance type: t2.medium, Security group name: launch-wizard-1, key:jenkins
- Connect with SSH 
```
  chmod 400 "jenkins.pem"
  ssh -i "jenkins.pem" ubuntu@ec2-44-201-113-107.compute-1.amazonaws.com
```

- Installation of JDK

```
sudo apt update
sudo apt install fontconfig openjdk-17-jre
java -version
```

- Installation of Jenkins

```
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc]" \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt-get update
sudo apt-get install jenkins
```

- Installation of Docker
```
sudo apt-get install docker.io -y
sudo usermod -aG docker $USER
sudo chmod 666 /var/run/docker.sock
```

- Enable Port 8080 in Ec2 Security Group
![add 8080 port on EC2 Jenkins Instance](./screenshots/image-17.png)

- Open EC2 <Instance_public_ip>:8080 on browser

- Open EC2 Connected terminal and hit below command:

```
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

- Setpup Jenkins with user like i.e., user: admin and pass: admin

- Install Plugins
  - Docker
  - Docker API Plugin
  - Docker Commons Plugin
  - docker-build-step
  - Amazon ECR plugin
  - AWS Code Commit Jobs Plugin
  - AWS CodeCommit URL Helper
  - AWS CodeCommit Trigger Plugin

- Setup Global credentials
  - Dashboard -> Manage Jenkins -> Credentials -> System -> Global credentials (unrestricted) -> Add Credentials
  - AWS Credentials
  - Docker
  - AWS CodeCommit

![Credentials](./screenshots/image-18.png)

- Create New Job of Pipeline with name of SampleMERNwithMicroservices
- Under the Pipeline below code :

```
pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE_FRONTEND = 'public.ecr.aws/t5n9y4h0/suri-simple-mern-fe'
        DOCKER_IMAGE_BACKEND_S1 = 'public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-hello-service'
        DOCKER_IMAGE_BACKEND_S2 = 'public.ecr.aws/t5n9y4h0/suri-simple-mern-be-micro-profile-service'        
        AWS_DEFAULT_REGION="us-east-1"         
        AWS_CODE_COMMIT_URL = 'https://git-codecommit.us-east-1.amazonaws.com/v1/repos/sample-mern-with-microservices'
        AWS_CODE_COMMIT_BRANCH = 'master'        
    }
    
    stages {
        stage('Checkout from Git'){
            steps{
                git credentialsId: 'aws-codecommit',  branch: env.AWS_CODE_COMMIT_BRANCH, url: env.AWS_CODE_COMMIT_URL
            }
        }
        stage('Logging into AWS ECR') {
            steps {
                sh 'docker logout'
                withCredentials([usernamePassword(credentialsId: 'docker', usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                    sh "echo -n ${DOCKER_PASSWORD} | docker login -u ${DOCKER_USERNAME} --password-stdin"
                }
                withCredentials([aws(credentialsId: 'aws-config', region: env.AWS_REGION )]) {
                    sh 'aws ecr-public get-login-password --region ${AWS_DEFAULT_REGION} | docker login --username AWS --password-stdin public.ecr.aws/t5n9y4h0'
                }
            }
        }
        stage("Docker Build & Push TO ECR"){
            parallel {
                stage('build backend hello service image') {
                    steps {
                        script {
                            dockerImage = docker.build("${env.DOCKER_IMAGE_BACKEND_S1}:${env.BUILD_ID}", "./backend/helloService")
                            sh "docker push ${env.DOCKER_IMAGE_BACKEND_S1}:${env.BUILD_ID}"
                        }
                    }
                }
                stage('build backend profile service image') {
                    steps {
                        script {
                            dockerImage = docker.build("${env.DOCKER_IMAGE_BACKEND_S2}:${env.BUILD_ID}", "./backend/profileService")
                            sh "docker push ${env.DOCKER_IMAGE_BACKEND_S2}:${env.BUILD_ID}"
                        }
                    }
                }
                stage('build frontend image') {
                    steps {
                        script {
                            dockerImage = docker.build("${env.DOCKER_IMAGE_FRONTEND}:${env.BUILD_ID}", "./frontend")
                            // sh "docker tag ${env.DOCKER_IMAGE_FRONTEND}:${IMAGE_TAG} ${env.DOCKER_IMAGE_FRONTEND}:${env.BUILD_ID}"
                            sh "docker push ${env.DOCKER_IMAGE_FRONTEND}:${env.BUILD_ID}"
                        }
                    }
                }
            }
        }
    }
}

```

- Apply and Save It.
- Click on Build Now

![Pipeline Result](./screenshots/image-19.png)

- Trigger the Jenkins jobs whenever there's a new commit in the CodeCommit repository
- Add Policy of Jenins User using IAM 
  - AmazonSNSFullAccess
  - AmazonSQSFullAccess
  - AWSAppRunnerServicePolicyForECRAccess

  ![alt text](./screenshots/image-21.png)

- Create SNS Topic

![alt text](./screenshots/image-23.png)

- Create SQS Queues Set Name and Everything Default

![alt text](./screenshots/image-22.png)

- Create Subscription of SNS TOPIC created earlier

![alt text](./screenshots/image-24.png)

- Subscribe to AMAZONE SNS Topic

![alt text](./screenshots/image-25.png)

- After Subscribe to AMAZONE SNS Topic Status Confirmed

![alt text](./screenshots/image-26.png)

- Create Trigger

![alt text](./screenshots/image-20.png)

![alt text](./screenshots/image-27.png)

- Now back to Jenkins 
  - Dashboard -> SampleMERNwithMicroservices -> Configuration
  - Setup below
![alt text](./screenshots/image-28.png)

- Webhook AWS CodeCommit Complete Through SNS and SQS
- Now whenever we push code to CodeCommit Auto Jenkins Pipeline executed




