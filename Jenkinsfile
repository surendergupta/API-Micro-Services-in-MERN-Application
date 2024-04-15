pipeline {
    agent any
    
    environment {
        DOCKER_HUB_KEY = credentials('docker')
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
                            sh "docker push ${env.DOCKER_IMAGE_FRONTEND}:${env.BUILD_ID}"
                        }
                    }
                }
            }
        }
    }
}