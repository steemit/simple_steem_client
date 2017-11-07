
from simple_steem_client.client import SteemRemoteBackend, SteemInterface

import json

backend = SteemRemoteBackend(nodes=["http://127.0.0.1:9990/"], appbase=True)
steem = SteemInterface(backend)

dgpo = steem.database_api.get_dynamic_global_properties()

print("dgpo:", json.dumps(dgpo, separators=(",", ":")))
