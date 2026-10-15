// CityServe DevSecOps Pipeline: Build -> Test -> SAST -> SCA -> Image Build -> Image Scan -> IaC Scan -> Deploy
pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    timeout(time: 40, unit: 'MINUTES')
  }

  parameters {
    booleanParam(name: 'FAIL_ON_CRITICAL', defaultValue: false, description: 'Fail the build if image contains fixable CRITICAL vulnerabilities')
    booleanParam(name: 'PUSH_IMAGE',       defaultValue: false, description: 'Push image to Docker Hub (requires dockerhub-creds credential)')
    booleanParam(name: 'DEPLOY',           defaultValue: true,  description: 'Deploy the container locally on port 8000')
  }

  environment {
    IMAGE_NAME     = 'cityserve'
    IMAGE_TAG      = "${env.BUILD_NUMBER ?: '1'}"
    DOCKERHUB_USER = 'storm756'
    SONAR_HOST_URL = 'http://sonarqube:9000'
    CONTAINER_NAME = 'cityserve-web'
    HOST_PORT      = '8000'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Install & Unit Test') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install --upgrade pip
          pip install -r requirements-dev.txt
          pytest -v --cov=app --cov-report=xml:coverage.xml --cov-report=term --junitxml=test-results.xml
        '''
      }
      post {
        always {
          junit allowEmptyResults: true, testResults: 'test-results.xml'
        }
      }
    }

    stage('SonarQube Analysis (SAST)') {
      steps {
        withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
          sh '''
            sonar-scanner \
              -Dsonar.host.url="$SONAR_HOST_URL" \
              -Dsonar.login="$SONAR_TOKEN" \
              -Dsonar.token="$SONAR_TOKEN" \
              -Dsonar.projectKey=CityServe \
              -Dsonar.qualitygate.wait=false
          '''
        }
      }
    }

    stage('Trivy: Dependency & Secret Scan') {
      steps {
        sh '''
          mkdir -p reports
          trivy fs --scanners vuln,secret --severity LOW,MEDIUM,HIGH,CRITICAL \
            --skip-dirs .venv --format table --output reports/trivy-fs.txt .
          trivy fs --scanners vuln,secret --skip-dirs .venv \
            --format json --output reports/trivy-fs.json .
          cat reports/trivy-fs.txt
        '''
      }
    }

    stage('Docker Build') {
      steps {
        sh 'docker build -t "$IMAGE_NAME:$IMAGE_TAG" -t "$IMAGE_NAME:latest" .'
      }
    }

    stage('Trivy: Container Image Scan') {
      steps {
        sh '''
          mkdir -p reports
          trivy image --severity LOW,MEDIUM,HIGH,CRITICAL \
            --format table --output reports/trivy-image.txt "$IMAGE_NAME:$IMAGE_TAG"
          trivy image --format json --output reports/trivy-image.json "$IMAGE_NAME:$IMAGE_TAG"
          cat reports/trivy-image.txt
        '''
      }
    }

    stage('Trivy: Security Quality Gate') {
      when { expression { return params.FAIL_ON_CRITICAL } }
      steps {
        sh 'trivy image --exit-code 1 --severity CRITICAL --ignore-unfixed "$IMAGE_NAME:$IMAGE_TAG"'
      }
    }

    stage('Trivy: Terraform (IaC) Scan') {
      steps {
        sh '''
          mkdir -p reports
          trivy config --severity LOW,MEDIUM,HIGH,CRITICAL \
            --format table --output reports/trivy-terraform.txt terraform/
          cat reports/trivy-terraform.txt
        '''
      }
    }

    stage('Push Image') {
      when { expression { return params.PUSH_IMAGE } }
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
          sh '''
            echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
            docker tag "$IMAGE_NAME:$IMAGE_TAG" "$DOCKERHUB_USER/$IMAGE_NAME:$IMAGE_TAG"
            docker tag "$IMAGE_NAME:$IMAGE_TAG" "$DOCKERHUB_USER/$IMAGE_NAME:latest"
            docker push "$DOCKERHUB_USER/$IMAGE_NAME:$IMAGE_TAG"
            docker push "$DOCKERHUB_USER/$IMAGE_NAME:latest"
            docker logout
          '''
        }
      }
    }

    stage('Deploy (Docker Container)') {
      when { expression { return params.DEPLOY } }
      steps {
        sh '''
          docker rm -f "$CONTAINER_NAME" || true
          docker run -d --name "$CONTAINER_NAME" --restart unless-stopped \
            -p "$HOST_PORT:8000" -v cityserve-data:/data \
            --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges \
            "$IMAGE_NAME:$IMAGE_TAG"

          echo "Waiting for container healthcheck..."
          for i in $(seq 1 20); do
            status=$(docker inspect --format '{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "starting")
            echo "Health status: $status"
            if [ "$status" = "healthy" ]; then
              echo "CityServe deployed successfully and healthy!"
              exit 0
            fi
            sleep 3
          done
          docker logs "$CONTAINER_NAME"
          exit 1
        '''
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'reports/**, coverage.xml, test-results.xml', allowEmptyArchive: true
    }
    success {
      echo "=== CityServe is live at http://localhost:${HOST_PORT} ==="
    }
  }
}
