from importlib import import_module

import esi_leap.conf

CONF = esi_leap.conf.CONF

module_path, class_name = CONF.esi.idp_plugin_class.rsplit('.', 1)
module = import_module(module_path)
idp = getattr(module, class_name)()
