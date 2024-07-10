import abc

class BaseIDP(abc.ABC):
  
  def get_project_list():
    pass

  def get_project_name(self, id, project_list=None):
    pass
  
  def get_parent_project_id_tree(project_id):
    pass

  def get_project_uuid_from_ident(project_ident):
    pass
