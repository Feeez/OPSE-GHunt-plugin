#!/usr/bin/python3
# -*- coding: utf-8 -*-

#OPSE imports
from classes.Profile import Profile
from classes.account.WebsiteAccount import WebsiteAccount
from classes.types.OpseAddress import OpseAddress
from classes.types.OpseStr import OpseStr
from tools.Tool import Tool

from utils.DataTypeInput import DataTypeInput
from utils.DataTypeOutput import DataTypeOutput
from utils.utils import print_debug, print_error, print_warning

#GHunt imports
from ghunt import globals as gb
from ghunt.helpers.utils import get_httpx_client
from ghunt.objects.base import GHuntCreds
from ghunt.apis.peoplepa import PeoplePaHttp
from ghunt.apis.vision import VisionHttp
from ghunt.helpers import gmaps, playgames, auth, calendar as gcalendar, ia
from ghunt.helpers.knowledge import get_user_type_definition
from ghunt.objects.encoders import GHuntEncoder
from geopy.geocoders import Nominatim
from ghunt.helpers.gmaps import *
import httpx

# Other imports
import json
import trio


class GHuntTool(Tool):
    """
    Class which describe a GHunt tool
    """
    deprecated = False

    def __init__(self):
        super().__init__()

    @staticmethod
    def get_config() -> dict[str]:
        return {
            'active': True,
            'deprecated': False
        }

    @staticmethod
    def get_lst_input_data_types() -> dict[str, bool]:
        return {
            DataTypeInput.EMAIL: True
        }

    @staticmethod
    def get_lst_output_data_types() -> list[str]:
        return [
            DataTypeOutput.ACCOUNT,
            DataTypeOutput.FIRSTNAME,
            DataTypeOutput.MIDDLENAME,
            DataTypeOutput.LASTNAME,
        ]

    async def getProbableLocation(self, as_client: httpx.AsyncClient, email_address):
        if not as_client:
            as_client = get_httpx_client()

        ghunt_creds = GHuntCreds()
        ghunt_creds.load_creds()
        
        people_pa = PeoplePaHttp(ghunt_creds)

        is_found, target = await people_pa.people_lookup(as_client, email_address, params_template="max_details")

        err, stats, reviews, photos = await gmaps.get_reviews(as_client, target.personId)

        reviews_and_photos: List[MapsReview|MapsPhoto] = reviews + photos
        if err != "private" and (err == "empty" or not reviews_and_photos):
            return

        geolocator = Nominatim(user_agent="nominatim")

        confidence, locations = calculate_probable_location(geolocator, reviews_and_photos, gb.config.gmaps_radius)
        
        return locations, confidence

    async def hunt(self, as_client: httpx.AsyncClient, email_address: str):
        if not as_client:
            as_client = get_httpx_client()
        
        ghunt_creds = GHuntCreds()
        ghunt_creds.load_creds()
        
        if not ghunt_creds.are_creds_loaded():
            raise Exception("[-] Creds aren't loaded. Are you logged in ?")
        
        if not auth.check_cookies(ghunt_creds.cookies):
            raise Exception("[-] Seems like the cookies are invalid. Exiting...")
        
        people_pa = PeoplePaHttp(ghunt_creds)
        
        vision_api = VisionHttp(ghunt_creds)
        
        is_found, target = await people_pa.people_lookup(as_client, email_address, params_template="max_details")
        
        if not is_found:
            return None
        
        containers = target.sourceIds
        
        if not "PROFILE" in containers:
            raise Exception("[-] Given information does not match a public Google Account.")
        
        container = "PROFILE"
        
        err, stats, reviews, photos = await gmaps.get_reviews(as_client, target.personId)
        
        cal_found, calendar, calendar_events = await gcalendar.fetch_all(ghunt_creds, as_client, email_address)

        if container == "PROFILE":
            json_results = {
                "profile": target,
                "maps": {
                    "photos": photos,
                    "reviews": reviews,
                    "stats": stats
                },
                "calendar": {
                    "details": calendar,
                    "events": calendar_events
                } if cal_found else None
            }
        else:
            json_results = {
                "profile": target
            }
                
        await as_client.aclose()
        return json.loads(json.dumps(json_results['profile'], cls=GHuntEncoder, indent=4))

    def execute(self):
        default_profile = self.get_default_profile()

        accounts = []
        firstNames = []
        lastNames = []
        middleNames = []
        addresses = []
        for mail in default_profile.get_lst_emails():
            try:
                data = trio.run(self.hunt, None, mail)
                try: # Information might not be present in the returned data, thus we escape the reading errors
                    firstNames.append(OpseStr(
                        data_source="GHunt",
                        str_value=data['names']['PROFILE']['firstName']
                        )
                    )
                except Exception as e:
                    print("firstname " + str(e))

                try:
                    lastNames.append(OpseStr(data_source="GHunt", str_value=data['names']['PROFILE']['lastName']))
                except Exception as e:
                    print("lastname " + str(e))

                try:
                    for middlename in data['names']['PROFILE']['fullname'].split()[1:-1]: # remove first and lastname
                        middleNames.append(OpseStr(
                            data_source="GHunt",
                            str_value=middlename)
                        )
                except Exception as e:
                    print("middlename " + str(e))
                
                try:
                    for account in data['inAppReachability']['PROFILE']['apps']:
                        accounts.append(WebsiteAccount(
                            website_url="Google " + account,
                            website_name="Google "+ account,
                            login=mail)
                        )
                except Exception as e:
                    print("accounts " + str(e))

                # Probable location
                try:
                    locations, confidence = trio.run(self.getProbableLocation, None, mail)
                    
                    for loc in locations:
                        addresses.append(OpseAddress(
                            data_source="GHunt",
                            state_code=loc['avg']['postcode'],
                            city=loc['avg']['town'],
                            country=loc['avg']['country'])
                        )
                except Exception as e:
                    print("location " + str(e))

            except Exception as e:
                # Might be an error during the request
                print_error(" " + str(e))
        profile: Profile = default_profile.clone()
        profile.set_lst_accounts(accounts)
        if len(firstNames) > 0: profile.set_firstname(firstNames[0]) # if several first names are found, we arbitrarily decide that the first one is the most correct
        if len(lastNames) > 0: profile.set_lastname(lastNames[0]) # idem for last name
        profile.set_lst_middlenames(middleNames)
        profile.set_lst_addresses(addresses)

        self.append_profile(profile)
