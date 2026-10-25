pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        PYTHON = 'C:\\Users\\Asus\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verify Project Structure') {
            steps {
                bat '''
                    if not exist v1\\app.py exit /b 1
                    if not exist v2\\app.py exit /b 1
                    if not exist v3\\app.py exit /b 1
                    if not exist v1\\requirements.txt exit /b 1
                    if not exist v2\\requirements.txt exit /b 1
                    if not exist v3\\requirements.txt exit /b 1
                '''

                echo 'All three application versions exist.'
            }
        }

        stage('Verify Python') {
            steps {
                bat '"%PYTHON%" --version'
                bat '"%PYTHON%" -m pip --version'
            }
        }

        stage('Install Dependencies') {
            steps {
                bat '"%PYTHON%" -m pip install -r v1/requirements.txt'
                bat '"%PYTHON%" -m pip install -r v2/requirements.txt'
                bat '"%PYTHON%" -m pip install -r v3/requirements.txt'
            }
        }

        stage('Verify Flask') {
            steps {
                bat '"%PYTHON%" -m pip show Flask'
            }
        }

        stage('Build Summary') {
            steps {
                echo 'Inventory System v1, v2 and v3 passed the dependency and structure checks.'
            }
        }
    }
}