"""Request validation/controller layer."""
from backend.models.project_model import save_project, get_project, list_projects, delete_project


def create_project(payload):
    return save_project(payload)


def update_project(project_id, payload):
    return save_project(payload, project_id=project_id)


def get_one(project_id):
    return get_project(project_id)


def get_many(search=""):
    return list_projects(search)


def remove(project_id):
    return delete_project(project_id)
