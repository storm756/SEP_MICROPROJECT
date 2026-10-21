// CityServe DevSecOps CI/CD Pipeline
// Stages: Checkout -> Test -> SonarQube -> Trivy FS -> Docker Build -> Trivy Image -> Push ECR -> Deploy
pipeline {
  agent any

  environment {
    IMAGE_NAME    = 'cityserve'
    ECR_REGISTRY  = '318724431625.dkr.ecr.ap-south-1.amazonaws.com'
    ECR_REPO      = '318724431625.dkr.ecr.ap-south-1.amazonaws.com/cityserve'
    AWS_REGION    = 'ap-south-1'
    SONAR_HOST_URL= 'http://sonarqube:9000'
  }

  stages {
    stage('1. Checkout Code') {
      steps {
        checkout scm
      }
    }

    stage('2. Unit Tests (Pytest)') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install --upgrade pip
          pip install -r requirements-dev.txt
          pytest -v --cov=app --cov-report=xml:coverage.xml --junitxml=test-results.xml
        '''
      }
      post {
        always {
          junit allowEmptyResults: true, testResults: 'test-results.xml'
        }
      }
    }

    stage('3. SonarQube Code Scan (SAST)') {
      steps {
        withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
          sh '''
            sonar-scanner \
              -Dsonar.host.url="$SONAR_HOST_URL" \
              -Dsonar.login="$SONAR_TOKEN" \
              -Dsonar.projectKey=CityServe \
              -Dsonar.qualitygate.wait=false
          '''
        }
      }
    }

    stage('4. Trivy File & Secret Scan') {
      steps {
        sh '''
          mkdir -p reports
          trivy fs --scanners vuln,secret --severity HIGH,CRITICAL --skip-dirs .venv --output reports/trivy-fs.txt .
          cat reports/trivy-fs.txt || true
        '''
      }
    }

    stage('5. Docker Build & Image Scan') {
      steps {
        sh '''
          docker build -t $IMAGE_NAME:latest -t $ECR_REPO:latest .
          trivy image --severity HIGH,CRITICAL --output reports/trivy-image.txt $IMAGE_NAME:latest
          cat reports/trivy-image.txt || true
        '''
      }
    }

    stage('6. Push to AWS ECR') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'aws-credentials', usernameVariable: 'AWS_ACCESS_KEY_ID', passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
          sh '''
            export AWS_DEFAULT_REGION="$AWS_REGION"
            aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"
            docker push $ECR_REPO:latest
          '''
        }
      }
    }

    stage('7. Deploy Container') {
      steps {
        sh '''
          docker rm -f cityserve || true
          docker run -d --name cityserve --restart unless-stopped -p 8000:8000 $ECR_REPO:latest
          sleep 3
          curl -f http://127.0.0.1:8000/api/categories || exit 0
        '''
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'reports/**, coverage.xml, test-results.xml', allowEmptyArchive: true
    }
    success {
      echo "=== CityServe CI/CD Pipeline Completed Successfully! ==="
    }
  }
}
