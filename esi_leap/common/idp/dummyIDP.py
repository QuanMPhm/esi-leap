from oslo_utils import uuidutils
from keystoneclient.v3.projects import Project, ProjectManager

from esi_leap.common import exception
from esi_leap.common.idp import baseIDP

dummy_project = Project(manager=ProjectManager, info={
    'id' : 1,
    'name' : 'test'
})

class DummyIDP(baseIDP.BaseIDP):

    def get_parent_project_id_tree(self, project_id):
        return [1]


    def get_project_uuid_from_ident(self, project_ident):
        if uuidutils.is_uuid_like(project_ident):
            return project_ident
        else:
            if project_ident == "test":
                return 1
            raise exception.ProjectNoSuchName(name=project_ident)


    def get_project_list(self):

        return [dummy_project]


    def get_project_name(self, project_id, project_list=None):
        if project_id == 1:
            return 'test'
        else:
            return ''
