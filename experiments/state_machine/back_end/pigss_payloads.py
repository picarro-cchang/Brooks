import attr

@attr.s
class PcSendPayload:
    message = attr.ib(str)
    timeout = attr.ib(1.0)

@attr.s
class PcResponsePayload:
    message = attr.ib(str)
