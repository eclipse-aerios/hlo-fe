'''
Pydantic models for validating input data and return objects
The ultimate task is to validate TOSCA yaml request payload for POST and PUT endpoints.
So we can know that incoming payload conforms to what is expected as an IoT deployment request
and we can map it to aeriOS  knwoledge graph.

aeriOS TOSCA example:
    tosca_definitions_version: tosca_simple_yaml_1_3
    description:  TOSCA simple container application with ports and hosts requirements

    node_templates:
    simple_application:
        type: tosca.nodes.Container.Application
        requirements:
        - host:
            node_filter:
                capabilities:
                - host:
                    properties:
                        cpu_usage: { greater_or_equal: 0.3 }
                        cpu_arch: { equal: x86_64 }  #data model supports : x86_64, arm64, arm32 
                        mem_size: { greater_or_equal: 2000 MB } #MB used in the data model
                        realtime: { equal: true }
                        area:
                        coordinates:
                            - [-0.3411743020092746, 39.48103451588121]
                            - [-0.3411743020092746, 39.4103451588121]
                            - [-0.3411743020092746, 39.48103451588121]
                            - [-0.3411743020092746, 39.48103451588121]

        - network:
            properties:
                ports:
                exposedport1:
                    properties:
                    protocol: [udp]
                    source: 1625
                exposedport2:
                    properties:
                    protocol: [udp, tcp]
                    source: 35
        artifacts:
        application_image:
            file: busybox
            type: tosca.artifacts.Deployment.Image.Container.Docker
            repository: docker_hub

        interfaces:
        Standard:
            create:
            implementation: application_image
            inputs:
                cliArgs:
                - RTperiodicity: 123
                - RTdeadline: 23
                envVars:
                - Var1: 22
'''

from enum import Enum
from typing import List, Dict, Any, Union, Optional
from pydantic import BaseModel, Field, ValidationError  #, field_validator
import yaml
from app.utils.log import get_app_logger


class ServiceNotFound(BaseModel):
    '''
    Docstring
    '''
    detail: str = "Service not found"


class CPUComparisonOperator(BaseModel):
    """
        CPU requirment for now is that usage should be less than
    """
    less_or_equal: Union[float, None] = None


class CPUArchComparisonOperator(BaseModel):
    """
        CPU arch requirment, equal to str
    """
    equal: Union[str, None] = None


class MEMComparisonOperator(BaseModel):
    """
        RAM requirment for now is that available RAM should be more than
    """
    greater_or_equal: Union[str, None] = None


class EnergyEfficienyComparisonOperator(BaseModel):
    """
        Energy Efficiency requirment for now is that IE should have energy efficiency more than a %
    """
    greater_or_equal: Union[str, None] = None


class GreenComparisonOperator(BaseModel):
    """
        IE Green requirment for now is that IE should have green energy mix which us more than a %
    """
    greater_or_equal: Union[str, None] = None


class RTComparisonOperator(BaseModel):
    """
        Real Time requirment T/F
    """
    equal: Union[bool, None] = None


class CpuArch(str, Enum):
    '''
    Enumeration with possible cpu types
    '''
    x86_64 = "x86_64"
    arm64 = "arm64"
    arm32 = "arm32"


class Coordinates(BaseModel):
    '''
    IE coordinate requirements
    '''
    coordinates: List[List[float]]


class DomainIdOperator(BaseModel):
    """
        CPU arch requirment, equal to str
    """
    equal: Union[str, None] = None


