@Library('gaming-jenkins-library') _

pipeline {
    options {
        timeout(time: 60)
        ansiColor('xterm')
        disableConcurrentBuilds()
    }

    agent { label "low-tier-build-agent" }

    environment {
        def project = 'mcp-gsheets'
        def environment = 'test'
        def imageTag = 'latest'
        def serviceNameEcs = "mcp-gsheets-${environment}"
        def shortCommitHash = env.GIT_COMMIT.substring(0, 8)
        def commitUrl = "https://github.com/opera-gaming/${project}/commit/${env.GIT_COMMIT}"
        def branchUrl = "https://github.com/opera-gaming/${project}/tree/${env.GIT_BRANCH}"
        BUILD_DETAILS = "\n- Jenkins: <${env.BUILD_URL}|build ${env.BUILD_DISPLAY_NAME}>.\n - GitHub: <${commitUrl}|${shortCommitHash}> commit, <${branchUrl}|${env.GIT_BRANCH}> branch."
        AWS_REGION = "eu-north-1"
        AWS_ECR_ACCOUNT = "184861730404"
        DOCKER_REGISTRY="${AWS_ECR_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        DOCKER_REPOSITORY="${DOCKER_REGISTRY}/mcp-gsheets"
    }

    stages {
        stage('Build & Push') {
            steps {
                script {
                    sh """
                        ./tools/scripts/build-and-push-docker-image.sh ${shortCommitHash}
                    """
                }
            }
        }
        stage('Deploy') {
            environment {
                GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no"
            }
            steps {
                script {
                    withCredentials([string(credentialsId: 'cloudflare-api-token', variable: 'CLOUDFLARE_API_TOKEN')]) {
                        sshagent(credentials: ['fb1c069e-46c6-4dad-9dae-927c73a2e6c6']) {
                            sh """
                                ./tools/scripts/deploy.sh "mcp-gsheets" ${shortCommitHash} ${environment} ${AWS_REGION}
                            """
                        }
                    }
                }
            }
        }
        stage('ECS deployment status check') {
            steps {
                script {
                    def startDelay = '10'
                    def deploymentStatus = isServiceDeploymentFinished(environment, serviceNameEcs, startDelay, env.AWS_REGION)
                    if (deploymentStatus != 0) {
                        slackSend(channel: 'D039ZS2SXJA', color: '#FF0000', message: "GSheets MCP Server: Deploy ${environment} to ECS ${env.AWS_REGION} failed. ${env.BUILD_DETAILS}\nCheck AWS Console and application logs in ${env.AWS_REGION}.")
                        currentBuild.result = 'ABORTED'
                        error('Deployment failed or timeout exceeded, aborting pipeline.')
                    }
                }
            }
        }
    }

    post {
        success {
            slackSend (channel: 'D039ZS2SXJA', color: '#00FF00', message: "GSheets MCP Server: mainline build and deployment succeeded. ${env.BUILD_DETAILS}\nCheck it out on https://mcp-gsheets.gmx.dev")
        }
        failure {
            slackSend (channel: 'D039ZS2SXJA', color: '#FF0000', message: "GSheets MCP Server: mainline build and deployment failed. ${env.BUILD_DETAILS}")
        }
        always {
            cleanWs()
        }
    }
}
