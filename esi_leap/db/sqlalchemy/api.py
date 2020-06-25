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

import sys

from oslo_config import cfg
from oslo_db.sqlalchemy import session as db_session
from oslo_log import log as logging
from oslo_utils import uuidutils

import sqlalchemy as sa

from esi_leap.common import exception
from esi_leap.db.sqlalchemy import models
from esi_leap.resource_objects import resource_object_factory as ro_factory


CONF = cfg.CONF
LOG = logging.getLogger(__name__)
_engine_facade = None


def get_facade():
    global _engine_facade
    if not _engine_facade:
        _engine_facade = db_session.EngineFacade.from_config(CONF)

    return _engine_facade


def get_session():
    return get_facade().get_session()


def reset_facade():
    global _engine_facade
    _engine_facade = None


def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]


def setup_db():
    engine = get_facade().get_engine()
    models.Base.metadata.create_all(engine)
    return True


def drop_db():
    engine = db_session.EngineFacade(CONF.database.connection,
                                     sqlite_fk=True).get_engine()
    models.Base.metadata.drop_all(engine)
    return True


def model_query(model, session=None):
    """Query helper.

    :param model: base model to query
    """
    session = session or get_session()

    return session.query(model)


# Helpers for building constraints / equality checks


def constraint(**conditions):
    return Constraint(conditions)


def equal_any(*values):
    return EqualityCondition(values)


def not_equal(*values):
    return InequalityCondition(values)


class Constraint(object):
    def __init__(self, conditions):
        self.conditions = conditions

    def apply(self, model, query):
        for key, condition in self.conditions.items():
            for clause in condition.clauses(getattr(model, key)):
                query = query.filter(clause)
        return query


class EqualityCondition(object):
    def __init__(self, values):
        self.values = values

    def clauses(self, field):
        return sa.or_([field == value for value in self.values])


class InequalityCondition(object):
    def __init__(self, values):
        self.values = values

    def clauses(self, field):
        return [field != value for value in self.values]


# Offer
def offer_get(context, offer_uuid):
    query = model_query(models.Offer, get_session())
    result = query.filter_by(uuid=offer_uuid).first()
    if not result:
        raise exception.OfferNotFound(offer_uuid=offer_uuid)
    if not context.is_admin:
        if context.project_id != result.project_id:
            raise exception.OfferNoPermission(offer_uuid=offer_uuid)
    return result


def offer_get_all(context, filters):

    query = model_query(models.Offer, get_session())

    start = filters.pop('start_time', None)
    end = filters.pop('end_time', None)

    query = query.filter_by(**filters)

    if start and end:

        query = query.filter((start >= models.Offer.start_time) &
                             (end <= models.Offer.end_time))

    return query


def offer_create(context, values):
    resource_type = values.get('resource_type')
    resource_uuid = values.get('resource_uuid')
    resource = ro_factory.ResourceObjectFactory.get_resource_object(
        resource_type, resource_uuid)
    if not resource.is_resource_admin(context.project_id):
        raise exception.ResourceNoPermission(
            resource_type=resource_type, resource_uuid=resource_uuid)

    offer_ref = models.Offer()
    values['uuid'] = uuidutils.generate_uuid()
    values['project_id'] = context.project_id

    if 'start_time' in values and 'end_time' in values and \
       values['start_time'] is not None and values['end_time'] is not None and \
       values['start_time'] >= values['end_time']:
        raise exception.InvalidTimeRange(resource="an offer",
                                         start_time=str(values['start_time']),
                                         end_time=str(values['end_time']))

    offer_ref.update(values)
    offer_ref.save(get_session())
    return offer_ref


