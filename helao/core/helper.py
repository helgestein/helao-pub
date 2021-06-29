""" helpers.py
Miscellaneous helper functions.

"""
import os
import uuid
import shortuuid
import zipfile
from typing import Any
from asyncio import Queue


def gen_uuid(label: str, trunc: int = 8):
    "Generate a uuid, encode with larger character set, and trucate."
    uuid1 = uuid.uuid1()
    uuid3 = uuid.uuid3(uuid.NAMESPACE_URL, f"{uuid1}-{label}")
    short = shortuuid.encode(uuid3)[:trunc]
    return short


def rcp_to_dict(rcppath: str):  # read common info/rcp/exp/ana structure into dict
    dlist = []

    def tab_level(astr):
        """Count number of leading tabs in a string"""
        return (len(astr) - len(astr.lstrip("    "))) / 4

    if rcppath.endswith(".zip"):
        if "analysis" in os.path.dirname(rcppath):
            ext = ".ana"
        elif "experiment" in os.path.dirname(rcppath):
            ext = ".exp"
        else:
            ext = ".rcp"
        rcpfn = os.path.basename(rcppath).split(".copied")[0] + ext
        archive = zipfile.ZipFile(rcppath, "r")
        with archive.open(rcpfn, "r") as f:
            for l in f:
                k, v = l.decode("ascii").split(":", 1)
                lvl = tab_level(l.decode("ascii"))
                dlist.append({"name": k.strip(), "value": v.strip(), "level": lvl})
    else:
        with open(rcppath, "r") as f:
            for l in f:
                k, v = l.split(":", 1)
                lvl = tab_level(l)
                dlist.append({"name": k.strip(), "value": v.strip(), "level": lvl})

    def ttree_to_json(ttree, level=0):
        result = {}
        for i in range(0, len(ttree)):
            cn = ttree[i]
            try:
                nn = ttree[i + 1]
            except:
                nn = {"level": -1}

            # Edge cases
            if cn["level"] > level:
                continue
            if cn["level"] < level:
                return result
            # Recursion
            if nn["level"] == level:
                dict_insert_or_append(result, cn["name"], cn["value"])
            elif nn["level"] > level:
                rr = ttree_to_json(ttree[i + 1 :], level=nn["level"])
                dict_insert_or_append(result, cn["name"], rr)
            else:
                dict_insert_or_append(result, cn["name"], cn["value"])
                return result
        return result

    def dict_insert_or_append(adict, key, val):
        """Insert a value in dict at key if one does not exist
        Otherwise, convert value to list and append
        """
        if key in adict:
            if type(adict[key]) != list:
                adict[key] = [adict[key]]
            adict[key].append(val)
        else:
            adict[key] = val

    return ttree_to_json(dlist)


def dict_to_rcp(d: dict, level: int = 0):
    lines = []
    for k, v in d.items():
        if isinstance(v, dict):
            lines.append(f"{'    '*level}{k}:")
            lines.append(dict_to_rcp(v, level + 1))
        else:
            lines.append(f"{'    '*level}{k}: {str(v).strip()}")
    return "\n".join(lines)


# multisubscriber queue by Kyle Smith
# https://github.com/smithk86/asyncio-multisubscriber-queue
class MultisubscriberQueue(object):
    def __init__(self, **kwargs):
        """
        The constructor for MultisubscriberQueue class
        """
        super().__init__()
        self.subscribers = list()

    def __len__(self):
        return len(self.subscribers)

    def __contains__(self, q):
        return q in self.subscribers

    async def subscribe(self):
        """
        Subscribe to data using an async generator
        Instead of working with the Queue directly, the client can
        subscribe to data and have it yielded directly.
        Example:
            with MultisubscriberQueue.subscribe() as data:
                print(data)
        """
        with self.queue_context() as q:
            while True:
                val = await q.get()
                if val is StopAsyncIteration:
                    break
                else:
                    yield val

    def queue(self):
        """
        Get a new async Queue
        """
        q = Queue()
        self.subscribers.append(q)
        return q

    def queue_context(self):
        """
        Get a new queue context wrapper
        The queue context wrapper allows the queue to be automatically removed
        from the subscriber pool when the context is exited.
        Example:
            with MultisubscriberQueue.queue_context() as q:
                await q.get()
        """
        return _QueueContext(self)

    def remove(self, q):
        """
        Remove queue from the pool of subscribers
        """
        if q in self.subscribers:
            self.subscribers.remove(q)
        else:
            raise KeyError("subscriber queue does not exist")

    async def put(self, data: Any):
        """
        Put new data on all subscriber queues
        Parameters:
            data: queue data
        """
        for q in self.subscribers:
            await q.put(data)

    async def close(self):
        """
        Force clients using MultisubscriberQueue.subscribe() to end iteration
        """
        await self.put(StopAsyncIteration)


class _QueueContext(object):
    def __init__(self, parent):
        self.parent = parent
        self.queue = None

    def __enter__(self):
        self.queue = self.parent.queue()
        return self.queue

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.parent.remove(self.queue)


def eval_array(x):
    ret = []
    for y in x:
        nv = eval_val(y)
        ret.append(nv)
    return ret


def eval_val(x):
    if isinstance(x, list):
        nv = eval_array(x)
    elif isinstance(x, dict):
        nv = {k: eval_val(dk) for k,dk in x.items()}
    elif isinstance(x, str):
        if x.replace('.','',1).lstrip("-").isdigit():
            if '.' in x:
                nv = float(x)
            else:
                nv = int(x)
        else:
            nv = x
    else:
        nv = x 
    return nv