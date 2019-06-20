
#-*- coding: utf-8 -*-

import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)

def store_credentials(credentials_tbl_obj, username, id_token, access_token, refresh_token):
    try:
        user_id = (credentials_tbl_obj.insert(username=username,  
                                    id_token=id_token, 
                                    access_token= access_token, 
                                    refresh_token=refresh_token)
           .on_conflict_replace()
           .execute())


        # new_entry = credentials_tbl_obj.create(username=username, 
        #                             password=password, 
        #                             id_token=id_token, 
        #                             access_token= access_token, 
        #                             refresh_token=refresh_token)
        # new_entry.save()
        logging.info(f"On insert the credentials userid is {user_id}")
    except Exception as e:
        logging.error(f"Couldnt save data to credentials_tbl because of {e}")
    return 


def get_credentials(credentials_tbl_obj):
    try:
        for person in credentials_tbl_obj.select().dicts():
            return person
    except Exception as e:
        logging.error(f"Couldnt fetch credentials data  {e}")
    return 