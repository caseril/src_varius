export password='ubuntu'

echo $password | sudo service inluxdb stop


# avvio della vpn
sudo openvpn --config ./lorenzocase94@gmail.com.ovpn --daemon

#avvio dei docker
for i in {1..3}
do
   sudo docker start $(sudo docker ps -a -q)
done
