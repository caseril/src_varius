#bash!
sudo docker kill modbus_plc2plc_writer
sudo docker rm modbus_plc2plc_writer
# avvio della vpn
#sudo openvpn --config "./../vpn_clients/case94@live.it.ovpn" --daemon

sudo docker-compose build
sudo docker run --name modbus_plc2plc_writer -d modbus_plc2plc_writer
