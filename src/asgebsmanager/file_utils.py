import os
from abc import ABC,abstractmethod
import time

def get_fs_util_for(filesystem,args):
    return eval(f'{filesystem.upper()}Util({args})')

class FsUtil(ABC):

    def wait_for_device(self, timeout=60, interval=5):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if os.path.exists(self.device):
                return True
            time.sleep(interval)
        return False

    @abstractmethod
    def format(self):
        raise NotImplementedError()
    
    @abstractmethod
    def mount(self):
        raise NotImplementedError()
    
    @abstractmethod
    def increase(self):
        raise NotImplementedError()

class XFSUtil(FsUtil):

    def __init__(self,args):
        self.device = args["device"] 
        self.mount_point = args["mount_point"]

    def format(self):
        is_xfs = os.system(f"blkid -t TYPE=xfs {self.device} > /dev/null 2>&1") == 0
        if not is_xfs:
            os.system(f"mkfs.xfs -f {self.device}")

    def mount(self):
        if not os.path.exists(self.mount_point):
            os.mkdir(self.mount_point)
        uuid = os.popen(f"blkid -s UUID -o value {self.device}").read().strip()
        with open('/etc/fstab', 'a') as f:
            f.write(f"UUID={uuid}\t{self.mount_point}\txfs\tdefaults\t0\t0\n")
        os.system(f"mount {self.device} {self.mount_point}")

    def increase(self):
        os.system(f"xfs_growfs {self.mount_point} > /dev/null 2>&1")