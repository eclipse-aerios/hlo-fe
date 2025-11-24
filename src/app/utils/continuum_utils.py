'''
 Docstring
'''
from typing import List, Dict
from app.api_clients.cb_client import CBClient
import app.app_models.aeriOS_continuum as aeriOS_C
from app.app_models.aeriOS_continuum import ServiceComponentStatusEnum as status
from app.app_models.aeriOS_continuum import ServiceActionTypeEnum


def check_service_exists(service_id: str) -> bool:
    '''
    Check if service  exists
    :param  service_id: id of the service of which part is service component
    :return True or False
    '''
    cb_client = CBClient()
    jsonld_params = 'format=simplified'
    service_json = cb_client.query_entity(entity_id=service_id,
                                          ngsild_params=jsonld_params)
    if service_json is not None and service_json.get('type') is not None:
        return True
    return False


def get_service_status(service_id: str):
    """
    Return a list of all components of a service with status
    :param service_id: id of service
    :return list of json objects
    [{
        "id": "urn:ngsi-ld:Service:1:Component:d8778501",
        "type": "ServiceComponent",
        "serviceComponentStatus": "urn:ngsi-ld:ServiceComponentStatus:Finished"
    }]
    """
    cb_client = CBClient()
    service_components_status_list = cb_client.query_entities(
        f'type=ServiceComponent&attrs=serviceComponentStatus&q=service=="{service_id}"&format=simplified'
    )
    return service_components_status_list


def check_service_component_exists(service_id: str,
                                   service_component_id: str) -> bool:
    '''
    Check if service component exists
    :param  service_id: id of the service of which part is service component
    :param  service_component_id: id of the service component id
    :return True or False
    '''
    cb_client = CBClient()
    jsonld_params = f'format=simplified&q=service=="{service_id}"'
    scomponent_json = cb_client.query_entity(entity_id=service_component_id,
                                             ngsild_params=jsonld_params)
    if scomponent_json is not None and scomponent_json.get(
            'serviceComponentStatus') is not None:
        if scomponent_json.get('serviceComponentStatus') == status.RUNNING:
            return True
    return False


def set_service_component_status(service_id, scomponent_id,
                                 scomponent_status: str):
    """
        Set the status for a service component in CB
    """
    cb_client = CBClient()
    data = {
        "serviceComponentStatus": {
            "type": "Relationship",
            "object": scomponent_status
        }
    }
    cb_client.patch_entity(entity_id=scomponent_id, upd_object=data)


def set_service_component_status_attr(service_id, scomponent_id,
                                      scomponent_status: str):
    """
        Set the status for a service component in CB
    """
    cb_client = CBClient()

    data = {'type': 'Relationship', 'value': scomponent_status}
    cb_client.patch_entity_attr(entity_id=scomponent_id,
                                attr='serviceComponentStatus',
                                upd_object=data)


def set_service_component_ie(service_id, scomponent_id, allocated_ie_id: str):
    """
        Update IE for Service Component
        Create relationship upon allocation
        Delete relationship upon deallocation
    """
    cb_client = CBClient()
    data = {
        "infrastructureElement": {
            "type": "Relationship",
            "object": allocated_ie_id
        }
    }
    cb_client.patch_entity(entity_id=scomponent_id, upd_object=data)


def set_service_component_ie_attr(service_id, scomponent_id,
                                  allocated_ie_id: str):
    """
        Update IE for Service Component
        Create relationship upon allocation
        Delete relationship upon deallocation
    """
    cb_client = CBClient()
    data = {
        "infrastructureElement": {
            "type": "Relationship",
            "object": allocated_ie_id
        }
    }
    data = {'type': 'Relationship', 'value': allocated_ie_id}
    cb_client.patch_entity_attr(entity_id=scomponent_id,
                                attr='infrastructureElement',
                                upd_object=data)


def get_service_component_status(service_component_id: str,
                                 service_id: str = ""):
    '''
    Check if service component exists
    :param  service_id: id of the service of which part is service component
    :param  service_component_id: id of the service component id
    :return ServiceComponentStatusEnum
    '''
    # FIXME: it is dangerous
    # In fact , we do not need it. It gets paranoid, servicecomponentId already contains service id and a uuid
    # if not service_id:
    #     # based on the naming convention: [urn:ngsi-ld]:[Service:05]:[Component:02]
    #     # Being paranoid? We could do without it also...
    #     scomponent_id = service_component_id
    #     parts = scomponent_id.split(':')
    #     service_id = ':'.join(parts[:4])
    cb_client = CBClient()
    jsonld_params = 'format=simplified'
    scomponent_json = cb_client.query_entity(entity_id=service_component_id,
                                             ngsild_params=jsonld_params)
    if scomponent_json is not None and scomponent_json.get(
            'serviceComponentStatus') is not None:
        return scomponent_json.get('serviceComponentStatus')
    return None


def get_service_components_list(entity_id: str) -> List[str]:
    """
        Get a list with all ids of service components of a service
    """
    cb_client = CBClient()
    scomponents_id_list = []
    service_components_list_json = cb_client.query_entities(
        f'format=simplified&type=ServiceComponent&q=service=="{entity_id}"')
    for scomponent in service_components_list_json:
        scomponents_id_list.append(scomponent.get('id'))
    return scomponents_id_list


