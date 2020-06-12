import mischbares_small
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json
from movement_mecademic import Movements
import requests
import time