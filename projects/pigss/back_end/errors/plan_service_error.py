class PlanServiceException(Exception):
    pass

class PlanExistsException(PlanServiceException):
    pass

class PlanRunningException(PlanServiceException):
    pass

class PlanDoesNotExistException(PlanServiceException):
    pass
