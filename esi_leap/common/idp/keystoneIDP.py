from keystoneauth1 import loading as ks_loading
from keystoneclient import client as keystone_client
from oslo_utils import uuidutils

from esi_leap.common import exception
import esi_leap.conf
from esi_leap.common.idp import baseIDP

CONF = esi_leap.conf.CONF
_cached_keystone_client = None
_cached_project_list = None

class KeystoneIDP(baseIDP.BaseIDP):
    
    def get_keystone_client(self):
        global _cached_keystone_client
        if _cached_keystone_client is not None:
            return _cached_keystone_client

        auth_plugin = ks_loading.load_auth_from_conf_options(CONF, 'keystone')
        sess = ks_loading.load_session_from_conf_options(CONF, 'keystone',
                                                        auth=auth_plugin)
        cli = keystone_client.Client(session=sess)
        _cached_keystone_client = cli

        return cli


    def get_parent_project_id_tree(self, project_id):
        ks_client = self.get_keystone_client()
        project = ks_client.projects.get(project_id)
        project_ids = [project.id]
        while project.parent_id is not None:
            project = ks_client.projects.get(project.parent_id)
            project_ids.append(project.id)
        return project_ids


    def get_project_uuid_from_ident(self, project_ident):
        if uuidutils.is_uuid_like(project_ident):
            return project_ident
        else:
            projects = self.get_keystone_client().projects.list(name=project_ident)
            if len(projects) > 0:
                # projects have unique names
                return projects[0].id
            raise exception.ProjectNoSuchName(name=project_ident)


    def get_project_list(self):
        return self.get_keystone_client().projects.list()


    def get_project_name(self, project_id, project_list=None):
        if project_id:
            if project_list is None:
                project = self.get_keystone_client().projects.get(project_id)
            else:
                project = next((p for p in project_list
                                if getattr(p, 'id') == project_id),
                            None)
            return project.name if project else ''
        else:
            return ''
