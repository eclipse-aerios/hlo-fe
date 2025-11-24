'''
 Docstring
'''
from app.app_models.tosca_models import TOSCA
from app.utils.log import get_app_logger
from app.config import existing_services



class FeEngine:
    '''
        Code Just for show case of endpoints
        All this code to be replaced by real allocaction deallocation code
        Code to access LLO 
    '''

    def __init__(self):
        self.logger = get_app_logger()
        # TBD: find service component exists from Orion-CB (ngsi-ld aeriOSS data model)
        self.existing_services = existing_services

    def tosca2jsonld(self, service_id: str, tosca_dict: TOSCA):
        '''
        Map tosca dict object to json-LD
        Create all ngsi-ld ids bsaed on service_id
        Create ngsi-ld entities
        Return json-ld object
        '''
        self.logger.info('For service %s,.\n Typed TOSCA oject example parsing: %s', service_id, tosca_dict.node_templates)
        return tosca_dict  # Change Me

    def check_service_exists(self, service_id: str):
        '''
        Check if service component exists
        TBD: Update check process
        aeriOSS knoledge graph in Orion-CB should be queried 
        '''
        if service_id in self.existing_services:
            self.logger.info('Existing services: %s', self.existing_services)
            return True
        return False

    def deallocate_service(self, service_id):
        '''
        Deallocate service component
        TBD: remove from aeriOSS knowlegde graph in Orion-CB
        '''
        del self.existing_services[service_id]
        return service_id

    def allocate_service(self, tosca_jsonld, service_id):
        '''
        Register service object in aeriOSS knowlegde graph
        TBD: access and create in Orion-CB
        :param tosca_jsonld: The json-ld object of tosca request
        :return service_id: id of service to be allocated, for kafka message
        '''
        # self.logger.info('TOSCA for allocate: %s', tosca_jsonld)
        existing_services[service_id] = tosca_jsonld
        # TBD: add ngsi-ld client
        return service_id

    def update_service(self, service_id, tosca_jsonld):
        '''
        Update service requirements
        TBD: Update service in aeriOSS knowlegde graph in Orion-CB 
        :param service_id: id of service to be updated
        :param tosca_jsonld: The json-ld object of tosca request
        :return service_id: id of service to be allocated, for kafka message
        '''
        self.logger.info('TOSCA for update: %s', tosca_jsonld)
        self.logger.info('TOSCA ID for update: %s', service_id)
        self.existing_services[service_id] = tosca_jsonld
        # TBD: add ngsi-ld client
        return service_id


    # def get_service(self, service_id: str):
    #     '''
    #     Get service component parameters
    #     '''
    #     parameters = existing_services.get(service_id)
    #     if not parameters:
    #         return False
    #     return parameters
