import platform
import aiohttp
import asyncio
import aiofiles
import json
from enum import Enum

from kiroframe_arcee.platforms_meta.azure import AzureMeta


def serialise(self) -> dict:
    result = dict()
    for k, v in self.__dict__.items():
        if k is not None:
            if isinstance(v, Enum):
                v = v.value
            result[k] = v
    return result


class PlatformType(Enum):
    alibaba = "alibaba"
    aws = "aws"
    azure = "azure"
    gcp = "gcp"
    unknown = "unknown"


class InstanceLifeCycle(Enum):
    OnDemand = "OnDemand"
    Preemptible = "Preemptible"
    Spot = "Spot"
    Unknown = "Unknown"


class PlatformMeta:
    def __init__(
        self,
        platform_type,
        instance_id="",
        account_id="",
        local_ip="",
        public_ip="",
        instance_lc=InstanceLifeCycle.Unknown,
        instance_type="",
        instance_region="",
        availability_zone="",
    ):
        self.platform_type = platform_type
        self.instance_id = instance_id
        self.account_id = account_id
        self.local_ip = local_ip
        self.public_ip = public_ip
        self.instance_lc = instance_lc
        self.instance_type = instance_type
        self.instance_region = instance_region
        self.availability_zone = availability_zone

    def to_dict(self) -> dict:
        return json.loads(json.dumps(self, default=serialise))


class Platform:
    match = {
        "Amazon EC2": PlatformType.aws,
        "Google": PlatformType.gcp,
        "Microsoft Corporation": PlatformType.azure,
        "Alibaba Cloud": PlatformType.alibaba,
    }

    def __int__(self, *args, **kwargs):
        raise TypeError("Can be used only statically")

    @staticmethod
    def platform_name() -> str:
        return platform.node()

    @staticmethod
    async def get_platform_vendor() -> PlatformType:
        try:
            async with aiofiles.open("/sys/hypervisor/uuid", "r") as vendor:
                data = await vendor.read()
                if data.rstrip().lower().startswith("ec2"):
                    return PlatformType.aws
        except (OSError, IOError):
            pass
        return PlatformType.unknown

    @classmethod
    async def board_version(cls) -> PlatformType:
        try:
            async with aiofiles.open(
                "/sys/class/dmi/id/board_vendor", "r"
            ) as board:
                data = await board.read()
                return cls.match.get(data.rstrip(), PlatformType.unknown)
        except (OSError, IOError):
            pass
        return PlatformType.unknown

    @classmethod
    async def sys_vendor(cls) -> PlatformType:
        try:
            async with aiofiles.open(
                "/sys/class/dmi/id/sys_vendor", "r"
            ) as board:
                data = await board.read()
                return cls.match.get(data.rstrip(), PlatformType.unknown)
        except (OSError, IOError):
            pass
        return PlatformType.unknown

    @classmethod
    async def platform(cls) -> PlatformType:
        pl = await cls.get_platform_vendor()
        if pl == PlatformType.unknown:
            pl = await cls.board_version()
        if pl == PlatformType.unknown:
            pl = await cls.sys_vendor()
        return pl


class BaseCollector:
    @staticmethod
    async def send_request(
        url, headers=None, params=None, response="text"
    ) -> str:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params) as resp:
                if response == "json":
                    resp = await resp.json()
                else:
                    resp = await resp.text()
                return resp


class AwsCollector(BaseCollector):
    base_url = "http://169.254.169.254/latest/meta-data/%s"

    @staticmethod
    async def send_request(
            url, headers=None, params=None, response="text"
    ) -> str:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 401:  # Handle Unauthorized error
                    # Request a token for IMDSv2
                    token = await AwsCollector.get_metadata_token(session)
                    if token:
                        headers = headers or {}
                        headers["X-aws-ec2-metadata-token"] = token
                        return await AwsCollector.send_request(
                            url, headers, params, response)
                    else:
                        raise Exception(
                            "Failed to retrieve IMDSv2 metadata token")

                if response == "json":
                    return await resp.json()
                return await resp.text()

    @staticmethod
    async def get_metadata_token(session, ttl=21600):
        token_url = "http://169.254.169.254/latest/api/token"
        headers = {"X-aws-ec2-metadata-token-ttl-seconds": "%s" % ttl}
        async with session.put(token_url, headers=headers) as token_resp:
            if token_resp.status == 200:
                return await token_resp.text()
            return None

    async def get_instance_id(self):
        return await self.send_request(
            self.base_url % "instance-id"
        )

    async def get_account_id(self):
        acc_info = await self.send_request(
            self.base_url % "identity-credentials/ec2/info"
        )
        return json.loads(acc_info).get("AccountId", "")

    async def get_local_ip(self):
        return await self.send_request(
            self.base_url % "local-ipv4"
        )

    async def get_public_ip(self):
        return await self.send_request(
            self.base_url % "public-ipv4"
        )

    async def get_life_cycle(self):
        match = {
            "spot": InstanceLifeCycle.Spot,
            "on-demand": InstanceLifeCycle.OnDemand,
        }
        life_cycle = await self.send_request(
            self.base_url % "instance-life-cycle"
        )
        return match.get(life_cycle.lower(), InstanceLifeCycle.Unknown)

    async def get_instance_type(self):
        return await self.send_request(
            self.base_url % "instance-type"
        )

    async def get_az(self):
        return await self.send_request(
            self.base_url % "placement/availability-zone"
        )

    async def get_region(self):
        return await self.send_request(
            self.base_url % "placement/region"
        )

    async def get_platform_meta(self):
        return PlatformMeta(
            PlatformType.aws,
            await self.get_instance_id(),
            await self.get_account_id(),
            await self.get_local_ip(),
            await self.get_public_ip(),
            await self.get_life_cycle(),
            await self.get_instance_type(),
            await self.get_region(),
            await self.get_az(),
        )


