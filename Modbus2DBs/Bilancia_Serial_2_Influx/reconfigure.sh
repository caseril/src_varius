#bash!

# da eseguire in seguito a modifiche a file di configurazione o software

export sudo_password='sarego'

echo $sudo_password | sudo -S docker kill serial_2_influxdb
sudo  docker rm serial_2_influxdb

sudo docker-compose build
# RUN con apertura della porta seriale
sudo docker run --device=/dev/ttyUSB0 --privileged --name serial_2_influxdb -d serial_2_influxdb
