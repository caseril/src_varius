#bash!

# da eseguire in seguito a modifiche a file di configurazione o software

export sudo_password='sarego'

# avvio di influxdb
echo $sudo_password | sudo service influxdb stop

sudo docker run --name influxdb -p 8086:8086 \
      -v influxdb:/var/lib/influxdb \
      -d influxdb:1.8
      
# avvio di grafana
sudo docker run --name grafana -d -p 3000:3000 grafana/grafana

sudo docker-compose build
# RUN con apertura della porta seriale
sudo docker run -v /dev:/dev --privileged --name serial_2_influxdb -d serial_2_influxdb
