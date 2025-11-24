'''
  HLO-FE endpoints
  aeriOS REST API for aeriOS Service LCM
  OpenAPI: https://aeriOS-public.pages.aeriOS-project.eu/openapis/#/hlo_fe
'''
from asyncio import to_thread
from fastapi import HTTPException, APIRouter, Body, BackgroundTasks
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR
from confluent_kafka import KafkaException
from app.app_models.tosca_models import ServiceNotFound, validate_tosca,\
    TOSCA_YAML_EXAMPLE, TOSCA_EXAMPLE
from app.utils import kafka_client
from app.fe_engine import FeEngine
from app.utils.log import get_app_logger
from app.utils import continuum_utils
from app.app_models.aeriOS_continuum import ServiceComponentStatusEnum, ServiceStatusResponse
import app.utils.aeriOS_contrinuum_generator as aeriOS_json_generator
import app.utils.aeriOS_ngsild as aeriOS_ngsild

logger = get_app_logger()

router = APIRouter()


@router.get("/hlo_fe/services/{service_id}",
            response_model=list[ServiceStatusResponse],
            responses={
                200: {
                    "description": "Success"
                },
                404: {
                    "model": ServiceNotFound,
                    "description": "Bad Request"
                }
            })
async def get_service_status(service_id):
    '''
    Get service status.
    Response: List of service components status
    '''
    if not continuum_utils.check_service_exists(service_id=service_id):
        raise HTTPException(status_code=404, detail="Service not found")
    return continuum_utils.get_service_status(service_id=service_id)


@router.post(
    "/hlo_fe/services/{service_id}",
    responses={
        202: {
            "description": "Service allocation initiated",
            "headers": {
                "Location": {
                    "description":
                    "The URL to retrieve service components status",
                    "schema": {
                        "type": "string",
                        "format": "uri"
                    }
                }
            },
        },
        400: {
            "description": "Invalid Service Parameters"
        }
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/x-yaml": {
                    "example": TOSCA_YAML_EXAMPLE
                }
            },
            "required": True,
        },
    },
)
async def allocate_service(background_tasks: BackgroundTasks,
                           service_id: str,
                           tosca_yaml: str = Body(..., example=TOSCA_EXAMPLE)):
    '''
    Allocate new service acrros domains
    :return: Response message and status code.
    '''

    # logger.info('TOSCA file recieved: %s', tosca_yaml)
    tosca_obj = validate_tosca(tosca_yaml=tosca_yaml)

    # import json
    # logger.info('Translated tosca request: %s', json.dumps(json.loads(tosca_obj.json()), indent=4))
    # return

    if not tosca_obj:
        raise HTTPException(status_code=400,
                            detail="Invalid Service Parameters")
    background_tasks.add_task(run_allocate_service,
                              service_id=service_id,
                              tosca_obj=tosca_obj)

    # Return a 202 Accepted response with a Location header
    response = JSONResponse(
        status_code=202,
        content={
            "serviceId": service_id,
            "status": "starting",
            "message":
            "Service allocation initiated. Check service components status at the URL provided.",
            "url": f"/hlo_fe/services/{service_id}"
        })
    response.headers["Location"] = f"/hlo_fe/services/{service_id}"

    return response


