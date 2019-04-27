#!usr/bin/env python

from abc import ABC, abstractmethod

class DecentralizeFilesystem(ABC):
    def __init__(self):
        super().__init__()
    

    @abstractmethod
    def check_filesystem(self, dir_name=None, uri=None):
        """
        check if filesystem is online or not
        if yes:
            return the id of the node
        """

        return 




    @abstractmethod
    def initiate_filesystem(self, dir_name=None, uri=None):
        """
        Retrieve directory contents from the directory name or on the basis of the 
        uri fo the diretory storage
        """

        return 





    @abstractmethod
    def store_file(self, file_object):
        """
        Methos to implement file storage on decentral cloud
        """
        return 

 

    @abstractmethod
    def retrieve_file(self, file_name=None, uri=None):
        """
        Retrieve file on the basis of the file_name or uri
        """
        return 

    @abstractmethod
    def retrieve_directory_contents(self, dir_name=None, uri=None):
        """
        Retrieve directory contents from the directory name or on the basis of the 
        uri fo the diretory storage
        """

        return 




    @abstractmethod
    def list_file_directories(self, user_id):
        """
        List file or directories stored by the user on ditributed file system
        """
        return 