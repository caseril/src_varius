#bash!
sudo docker kill mb_plc2azure_directmethod
sudo docker rm mb_plc2azure_directmethod

sudo docker-compose build
sudo docker run --name mb_plc2azure_directmethod -d mb_plc2azure_directmethod