def run_allocate_service(service_id: str, tosca_obj):
    '''
    Run the allocation
    @service_id: the id of the allocated service
    @tosca_obj: TOSCA modeled service
    '''
    # If service exists and service components in RUNNING or STARTING status, STOP here
    if continuum_utils.check_service_exists(service_id=service_id):
        for scomponent_id in continuum_utils.get_service_components_list(
                service_id):
            if continuum_utils.get_service_component_status(
                    service_component_id=scomponent_id) in [
                        ServiceComponentStatusEnum.RUNNING,
                        ServiceComponentStatusEnum.STARTING
                    ]:
                logger.info(
                    "Service Component %s: Already started or starting",
                    scomponent_id)
                return
                # return {
                #     "status":
                #     f"service component {scomponent_id} already Started or Running Returning "
                # }

    # ... else proceed with entities create and continuum upadte and ....
    aeriOS = aeriOS_json_generator.aeriOSContinuumEnitiesGenerator(
        service_id=service_id, tosca_obj=tosca_obj)
    json_entities = aeriOS.run()
    # logger.info("JSON Entities created: ")
    # for item in json_entities:
    #     print(item.json())
    # return

    if json_entities:
        aeriOS_json_ld = aeriOS_ngsild.aeriOSNgsild(json_entities)
        created_all_entities = aeriOS_json_ld.run()
    else:
        # raise HTTPException(
        #     status_code=409,
        #     detail="Failed to create all aeriOS entities for service allocation"
        # )
        logger.error(
            "Failed to create all aeriOS entities for service allocation")
        created_all_entities = None

    if created_all_entities:
        try:
            # pass
            kafka_client.produce_message(service_id=service_id)
        except KafkaException as ex:
            # raise HTTPException(
            #     status_code=500,
            #     detail=f"Redpanda failure,HLO pipeline broken: {ex}") from ex
            logger.error("Redpanda failure,HLO pipeline broken: %s", ex)
        # return {"status": "service allocation initiated"}
    else:
        # raise HTTPException(
        #     status_code=409,
        #     detail="Failed to create all aeriOS entities for service allocation"
        # )
        logger.error(
            "Failed to create all aeriOS entities for service allocation")


@router.put("/hlo_fe/services/{service_id}",
            responses={
                200: {
                    "description": "Success"
                },
                404: {
                    "model": ServiceNotFound,
                    "description": "Bad Request"
                }
            })
async def re_allocate(background_tasks: BackgroundTasks, service_id: str):
    '''
    Re-allocate service
    @service_id: the id of the service to re-allocate
    '''
    # If service does not exist, return 404
    if not continuum_utils.check_service_exists(service_id=service_id):
        logger.error("Service %s not found", service_id)
        raise HTTPException(status_code=404, detail="Service not found")

    background_tasks.add_task(run_re_allocate_service, service_id=service_id)

    # Return a 202 Accepted response with a Location header
    response = JSONResponse(
        status_code=202,
        content={
            "serviceId": service_id,
            "status": "starting",
            "message":
            "Service Re-allocation initiated. Check service components status at the URL provided.",
            "url": f"/hlo_fe/services/{service_id}"
        })
    response.headers["Location"] = f"/hlo_fe/services/{service_id}"

    return response


def run_re_allocate_service(service_id: str):
    '''
    Run the service re-allocation
    @service_id: the id of the service to re-allocate
    '''
    # If service exists and service components in RUNNING or STARTING status, STOP here
    if continuum_utils.check_service_exists(service_id=service_id):
        for scomponent_id in continuum_utils.get_service_components_list(
                service_id):
            if continuum_utils.get_service_component_status(
                    service_component_id=scomponent_id) in [
                        ServiceComponentStatusEnum.RUNNING,
                        ServiceComponentStatusEnum.STARTING
                    ]:
                logger.info(
                    "Service Component %s: Already started or starting",
                    scomponent_id)
                return
        # If no service component in RUNNING or STARTING status,
        # reset all service components status to STARTING and service status to DEPLOYING
        continuum_utils.reset_service_component_starting(entity_id=service_id)
        continuum_utils.reset_service_deploying(entity_id=service_id)
    try:
        kafka_client.produce_message(service_id=service_id)
    except KafkaException as ex:
        logger.error("Redpanda failure,HLO pipeline broken: %s", ex)


