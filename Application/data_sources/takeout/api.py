import shutil
import asyncio
from sanic import Blueprint
from sanic import response
import os
from errors_module.errors import APIBadRequest
from .parse_emails import TakeoutEmails
from .location import  LocationHistory
from .purchases_n_reservations import PurchaseReservations
import base64
import  database_calls.db_purchases_n_reservations as q_purchase_db
import  database_calls.db_images as q_images_db
from   database_calls.db_emails  import match_text as e_match_text
from utils.utils import check_production
from .images import ParseGoogleImages
import datetime
import coloredlogs, verboselogs, logging
verboselogs.install()
coloredlogs.install()
logger = logging.getLogger(__file__)
TAKEOUT_BP = Blueprint("", url_prefix="/takeout/")




async def parse_takeout(config):
    ##add this if this has to executed periodically
    ##while True:
    logger.info('Periodic task has begun execution')

    instance = await TakeoutEmails(config)
    # instance.download_emails()

    await asyncio.gather(*[instance.download_emails(), 
                purchase_n_reservations(config),
                parse_images(config)])

    logger.info('Periodic task has finished execution')

    
    return 

@TAKEOUT_BP.post('parse')
async def parse_takeout_api(request):
    """
    To get all the assets created by the requester
    """
    request.app.config.VALIDATE_FIELDS(["path"], request.json)

    if not os.path.exists(request.json["path"]):
        raise APIBadRequest("This path doesnt exists")

    logger.info("Copying and extracting takeout data")
    shutil.unpack_archive(request.json["path"], extract_dir=request.app.config.RAW_DATA_PATH, format=None)
    
        
    request.app.add_task(parse_takeout(request.app.config))
    # request.app.add_task(purchase_n_reservations(request.app.config))
    # asyncio.ensure_future(parse_emails(request.app.config))
    # asyncio.ensure_future(purchase_n_reservations(request.app.config))
    
    

    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Takeout data parsing has been Started and you will be notified once it is complete"
        })


@TAKEOUT_BP.get('purchase_n_reservations')
@check_production()
async def purchase_n_reservations_api(request):
    """
    To get all the assets created by the requester
    """
    await purchase_n_reservations(request.app.config)
    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Successful"
        })


async def purchase_n_reservations(config):
    path = os.path.join(config.RAW_DATA_PATH, "Takeout")

    ins = await PurchaseReservations(path, config)
    reservations, purchases = await ins.parse()
    
    for purchase in purchases:
        #print (purchase)
        q_purchase_db.store_purchase(config.PURCHASES_TBL, purchase)
    
    for reservation in reservations:
        logger.info(reservation)
    return 



@TAKEOUT_BP.get('purchase_n_reservations/filter')
async def purchase_n_reservation_filter(request):
    """
    Page is the page number 
    NUmber is the number of items on the page 
    """
    #request.app.config.VALIDATE_FIELDS(["page", "number"], request.json)

    if request.args.get("page"):
        try:
            page = int(request.args.get("page"))
        except:
            raise APIBadRequest("Invalid page type")

    else:
        page = 1


    if request.args.get("number"):
        try:
            number = int(request.args.get("number"))
        except:
            raise APIBadRequest("Invalid Number type")
    else:
        number = request.app.config.DEFAULT_ITEMS_NUMBER


    result =  [q_purchase_db.format(request.app.config, purchase) for purchase in \
                q_purchase_db.filter_merchant_name(request.app.config.PURCHASES_TBL, 
                page, number,  request.args.get("merchant_name"))] 

    return response.json(
        {
        'error': False,
        'success': True,
        "data": result,
        "message": None
        })





@TAKEOUT_BP.get('images/filter')
async def images_filter(request):
    """
    To get all the assets created by the requester
    """
    #request.app.config.VALIDATE_FIELDS(["page", "number"], request.json)
    if request.args.get("page"):
        page = request.args.get("page")
    else:
        page = 1


    if request.args.get("number"):
        number = request.args.get("number")
    else:
        number = 200


    images = q_images_db.filter_date(request.app.config.IMAGES_TBL, page, number,  time=None)
    for image in images:
        creation_time = image.pop("creation_time")
        #data:image/png;base64
        image.update({"creation_time": creation_time.strftime("%Y-%m-%d")})

    logger.success(images)
    return response.json(
        {
        'error': False,
        'success': True,
        "data": images,
        "message": None
        })





@TAKEOUT_BP.get('images')
@check_production()
async def parse_images_api(request):
    """
    To get all the assets created by the requester
    """
    
    await prase_images(request.app.config)
    return response.json(
        {
        'error': False,
        'success': True,
        "data": "Successful"
        })

async def parse_images(config):
    path = os.path.join(config.RAW_DATA_PATH, "Takeout")

    ins = await ParseGoogleImages(path, config)
    await ins.parse()
    images_data = ins.images_data

    for image_data in images_data:
        image_data.update({"tbl_object": config.IMAGES_TBL}) 
    
    await asyncio.gather(*[q_images_db.store(**image_data) for image_data in images_data])
    return 



@TAKEOUT_BP.get('location_history')
@check_production()
async def takeout_location_history(request):
    """
    To get all the assets created by the requester
    """
    
    path = os.path.join(request.app.config.user_data_path, "Takeout")
    
    if not os.path.exists(path):
        raise Exception(f"Path {path} doesnt exists")
    
    
    ins =  LocationHistory(path, request.app.config.db_dir_path)
    results = ins.format()
    
    return response.json(
        {
        'error': False,
        'success': True,
        "data": results
        })
    

@TAKEOUT_BP.get('email/match_text')
async def match_text_email(request):
    


    if request.args.get("page"):
        page = request.args.get("page")
    else:
        page = 1


    if request.args.get("number"):
        number = request.args.get("number")
    else:
        number = 200

    if not request.args.get("match_string"):
        raise APIBadRequest("get params match_string is required")

    matching_string = request.args.get("match_string") 


    logging.info(request.args)
    logging.info(f"This is the matching string {matching_string}")


    res = e_match_text(request.app.config.EMAILS_TBL, request.app.config.INDEX_EMAIL_CONTENT_TBL, \
            matching_string , page, number)

    return response.json(
        {
        'error': False,
        'success': True,
        "data": res
        })
    

