import datetime
import logging
import logging.config
import os
import sys
from ecmwf.opendata import Client
import NRUtil.NRObjStoreUtil as NRObjStoreUtil


mod = "ifs"
res = "0p25"
client = Client(
    source="ecmwf",
    model=mod,
    resol=res,
    preserve_request_order=False,
    infer_stream_keyword=True,
    )


iteratorlist = list(range(0,147,3))
iteratorlist = iteratorlist + list(range(144,246,6))
paramlist = ["2t","tp"]
modelrun = 0
dt=datetime.date.today()
dtstring = dt.strftime("%Y%m%d")

dirname = "ecmwfdata"
if not os.path.isdir(dirname):
    os.makedirs(dirname)

ostore = NRObjStoreUtil.ObjectStoreUtil()
for var in paramlist:
    for hr in iteratorlist:
        fname = f'ECMWF{mod}{modelrun:02}Z_{var}_{dtstring}_H{hr:02}.grib2'
        fpath = os.path.join(dirname,fname)
        objpath= os.path.join('ecmwf',f"{mod}{modelrun:02}Z",dtstring,fname)
        client.retrieve(
            date=dt,
            time=modelrun,
            step=hr,
            type="fc",
            param=var,
            target=fpath,)
        ostore.put_object(local_path=fpath, ostore_path=objpath)
        os.remove(fpath)
