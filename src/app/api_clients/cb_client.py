'''
 NGSI-LD REST API Client
'''
import json
import requests
from app import config
from app.utils.decorators import catch_requests_exceptions
from app.api_clients import k8s_shim_client


class CBClient:
    '''
        Client to query CB
          query entities/{entity_id}
             or
          query entities/
        ... ngsi-ld url params welcome
          patch entity
    '''

    def __init__(self):
        self.api_url = config.CB_URL
        self.api_port = config.CB_PORT
        self.url_version = config.URL_VERSION
        self.m2m_cb_token = k8s_shim_client.get_m2m_cb_token()
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'aeriOS': 'true',
            'Authorization': f'Bearer {self.m2m_cb_token}'
        }

    @catch_requests_exceptions
    def query_entity(self, entity_id, ngsild_params) -> dict:
        '''
            Query entity with ngsi-ld params
            :input
            @param entity_id: the id of the queried entity
            @param ngsi-ld: the query params
            :output
            ngsi-ld object
        '''
        entity_url = f'{self.api_url}:{self.api_port}/{self.url_version}entities/{entity_id}?{ngsild_params}'
        response = requests.get(entity_url, headers=self.headers, timeout=15)
        response.raise_for_status()
        return response.json()

    @catch_requests_exceptions
    def query_entities(self, ngsild_params):
        '''
            Query entities with ngsi-ld params
            :input
            @param ngsi-ld: the query params
            :output
            ngsi-ld object
        '''
        entity_url = f"{self.api_url}:{self.api_port}/{self.url_version}entities?{ngsild_params}"
        response = requests.get(entity_url, headers=self.headers, timeout=15)
        response.raise_for_status()
        return response.json()

    @catch_requests_exceptions
    def patch_entity(self, entity_id, upd_object: dict) -> dict:
        '''
            Upadte entity in aeriOS contiunuum
            :input
            @param entity_id: the id of the queried entity
            @param upd_object: the  json object to update the entity with
            :output
            
        '''
        entity_url = f'{self.api_url}:{self.api_port}/{self.url_version}entities/{entity_id}'
        # print(entity_url)
        # print(upd_object)
        response = requests.patch(entity_url,
                                  headers=self.headers,
                                  data=json.dumps(upd_object),
                                  timeout=1)
        response.raise_for_status()
        return response.status_code

    @catch_requests_exceptions
    def patch_entity_attr(self, entity_id, attr, upd_object: dict) -> dict:
        '''
            Do NOT use this one, prefer the patch above
            Upadte entity in aeriOS contiunuum
            :input
            @param entity_id: the id of the queried entity
            @attr: the attribute to be updated
            @param upd_object: the  json object to update the entity with
            :output
            
        '''
        entity_url = f'{self.api_url}:{self.api_port}/{self.url_version}entities/{entity_id}/attrs/{attr}'
        response = requests.patch(entity_url,
                                  headers=self.headers,
                                  data=json.dumps(upd_object),
                                  timeout=15)
        response.raise_for_status()
        return response.status_code

    @catch_requests_exceptions
    def create_entity(self, create_object: dict) -> int:
        '''
            Create entity in aeriOS contiunuum
            :input
            @param create_object: the  json object to update the entity with
            :output
            
        '''
        entity_url = f'{self.api_url}:{self.api_port}/{self.url_version}entities'

        response = requests.post(entity_url,
                                 headers=self.headers,
                                 data=json.dumps(create_object),
                                 timeout=1)
        if response.status_code == 409:
            #FIXME: Service exists, check service components status
            return 409
        response.raise_for_status()
        return response.status_code

    @catch_requests_exceptions
    def delete_entity(self, entity_id) -> int:
        '''
            Upadte entity in aeriOS contiunuum
            :input
            @param entity_id: the id of the queried entity
            @param upd_object: the  json object to update the entity with
            :output
            
        '''
        entity_url = f'{self.api_url}:{self.api_port}/{self.url_version}entities/{entity_id}'
        if not entity_id:
            raise ValueError("Entity ID must be provided for deletion.")
        if not isinstance(entity_id, str):
            raise TypeError("Entity ID must be a string.")
        if not entity_id.startswith("urn:ngsi-ld:"):
            entity_id = f"urn:ngsi-ld:{entity_id}"
        response = requests.delete(entity_url, headers=self.headers, timeout=1)
        return response.status_code
