
To build backend image for datapod from the updated code 
```
 sudo docker build -t datapod_ubuntu_1604 .
 ##this will not run  the container 
 sudo docker create -ti --name datapod_container  datapod_ubuntu_1604 bash
	
 ##this will run the container
 sudo docker run  -p 8000:8000 -it --name datapod_ubuntu_1604_container datapod_ubuntu_1604
 sudo docker cp datapod_ubuntu_1604_container:/releases/Datapod_ubuntu <Destination to copy>
 ```

To be used with UPX
Download UPX binary from their official repository and copy it to /usr/local/share

```
pyinstaller Datapod_ubuntu.spec --upx-dir=/usr/local/share   --distpath releases/
```

