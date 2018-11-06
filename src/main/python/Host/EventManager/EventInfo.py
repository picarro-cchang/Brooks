
from Host.Common import SharedTypes #to get the right TCP port to use

class EventInfo(object):
    """The general class object for identifying event types - NOT discrete events.

    Discrete events (with time and other instance data) are captured with the
    EventLog class.

      Description = The text description of the event (eg: 'Application started')
      Level       = The severity of the event (from 0-3).  See below.
                      3 = Causes a performance hit or crash (eg: top level
                          exception trap, app restarted)
                      2 = Significant (eg: Conc Alarm occurred, Flow stopped, etc)
                      1 = info only; used to help with post-mortems (eg: Command
                          received)
                      0 = debug. ONLY for msg's that would normally be spam - only
                          send if debugging.  Please wrap with 'if __debug__'
      Code        = Numeric code for the event.  Should be unique across apps.
                      - A value of -1 is default and generic
      AccessLevel = Who should be able to see the event.
                       0 = Public... anyone can see
                       1 = Access level 1 (service tech?)
                     100 = Picarro only (the default)
                    eg: "Pump disabled" would be public
      VerboseDesc = A nice lengthy explanation of a pre-defined event.  This
                    should really not be used for one-time-only message events
                    that are created.
    """
    def __init__(self, Description, Data = "", Level = 1, Code = 0, AccessLevel = SharedTypes.ACCESS_PICARRO_ONLY,
                 VerboseDesc = ""):
        self.Description = Description
        self.Level = Level
        self.Code = Code      #Numeric code for the eventr.  Should be
        self.AccessLevel = AccessLevel  #
        self.VerboseDescription = VerboseDesc
        if self.AccessLevel < SharedTypes.ACCESS_PICARRO_ONLY:
            self.Public = True
        else:
            self.Public = False

    def __str__(self):
        if self.Code == 0:
            codeStr = "n/a"
        else:
            codeStr = str(self.Code)
        ret = "L%s | C%s | '%s'" % (self.Level, codeStr, self.Description)
        return ret