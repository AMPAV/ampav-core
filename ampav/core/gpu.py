"""
GPU Utilities that tools might need. 

The functionality requires `torch`, but it will be loaded at use-time
since I don't want to bog down the startup time if someone isn't going
to use this functionality.

"""
from .utils import rgetattr, rsetattr


class ForceComputeDevice:
    def __init__(self, device="cpu"):
        """
        Force torch-based functionality to only use the device specified within
        this context
        
        :param device: Preferred device
        """
        import torch
        self.torch = torch
        self.device = device
        self.old_handlers = {}


    def __enter__(self):        
        # override is_available and device_count functions as necessary
        # ROCm (amd) overrides the cuda namespace
        overrides = {'cpu': ['accelerator', 'xpu', 'cuda', 'mps'],
                     'cuda': ['xpu', 'mps'], # nvidia (or AMD)
                     'mps': ['cuda', 'xpu'], # apple metal
                     'xpu': ['cuda', 'mps']} # intel 
        if self.device is not None:
            for dev, over in overrides.items():
                if self.device.startswith(dev):
                    for module in over:
                        for name, func in (('is_available', lambda: False),
                                        ('device_count', lambda: 0)):
                            attr = f"{module}.{name}"
                            try:
                                self.old_handlers[attr] = rgetattr(self.torch, attr)
                                rsetattr(self.torch, attr, func)
                            except:
                                pass


    def __exit__(self, exc_type, exc_value, traceback):
        # restore the original function handlers
        for attr, func in self.old_handlers.items():
            rsetattr(self.torch, attr, func)


if __name__ == "__main__":
    import torch
    for dev in ('accelerator', 'cpu', 'cuda', 'mps', 'xpu'):
        print(f"Device {dev}:")
        for dev2 in ('accelerator', 'cpu', 'cuda', 'mps', 'xpu'):
            print(f"\t{dev2} Is available (pre): ", rgetattr(torch, f"torch.{dev2}.is_available")())
            print(f"\t{dev2}Count: (pre)", rgetattr(torch, f"torch.{dev2}.device_count")())

        print(f"\tForced to {dev}:")
        with ForceComputeDevice(dev):
            for dev2 in ('accelerator', 'cpu', 'cuda', 'mps', 'xpu'):
                print(f"\t\t{dev2} Is available (forced): ", rgetattr(torch, f"torch.{dev2}.is_available")())
                print(f"\t\t{dev2}Count: (forced)", rgetattr(torch, f"torch.{dev2}.device_count")())
        
        for dev2 in ('accelerator', 'cpu', 'cuda', 'mps', 'xpu'):
            print(f"\t{dev2} Is available (post): ", rgetattr(torch, f"torch.{dev2}.is_available")())
            print(f"\t{dev2}Count: (post)", rgetattr(torch, f"torch.{dev2}.device_count")())