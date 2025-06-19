from functools import lru_cache

import b2sdk.v2 as b2

from config import config, logger


@lru_cache
def b2_api():
    logger.debug("Creating and authorizing B2 API")
    info = b2.InMemoryAccountInfo()
    b2_api = b2.B2Api(info)  # type: ignore

    b2_api.authorize_account("production", config.B2_KEY_ID, config.B2_APPLICATION_KEY)
    return b2_api


@lru_cache
def b2_get_bucket(api: b2.B2Api):
    return api.get_bucket_by_name(config.B2_BUCKET_NAME)  # type: ignore


def b2_upload_file(local_file: str, file_name: str) -> str:
    api = b2_api()
    logger.debug(f"Uploading {local_file} to B2 as {file_name}")

    upload_file = b2_get_bucket(api).upload_local_file(
        local_file=local_file, file_name=file_name
    )

    download_url = api.get_download_url_for_fileid(upload_file.id_)
    logger.debug(
        f"Uploaded {local_file} to B2 succesfully and got download url {download_url}"
    )

    return download_url
