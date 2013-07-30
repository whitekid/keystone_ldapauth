# vim: tabstop=4 shiftwidth=4 softtabstop=4
from keystone.identity.backends import sql
from keystone import exception
from keystone import config
import ldap
import uuid
import logging

CONF = config.CONF
LOG = logging.getLogger(__name__)

config.register_str('url', group='ldap_auth', default='ldap://localhost')
config.register_str('ldap_postfix', group='ldap_auth', default='@yourcompany.com')
config.register_str('email_postfix', group='ldap_auth', default='@yourcompany.com')
config.register_str('default_project', group='ldap_auth', default='default')
config.register_str('member_role', group='ldap_auth', default='Member')

class Identity(sql.Identity):
    def _check_ldap_password(self, username, password):
        url = CONF.ldap.url
        conn = ldap.initialize(url)
        conn.protocol_version = ldap.VERSION3
        try:
            conn.simple_bind_s(username + CONF.ldap_auth.ldap_postfix, password)
            return True
        except ldap.INVALID_CREDENTIALS:
            LOG.debug('ldap.INVALID_CREDENTIALS for %s', username)
            raise AssertionError('Invalid user / password')
        except ldap.SERVER_DOWN:
            LOG.debug('ldap.SERVER_DOWN %s', url)
            raise AssertionError('Invalid user / password')


    def get_user_by_name(self, user_name, domain_id, password=None):
        try:
            return super(Identity, self).get_user_by_name(user_name, domain_id)
        except exception.UserNotFound:
            LOG.debug('LDAP success but not in SQL. Create new user')
            self._check_ldap_password(user_name, password):
            user_id = str(uuid.uuid4().hex)
            tenant_id = self.get_project_by_name(CONF.ldap_auth.default_project, domain_id)['id']
            roles = [x for x in self.list_roles() if x['name'] == CONF.ldap_auth.member_role]
            if len(roles) != 1:
                raise exception.RoleNotFound('role %s not found' % CONF.ldap_auth.member_role)
            role_id = roles[0]['id']

            user = {
                'id': user_id,
                'name': user_name,
                'domain_id': domain_id,
                'password': password,
                'enabled': True,
                'email': user_name + CONF.ldap_auth.email_postfix,
                'tenantId': tenant_id,
            }
            new_user = self.create_user(user_id, user)

            # grant default project
            self.create_grant(role_id, user_id, None, domain_id, tenant_id)

            return super(Identity, self).get_user_by_name(user_name, domain_id)

