import torch
import torchvision
print(torch.cuda.is_available())
print(torch.version.cuda)
print(torch.__version__)
print(torchvision.__version__)

for i in range(torch.cuda.device_count()):
    print(f"Device {i}: {torch.cuda.get_device_name(i)}")