def offer_update(context, offer_uuid, values):
    offer_ref = offer_get(context, offer_uuid)
    if not context.is_admin:
        if context.project_id != offer_ref.project_id:
            raise exception.OfferNoPermission(offer_uuid=offer_uuid)

        resource = ro_factory.ResourceObjectFactory.get_resource_object(
            offer_ref.resource_type, offer_ref.resource_uuid)
        if not resource.is_resource_admin(context.project_id):
            raise exception.ResourceNoPermission(
                resource_type=offer_ref.resource_type,
                resource_uuid=offer_ref.resource_uuid)

    values.pop('uuid', None)
    values.pop('project_id', None)

    start = values.pop('start_time', None)
    end = values.pop('end_time', None)
    if start is None:
        start = offer_ref.start_time
    if end is None:
        end = offer_ref.end_time
    if start >= end:
        raise exception.InvalidTimeRange(resource="an offer",
                                         start_time=str(values['start_time']),
                                         end_time=str(values['end_time']))

    offer_ref.update(values)
    offer_ref.save(get_session())
    return offer_ref


def offer_destroy(context, offer_uuid):
    offer_ref = offer_get(context, offer_uuid)
    if not offer_ref:
        raise exception.OfferNotFound(offer_uuid=offer_uuid)
    if not context.is_admin:
        if context.project_id != offer_ref.project_id:
            raise exception.OfferNoPermission(offer_uuid=offer_uuid)
        resource = ro_factory.ResourceObjectFactory.get_resource_object(
            offer_ref.resource_type, offer_ref.resource_uuid)
        if not resource.is_resource_admin(context.project_id):
            raise exception.ResourceNoPermission(
                resource_type=offer_ref.resource_type,
                resource_uuid=offer_ref.resource_uuid)

    model_query(
        models.Offer,
        get_session()).filter_by(uuid=offer_uuid).delete()


# Contracts
def contract_get(context, contract_uuid):
    query = model_query(models.Contract, get_session())
    result = query.filter_by(uuid=contract_uuid).first()
    if not result:
        raise exception.ContractNotFound(contract_uuid=contract_uuid)
    if not context.is_admin:
        if context.project_id != result.project_id:
            raise exception.ContractNoPermission(contract_uuid=contract_uuid)
    return result


def contract_get_all(filters):
    query = model_query(models.Contract, get_session())

    start = filters.pop('start_time', None)
    end = filters.pop('end_time', None)
    owner = filters.pop('owner', None)

    query = query.filter_by(**filters)

    if start and end:
        query = query.filter((start >= models.Contract.start_time) &
                             (end <= models.Contract.end_time))

    if owner:
        query = query.join(models.Offer).\
            filter(models.Offer.project_id == owner)

    return query


def contract_create(context, values):
    contract_ref = models.Contract()
    values['uuid'] = uuidutils.generate_uuid()
    values['project_id'] = context.project_id

    if 'start_time' in values and 'end_time' in values and \
       values['start_time'] is not None and values['end_time'] is not None and \
       values['start_time'] >= values['end_time']:
        raise exception.InvalidTimeRange(resource="a contract",
                                         start_time=str(values['start_time']),
                                         end_time=str(values['end_time']))

    contract_ref.update(values)
    contract_ref.save(get_session())
    return contract_ref


def contract_update(context, contract_uuid, values):
    contract_ref = contract_get(context, contract_uuid)
    if not context.is_admin:
        if context.project_id != contract_ref.project_id:
            raise exception.ContractNoPermission(contract_uuid=contract_uuid)

    values.pop('uuid', None)
    values.pop('project_id', None)

    start = values.pop('start_time', None)
    end = values.pop('end_time', None)
    if start is None:
        start = contract_ref.start_time
    if end is None:
        end = contract_ref.end_time
    if start >= end:
        raise exception.InvalidTimeRange(resource="a contract",
                                         start_time=str(values['start_time']),
                                         end_time=str(values['end_time']))

    contract_ref.update(values)
    contract_ref.save(get_session())
    return contract_ref


def contract_destroy(context, contract_uuid):
    contract_ref = contract_get(context, contract_uuid)
    if not contract_ref:
        raise exception.ContractNotFound(contract_uuid=contract_uuid)
    if not context.is_admin:
        if context.project_id != contract_ref.project_id:
            raise exception.ContractNoPermission(contract_uuid=contract_uuid)
    model_query(
        models.Contract,
        get_session()).filter_by(uuid=contract_uuid).delete()
