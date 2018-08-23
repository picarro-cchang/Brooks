from Host.Utilities.ExtLaserControl.ConfigValidator import CONFIG_SPEC
import configobj
import validate

class ConfigProcessor(object):
    def process_config(self, config_filename):
        try:
            self.config = configobj.ConfigObj(config_filename, configspec=CONFIG_SPEC.splitlines(), file_error=True)
            validator = validate.Validator()
            results = self.config.validate(validator, preserve_errors=True)
        except IOError:
            raise RuntimeError("Config file %s not found" % config_filename)
        except configobj.ConfigObjError, e:
            raise RuntimeError("Could not process configuration: %s" % (e,))
        if results != True:
            for (section_list, key, _) in configobj.flatten_errors(self.config, results):
                if key is not None:
                    raise RuntimeError('Config file %s\nThe "%s" key in the section "%s" failed validation' % (
                        config_filename, key, ', '.join(section_list)))
                else:
                    raise RuntimeError('Config file %s\nThe following section was missing:%s ' % ', '.join(
                        section_list))
        extra_values = configobj.get_extra_values(self.config)
        if extra_values:
            print "Config file extra_values: %s" % (extra_values, )

