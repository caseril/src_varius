#bash!

sudo docker kill fastapi_edgedev_write && sudo docker rm fastapi_edgedev_write
sudo docker-compose build
sudo docker run --name fastapi_edgedev_write -d fastapi_edgedev_write


#uvicorn main:app --reload
