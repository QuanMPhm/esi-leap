import os

from esi_leap.common.idp import keystoneIDP, dummyIDP

if os.environ.get('ESI_DEBUG', '') == 'True':
    idp = dummyIDP.DummyIDP()
else:
    idp = keystoneIDP.KeystoneIDP()
