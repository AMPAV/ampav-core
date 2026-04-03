import torch

def get_devices() -> list:
    devs = []
    # nvidia & amd
    try:
        devs.extend([f"cuda:{i}" for i in range(torch.cuda.device_count())])
    except:
        pass

    # intel
    try:
        devs.extend([f"xpu:{i}" for i in range(torch.xpu.device_count())])
    except:
        pass

    # mac
    try:
        devs.extend([f"mps:{i}" for i in range(torch.mps.device_count())])
    except:
        pass

    # cpu fallback
    devs.append('cpu')
    return devs


def get_best_device():
    """The first device listed from get_devices should be the "best" of
    all of the options."""
    return get_devices()[0]