class GcpCollector(BaseCollector):
    base_url = "http://169.254.169.254/computeMetadata/v1/%s"
    headers = {"Metadata-Flavor": "Google"}

    async def get_instance_id(self):
        return await self.send_request(
            self.base_url % "instance/id",
            headers=self.headers
        )

    async def get_account_id(self):
        return await self.send_request(
            self.base_url % "project/project-id",
            headers=self.headers
        )

    async def get_local_ip(self):
        return await self.send_request(
            self.base_url % "instance/network-interfaces/0/ip",
            headers=self.headers
        )

    async def get_public_ip(self):
        return await self.send_request(
            self.base_url
            % "instance/network-interfaces/0/access-configs/0/external-ip",
            headers=self.headers
        )

    async def get_life_cycle(self):
        match = {
            "true": InstanceLifeCycle.Spot,
            "false": InstanceLifeCycle.OnDemand,
        }
        life_cycle = await self.send_request(
            self.base_url % "instance/scheduling/preemptible",
            headers=self.headers
        )
        return match.get(life_cycle.lower(), InstanceLifeCycle.Unknown)

    async def get_instance_type(self):
        instance_type = await self.send_request(
            self.base_url % "instance/machine-type",
            headers=self.headers
        )
        return instance_type.split("/")[-1]

    async def get_locations(self):
        location = await self.send_request(
            self.base_url % "instance/zone",
            headers=self.headers
        )
        zone = location.rsplit("/")[-1]
        region = zone.rsplit("-", 1)[0]
        return region, zone

    async def get_platform_meta(self):
        return PlatformMeta(
            PlatformType.gcp,
            await self.get_instance_id(),
            await self.get_account_id(),
            await self.get_local_ip(),
            await self.get_public_ip(),
            await self.get_life_cycle(),
            await self.get_instance_type(),
            *(await self.get_locations())
        )


class AzureCollector(BaseCollector):
    base_url = "http://169.254.169.254/metadata/instance/"

    async def collect(self) -> str:
        """
        Collects data from metadata server
        :return: (str) metadata json
        """
        headers = {"Metadata": "true"}
        params = [("format", "json"), ("api-version", "2021-10-01")]
        return await self.send_request(self.base_url, headers, params,
                                       response="json")

    async def get_platform_meta(self) -> PlatformMeta:
        meta_response = await self.collect()
        if meta_response:
            meta = AzureMeta.from_dict(meta_response)
            private_ip = public_ip = ""
            # TODO: check usage
            if meta.network and meta.network.interface:
                private_ip = (
                    meta.network.interface[0]
                    .ipv4.ipAddress[0]
                    .privateIpAddress
                )
                public_ip = (
                    meta.network.interface[0].ipv4.ipAddress[0].publicIpAddress
                )
            return PlatformMeta(
                PlatformType.azure,
                meta.compute.resourceId,
                meta.compute.subscriptionId,
                private_ip,
                public_ip,
                InstanceLifeCycle.Unknown,
                meta.compute.vmSize,
                meta.compute.location,
                meta.compute.zone,
            )
        return PlatformMeta(PlatformType.azure)


class AlibabaCollector(BaseCollector):
    base_url = "http://100.100.100.200/latest/meta-data/%s"

    @staticmethod
    async def send_request(
        url, headers=None, params=None, response="text"
    ) -> str:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 404:
                    resp = ""
                else:
                    resp = await resp.text()
                return resp

    async def get_instance_id(self):
        return await self.send_request(
            self.base_url % "instance-id"
        )

    async def get_account_id(self):
        return await self.send_request(
            self.base_url % "owner-account-id"
        )

    async def get_local_ip(self):
        return await self.send_request(
            self.base_url % "private-ipv4"
        )

    async def get_public_ip(self):
        public_ip = await self.send_request(
            self.base_url % "public-ipv4"
        )
        if not public_ip:
            public_ip = await self.send_request(
                self.base_url % "eipv4"
            )
        return public_ip

    async def get_life_cycle(self):
        instance_lc = InstanceLifeCycle.Unknown
        life_cycle = await self.send_request(
            self.base_url % "instance/spot/termination-time"
        )
        if life_cycle:
            instance_lc = InstanceLifeCycle.Spot
        return instance_lc

    async def get_instance_type(self):
        return await self.send_request(
            self.base_url % "instance/instance-type"
        )

    async def get_az(self):
        return await self.send_request(
            self.base_url % "zone-id"
        )

    async def get_region(self):
        return await self.send_request(
            self.base_url % "region-id"
        )

    async def get_platform_meta(self):
        return PlatformMeta(
            PlatformType.alibaba,
            await self.get_instance_id(),
            await self.get_account_id(),
            await self.get_local_ip(),
            await self.get_public_ip(),
            await self.get_life_cycle(),
            await self.get_instance_type(),
            await self.get_region(),
            await self.get_az(),
        )


class UnknownCollector(BaseCollector):
    @staticmethod
    async def send_request(
        url, headers=None, params=None, response="json"
    ) -> str:
        return await asyncio.sleep(0)

    @staticmethod
    async def get_platform_meta() -> PlatformMeta:
        return PlatformMeta(PlatformType.unknown, Platform.platform_name())


class CollectorFactory:
    match = {
        PlatformType.azure: AzureCollector,
        PlatformType.aws: AwsCollector,
        PlatformType.alibaba: AlibabaCollector,
        PlatformType.gcp: GcpCollector
    }

    @classmethod
    async def get(cls):
        pf = await Platform.platform()
        return cls.match.get(pf, UnknownCollector)