@router.patch(
    "/hlo_fe/services/{service_id}",
    responses={
        200: {
            "description": "Success"
        },
        400: {
            "description": "Invalid Service Parameters"
        },
        404: {
            "model": ServiceNotFound,
            "description": "Bad Request"
        }
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/x-yaml": {
                    "example": TOSCA_YAML_EXAMPLE
                }
            },
            "required": True,
        },
    },
)
async def change_service_allocation_paramters(service_id: str,
                                              tosca_yaml: str = Body(
                                                  ...,
                                                  example=TOSCA_YAML_EXAMPLE)):
    '''
    Update service allocation parameters
    '''
    # logger.info('TOSCA file recieved: %s', tosca_yaml)
    tosca_obj = validate_tosca(tosca_yaml=tosca_yaml)
    # logger.info('Translated tosca request: %s', tosca_obj)

    if not tosca_obj:
        raise HTTPException(status_code=400,
                            detail="Invalid Service Parameters")
    if not continuum_utils.check_service_exists(service_id=service_id):
        raise HTTPException(status_code=404, detail="Service not found")

    client = FeEngine()
    tocsa_jsonld = client.tosca2jsonld(service_id=service_id,
                                       tosca_dict=tosca_obj)
    logger.info("SERVICE RECEIVED FROM TOSCA ")
    logger.info("SERVICE PYDANTIC FROM TOSCA CREATED ")
    logger.info(
        "PLEASE CREATE NGSI-LD entities FROM PYDANTIC AND UPDATE ALL RELATED ENTITIES TO ORION-CB"
    )
    logger.info("PUSHING SERVICE ID RECEIVED ")
    client.allocate_service(service_id=service_id, tosca_jsonld=tocsa_jsonld)

    ## FIXME: Map TOSCA to NGSI-LD
    ## FIXME: create service component IDs based on service ID
    ##         and update their status
    for scomponent_id in [
            "urn:ngsi-ld:Service:05:Component:01",
            "urn:ngsi-ld:Service:05:Component:02"
    ]:
        continuum_utils.set_service_component_status(
            service_id=service_id,
            scomponent_id=
            scomponent_id,  # FIXME: create actual scomponent and ids
            scomponent_status=ServiceComponentStatusEnum.LOCATING
        )  # FIXME: is correct?

    try:
        kafka_client.produce_message(service_id=service_id)
    except KafkaException as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Redpanda failure,HLO pipeline broken: {ex}") from ex

    return {"status": "service allocation parameters change initiated"}


@router.delete("/hlo_fe/services/{service_id}",
               responses={
                   200: {
                       "description": "Success"
                   },
                   404: {
                       "model": ServiceNotFound,
                       "description": "Bad Request"
                   }
               })
async def deallocate_service(service_id: str):
    '''
    Deallocate an existing service accross domaina
    '''
    logger.info('Service id: %s', service_id)

    if not continuum_utils.check_service_exists(service_id=service_id):
        raise HTTPException(status_code=404, detail="Service not found")

    # Update service components status to Stopping and service action type to destroying
    success: bool = True
    success &= continuum_utils.set_service_components_removing(
        entity_id=service_id)
    try:
        if success:
            kafka_client.produce_message(service_id=service_id)
            continuum_utils.set_service_destroying(entity_id=service_id)
            message = "service deallocation initiated"
        else:
            message = "Can not deallocate when service component(s) not in Running or Failed state"
    except KafkaException as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Redpanda failure,HLO pipeline broken: {ex}") from ex

    return {"status": message}


@router.delete("/hlo_fe/services/{service_id}/purge",
               status_code=HTTP_200_OK)
async def purge_service(service_id: str):
    """
    Asynchronously purge a service and its components from the Continuum.
    """
    if not continuum_utils.check_service_exists(service_id=service_id):
        raise HTTPException(status_code=404, detail="Service not found")
    if not continuum_utils.check_service_can_be_purged(service_id=service_id):
        raise HTTPException(
            status_code=400,
            detail="Service cannot be purged. Ensure it has beed stopped."
        )
    
    try:

        # Call the sync purge function in a thread-safe way
        await to_thread(continuum_utils.delete_from_continuum_service_by_id,
                        service_id)
        return JSONResponse(
            status_code=HTTP_200_OK,
            content={"message": f"Service '{service_id}' has been purged successfully."}
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to purge service {service_id}: {str(e)}"
        ) from e


# @router.get(
#     "/hlo_al/services/{service_id}")
# async def get_service_data(service_id: str):
#     '''
#   Not in the OpenAPI, do we need it though??
#     Get the service allocation parameters accross domains

#     :param service_id: The ID of the service (path parameter).
#     :return: Information about the service.
#     '''
# logger.info('Service id: %s', service_id)
# client = FeEngine()

# if not client.check_service_exists(service_id=service_id):
#     raise HTTPException(status_code=404,
#                         detail="Service not found")
# Do more things ....
#     return r
