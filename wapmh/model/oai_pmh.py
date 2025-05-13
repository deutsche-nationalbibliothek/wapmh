from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union

from xsdata.models.datatype import XmlDate, XmlDateTime

__NAMESPACE__ = "http://www.openarchives.org/OAI/2.0/"


class OaiPmherrorcodeType(Enum):
    CANNOT_DISSEMINATE_FORMAT = "cannotDisseminateFormat"
    ID_DOES_NOT_EXIST = "idDoesNotExist"
    BAD_ARGUMENT = "badArgument"
    BAD_VERB = "badVerb"
    NO_METADATA_FORMATS = "noMetadataFormats"
    NO_RECORDS_MATCH = "noRecordsMatch"
    BAD_RESUMPTION_TOKEN = "badResumptionToken"
    NO_SET_HIERARCHY = "noSetHierarchy"


@dataclass
class AboutType:
    """
    Data "about" the record must be expressed in XML that is compliant with an XML
    Schema defined by a community.
    """

    class Meta:
        name = "aboutType"

    other_element: Optional[object] = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )


class DeletedRecordType(Enum):
    NO = "no"
    PERSISTENT = "persistent"
    TRANSIENT = "transient"


@dataclass
class DescriptionType:
    """The descriptionType is used for the description element in Identify and for
    setDescription element in ListSets.

    Content must be compliant with an XML Schema defined by a community.
    """

    class Meta:
        name = "descriptionType"

    other_element: Optional[object] = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )


class GranularityType(Enum):
    YYYY_MM_DD = "YYYY-MM-DD"
    YYYY_MM_DDTHH_MM_SS_Z = "YYYY-MM-DDThh:mm:ssZ"


@dataclass
class MetadataFormatType:
    class Meta:
        name = "metadataFormatType"

    metadata_prefix: Optional[str] = field(
        default=None,
        metadata={
            "name": "metadataPrefix",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
            "pattern": r"[A-Za-z0-9\-_\.!~\*'\(\)]+",
        },
    )
    schema: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
        },
    )
    metadata_namespace: Optional[str] = field(
        default=None,
        metadata={
            "name": "metadataNamespace",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
        },
    )


@dataclass
class MetadataType:
    """Metadata must be expressed in XML that complies with another XML Schema
    (namespace=#other).

    Metadata must be explicitly qualified in the response.
    """

    class Meta:
        name = "metadataType"

    other_element: Optional[object] = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )


class ProtocolVersionType(Enum):
    VALUE_2_0 = "2.0"


@dataclass
class ResumptionTokenType:
    """
    A resumptionToken may have 3 optional attributes and can be used in ListSets,
    ListIdentifiers, ListRecords responses.
    """

    class Meta:
        name = "resumptionTokenType"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    expiration_date: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "expirationDate",
            "type": "Attribute",
        },
    )
    complete_list_size: Optional[int] = field(
        default=None,
        metadata={
            "name": "completeListSize",
            "type": "Attribute",
        },
    )
    cursor: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


class StatusType(Enum):
    DELETED = "deleted"


class VerbType(Enum):
    IDENTIFY = "Identify"
    LIST_METADATA_FORMATS = "ListMetadataFormats"
    LIST_SETS = "ListSets"
    GET_RECORD = "GetRecord"
    LIST_IDENTIFIERS = "ListIdentifiers"
    LIST_RECORDS = "ListRecords"


@dataclass
class IdentifyType:
    repository_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "repositoryName",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
        },
    )
    base_url: Optional[str] = field(
        default=None,
        metadata={
            "name": "baseURL",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
        },
    )
    protocol_version: Optional[ProtocolVersionType] = field(
        default=None,
        metadata={
            "name": "protocolVersion",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
        },
    )
    admin_email: list[str] = field(
        default_factory=list,
        metadata={
            "name": "adminEmail",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "min_occurs": 1,
            "pattern": r"\S+@(\S+\.)+\S+",
        },
    )
    earliest_datestamp: Optional[Union[XmlDate, str]] = field(
        default=None,
        metadata={
            "name": "earliestDatestamp",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
            "pattern": r".*Z",
        },
    )
    deleted_record: Optional[DeletedRecordType] = field(
        default=None,
        metadata={
            "name": "deletedRecord",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
        },
    )
    granularity: Optional[GranularityType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
        },
    )
    compression: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
        },
    )
    description: list[DescriptionType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
        },
    )


@dataclass
class ListMetadataFormatsType:
    metadata_format: list[MetadataFormatType] = field(
        default_factory=list,
        metadata={
            "name": "metadataFormat",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "min_occurs": 1,
        },
    )