class Property(BaseModel):
    '''
    IE capabilities
    '''
    cpu_usage: CPUComparisonOperator = Field(
        default_factory=CPUComparisonOperator)
    cpu_arch: CPUArchComparisonOperator = Field(
        default_factory=CPUArchComparisonOperator)
    mem_size: MEMComparisonOperator = Field(
        default_factory=MEMComparisonOperator)
    realtime: RTComparisonOperator = Field(
        default_factory=RTComparisonOperator)
    area: Coordinates = None
    energy_efficiency: EnergyEfficienyComparisonOperator = Field(
        default_factory=EnergyEfficienyComparisonOperator)
    green: GreenComparisonOperator = Field(
        default_factory=GreenComparisonOperator)
    domain_id: DomainIdOperator = Field(default_factory=DomainIdOperator)

    # @field_validator('mem_size')
    # def validate_mem_size(cls, v):
    #     if not v or "MB" not in v:
    #         raise ValueError("mem_size must be in MB and specified")
    #     mem_size_value = int(v.split(" ")[0])
    #     if mem_size_value < 2000:
    #         raise ValueError("mem_size must be greater or equal to 2000 MB")
    #     return v


class HostCapability(BaseModel):
    '''
    Host properties
    '''
    properties: Property


class NodeFilter(BaseModel):
    '''
    Node filter,
    How to filter continuum IE and select canditate list
    '''
    properties: Optional[Dict[str, List[str]]] = None
    capabilities: Optional[List[Dict[str, HostCapability]]] = None


class HostRequirement(BaseModel):
    '''
    capabilities of node
    '''
    # node_filter: Dict[str, List[Dict[str, HostCapability]]]
    node_filter: NodeFilter


class PortProperties(BaseModel):
    '''
    Workload port description
    '''
    protocol: List[str] = Field(...)
    source: int = Field(...)


class ExposedPort(BaseModel):
    '''
    Workload exposed network ports
    '''
    properties: PortProperties = Field(...)


class NetworkProperties(BaseModel):
    '''
    Dict of network requirments, name of port and protperty = [protocol, port] mapping
    '''
    ports: Dict[str, ExposedPort] = Field(...)
    exposePorts: Optional[bool]


class NetworkRequirement(BaseModel):
    '''
    Top level key of network requirments
    '''
    properties: NetworkProperties


class CustomRequirement(BaseModel):
    '''
    Define a custom requirement type that can be either a host or a network requirement  
    '''
    host: HostRequirement = None
    network: NetworkRequirement = None


class ArtifactModel(BaseModel):
    '''
    Artifact has a useer defined id and then a dict with the following keys:
    '''
    file: str
    type: str
    repository: str
    isPrivate: Optional[bool] = False
    username: Optional[str] = None
    password: Optional[str] = None


class NodeTemplate(BaseModel):
    '''
    Node template "tosca.nodes.Container.Application"
    '''
    type: str
    requirements: List[CustomRequirement]
    artifacts: Dict[str, ArtifactModel]
    interfaces: Dict[str, Any]
    isJob: Optional[bool] = False


class TOSCA(BaseModel):
    '''
    The TOSCA structure
    '''
    tosca_definitions_version: str
    description: str
    serviceOverlay: Optional[bool] = False
    node_templates: Dict[str, NodeTemplate]


def validate_tosca(tosca_yaml) -> TOSCA:
    '''
    Get Tosca yaml from REST endpoint.
    Load in yaml.
    Validate and cretae TOSCA typed pydantic model.
    Return TOSCA oject or None
    '''
    logger = get_app_logger()
    # Load yaml to json
    try:
        data = yaml.safe_load(tosca_yaml)
    except yaml.YAMLError as e:
        logger.error("Error while loading yaml: %s", str(e))
        return None
    # Validate and create Pydantic (typed) object
    try:
        tosca_obj = TOSCA(**data)
        return tosca_obj
    except ValidationError as e:
        logger.error('TOSCA validation error: %s', e.json())
        return None
    except Exception as e:
        logger.error('TOSCA execption: %s', str(e))
        return None