def reset_service_component_starting(
        entity_id) -> List[aeriOS_C.ServiceComponent]:
    """
    Get service components from CB
    """
    cb_client = CBClient()

    service_components_list_json = cb_client.query_entities(
        f'format=simplified&type=ServiceComponent&q=service=="{entity_id}"')
    service_components_py = [
        aeriOS_C.ServiceComponent(**item)
        for item in service_components_list_json
    ]
    for scomponent in service_components_py:
        if scomponent.serviceComponentStatus in [
                status.FAILED, status.FINISHED
        ]:
            set_service_component_status(service_id="",
                                         scomponent_id=scomponent.id,
                                         scomponent_status=status.STARTING)


def set_service_components_removing(
        entity_id) -> List[aeriOS_C.ServiceComponent]:
    """
    Get service components from CB
    """
    cb_client = CBClient()

    service_components_list_json = cb_client.query_entities(
        f'format=simplified&type=ServiceComponent&q=service=="{entity_id}"')
    service_components_py = [
        aeriOS_C.ServiceComponent(**item)
        for item in service_components_list_json
    ]
    for scomponent in service_components_py:
        in_state_running: bool = True
        if scomponent.serviceComponentStatus in [
                status.RUNNING, status.FAILED
        ]:
            set_service_component_status(service_id="",
                                         scomponent_id=scomponent.id,
                                         scomponent_status=status.REMOVING)
        else:
            in_state_running = False
    return in_state_running


def get_host_domain():
    """
    Get local domain id
    local=true in ngsi-ld returns domain tha is localy registred in Orion-ld,
    The only locally registered domain is ...local domain
    Returns:
      id of host domain
    """
    cb_client = CBClient()
    jsonld_params = 'type=Domain&format=simplified&local=true&attrs=publicUrl'
    domain_json = cb_client.query_entities(ngsild_params=jsonld_params)
    # We are confident about [0] because each domain has just one domain registered locally
    if domain_json:
        return domain_json[0].get("id")
    else:
        return None


def set_service_destroying(entity_id):
    """
    Set the action type destroying for service  in CB
    Used when delete API endpoint for service called
    Reset to None in Deployment Engine when delete request is handled.
    """
    cb_client = CBClient()
    data = {
        "actionType": {
            "type": "Property",
            "value": ServiceActionTypeEnum.DESTROYING
        }
    }
    cb_client.patch_entity(entity_id=entity_id, upd_object=data)


def reset_service_deploying(entity_id):
    """
    Set the action type deploying for service  in CB
    Used when delete API endpoint for start service 
      called for a service that is already in CB but in a stopped (finished) state
    Reset to None in Deployment Engine when delete request is handled.
    """
    cb_client = CBClient()
    data = {
        "actionType": {
            "type": "Property",
            "value": ServiceActionTypeEnum.DEPLOYING
        },
        "domainHandler": {
            "type": "Relationship",
            "object": get_host_domain()
        }
    }
    cb_client.patch_entity(entity_id=entity_id, upd_object=data)


def check_service_can_be_purged(service_id: str) -> bool:
    """
    Check if a service can be purged (deleted) from the system.
    A service can be purged if it is in a 'FINISHED' state and has no components.
    :param service_id: ID of the service to check
    :return: True if the service can be purged, False otherwise
    """
    cb_client = CBClient()

    query_str = "format=simplified&attrs=actionType"
    # Get the status of the service
    service_status = cb_client.query_entity(entity_id=service_id,
                                            ngsild_params=query_str)
    if service_status.get('actionType') in [ServiceActionTypeEnum.FINISHED, ServiceActionTypeEnum.HANDLED, ServiceActionTypeEnum.DESTROYING]:
        return True
    return False


def get_service_components_for_delete(entity_id: str) -> Dict[str, List[str]]:
    '''
    Get all service components, network ports and infrastructure element requirements
    for a given service entity.
    :param entity_id: ID of the service entity
    :return: Dictionary with lists of IDs for service components, network ports, and infrastructure element requirements
    '''
    cb_client = CBClient()

    # Initialize result structure
    result = {
        "serviceComponentsIds": [],
        "networkPortsList": [],
        "InfrastructureElementRequirementsList": []
    }

    # Query all ServiceComponent entities for this service
    service_components_list_json = cb_client.query_entities(
        f'format=simplified&type=ServiceComponent&q=service=="{entity_id}"')

    # Iterate and collect IDs
    for scomponent in service_components_list_json:
        sc_id = scomponent.get("id")
        if sc_id:
            result["serviceComponentsIds"].append(sc_id)

        # Collect infrastructureElementRequirements (if present)
        ie_req = scomponent.get("infrastructureElementRequirements")
        if ie_req:
            result["InfrastructureElementRequirementsList"].append(ie_req)

        # Collect networkPorts (if present)
        network_ports = scomponent.get("networkPorts", [])
        if isinstance(network_ports, list):
            result["networkPortsList"].extend(network_ports)

    return result


def delete_from_continuum_service_by_id(service_id):
    """
    Purge service and all its components from continuum
    :param service_id: id of the service to delete
    :return: None
    """
    cb_client = CBClient()

    # Get all related IDs
    summary = get_service_components_for_delete(service_id)

    # Delete the main service entity
    cb_client.delete_entity(entity_id=service_id)

    # Delete all NetworkPort entities
    for port_id in summary.get("networkPortsList", []):
        cb_client.delete_entity(entity_id=port_id)

    # Delete all InfrastructureElementRequirements entities
    for ie_req_id in summary.get("InfrastructureElementRequirementsList", []):
        cb_client.delete_entity(entity_id=ie_req_id)

    # Delete all ServiceComponent entities
    for component_id in summary.get("serviceComponentsIds", []):
        cb_client.delete_entity(entity_id=component_id)
