
#avvio dei docker
for i in {1..3}
do
   sudo docker start $(sudo docker ps -a -q)
done
