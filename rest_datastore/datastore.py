from flask_security.datastore import Datastore, UserDatastore


class RESTDatastore(Datastore):

    def put(self, model):
        raise NotImplementedError

    def delete(self, model):
        raise NotImplementedError


class RESTUserDatastore(RESTDatastore, UserDatastore):

    def get_user(self, id_or_email):
        """Returns a user matching the specified ID or email address."""
        raise NotImplementedError

    def find_user(self, *args, **kwargs):
        """Returns a user matching the provided parameters."""
        raise NotImplementedError

    def find_role(self, *args, **kwargs):
        """Returns a role matching the provided name."""
        raise NotImplementedError