TOSCA_YAML_EXAMPLE = """
aeriOS TOSCA example:
description: A test service for testing TOSCA generation
node_templates:
  auto-component:
    isJob: False
    artifacts:
      application_image:
        file: aeriOS-public/common-deployments/nginx:latest
        repository: registry.gitlab.aeriOS-project.eu
        type: tosca.artifacts.Deployment.Image.Container.Docker
    interfaces:
      Standard:
        create:
          implementation: application_image
          inputs:
            cliArgs:
            - -a: aa
            envVars:
            - URL: bb
    requirements:
    - network:
        properties:
          ports:
            port1:
              properties:
                protocol:
                - tcp
                source: 80
            port2:
              properties:
                protocol:
                - tcp
                source: 443
          exposePorts: True
    - host:
        node_filter:
          capabilities:
          - host:
              properties:
                cpu_arch:
                  equal: x64
                realtime:
                  equal: false
                cpu_usage:
                  less_or_equal: '0.4'
                mem_size:
                  greater_or_equal: '1'
                domain_id:
                  equal: urn:ngsi-ld:Domain:NCSRD
                energy_efficiency:
                  greater_or_equal: '0.5'
                green:
                    greater_or_equal: '0.5'
          properties: null
    type: tosca.nodes.Container.Application

  manual-sc:
    artifacts:
      application_image:
        file: mosquitto:latest
        repository: docker_hub
        type: tosca.artifacts.Deployment.Image.Container.Docker
    interfaces:
      Standard:
        create:
          implementation: application_image
          inputs:
            cliArgs:
            - -a: aa
            envVars:
            - AA: aa
    requirements:
    - network:
        properties:
          ports:
            port1:
              properties:
                protocol:
                - tcp
                source: 1883
          exposePorts: False
    - host:
        node_filter:
          capabilities: null
          properties:
            id: urn:ngsi-ld:InfrastructureElement:NCSRD:fac2b1a81a2e
    type: tosca.nodes.Container.Application
tosca_definitions_version: tosca_simple_yaml_1_3


"""

TOSCA_EXAMPLE = {
    "tosca_definitions_version": "tosca_simple_yaml_1_3",
    "description":
    "TOSCA simple container application with ports and hosts requirements",
    "node_templates": {
        "simple_application": {
            "type":
            "tosca.nodes.Container.Application",
            "requirements": [{
                "host": {
                    "node_filter": {
                        "capabilities": [{
                            "host": {
                                "properties": {
                                    "cpu_usage": {
                                        "greater_or_equal": 0.3
                                    },
                                    "cpu_arch": {
                                        "equal": "x86_64"
                                    },
                                    "mem_size": {
                                        "greater_or_equal": "2000 MB"
                                    },
                                    "realtime": {
                                        "equal": True
                                    },
                                    "area": {
                                        "coordinates": [
                                            [
                                                -0.3411743020092746,
                                                39.48103451588121
                                            ],
                                            [
                                                -0.3411743020092746,
                                                39.4103451588121
                                            ],
                                            [
                                                -0.3411743020092746,
                                                39.48103451588121
                                            ],
                                            [
                                                -0.3411743020092746,
                                                39.48103451588121
                                            ]
                                        ]
                                    }
                                }
                            }
                        }]
                    }
                }
            }, {
                "network": {
                    "properties": {
                        "ports": {
                            "exposedport1": {
                                "properties": {
                                    "protocol": ["udp"],
                                    "source": 1625
                                }
                            },
                            "exposedport2": {
                                "properties": {
                                    "protocol": ["udp", "tcp"],
                                    "source": 35
                                }
                            }
                        }
                    }
                }
            }],
            "artifacts": {
                "application_image": {
                    "file": "busybox",
                    "type":
                    "tosca.artifacts.Deployment.Image.Container.Docker",
                    "repository": "docker_hub"
                }
            },
            "interfaces": {
                "Standard": {
                    "create": {
                        "implementation": "application_image",
                        "inputs": {
                            "cliArgs": [{
                                "RTperiodicity": 123
                            }, {
                                "RTdeadline": 23
                            }],
                            "envVars": [{
                                "Var1": 22
                            }]
                        }
                    }
                }
            }
        }
    }
}
