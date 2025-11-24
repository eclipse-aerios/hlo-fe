""""
    Module for conformance with NGSI-LD data model and API
"""
from typing import List, Dict
import app.app_models.aeriOS_continuum as aeriOS_c
from app.api_clients.cb_client import CBClient
from app.utils.log import get_app_logger
from app.utils import continuum_utils


class aeriOSNgsild:
    """"
        Class to ensure we conform to aeriOS continuum NGSI-LD model
        Class to POST to Orion-CB aeriOS ngsi-ld entities
    """

    def __init__(self, aeriOS_json: List[Dict]):
        self.logger = get_app_logger()
        self.cb_client = CBClient()
        self.success = True
        self.aeriOS_json = aeriOS_json

    def run(self):
        """
            Class executor
        """
        for item in self.aeriOS_json:
            if isinstance(item, aeriOS_c.Service):
                r = self.create_service_entity(item)
                # FIXME : make a more genral approach
                # Response 409 means service is already registered in the continuum (probably in Finished state)
                # So we restart it, which means:
                #  a) set service components to Starting state and b) service action type to Seploying
                if r == 409:
                    continuum_utils.reset_service_component_starting(
                        entity_id=item.id)
                    continuum_utils.reset_service_deploying(entity_id=item.id)
                    return True
            if isinstance(item, aeriOS_c.ServiceComponent):
                self.create_service_component_entity(item)
            if isinstance(item, aeriOS_c.InfrastructureElementRequirements):
                self.create_ie_requirements_entity(item)
            if isinstance(item, aeriOS_c.NetworkPort):
                self.create_network_port_entity(item)
        return self.success

    def create_service_entity(self, item: aeriOS_c.Service):
        """
            Create Service NGSI-LD entity
        """
        json_ld_service = {
            "id": item.id,
            "type": "Service",
            "name": {
                "type": "Property",
                "value": item.name
            },
            "description": {
                "type": "Property",
                "value": item.description
            },
            "domainHandler": {
                "type": "Relationship",
                "object": item.domainHandler
            },
            "actionType": {
                "type": "Property",
                "value": item.actionType
            },
            "hasOverlay": {
                "type": "Property",
                "value": item.hasOverlay
            }
        }
        succeeded = False
        r = self.cb_client.create_entity(create_object=json_ld_service)
        if r == 201:
            succeeded = True
            self.logger.info('Created entity with id: %s, entity: %s:',
                             item.id, json_ld_service)
        elif r == 409:
            #FIXME: Service exists check status of service components and decide what to do
            # For now just STOP process
            self.logger.info('Service Entity with id: %s, exists. Entity: %s:',
                             item.id, json_ld_service)
            return 409
        else:
            self.logger.error(
                'Failed to Create entity with id: %s, entity: %s:', item.id,
                json_ld_service)
        self.success &= succeeded

    def create_service_component_entity(self, item: aeriOS_c.ServiceComponent):
        """
            Create Service Component NGSI-LD entity
        """
        json_ld_service_component = {
            "id": f"{item.id}",
            "type": "ServiceComponent",
            **({"infrastructureElement": {"type": "Relationship", "object": item.infrastructureElement} } if item.infrastructureElement and item.infrastructureElement != "urn:ngsi-ld:null" else {}),
            **({"service": {"type": "Relationship", "object": item.service}} if item.service and item.service != "urn:ngsi-ld:null" else {}),
            **({"serviceComponentStatus": {"type": "Relationship", "object": item.serviceComponentStatus}} if item.serviceComponentStatus and item.serviceComponentStatus != "urn:ngsi-ld:null" else {}),
            **({"containerImage": {"type": "Property", "value": item.containerImage}} if item.containerImage and item.containerImage != "urn:ngsi-ld:null" else {}),
            **({"infrastructureElementRequirements": {"type": "Relationship", "object": item.infrastructureElementRequirements}} if item.infrastructureElementRequirements and item.infrastructureElementRequirements != "urn:ngsi-ld:null" else {}),
            **({"networkPorts": {"type": "Relationship", "object": item.networkPorts}} if item.networkPorts and item.networkPorts != "urn:ngsi-ld:null" else {}),
            **({"cliArgs": {"type": "Property", "value":  [cli_dict.model_dump() for cli_dict in item.cliArgs]}} if item.cliArgs and item.cliArgs != "urn:ngsi-ld:null" else {}),
            **({"envVars": {"type": "Property", "value":  [env_dict.model_dump() for env_dict in item.envVars]}} if item.envVars and item.envVars != "urn:ngsi-ld:null" else {}),
            **({"exposePorts": {"type": "Property", "value": item.exposePorts}} if item.exposePorts is not None else {}),
            **({"isJob": {"type": "Property", "value": item.isJob}} if item.isJob is not None else {}),
            **({"isPrivate": {"type": "Property", "value": item.isPrivate}} if item.isPrivate is not None else {}),
            **({"repoUsername": {"type": "Property", "value": item.repoUsername}} if item.repoUsername else {}),
            **({"repoPassword": {"type": "Property", "value": item.repoPassword}} if item.repoPassword else {}),
            # **({"sla": {"type": "Property", "value": item.sla}} if item.sla and item.sla != "urn:ngsi-ld:null" else {}),
        }

        # print(json_ld_service_component)
        succeeded = False
        r = self.cb_client.create_entity(
            create_object=json_ld_service_component)
        if r == 201:
            succeeded = True
            self.logger.info('Created entity with id: %s, entity: %s:',
                             item.id, json_ld_service_component)
        else:
            self.logger.error(
                'Failed to Create entity with id: %s, entity: %s:', item.id,
                json_ld_service_component)
        self.success &= succeeded

    def create_ie_requirements_entity(
            self, item: aeriOS_c.InfrastructureElementRequirements):
        """
            Create Service IE Requirments NGSI-LD entity
        """
        json_ld_ie_requirments = {
            "id": item.id,
            "type": "InfrastructureElementRequirements",
            **({"infrastructureElement": [{"type": "Relationship", "object": ie} for ie in item.infrastructureElement]} if item.infrastructureElement else {}),
            **({"requiredCpuUsage": {"type": "Property", "value": item.requiredCpuUsage}} if item.requiredCpuUsage is not None else {}),
            **({"requiredRam": {"type": "Property", "value": item.requiredRam}} if item.requiredRam is not None else {}),
            **({"cpuArchitecture": {"type": "Relationship", "object": item.cpuArchitecture}} if item.cpuArchitecture and item.cpuArchitecture != "urn:ngsi-ld:null" else {}),
            **({"realTimeCapable": {"type": "Property", "value": item.realTimeCapable}} if item.realTimeCapable is not None else {}),
            **({"energyEfficiencyRatio": {"type": "Property", "value": item.energyEfficiencyRatio}} if item.energyEfficiencyRatio is not None else {}),
            **({"greenEnergyRatio": {"type": "Property", "value": item.greenEnergyRatio}} if item.greenEnergyRatio is not None else {}),
            **({'domainId': {"type": "Relationship", "object": item.domainId}} if item.domainId and item.domainId != "urn:ngsi-ld:null" else {})
        }

        # print(json_ld_ie_requirments)
        succeeded = False
        r = self.cb_client.create_entity(create_object=json_ld_ie_requirments)
        if r == 201:
            succeeded = True
            self.logger.info('Created entity with id: %s, entity: %s:',
                             item.id, json_ld_ie_requirments)
        else:
            self.logger.info('Failed to Creat entity with id: %s, entity: %s:',
                             item.id, json_ld_ie_requirments)
        self.success &= succeeded

    def create_network_port_entity(self, item: aeriOS_c.NetworkPort):
        """
            Create Service Nertwork Port NGSI-LD entity
        """
        json_ld_network_port = {
            "id": item.id,
            "type": "NetworkPort",
            "portNumber": {
                "type": "Property",
                "value": item.portNumber
            },
            "portProtocol": {
                "type": "Property",
                "value": item.portProtocol
            }
        }
        succeeded = False
        r = self.cb_client.create_entity(create_object=json_ld_network_port)
        if r == 201:
            succeeded = True
            self.logger.info('Created entity with id: %s, entity: %s:',
                             item.id, json_ld_network_port)
        else:
            self.logger.info('Created entity with id: %s, entity: %s:',
                             item.id, json_ld_network_port)
        self.success &= succeeded
