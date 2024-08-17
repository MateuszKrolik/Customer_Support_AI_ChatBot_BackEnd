import os, sys
import shutil

from langchain_chroma import Chroma

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from get_embedding_func import get_embedding_func


class VectorStorageSingleton(object):
    VECTOR_STORAGE_ABSOLUTE_PATH = "../data/chroma"
    VECTOR_STORAGE_RELATIVE_PATH = "data/chroma"
    IS_DOCKER_IMAGE = bool(os.environ.get("IS_DOCKER_IMAGE", False))
    _instance = None

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            print('Creating new instance')
            cls._instance = cls.__new__(cls)
            # Put any initialization here.
            cls._instance.get_vector_storage = cls._initialize_vector_storage()
        return cls._instance

    @classmethod
    def _initialize_vector_storage(cls):
        if cls.IS_DOCKER_IMAGE:
            cls._copy_vector_storage_to_tmp()
        return Chroma(
            embedding_function=get_embedding_func(),
            persist_directory=cls._get_vector_storage_path(),
            collection_metadata={
                "hnsw:space": "cosine"
            }, )  # for relevance scores to be between 0-1

    @classmethod
    def _get_vector_storage_path(cls):
        if not cls.IS_DOCKER_IMAGE:
            return cls.VECTOR_STORAGE_ABSOLUTE_PATH
        else:
            return f"/tmp/{cls.VECTOR_STORAGE_ABSOLUTE_PATH}"

    # aws lambda only allows write access to "tmp/" dir
    @classmethod
    def _copy_vector_storage_to_tmp(cls):
        vector_storage_path = cls._get_vector_storage_path()
        if not os.path.exists(vector_storage_path):
            os.makedirs(vector_storage_path)

        tmp_contents = os.listdir(vector_storage_path)

        if not tmp_contents:
            print(f"copying vector storage to /tmp/...")
            os.makedirs(vector_storage_path, exist_ok=True)
            shutil.copytree(cls.VECTOR_STORAGE_RELATIVE_PATH, vector_storage_path, dirs_exist_ok=True)
        else:
            print(f"vector storage already exists in {vector_storage_path}")
