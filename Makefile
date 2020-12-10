deploy:
	scp aemnet_msgs.py datalogger.py serial_msgs.py m202a:~/m202a_project_rpi/

pull:
	scp m202a:~/m202a_project_rpi/*.db ./dbs/

clean:
	rm -f dbs/*
