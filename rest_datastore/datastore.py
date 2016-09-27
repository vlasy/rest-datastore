import requests
from flask_security.datastore import Datastore, UserDatastore
from flask_security.utils import get_identity_attributes
from flask.ext.security import UserMixin, RoleMixin


class RESTModel(dict):
    url = None

    def __getattr__(self, key):
        return self[key]


class RoleModel(RESTModel, RoleMixin):
    url = "role"


class UserModel(RESTModel, UserMixin):
    url = "user"

    def has_role(self, role):
        """Returns `True` if the user identifies with the specified role.

        :param role: A role name or `Role` instance"""
        if isinstance(role, str):
            return role in (role['name'] for role in self.roles)
        else:
            return role in self.roles


class RESTDatastore(Datastore):

    def __init__(self, api_url, db=None):
        Datastore.__init__(self, db)
        self._url = api_url

    def get(self, model, params):
        result = requests.get(self._url + '/' + model.url, params=params)
        if result.json()['_meta']['total'] > 0:
            return model(result.json()['_items'][0])
        return None

    def _prepare_role_modify_args(self, user, role):
        if isinstance(user, str):
            user = self.find_user(email=user)
        if isinstance(role, str):
            role = self.find_role(name=role)
        return user, role

    def add_role_to_user(self, user, role):
        """Adds a role to a user.

        :param user: The user to manipulate
        :param role: The role to add to the user
        """
        user, role = self._prepare_role_modify_args(user, role)
        if role not in user.roles:
            # update online repre
            requests.post(self._url + '/user/' + str(user['id']) +
                          '/roles', json=role)
            # update local repre
            user.roles.append(role)
            return True
        return False

    def remove_role_from_user(self, user, role):
        """Removes a role from a user.

        :param user: The user to manipulate
        :param role: The role to remove from the user
        """
        rv = False
        user, role = self._prepare_role_modify_args(user, role)
        if role.id in (role['id'] for role in user.roles):
            rv = True
            # update online repre
            requests.delete(self._url + '/user/' + str(user['id']) +
                            '/roles', json=role)
            # update local repre
            user.roles = [x for x in user.roles if x['id'] != role['id']]
        return rv

    def put(self, model):
        backup_roles = None
        if 'roles' in model.keys():
            backup_roles = list(model['roles'])
            model['roles'] = []  # prevent roles from being sent with user
        res = requests.post(self._url + '/' + model.url, json=model)
        model['id'] = res.json()['id']
        if backup_roles:
            for role in backup_roles:
                self.add_role_to_user(model, role)
        model['roles'] = backup_roles    # give roles back
        return model

    def delete(self, model):
        requests.delete(self._url + '/' + model.url, json=model)


class RESTUserDatastore(RESTDatastore, UserDatastore):

    def __init__(self, api_url):
        RESTDatastore.__init__(self, api_url)
        UserDatastore.__init__(self, UserModel, RoleModel)

    def get_user(self, id_or_email):
        """Returns a user matching the specified ID or email address."""
        if (isinstance(id_or_email, int)):  # id
            result = requests.get(self._url + '/' + UserModel.url +
                                  '/' + str(id_or_email))
            return UserModel(result.json())
        else:   # email
            for a in get_identity_attributes():
                # this will pass kwargs explicitly
                u = self.find_user(**{a: id_or_email})
                if u:
                    return u
            return None

    def find_user(self, *args, **kwargs):
        """Returns a user matching the provided parameters."""
        # TODO: merge it with solution from find_role so you can use
        # both args and kwargs - something like dict update or merge
        s = ""
        # print("find_user method")
        for key, val in kwargs.items():
            s += str(key) + "==\"" + str(val) + "\""
        query = {"where": s}
        # print(query)
        return self.get(UserModel, query)

    def find_role(self, *args, **kwargs):
        """Returns a role matching the provided name."""
        name = None
        if len(args) > 0:
            name = args[0]
        if not name and 'name' in kwargs.keys():
            name = kwargs['name']
        if not name:
            return
        # TODO: ok - this just works but its ugly!
        query = {"where": "name==" + name}
        return self.get(RoleModel, query)
