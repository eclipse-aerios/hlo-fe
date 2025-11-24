"""
    Class that transforms TOSCA to aeriOS JSON entities.
"""
import re
import uuid
from typing import List, Dict, Tuple, Optional
from app.app_models import tosca_models
import app.app_models.aeriOS_continuum as aeriOS_c
import app.utils.continuum_utils as c_utils
from app.utils.log import get_app_logger


def extract_number(text):
    """
        Get e.g. "2048 MB" and return 2048
    """
    match = re.search(r'\d+', text)
    if match:
        return int(match.group())
    return None


class aeriOSContinuumEnitiesGenerator:
    """
        Class genrates aeriOS NGSILD entities from TOSCA
        FIXME: Needs beeter TOSCA typing and checks
    """

    def __init__(self, service_id, tosca_obj: tosca_models.TOSCA):
        self.logger = get_app_logger()
        self.ngsi_ld_entities: List[Dict] = []
        self.service_id = service_id
        self.tosca_obj = tosca_obj
        self.host_domain = c_utils.get_host_domain()
        self.expose_ports = False

    def get_scomponent_env_vars(self, env_vars: List) -> List[Dict]:
        '''
            Get service component container environment variables
        '''
        # FIXME : tooo many conventions, needs stronger typing
        # aeriOS tosca interfaces has Standard, create,
        #   implementation with ref to artifact, inputs and then envVars
        scomponent_env_vars = []
        for env_var in env_vars:
            for key, value in env_var.items():
                item = {'key': str(key), 'value': str(value)}
                scomponent_env_vars.append(item)
        return scomponent_env_vars

    def get_scomponent_cli_args(self, cli_args: List) -> List[Dict]:
        '''
            Get service component container cli arguments
        '''
        # FIXME : tooo many conventions, needs stronger typing
        # aeriOS tosca interfaces has Standard, create,
        #   implementation with ref to artifact, inputs and then cliArgs
        scomponent_cli_args = []
        for cli_arg in cli_args:
            for key, value in cli_arg.items():
                item = {'key': str(key), 'value': str(value)}
                scomponent_cli_args.append(item)
        return scomponent_cli_args

    def get_container_image_and_credentials(
        self, artifact: Dict[str, tosca_models.ArtifactModel]
    ) -> Tuple[str, Optional[str], Optional[str], Optional[bool]]:
        """
        Get container image, credentials, and is_private flag.

        Returns:
            (image: str, username: Optional[str], password: Optional[str], is_private: Optional[bool])
        """
        repo = ''
        username = None
        password = None
        is_private = None

        for _, item in artifact.items():
            image = item.file
            if item.repository and 'docker' not in item.repository:
                repo = item.repository

            # Pull explicitly defined values
            is_private = getattr(item, 'isPrivate', None)
            if is_private:
                username = getattr(item, 'username', None)
                password = getattr(item, 'password', None)

            full_image = f"{repo}/{image}" if repo else image
            return full_image, username, password, is_private

        return "", None, None, None

    def get_network_requrierements(
            self, requirements: List[tosca_models.NetworkRequirement]) -> List:
        """
            Get service component network requirements
        """
        ports_id_list = []
        net_properties: tosca_models.NetworkProperties
        exposed_port: tosca_models.ExposedPort
        port_properties: tosca_models.PortProperties
        for _, net_properties in requirements:  # _ => "network" literal
            for item in net_properties:
                cap_key, value = item  # cap_key is either ports or exposePorts
                if cap_key == "exposePorts":
                    self.expose_ports = value
                elif cap_key == "ports":
                    exposed_port = value  # just for clarity
                    for _, port_properties in exposed_port.items():
                        uid = uuid.uuid4().hex[:8]
                        port_id = f"urn:ngsi-ld:NetworkPort:{uid}"
                        port_type = "NetworkPort"
                        port_number = port_properties.properties.source
                        # FIXME aeriOS continuum has it as string, tosca sends list[str].
                        #       So we assume one protocol per port.
                        protocol = port_properties.properties.protocol[0]
                        ports_id_list.append(port_id)
                        network_port = aeriOS_c.NetworkPort(
                            id=port_id,
                            type=port_type,
                            portNumber=port_number,
                            portProtocol=protocol)
                        self.ngsi_ld_entities.append(network_port)
        return ports_id_list

    def get_ie_requrierement(
        self,
        properties: Dict[str, str],
        capabilities: List[Dict[str,
                                tosca_models.HostCapability]],  # capabilities
        scomponent_id,
    ) -> str:
        """
            Get service component host requirements
        """
        if properties and "id" in properties:
            selected_ie_list = properties.get("id")
            if not isinstance(selected_ie_list, list):
                selected_ie_list = [selected_ie_list]
        else:
            selected_ie_list = []
        ie_requirment_id = f'{scomponent_id}:InfrastructureElementRequirements'
        ie_requirment = "ngsi-ld:null"
        if selected_ie_list:
            ie_requirment = aeriOS_c.InfrastructureElementRequirements(
                id=ie_requirment_id,
                type="InfrastructureElementRequirements",
                infrastructureElement=selected_ie_list
                if selected_ie_list else None)
        else:
            selected_ie_id = "urn:ngsi-ld:null"
            for capability in capabilities:
                # cap_key is either host or energy
                for cap_key, host_capabilities in capability.items():
                    if cap_key == "host":
                        ie_requirements = host_capabilities.properties
                        # My guess is that TOSCA send % of cpu_usage mapped to range [0,1]
                        cpu_usage = 100 * (
                            ie_requirements.cpu_usage.less_or_equal)
                        _cpu = ie_requirements.cpu_arch.equal
                        if _cpu == "x86_64":
                            _cpu = "x64"
                        cpu_arch = f"urn:ngsi-ld:CpuArchitecture:{_cpu}"
                        mem_size = extract_number(
                            ie_requirements.mem_size.greater_or_equal)
                        energy_efficiency_ratio = ie_requirements.energy_efficiency.greater_or_equal
                        green_energy_ratio = ie_requirements.green.greater_or_equal
                        realtime = ie_requirements.realtime.equal
                        domain_id = ie_requirements.domain_id.equal
                        # FIXME: parse this too
                        # area = ie_requirements.area
                        area = {"type": "Polygon", "coordinates": [[[]]]}
                        ie_requirment = aeriOS_c.InfrastructureElementRequirements(
                            id=ie_requirment_id,
                            type="InfrastructureElementRequirements",
                            infrastructureElement=selected_ie_id,
                            requiredCpuUsage=cpu_usage,
                            requiredRam=mem_size,
                            cpuArchitecture=cpu_arch,
                            realTimeCapable=realtime,
                            energyEfficiencyRatio=energy_efficiency_ratio,
                            greenEnergyRatio=green_energy_ratio,
                            domainId=domain_id,
                            area=area)
                    # elif cap_key == "energy":
                    #     # Energy requirements integrated in host capabilities
                    #     pass
        self.ngsi_ld_entities.append(ie_requirment)
        return ie_requirment_id

    def get_custom_requrierement(
            self, requirements: List[tosca_models.CustomRequirement],
            scomponent_id):
        """
            Get service component custom requirements
            FIXME: Needs some more careful update
        """
        custom_requirements = {}
        network_ports_ids = None
        ie_req_id = ""

        for item in requirements:
            # TOSCA CustomRequirement is a tuple: (host, network)
            host_requirement, network_requirement = item
            # req_key: 'host', req_value: HostRequirments
            req_value: tosca_models.HostRequirement
            req_host_key, req_value = host_requirement
            if req_value:
                ie_req_id = self.get_ie_requrierement(
                    properties=req_value.node_filter.properties,
                    capabilities=req_value.node_filter.capabilities,
                    scomponent_id=scomponent_id)

            req_net_key, req_value = network_requirement
            if req_value:
                network_ports_ids = self.get_network_requrierements(
                    requirements=req_value)
            elif network_ports_ids is None:
                network_ports_ids = []

        custom_requirements[req_host_key] = ie_req_id
        custom_requirements[req_net_key] = network_ports_ids
        return custom_requirements

    def create_service_components(self):
        """
            Create aeriOS representation for each Service Component
        """
        scomponent_specs: tosca_models.NodeTemplate
        for scomponent_name, scomponent_specs in self.tosca_obj.node_templates.items(
        ):
            if scomponent_specs.type == "tosca.nodes.Container.Application":
                # uid = uuid.uuid4().hex[:8]
                # scomponent_id = self.service_id + f':Component:{uid}'
                scomponent_id = self.service_id + f':Component:{scomponent_name}'
                scomponent_type = "ServiceComponent"
                service_component_status = aeriOS_c.ServiceComponentStatusEnum.STARTING
                container_image, repo_username, repo_password, is_private = self.get_container_image_and_credentials(
                    scomponent_specs.artifacts)
                custom_requirments = self.get_custom_requrierement(
                    requirements=scomponent_specs.requirements,
                    scomponent_id=scomponent_id)
                network_ports = custom_requirments["network"]
                infrastructure_element_requirements = custom_requirments[
                    "host"]

                env_vars = []
                cli_args = []
                # sla = []
                for _, value in scomponent_specs.interfaces.items():
                    #     env_vars =  value['create']['inputs']['envVars']
                    #     cli_args =  value['create']['inputs']['cliArgs']
                    if 'cliArgs' in value['create']['inputs']:
                        cli_args = self.get_scomponent_cli_args(
                            value['create']['inputs']['cliArgs'])
                    if 'envVars' in value['create']['inputs']:
                        env_vars = self.get_scomponent_env_vars(
                            value['create']['inputs']['envVars'])

                scomponent = aeriOS_c.ServiceComponent(
                    id=scomponent_id,
                    type=scomponent_type,
                    service=self.service_id,
                    serviceComponentStatus=service_component_status,
                    containerImage=container_image,
                    networkPorts=network_ports,
                    infrastructureElementRequirements=
                    infrastructure_element_requirements,
                    cliArgs=cli_args,
                    envVars=env_vars,
                    exposePorts=self.expose_ports,
                    isJob=scomponent_specs.isJob,
                    isPrivate=is_private,
                    repoUsername=repo_username,
                    repoPassword=repo_password)
                self.ngsi_ld_entities.append(scomponent)

    def create_aeriOS_service_entity(self):
        """
            Create ngsi-ld entites representing aeriOS continuum objects
        """
        service = aeriOS_c.Service(
            id=self.service_id,
            type="Service",
            name=f'aeriOS_service_{self.service_id}',
            description=self.tosca_obj.description,
            domainHandler=self.host_domain,
            actionType=aeriOS_c.ServiceActionTypeEnum.DEPLOYING,
            hasOverlay=self.tosca_obj.serviceOverlay)
        self.ngsi_ld_entities.append(service)

    def run(self):
        """
            Ruuner for ll the job
        """
        try:
            self.create_aeriOS_service_entity()
            self.create_service_components()
            return self.ngsi_ld_entities
        except (KeyError, TypeError, AttributeError) as e:
            error_msg = f"Failed to create continuum entities. Error: {e.__class__.__name__}"
            self.logger.exception("Failed to create contimuum entities, %s",
                                  error_msg)
            return None

    # print("###################################################")

    # print(json.dumps(json.loads(tosca_obj.json()), indent=4))
    # print("###################################################")
