def remote = [:]
remote.name = 'efullmakt.io'
remote.host = 'efullmakt.io'
remote.user = 'root'
remote.identityFile = '~/.ssh/key'
remote.allowAnyHosts = true

pipeline {
  agent any
  stages {
    stage('Build') {
      steps {
        sh 'docker-compose -f docker-compose.test.yml -H tcp://localhost:2375 build'
      }
    }

    stage('Test') {
      steps {
        sh 'docker-compose -f docker-compose.test.yml -H tcp://localhost:2375 up -V --abort-on-container-exit'
      }
    }

    stage('Deploy') {
      when { branch 'production' }
      steps {
        sshCommand(remote: remote, command: 'cd efullmakt-server && docker-compose build api')
        sshCommand(remote: remote, command: 'cd efullmakt-server && docker-compose stop api')
        sshCommand(remote: remote, command: 'cd efullmakt-server && docker-compose rm api')
        sshCommand(remote: remote, command: 'cd efullmakt-server && docker-compose create --force-recreate api')
        sshCommand(remote: remote, command: 'cd efullmakt-server && docker-compose start api')
        echo 'Deployment complete'
      }
    }

  }
  post { 
        always { 
            sh 'docker-compose -f docker-compose.test.yml -H tcp://localhost:2375 down -v || true'
            cleanWs()
        }
    }
}