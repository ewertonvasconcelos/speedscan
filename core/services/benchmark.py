#!/usr/bin/env python3
import time,psutil,pathlib
class DiskBenchmark:
    def sequential_test(self,size_mb=100):
        try:
            path=f"/tmp/sb_{int(time.time())}"
            start=time.time();open(path,'wb').write(b'X'*(size_mb*1024*1024));w_t=time.time()-start
            start=time.time();open(path,'rb').read();r_t=time.time()-start
            pathlib.Path(path).unlink(missing_ok=True)
            return{'write':f"{size_mb/w_t:.1f} MB/s",'read':f"{size_mb/r_t:.1f} MB/s"}
        except Exception as e:return{'error':str(e)[:80]}
