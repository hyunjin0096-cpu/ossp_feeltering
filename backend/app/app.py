from fastapi import FastAPI

app = FastAPI()

import torch
import torch.nn as nn

from torchvision import models

device = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
)

model = models.efficientnet_b0(
    weights=None
)