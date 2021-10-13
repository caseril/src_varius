#bash!

# da eseguire in seguito a modifiche a file di configurazione o software

export sudo_password='sarego'

echo $sudo_password | sudo -S docker kill plc_writer
sudo  docker rm plc_writer

sudo docker-compose build
sudo docker run --name plc_writer -d plc_writer
