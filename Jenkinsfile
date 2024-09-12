pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'docker.io'
        DOCKER_IMAGE = 'blabbleu/digital_lib'
        DB_HOST = '127.0.0.1'
        DB_PORT = '3306'
        DOCKER_DATABASE_URL = credentials('DOCKER_DATABASE_URL')
        CELERY_BROKER_URL = credentials('CELERY_BROKER_URL')
        CELERY_RESULT_BACKEND = credentials('CELERY_RESULT_BACKEND')
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', credentialsId: 'jenkins-ssh-key', url: 'git@git.mtsolution.com.vn:intern/digital_lib.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def app = docker.build("${env.DOCKER_REGISTRY}/${env.DOCKER_IMAGE}:${env.BUILD_ID}")
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'docker-credentials-id') {
                        def app = docker.image("${env.DOCKER_REGISTRY}/${env.DOCKER_IMAGE}:${env.BUILD_ID}")
                        app.push()
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    sh """
                    docker-compose -f docker-compose.yml pull
                    docker-compose -f docker-compose.yml up -d
                    """
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo 'Build and Deployment succeeded!'
        }
        failure {
            echo 'Build or Deployment failed!'
        }
    }
}
