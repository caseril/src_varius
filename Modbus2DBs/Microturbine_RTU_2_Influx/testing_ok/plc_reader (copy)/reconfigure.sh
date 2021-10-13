#bash!

# da eseguire in seguito a modifiche a file di configurazione o software

export sudo_password='sarego'

echo $sudo_password | sudo -S docker kill plc_read_2_influxdb
sudo  docker rm plc_writer

sudo docker-compose build
sudo docker run --name plc_read_2_influxdb -d plc_read_2_influxdb
