import os

def env(key, default=None):
    return os.getenv(key, default)

API_ID = int(env("API_ID", "28483345"))
API_HASH = env("API_HASH", "0b04eb0deb137eb4d75bda5ca0bc49e8")

MONGO_URL = env(
    "MONGO_URL",
    "mongodb+srv://anmol:gII62eQDVpFw1SlZ@cluster0.k30u3uc.mongodb.net/?appName=Cluster0"
)

BOT_TOKEN = env("BOT_TOKEN", "8467280293:AAGNiwcFcR8zPC2TWnDpignN6uS4PXHymYo")

OWNER_ID = [7113972959]

STRING_SESSION = env(
    "STRING_SESSION",
    "1BVtsOGsBuyes_CENppMDp6QgDcyGS6p77xBSA46k9ObMqZW2O37psCosZYVbWykE0S9FeMtTmkYCgRYBuzWUeeZSZ6x1VPIKbUpv-Ug4B-DNCqCaeqN6o5tj3VWxVFTafM3qiFfDoBtOqJn8CmFG5VDe2SrAhKnGJ7VpP3ffcIODiq5-A1aO0RTUqdtssc9wXuje22NxMjX28EBuAq7xvReXTfsCY9Djlhbt5uYAqRKJKI-648MZNxT1uQm0-TGwmOPktYxvBvv0s7ViqXa_Jvtk7lxehJXAHemT23xWni8fJD05X-9kokkLmxrZFeIZS1-LkYYwb8qK5_PXrZHUzkltlYVgf1U="
)
