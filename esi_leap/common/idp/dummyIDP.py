#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from keystoneclient.v3.projects import Project
from keystoneclient.v3.projects import ProjectManager
from oslo_utils import uuidutils

from esi_leap.common import exception
from esi_leap.common.idp import baseIDP

dummy_project = Project(manager=ProjectManager, info={
    'id': 1,
    'name': 'test'
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
        
    def add_project(id, name):
        pass

    def add_user():
        pass