@dataclass
class OaiPmherrorType:
    class Meta:
        name = "OAI-PMHerrorType"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    code: Optional[OaiPmherrorcodeType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class HeaderType:
    """A header has a unique identifier, a datestamp, and setSpec(s) in case the
    item from which the record is disseminated belongs to set(s).

    the header can carry a deleted status indicating that the record is
    deleted.
    """

    class Meta:
        name = "headerType"

    identifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
        },
    )
    datestamp: Optional[Union[XmlDate, str]] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
            "pattern": r".*Z",
        },
    )
    set_spec: list[str] = field(
        default_factory=list,
        metadata={
            "name": "setSpec",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "pattern": r"([A-Za-z0-9\-_\.!~\*'\(\)])+(:[A-Za-z0-9\-_\.!~\*'\(\)]+)*",
        },
    )
    status: Optional[StatusType] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class RequestType:
    """Define requestType, indicating the protocol request that led to the
    response.

    Element content is BASE-URL, attributes are arguments of protocol
    request, attribute-values are values of arguments of protocol
    request
    """

    class Meta:
        name = "requestType"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    verb: Optional[VerbType] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    identifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    metadata_prefix: Optional[str] = field(
        default=None,
        metadata={
            "name": "metadataPrefix",
            "type": "Attribute",
            "pattern": r"[A-Za-z0-9\-_\.!~\*'\(\)]+",
        },
    )
    from_value: Optional[Union[XmlDate, str]] = field(
        default=None,
        metadata={
            "name": "from",
            "type": "Attribute",
            "pattern": r".*Z",
        },
    )
    until: Optional[Union[XmlDate, str]] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r".*Z",
        },
    )
    set: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r"([A-Za-z0-9\-_\.!~\*'\(\)])+(:[A-Za-z0-9\-_\.!~\*'\(\)]+)*",
        },
    )
    resumption_token: Optional[str] = field(
        default=None,
        metadata={
            "name": "resumptionToken",
            "type": "Attribute",
        },
    )


@dataclass
class SetType:
    class Meta:
        name = "setType"

    set_spec: Optional[str] = field(
        default=None,
        metadata={
            "name": "setSpec",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
            "pattern": r"([A-Za-z0-9\-_\.!~\*'\(\)])+(:[A-Za-z0-9\-_\.!~\*'\(\)]+)*",
        },
    )
    set_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "setName",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
        },
    )
    set_description: list[DescriptionType] = field(
        default_factory=list,
        metadata={
            "name": "setDescription",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
        },
    )


@dataclass
class ListIdentifiersType:
    header: list[HeaderType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "min_occurs": 1,
        },
    )
    resumption_token: Optional[ResumptionTokenType] = field(
        default=None,
        metadata={
            "name": "resumptionToken",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
        },
    )


@dataclass
class ListSetsType:
    set: list[SetType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "min_occurs": 1,
        },
    )
    resumption_token: Optional[ResumptionTokenType] = field(
        default=None,
        metadata={
            "name": "resumptionToken",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
        },
    )


@dataclass
class RecordType:
    """
    A record has a header, a metadata part, and an optional about container.
    """

    class Meta:
        name = "recordType"

    header: Optional[HeaderType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
        },
    )
    metadata: Optional[MetadataType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
        },
    )
    about: list[AboutType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
        },
    )


@dataclass
class GetRecordType:
    record: Optional[RecordType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
        },
    )


@dataclass
class ListRecordsType:
    record: list[RecordType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "min_occurs": 1,
        },
    )
    resumption_token: Optional[ResumptionTokenType] = field(
        default=None,
        metadata={
            "name": "resumptionToken",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
        },
    )


@dataclass
class OaiPmhtype:
    class Meta:
        name = "OAI-PMHtype"

    response_date: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "responseDate",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
        },
    )
    request: Optional[RequestType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
            "required": True,
        },
    )
    error: list[OaiPmherrorType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
        },
    )
    identify: Optional[IdentifyType] = field(
        default=None,
        metadata={
            "name": "Identify",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
        },
    )
    list_metadata_formats: Optional[ListMetadataFormatsType] = field(
        default=None,
        metadata={
            "name": "ListMetadataFormats",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
        },
    )
    list_sets: Optional[ListSetsType] = field(
        default=None,
        metadata={
            "name": "ListSets",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
        },
    )
    get_record: Optional[GetRecordType] = field(
        default=None,
        metadata={
            "name": "GetRecord",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
        },
    )
    list_identifiers: Optional[ListIdentifiersType] = field(
        default=None,
        metadata={
            "name": "ListIdentifiers",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
        },
    )
    list_records: Optional[ListRecordsType] = field(
        default=None,
        metadata={
            "name": "ListRecords",
            "type": "Element",
            "namespace": "http://www.openarchives.org/OAI/2.0/",
        },
    )


@dataclass
class OaiPmh(OaiPmhtype):
    class Meta:
        name = "OAI-PMH"
        namespace = "http://www.openarchives.org/OAI/2.0/"
