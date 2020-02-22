# happychain
Greeting platform for teams

config.yml:
`app:
  debug: False
  app_name: "HappyChain"
  log_level: "DEBUG"
  log_format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  transfer_secret: "your_random_transfer_secret"
db:
  host: "mysql_host"
  port: "mysql_port"
  name: "mysql_db_name"
  user: "mysql_user"
  passwd: "mysql_passwd"
bip:
  environment: "TEST or PROD"
  user: "username"
  passwd: "passwd"
flask:
  basic_auth:
    username: "username"
    password: "password"
    force: False
    realm: ""`
